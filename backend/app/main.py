from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv
from datetime import datetime

from .database import engine, SessionLocal
from .models import Base, Prospectus, Property, Match
from .parsers.prospectus_parser import ProspectusParser
from .parsers.gsa_scraper import GSAScraper
from .matchers.property_matcher import PropertyMatcher
from .notion_sync import NotionSync

load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LeaseHawk MVP")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services lazily to avoid startup errors
parser = None
scraper = None
matcher = None
notion = None

def get_parser():
    global parser
    if parser is None:
        parser = ProspectusParser()
    return parser

def get_scraper():
    global scraper
    if scraper is None:
        scraper = GSAScraper()
    return scraper

def get_matcher():
    global matcher
    if matcher is None:
        matcher = PropertyMatcher()
    return matcher

def get_notion():
    global notion
    if notion is None:
        notion = NotionSync()
    return notion

@app.get("/")
def read_root():
    return {
        "name": "LeaseHawk MVP",
        "version": "0.1.0",
        "status": "operational"
    }

@app.post("/parse-prospectus/")
async def parse_prospectus(file: UploadFile = File(...)):
    """Upload and parse a GSA prospectus PDF"""
    
    # Save uploaded file
    file_path = f"data/prospectuses/{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Extract text and parse
    parser = get_parser()
    text = parser.extract_text_from_pdf(file_path)
    
    # Try LLM parsing first, fallback to regex
    try:
        data = parser.parse_with_llm(text)
    except Exception as e:
        print(f"LLM parsing failed: {e}")
        data = parser.quick_parse(text)
    
    # Save to database
    db = SessionLocal()
    prospectus = Prospectus(**data)
    db.add(prospectus)
    db.commit()
    db.refresh(prospectus)
    
    return {
        "message": "Prospectus parsed successfully",
        "data": data
    }

@app.get("/prospectuses/")
def get_prospectuses():
    """Get all parsed prospectuses"""
    db = SessionLocal()
    prospectuses = db.query(Prospectus).all()
    return prospectuses

@app.post("/match-properties/{prospectus_id}")
def match_properties(prospectus_id: int):
    """Find matching properties for a prospectus"""
    db = SessionLocal()
    
    # Get prospectus
    prospectus = db.query(Prospectus).filter(Prospectus.id == prospectus_id).first()
    if not prospectus:
        raise HTTPException(status_code=404, detail="Prospectus not found")
    
    # Get all properties (in production, filter by location)
    properties = db.query(Property).all()
    
    # Find matches
    matcher = get_matcher()
    matches = matcher.find_matches(
        prospectus.__dict__,
        [p.__dict__ for p in properties]
    )
    
    # Save matches to database
    for match in matches:
        db_match = Match(
            prospectus_id=prospectus_id,
            property_id=match['property']['id'],
            total_score=match['scores']['total_score'],
            size_score=match['scores']['size_score'],
            parking_score=match['scores']['parking_score'],
            price_score=match['scores']['price_score'],
            location_score=match['scores']['location_score']
        )
        db.add(db_match)
    
    db.commit()
    
    return {
        "prospectus_id": prospectus_id,
        "matches_found": len(matches),
        "top_matches": matches[:5]
    }

@app.get("/opportunities/")
def get_opportunities():
    """Get upcoming lease opportunities with match counts"""
    db = SessionLocal()
    
    opportunities = []
    prospectuses = db.query(Prospectus).filter(Prospectus.status == "active").all()
    
    for p in prospectuses:
        match_count = db.query(Match).filter(Match.prospectus_id == p.id).count()
        opportunities.append({
            "prospectus": p,
            "potential_matches": match_count,
            "days_until_expiration": (p.current_lease_expiration - datetime.utcnow()).days if p.current_lease_expiration else None
        })
    
    return opportunities

@app.post("/sync-from-notion/")
async def sync_from_notion():
    """Pull latest data from Notion databases"""
    db = SessionLocal()
    
    try:
        # Sync prospectuses
        notion = get_notion()
        notion_prospectuses = notion.get_prospectuses()
        prospectuses_synced = 0
        
        for np in notion_prospectuses:
            if not np.get("prospectus_number"):
                continue
                
            # Check if exists
            existing = db.query(Prospectus).filter(
                Prospectus.prospectus_number == np["prospectus_number"]
            ).first()
            
            if existing:
                # Update existing
                for key, value in np.items():
                    if key != "notion_id" and hasattr(existing, key):
                        setattr(existing, key, value)
            else:
                # Create new
                prospectus_data = {k: v for k, v in np.items() if k != "notion_id" and v is not None}
                prospectus = Prospectus(**prospectus_data)
                db.add(prospectus)
                prospectuses_synced += 1
        
        # Sync properties
        notion_properties = notion.get_properties()
        properties_synced = 0
        
        for nprop in notion_properties:
            if not nprop.get("address"):
                continue
                
            existing = db.query(Property).filter(
                Property.address == nprop["address"]
            ).first()
            
            if not existing:
                property_data = {k: v for k, v in nprop.items() if k != "notion_id" and v is not None}
                property = Property(**property_data)
                db.add(property)
                properties_synced += 1
        
        db.commit()
        
        return {
            "status": "success",
            "prospectuses_synced": prospectuses_synced,
            "properties_synced": properties_synced,
            "total_prospectuses": len(notion_prospectuses),
            "total_properties": len(notion_properties)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/push-match-to-notion/")
async def push_match_to_notion(prospectus_id: int, property_id: int):
    """Push a match score back to Notion"""
    db = SessionLocal()
    
    try:
        # Get the match
        match = db.query(Match).filter(
            Match.prospectus_id == prospectus_id,
            Match.property_id == property_id
        ).first()
        
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        # Get Notion IDs (we'll need to add these to our models)
        prospectus = db.query(Prospectus).filter(Prospectus.id == prospectus_id).first()
        property = db.query(Property).filter(Property.id == property_id).first()
        
        if not prospectus or not property:
            raise HTTPException(status_code=404, detail="Prospectus or property not found")
        
        # For now, we'll use the prospectus number as a fallback
        # In production, you'd store Notion IDs in your database
        notion = get_notion()
        notion.update_match_score(
            prospectus.prospectus_number,  # This should be notion_id
            str(property.id),  # This should be notion_id
            match.total_score
        )
        
        return {"status": "success", "score_updated": match.total_score}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/upload-pdf-to-notion/")
async def upload_pdf_to_notion(file: UploadFile = File(...)):
    """Parse PDF and create entry in Notion"""
    
    try:
        # First parse the PDF (same as existing endpoint)
        file_path = f"data/prospectuses/{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Extract and parse
        parser = get_parser()
        text = parser.extract_text_from_pdf(file_path)
        
        # Try LLM parsing first, fallback to regex
        try:
            data = parser.parse_with_llm(text)
        except Exception as e:
            print(f"LLM parsing failed: {e}")
            data = parser.quick_parse(text)
        
        # Create in Notion
        notion = get_notion()
        notion_id = notion.add_prospectus(data)
        
        # Also save to local database
        db = SessionLocal()
        prospectus = Prospectus(**data)
        db.add(prospectus)
        db.commit()
        db.refresh(prospectus)
        db.close()
        
        return {
            "status": "success",
            "notion_id": notion_id,
            "local_id": prospectus.id,
            "data": data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
