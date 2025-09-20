#!/usr/bin/env python3
"""
Quick loader script to fetch and load all GSA prospectuses
Downloads PDFs, parses them, and loads into database and Notion
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse
from pathlib import Path
import concurrent.futures
from threading import Lock

from app.parsers.gsa_scraper import GSAScraper
from app.parsers.prospectus_parser import ProspectusParser
from app.notion_sync import NotionSync
from app.database import SessionLocal, engine
from app.models import Base, Prospectus

# Thread-safe counter
class Counter:
    def __init__(self):
        self._value = 0
        self._lock = Lock()
    
    def increment(self):
        with self._lock:
            self._value += 1
            return self._value
    
    @property
    def value(self):
        return self._value

def setup_directories():
    """Create necessary directories"""
    Path("data/prospectuses").mkdir(parents=True, exist_ok=True)
    Path("data/exports").mkdir(parents=True, exist_ok=True)

def download_pdf(url: str, filename: str, retries: int = 3) -> bool:
    """Download a PDF file with retry logic"""
    filepath = f"data/prospectuses/{filename}"
    
    # Skip if already exists
    if os.path.exists(filepath):
        return True
    
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
            
        except Exception as e:
            print(f"❌ Download attempt {attempt + 1} failed for {filename}: {e}")
            if attempt < retries - 1:
                time.sleep(2)
    
    return False

def process_prospectus(prospectus_info: dict, parser: ProspectusParser, 
                      notion: NotionSync, counter: Counter) -> dict:
    """Process a single prospectus: download, parse, store"""
    
    result = {
        'title': prospectus_info['title'],
        'url': prospectus_info['url'],
        'success': False,
        'error': None,
        'data': None
    }
    
    try:
        # Create safe filename
        safe_title = "".join(c for c in prospectus_info['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title[:50]}.pdf"
        
        # Download PDF
        print(f"📥 Downloading: {safe_title[:60]}...")
        if not download_pdf(prospectus_info['url'], filename):
            result['error'] = "Download failed"
            return result
        
        # Parse PDF
        filepath = f"data/prospectuses/{filename}"
        text = parser.extract_text_from_pdf(filepath)
        
        # Try LLM parsing first, fallback to quick parse
        try:
            data = parser.parse_with_llm(text)
        except Exception as e:
            print(f"⚠️  LLM parsing failed for {filename}, using quick parse: {e}")
            data = parser.quick_parse(text)
        
        # Add metadata
        data['pdf_url'] = prospectus_info['url']
        data['status'] = 'active'
        
        result['data'] = data
        result['success'] = True
        
        count = counter.increment()
        print(f"✅ [{count}] Parsed: {data.get('prospectus_number', 'Unknown')} - {data.get('location', 'Unknown')}")
        
        return result
        
    except Exception as e:
        result['error'] = str(e)
        print(f"❌ Error processing {prospectus_info['title']}: {e}")
        return result

def get_all_gsa_prospectuses():
    """Get prospectuses from multiple GSA sources"""
    prospectuses = []
    
    # Source 1: GSA Prospectus Library (Enhanced)
    print("🔍 Searching GSA Prospectus Library...")
    
    # Multiple year prospectus pages
    prospectus_urls = [
        "https://www.gsa.gov/real-estate/gsa-properties/capital-investment-and-leasing-prospectus-library/2025-prospectus",
        "https://www.gsa.gov/real-estate/gsa-properties/capital-investment-and-leasing-prospectus-library/2024-prospectus",
        "https://www.gsa.gov/real-estate/gsa-properties/capital-investment-and-leasing-prospectus-library/2023-prospectus"
    ]
    
    for url in prospectus_urls:
        try:
            print(f"   Scanning {url.split('/')[-1]}...")
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all PDF links
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.text.strip()
                
                # Look for prospectus PDFs
                if (('.pdf' in href.lower()) and 
                    ('lease' in text.lower() or 'prospectus' in text.lower() or 
                     'va' in text.lower() or 'gsa' in text.lower())):
                    
                    pdf_url = f"https://www.gsa.gov{href}" if not href.startswith('http') else href
                    
                    prospectuses.append({
                        'title': text,
                        'url': pdf_url,
                        'date_found': datetime.utcnow().isoformat(),
                        'source': url.split('/')[-1]
                    })
            
        except Exception as e:
            print(f"⚠️  Failed to scrape {url}: {e}")
    
    # Source 2: Known high-value VA opportunities
    va_opportunities = [
        {
            'title': 'VA Medical Center Franklin County OH - POH-09-VA25',
            'url': 'https://www.gsa.gov/cdnstatic/POH-09-VA25_Franklin_County_OH.pdf',
            'date_found': datetime.utcnow().isoformat(),
            'source': 'manual_va_targets'
        },
        {
            'title': 'VA Medical Center Salt Lake City UT - PUT-24-VA25',
            'url': 'https://www.gsa.gov/cdnstatic/PUT-24-VA25_Salt_Lake_City_UT.pdf',
            'date_found': datetime.utcnow().isoformat(),
            'source': 'manual_va_targets'
        }
    ]
    
    prospectuses.extend(va_opportunities)
    
    # Source 3: D2D Pipeline (if available)
    try:
        pipeline_prospectuses = get_d2d_pipeline_data()
        prospectuses.extend(pipeline_prospectuses)
        print(f"✅ Found {len(pipeline_prospectuses)} from D2D pipeline")
    except Exception as e:
        print(f"⚠️  D2D pipeline access failed: {e}")
    
    # Remove duplicates
    unique_prospectuses = []
    seen_urls = set()
    
    for p in prospectuses:
        if p['url'] not in seen_urls:
            unique_prospectuses.append(p)
            seen_urls.add(p['url'])
    
    print(f"📋 Total unique prospectuses to process: {len(unique_prospectuses)}")
    return unique_prospectuses

def get_d2d_pipeline_data():
    """Get prospectus data from d2d.gsa.gov pipeline"""
    # This would scrape or use API to get upcoming opportunities
    # For now, return empty list
    return []

def load_to_database(parsed_data: list):
    """Load parsed data into local database"""
    print("\n💾 Loading data into database...")
    
    db = SessionLocal()
    loaded_count = 0
    
    try:
        for item in parsed_data:
            if not item['success'] or not item['data']:
                continue
            
            data = item['data']
            
            # Check if already exists
            existing = db.query(Prospectus).filter(
                Prospectus.prospectus_number == data.get('prospectus_number')
            ).first()
            
            if existing:
                print(f"⚠️  Skipping duplicate: {data.get('prospectus_number')}")
                continue
            
            # Create new prospectus
            try:
                prospectus = Prospectus(**data)
                db.add(prospectus)
                loaded_count += 1
            except Exception as e:
                print(f"❌ Error creating prospectus from data: {e}")
                print(f"   Data keys: {list(data.keys())}")
                continue
        
        db.commit()
        print(f"✅ Loaded {loaded_count} prospectuses into database")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        db.rollback()
    finally:
        db.close()
    
    return loaded_count

def load_to_notion(parsed_data: list, notion: NotionSync):
    """Load parsed data into Notion"""
    print("\n☁️  Loading data into Notion...")
    
    loaded_count = 0
    
    for item in parsed_data:
        if not item['success'] or not item['data']:
            continue
        
        try:
            notion_id = notion.add_prospectus(item['data'])
            if notion_id:
                loaded_count += 1
                print(f"✅ Added to Notion: {item['data'].get('prospectus_number')}")
        except Exception as e:
            print(f"❌ Notion error for {item['data'].get('prospectus_number')}: {e}")
    
    print(f"✅ Loaded {loaded_count} prospectuses into Notion")
    return loaded_count

def main():
    """Main loader function"""
    print("🦅 GSA Prospectus Bulk Loader")
    print("=" * 60)
    
    # Setup
    setup_directories()
    Base.metadata.create_all(bind=engine)
    
    # Initialize services
    parser = ProspectusParser()
    notion = NotionSync()
    counter = Counter()
    
    # Get all prospectuses
    prospectuses = get_all_gsa_prospectuses()
    
    if not prospectuses:
        print("❌ No prospectuses found to process")
        return
    
    # Process prospectuses in parallel
    print(f"\n🔄 Processing {len(prospectuses)} prospectuses...")
    start_time = time.time()
    
    parsed_results = []
    
    # Use ThreadPoolExecutor for parallel processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_prospectus = {
            executor.submit(process_prospectus, p, parser, notion, counter): p 
            for p in prospectuses
        }
        
        for future in concurrent.futures.as_completed(future_to_prospectus):
            result = future.result()
            parsed_results.append(result)
    
    processing_time = time.time() - start_time
    
    # Count results
    successful = [r for r in parsed_results if r['success']]
    failed = [r for r in parsed_results if not r['success']]
    
    print(f"\n📊 Processing Complete!")
    print(f"⏱️  Time: {processing_time:.1f} seconds")
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    
    if failed:
        print("\n❌ Failed items:")
        for item in failed:
            print(f"   • {item['title'][:50]} - {item['error']}")
    
    # Load into database
    if successful:
        db_count = load_to_database(successful)
        
        # Load into Notion (optional, can be slow)
        try:
            notion_count = load_to_notion(successful, notion)
        except Exception as e:
            print(f"⚠️  Notion loading failed: {e}")
            notion_count = 0
        
        # Summary
        print(f"\n🎉 Final Results:")
        print(f"   Processed: {len(successful)} prospectuses")
        print(f"   Database: {db_count} loaded")
        print(f"   Notion: {notion_count} loaded")
        
        # Calculate potential value
        total_value = 0
        high_value_count = 0
        
        for item in successful:
            if item['data'] and item['data'].get('estimated_annual_cost'):
                value = item['data']['estimated_annual_cost']
                total_value += value
                if value > 5000000:  # $5M+
                    high_value_count += 1
        
        if total_value > 0:
            print(f"\n💰 Opportunity Analysis:")
            print(f"   Total Annual Value: ${total_value:,.0f}")
            print(f"   High-Value (>$5M): {high_value_count}")
            print(f"   Potential Fees (2%): ${total_value * 0.02:,.0f}")
    
    print("\n🚀 Next Steps:")
    print("1. Run property matching: python scripts/complete_workflow.py --full")
    print("2. Start Notion watcher: python -c \"from app.notion_watcher import start_notion_watcher; start_notion_watcher()\"")
    print("3. Start API server: uvicorn app.main:app --reload")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load all GSA prospectuses")
    parser.add_argument("--no-notion", action="store_true", help="Skip Notion upload")
    parser.add_argument("--max-count", type=int, help="Maximum number to process (for testing)")
    
    args = parser.parse_args()
    
    main()