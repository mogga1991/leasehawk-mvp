from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

# Mount static files (frontend)
frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
frontend_path = os.path.abspath(frontend_path)
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

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
    # Serve the frontend index.html at root
    frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
    frontend_path = os.path.abspath(frontend_path)
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {
            "name": "LeaseHawk MVP",
            "version": "0.1.0",
            "status": "operational",
            "message": "Frontend files not found"
        }

@app.get("/api/status")
def api_status():
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
    
    # Return sample matches for demo purposes
    sample_matches = [
        {
            "property": {
                "id": 1,
                "address": "1600 Pennsylvania Ave NW, Washington, DC",
                "available_sqft": 45000,
                "asking_rent_per_sqft": 55,
                "latitude": 38.8977,
                "longitude": -77.0365
            },
            "scores": {
                "total_score": 92,
                "size_score": 95,
                "location_score": 88,
                "price_score": 94,
                "parking_score": 90
            }
        },
        {
            "property": {
                "id": 2,
                "address": "2000 M Street NW, Washington, DC",
                "available_sqft": 42000,
                "asking_rent_per_sqft": 52,
                "latitude": 38.9055,
                "longitude": -77.0459
            },
            "scores": {
                "total_score": 87,
                "size_score": 88,
                "location_score": 85,
                "price_score": 89,
                "parking_score": 85
            }
        },
        {
            "property": {
                "id": 3,
                "address": "1900 K Street NW, Washington, DC",
                "available_sqft": 48000,
                "asking_rent_per_sqft": 58,
                "latitude": 38.9017,
                "longitude": -77.0430
            },
            "scores": {
                "total_score": 84,
                "size_score": 92,
                "location_score": 82,
                "price_score": 78,
                "parking_score": 88
            }
        }
    ]
    
    return {
        "prospectus_id": prospectus_id,
        "matches_found": len(sample_matches),
        "top_matches": sample_matches
    }

@app.get("/opportunities/")
def get_opportunities():
    """Get upcoming lease opportunities with match counts"""
    db = SessionLocal()
    
    opportunities = []
    prospectuses = db.query(Prospectus).all()
    
    # If no data in database, return sample data for demo
    if not prospectuses:
        sample_opportunities = [
            {
                "prospectus": {
                    "id": 1,
                    "agency": "Department of Veterans Affairs",
                    "location": "Washington, DC",
                    "estimated_nusf": 45000,
                    "estimated_annual_cost": 2250000,
                    "lease_term": 10,
                    "status": "active",
                    "prospectus_number": "DC-2024-001"
                },
                "potential_matches": 8,
                "days_until_expiration": 45
            },
            {
                "prospectus": {
                    "id": 2,
                    "agency": "Social Security Administration",
                    "location": "Baltimore, MD",
                    "estimated_nusf": 32000,
                    "estimated_annual_cost": 1600000,
                    "lease_term": 15,
                    "status": "active",
                    "prospectus_number": "MD-2024-002"
                },
                "potential_matches": 5,
                "days_until_expiration": 72
            },
            {
                "prospectus": {
                    "id": 3,
                    "agency": "Environmental Protection Agency",
                    "location": "Denver, CO",
                    "estimated_nusf": 28000,
                    "estimated_annual_cost": 1120000,
                    "lease_term": 10,
                    "status": "active",
                    "prospectus_number": "CO-2024-003"
                },
                "potential_matches": 12,
                "days_until_expiration": 90
            }
        ]
        return sample_opportunities
    
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

# Catch-all route to serve frontend for SPA routing
@app.get("/{full_path:path}")
def catch_all(full_path: str):
    # Don't interfere with API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Serve static files
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
    file_path = os.path.join(frontend_path, full_path)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # For everything else, serve index.html (SPA routing)
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    raise HTTPException(status_code=404, detail="Page not found")

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

# Catch-all route to serve frontend for SPA routing
@app.get("/{full_path:path}")
def catch_all(full_path: str):
    # Don't interfere with API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Serve static files
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
    file_path = os.path.join(frontend_path, full_path)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # For everything else, serve index.html (SPA routing)
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    raise HTTPException(status_code=404, detail="Page not found")
