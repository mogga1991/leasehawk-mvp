from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
import os
import requests
import urllib.parse
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
frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "frontend")
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
    frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "frontend")
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
    
    try:
        opportunities = []
        prospectuses = db.query(Prospectus).filter(Prospectus.status == "active").all()
        
        for p in prospectuses:
            match_count = db.query(Match).filter(Match.prospectus_id == p.id).count()
            top_matches = db.query(Match).filter(Match.prospectus_id == p.id).order_by(Match.total_score.desc()).limit(3).all()
            
            # Calculate days until expiration
            days_until_expiration = None
            if p.current_lease_expiration:
                days_until_expiration = (p.current_lease_expiration - datetime.utcnow()).days
            
            opportunity = {
                "id": p.id,
                "prospectus_number": p.prospectus_number,
                "agency": p.agency,
                "location": p.location,
                "state": p.state,
                "estimated_nusf": p.estimated_nusf,
                "estimated_annual_cost": p.estimated_annual_cost,
                "rental_rate_per_nusf": p.rental_rate_per_nusf,
                "current_lease_expiration": p.current_lease_expiration.isoformat() if p.current_lease_expiration else None,
                "parking_spaces": p.parking_spaces,
                "special_requirements": p.special_requirements,
                "status": p.status,
                "potential_matches": match_count,
                "days_until_expiration": days_until_expiration,
                "top_matches": [
                    {
                        "match_id": m.id,
                        "property_id": m.property_id,
                        "total_score": m.total_score,
                        "notes": m.notes
                    } for m in top_matches
                ]
            }
            opportunities.append(opportunity)
        
        # Sort by urgency (soonest expiration first)
        opportunities.sort(key=lambda x: x["days_until_expiration"] if x["days_until_expiration"] is not None else 999999)
        
        return {
            "status": "success",
            "count": len(opportunities),
            "opportunities": opportunities
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/gsa-pipeline/")
def get_gsa_pipeline():
    """Get GSA prospectuses pipeline data optimized for dashboard display"""
    db = SessionLocal()
    
    try:
        # Get all active prospectuses with match data
        prospectuses = db.query(Prospectus).filter(Prospectus.status == "active").all()
        
        pipeline_data = []
        total_value = 0
        
        for p in prospectuses:
            # Get match statistics
            matches = db.query(Match).filter(Match.prospectus_id == p.id).all()
            match_count = len(matches)
            avg_score = sum(m.total_score for m in matches) / match_count if matches else 0
            best_score = max(m.total_score for m in matches) if matches else 0
            
            # Calculate urgency score (days until expiration)
            urgency_score = "Low"
            if p.current_lease_expiration:
                days_left = (p.current_lease_expiration - datetime.utcnow()).days
                if days_left <= 90:
                    urgency_score = "High"
                elif days_left <= 180:
                    urgency_score = "Medium"
            
            pipeline_item = {
                "id": p.id,
                "prospectus_number": p.prospectus_number,
                "agency": p.agency,
                "location": f"{p.location}, {p.state}",
                "square_footage": p.estimated_nusf,
                "annual_value": p.estimated_annual_cost,
                "lease_expiration": p.current_lease_expiration.strftime("%Y-%m-%d") if p.current_lease_expiration else "TBD",
                "days_until_expiration": (p.current_lease_expiration - datetime.utcnow()).days if p.current_lease_expiration else None,
                "urgency": urgency_score,
                "match_count": match_count,
                "best_match_score": round(best_score * 100, 1) if best_score > 0 else 0,
                "avg_match_score": round(avg_score * 100, 1) if avg_score > 0 else 0,
                "parking_required": p.parking_spaces,
                "special_requirements": p.special_requirements[:100] + "..." if p.special_requirements and len(p.special_requirements) > 100 else p.special_requirements
            }
            
            pipeline_data.append(pipeline_item)
            if p.estimated_annual_cost:
                total_value += p.estimated_annual_cost
        
        # Sort by urgency and value
        pipeline_data.sort(key=lambda x: (
            0 if x["urgency"] == "High" else 1 if x["urgency"] == "Medium" else 2,
            -x["annual_value"] if x["annual_value"] else 0
        ))
        
        return {
            "status": "success",
            "pipeline_summary": {
                "total_opportunities": len(pipeline_data),
                "total_annual_value": total_value,
                "high_urgency": len([p for p in pipeline_data if p["urgency"] == "High"]),
                "medium_urgency": len([p for p in pipeline_data if p["urgency"] == "Medium"]),
                "low_urgency": len([p for p in pipeline_data if p["urgency"] == "Low"])
            },
            "opportunities": pipeline_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/dashboard-stats/")
def get_dashboard_stats():
    """Get key statistics for dashboard"""
    db = SessionLocal()
    
    try:
        # Count totals
        total_prospectuses = db.query(Prospectus).filter(Prospectus.status == "active").count()
        total_properties = db.query(Property).count()
        total_matches = db.query(Match).count()
        
        # Calculate total pipeline value
        pipeline_value = db.query(Prospectus).filter(
            Prospectus.status == "active",
            Prospectus.estimated_annual_cost.isnot(None)
        ).all()
        total_value = sum(p.estimated_annual_cost for p in pipeline_value)
        
        # Get urgency breakdown
        high_urgency = 0
        medium_urgency = 0
        for p in db.query(Prospectus).filter(Prospectus.status == "active").all():
            if p.current_lease_expiration:
                days_left = (p.current_lease_expiration - datetime.utcnow()).days
                if days_left <= 90:
                    high_urgency += 1
                elif days_left <= 180:
                    medium_urgency += 1
        
        # Get top matches
        top_matches = db.query(Match).order_by(Match.total_score.desc()).limit(5).all()
        
        return {
            "status": "success",
            "stats": {
                "total_opportunities": total_prospectuses,
                "total_properties": total_properties,
                "total_matches": total_matches,
                "pipeline_value": total_value,
                "high_urgency_count": high_urgency,
                "medium_urgency_count": medium_urgency,
                "top_match_score": round(top_matches[0].total_score * 100, 1) if top_matches else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

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

# Serve static frontend files
@app.get("/app.js")
def serve_app_js():
    frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "frontend")
    js_path = os.path.join(frontend_path, "app.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/style.css")
def serve_style_css():
    frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "frontend")
    css_path = os.path.join(frontend_path, "style.css")
    if os.path.exists(css_path):
        return FileResponse(css_path, media_type="text/css")
    raise HTTPException(status_code=404, detail="File not found")

# Catch-all route to serve frontend for SPA routing
@app.get("/{full_path:path}")
def catch_all(full_path: str):
    # Don't interfere with API routes or auth routes
    if full_path.startswith("api/") or full_path.startswith("auth/"):
        raise HTTPException(status_code=404, detail="Endpoint not found")
    
    # Serve specific static files
    frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "frontend")
    frontend_path = os.path.abspath(frontend_path)
    file_path = os.path.join(frontend_path, full_path)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # For everything else, serve index.html (SPA routing)
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    raise HTTPException(status_code=404, detail="Page not found")

