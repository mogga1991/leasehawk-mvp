#!/usr/bin/env python3
"""
Script to seed Neon database with sample GSA prospectus data
"""
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.models import Prospectus, Property, Match

def create_sample_prospectuses():
    """Create sample GSA prospectus data"""
    
    sample_prospectuses = [
        {
            "prospectus_number": "GSA-R11-PX-22-000123",
            "agency": "Social Security Administration",
            "location": "Atlanta, GA",
            "state": "GA",
            "current_nusf": 45000,
            "estimated_nusf": 50000,
            "estimated_rsf": 75000,
            "expansion_nusf": 5000,
            "estimated_annual_cost": 1250000.00,
            "rental_rate_per_nusf": 25.00,
            "current_annual_cost": 1125000.00,
            "current_lease_expiration": datetime.now() + timedelta(days=180),
            "prospectus_date": datetime.now() - timedelta(days=30),
            "max_lease_term_years": 20,
            "delineated_area": {
                "north": "I-285 Perimeter",
                "south": "I-20",
                "east": "I-285 East",
                "west": "I-285 West"
            },
            "parking_spaces": 200,
            "special_requirements": "Must meet Level IV security requirements, backup power generation required",
            "scoring_type": "technical_and_cost",
            "energy_requirements": "LEED Gold certification preferred, Energy Star rated equipment required",
            "pdf_url": "https://gsa.gov/prospectuses/2024/SSA-Atlanta-RFP.pdf",
            "status": "active"
        },
        {
            "prospectus_number": "GSA-R03-PX-22-000456",
            "agency": "Department of Veterans Affairs",
            "location": "Philadelphia, PA",
            "state": "PA",
            "current_nusf": 32000,
            "estimated_nusf": 35000,
            "estimated_rsf": 52500,
            "expansion_nusf": 3000,
            "estimated_annual_cost": 875000.00,
            "rental_rate_per_nusf": 25.00,
            "current_annual_cost": 800000.00,
            "current_lease_expiration": datetime.now() + timedelta(days=120),
            "prospectus_date": datetime.now() - timedelta(days=15),
            "max_lease_term_years": 15,
            "delineated_area": {
                "north": "Germantown Ave",
                "south": "South Street",
                "east": "Delaware River",
                "west": "Schuylkill River"
            },
            "parking_spaces": 150,
            "special_requirements": "ADA compliant, medical facility requirements, patient privacy considerations",
            "scoring_type": "lowest_price_technically_acceptable",
            "energy_requirements": "Energy Star building rating required",
            "pdf_url": "https://gsa.gov/prospectuses/2024/VA-Philadelphia-RFP.pdf",
            "status": "active"
        },
        {
            "prospectus_number": "GSA-R09-PX-22-000789",
            "agency": "Internal Revenue Service",
            "location": "Denver, CO",
            "state": "CO",
            "current_nusf": 28000,
            "estimated_nusf": 30000,
            "estimated_rsf": 45000,
            "expansion_nusf": 2000,
            "estimated_annual_cost": 750000.00,
            "rental_rate_per_nusf": 25.00,
            "current_annual_cost": 700000.00,
            "current_lease_expiration": datetime.now() + timedelta(days=240),
            "prospectus_date": datetime.now() - timedelta(days=45),
            "max_lease_term_years": 20,
            "delineated_area": {
                "north": "I-70",
                "south": "I-25 & 6th Ave",
                "east": "I-225",
                "west": "Wadsworth Blvd"
            },
            "parking_spaces": 125,
            "special_requirements": "High security requirements, evidence storage capability, 24/7 access control",
            "scoring_type": "best_value",
            "energy_requirements": "LEED Silver minimum, renewable energy preferred",
            "pdf_url": "https://gsa.gov/prospectuses/2024/IRS-Denver-RFP.pdf",
            "status": "active"
        },
        {
            "prospectus_number": "GSA-R06-PX-22-000321",
            "agency": "Department of Labor",
            "location": "Kansas City, MO",
            "state": "MO",
            "current_nusf": 18000,
            "estimated_nusf": 20000,
            "estimated_rsf": 30000,
            "expansion_nusf": 2000,
            "estimated_annual_cost": 500000.00,
            "rental_rate_per_nusf": 25.00,
            "current_annual_cost": 450000.00,
            "current_lease_expiration": datetime.now() + timedelta(days=90),
            "prospectus_date": datetime.now() - timedelta(days=60),
            "max_lease_term_years": 15,
            "delineated_area": {
                "north": "Missouri River",
                "south": "I-435",
                "east": "I-35",
                "west": "I-29"
            },
            "parking_spaces": 80,
            "special_requirements": "Public access required, hearing room facilities, accessibility compliance",
            "scoring_type": "technical_and_cost",
            "energy_requirements": "Energy efficient lighting and HVAC systems required",
            "pdf_url": "https://gsa.gov/prospectuses/2024/DOL-KansasCity-RFP.pdf",
            "status": "active"
        },
        {
            "prospectus_number": "GSA-R10-PX-22-000654",
            "agency": "Environmental Protection Agency",
            "location": "Seattle, WA",
            "state": "WA",
            "current_nusf": 15000,
            "estimated_nusf": 17000,
            "estimated_rsf": 25500,
            "expansion_nusf": 2000,
            "estimated_annual_cost": 595000.00,
            "rental_rate_per_nusf": 35.00,
            "current_annual_cost": 525000.00,
            "current_lease_expiration": datetime.now() + timedelta(days=300),
            "prospectus_date": datetime.now() - timedelta(days=10),
            "max_lease_term_years": 20,
            "delineated_area": {
                "north": "Ship Canal",
                "south": "I-90",
                "east": "Lake Washington",
                "west": "Puget Sound"
            },
            "parking_spaces": 60,
            "special_requirements": "LEED Platinum required, laboratory space, chemical storage capabilities",
            "scoring_type": "best_value",
            "energy_requirements": "Net-zero energy building preferred, solar panels required",
            "pdf_url": "https://gsa.gov/prospectuses/2024/EPA-Seattle-RFP.pdf",
            "status": "active"
        }
    ]
    
    return sample_prospectuses

def create_sample_properties():
    """Create sample property data that could match prospectuses"""
    
    sample_properties = [
        {
            "address": "1234 Peachtree Street NE",
            "city": "Atlanta",
            "state": "GA",
            "zip_code": "30309",
            "total_sqft": 85000,
            "available_sqft": 75000,
            "parking_spaces": 250,
            "year_built": 2018,
            "asking_rent_per_sqft": 24.50,
            "latitude": 33.7849,
            "longitude": -84.3885,
            "source": "loopnet",
            "source_url": "https://loopnet.com/sample-atlanta-property"
        },
        {
            "address": "5678 Market Street",
            "city": "Philadelphia",
            "state": "PA", 
            "zip_code": "19106",
            "total_sqft": 60000,
            "available_sqft": 52500,
            "parking_spaces": 180,
            "year_built": 2015,
            "asking_rent_per_sqft": 26.00,
            "latitude": 39.9526,
            "longitude": -75.1652,
            "source": "costar",
            "source_url": "https://costar.com/sample-philadelphia-property"
        },
        {
            "address": "9012 17th Street",
            "city": "Denver",
            "state": "CO",
            "zip_code": "80202",
            "total_sqft": 50000,
            "available_sqft": 45000,
            "parking_spaces": 140,
            "year_built": 2020,
            "asking_rent_per_sqft": 24.00,
            "latitude": 39.7392,
            "longitude": -104.9903,
            "source": "loopnet",
            "source_url": "https://loopnet.com/sample-denver-property"
        },
        {
            "address": "3456 Main Street",
            "city": "Kansas City",
            "state": "MO",
            "zip_code": "64111",
            "total_sqft": 35000,
            "available_sqft": 30000,
            "parking_spaces": 90,
            "year_built": 2017,
            "asking_rent_per_sqft": 23.50,
            "latitude": 39.0997,
            "longitude": -94.5786,
            "source": "costar",
            "source_url": "https://costar.com/sample-kc-property"
        },
        {
            "address": "7890 First Avenue",
            "city": "Seattle",
            "state": "WA",
            "zip_code": "98104",
            "total_sqft": 30000,
            "available_sqft": 25500,
            "parking_spaces": 75,
            "year_built": 2019,
            "asking_rent_per_sqft": 36.00,
            "latitude": 47.6062,
            "longitude": -122.3321,
            "source": "loopnet",
            "source_url": "https://loopnet.com/sample-seattle-property"
        }
    ]
    
    return sample_properties

def seed_database():
    """Seed the database with sample data"""
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Clear existing data (optional - remove if you want to keep existing data)
        print("Clearing existing data...")
        db.query(Match).delete()
        db.query(Property).delete()
        db.query(Prospectus).delete()
        db.commit()
        
        # Create prospectuses
        print("Creating sample prospectuses...")
        prospectuses_data = create_sample_prospectuses()
        prospectuses = []
        
        for p_data in prospectuses_data:
            prospectus = Prospectus(**p_data)
            db.add(prospectus)
            prospectuses.append(prospectus)
        
        db.commit()
        print(f"Created {len(prospectuses)} prospectuses")
        
        # Create properties
        print("Creating sample properties...")
        properties_data = create_sample_properties()
        properties = []
        
        for prop_data in properties_data:
            property_obj = Property(**prop_data)
            db.add(property_obj)
            properties.append(property_obj)
        
        db.commit()
        print(f"Created {len(properties)} properties")
        
        # Create some sample matches
        print("Creating sample matches...")
        matches_created = 0
        
        for i, prospectus in enumerate(prospectuses):
            if i < len(properties):
                # Create a high-scoring match for demonstration
                match = Match(
                    prospectus_id=prospectus.id,
                    property_id=properties[i].id,
                    total_score=0.92,
                    size_score=0.95,
                    location_score=0.90,
                    parking_score=0.88,
                    price_score=0.94,
                    notes=f"Excellent match for {prospectus.agency} requirements",
                    compliance_gaps={"security": "Level IV clearance needed", "parking": "Additional 10 spaces recommended"},
                    status="potential"
                )
                db.add(match)
                matches_created += 1
                
                # Add a secondary match with lower score
                if i + 1 < len(properties):
                    match2 = Match(
                        prospectus_id=prospectus.id,
                        property_id=properties[i + 1].id,
                        total_score=0.75,
                        size_score=0.80,
                        location_score=0.85,
                        parking_score=0.70,
                        price_score=0.65,
                        notes=f"Good alternative option for {prospectus.agency}",
                        compliance_gaps={"size": "5000 sqft short", "parking": "30 spaces short"},
                        status="potential"
                    )
                    db.add(match2)
                    matches_created += 1
        
        db.commit()
        print(f"Created {matches_created} sample matches")
        
        print("\n✅ Database seeded successfully!")
        print("\nSample data summary:")
        print(f"- {len(prospectuses)} GSA prospectuses")
        print(f"- {len(properties)} available properties")
        print(f"- {matches_created} potential matches")
        
        # Display first prospectus as example
        if prospectuses:
            p = prospectuses[0]
            print(f"\nExample prospectus:")
            print(f"- Number: {p.prospectus_number}")
            print(f"- Agency: {p.agency}")
            print(f"- Location: {p.location}")
            print(f"- Space needed: {p.estimated_nusf:,} NUSF")
            print(f"- Annual cost: ${p.estimated_annual_cost:,.2f}")
            print(f"- Lease expires: {p.current_lease_expiration.strftime('%Y-%m-%d')}")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🌱 Seeding Neon database with GSA prospectus data...")
    seed_database()