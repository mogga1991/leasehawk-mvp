from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import sys
from datetime import datetime

# Add the backend directory to the path so we can import our modules
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend")
sys.path.append(backend_path)

from backend.app.database import engine, SessionLocal
from backend.app.models import Base, Prospectus, Property, Match

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LeaseHawk MVP - Production")

# Configure CORS for Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "name": "LeaseHawk MVP",
        "version": "0.1.0",
        "status": "operational",
        "environment": "production"
    }

@app.get("/api/status")
def api_status():
    return {
        "name": "LeaseHawk MVP",
        "version": "0.1.0",
        "status": "operational",
        "environment": "production"
    }

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

@app.get("/prospectuses/")
def get_prospectuses():
    """Get all parsed prospectuses"""
    db = SessionLocal()
    
    try:
        prospectuses = db.query(Prospectus).all()
        # Convert to dict format for JSON serialization
        result = []
        for p in prospectuses:
            prospectus_dict = {
                "id": p.id,
                "prospectus_number": p.prospectus_number,
                "agency": p.agency,
                "location": p.location,
                "state": p.state,
                "current_nusf": p.current_nusf,
                "estimated_nusf": p.estimated_nusf,
                "estimated_rsf": p.estimated_rsf,
                "estimated_annual_cost": p.estimated_annual_cost,
                "rental_rate_per_nusf": p.rental_rate_per_nusf,
                "current_lease_expiration": p.current_lease_expiration.isoformat() if p.current_lease_expiration else None,
                "prospectus_date": p.prospectus_date.isoformat() if p.prospectus_date else None,
                "parking_spaces": p.parking_spaces,
                "special_requirements": p.special_requirements,
                "status": p.status
            }
            result.append(prospectus_dict)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/properties/")
def get_properties():
    """Get all properties"""
    db = SessionLocal()
    
    try:
        properties = db.query(Property).all()
        result = []
        for p in properties:
            property_dict = {
                "id": p.id,
                "address": p.address,
                "city": p.city,
                "state": p.state,
                "zip_code": p.zip_code,
                "total_sqft": p.total_sqft,
                "available_sqft": p.available_sqft,
                "parking_spaces": p.parking_spaces,
                "year_built": p.year_built,
                "asking_rent_per_sqft": p.asking_rent_per_sqft,
                "source": p.source
            }
            result.append(property_dict)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/matches/")
def get_matches():
    """Get all matches with prospectus and property details"""
    db = SessionLocal()
    
    try:
        matches = db.query(Match).all()
        result = []
        for m in matches:
            # Get prospectus and property details
            prospectus = db.query(Prospectus).filter(Prospectus.id == m.prospectus_id).first()
            property = db.query(Property).filter(Property.id == m.property_id).first()
            
            match_dict = {
                "id": m.id,
                "prospectus_id": m.prospectus_id,
                "property_id": m.property_id,
                "total_score": m.total_score,
                "size_score": m.size_score,
                "location_score": m.location_score,
                "parking_score": m.parking_score,
                "price_score": m.price_score,
                "notes": m.notes,
                "status": m.status,
                "prospectus": {
                    "prospectus_number": prospectus.prospectus_number if prospectus else None,
                    "agency": prospectus.agency if prospectus else None,
                    "location": prospectus.location if prospectus else None,
                } if prospectus else None,
                "property": {
                    "address": property.address if property else None,
                    "city": property.city if property else None,
                    "state": property.state if property else None,
                } if property else None
            }
            result.append(match_dict)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()