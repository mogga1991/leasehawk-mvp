#!/usr/bin/env python3
"""
Simple script to seed Neon database with GSA prospectus data
"""
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.models import Prospectus, Property, Match

def seed_database():
    """Create tables and seed the database with sample data"""
    
    print("🔗 Connecting to Neon database...")
    
    # Create all tables
    print("📋 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create prospectuses first
        print("🏢 Creating sample prospectuses...")
        
        p1 = Prospectus(
            prospectus_number="GSA-R11-PX-22-000123",
            agency="Social Security Administration",
            location="Atlanta, GA",
            state="GA",
            current_nusf=45000,
            estimated_nusf=50000,
            estimated_rsf=75000,
            expansion_nusf=5000,
            estimated_annual_cost=1250000.00,
            rental_rate_per_nusf=25.00,
            current_annual_cost=1125000.00,
            current_lease_expiration=datetime.now() + timedelta(days=180),
            prospectus_date=datetime.now() - timedelta(days=30),
            max_lease_term_years=20,
            delineated_area={
                "north": "I-285 Perimeter",
                "south": "I-20",
                "east": "I-285 East",
                "west": "I-285 West"
            },
            parking_spaces=200,
            special_requirements="Must meet Level IV security requirements, backup power generation required",
            scoring_type="technical_and_cost",
            energy_requirements="LEED Gold certification preferred, Energy Star rated equipment required",
            pdf_url="https://gsa.gov/prospectuses/2024/SSA-Atlanta-RFP.pdf",
            status="active"
        )
        
        p2 = Prospectus(
            prospectus_number="GSA-R03-PX-22-000456",
            agency="Department of Veterans Affairs",
            location="Philadelphia, PA",
            state="PA",
            current_nusf=32000,
            estimated_nusf=35000,
            estimated_rsf=52500,
            expansion_nusf=3000,
            estimated_annual_cost=875000.00,
            rental_rate_per_nusf=25.00,
            current_annual_cost=800000.00,
            current_lease_expiration=datetime.now() + timedelta(days=120),
            prospectus_date=datetime.now() - timedelta(days=15),
            max_lease_term_years=15,
            delineated_area={
                "north": "Germantown Ave",
                "south": "South Street",
                "east": "Delaware River",
                "west": "Schuylkill River"
            },
            parking_spaces=150,
            special_requirements="ADA compliant, medical facility requirements, patient privacy considerations",
            scoring_type="lowest_price_technically_acceptable",
            energy_requirements="Energy Star building rating required",
            pdf_url="https://gsa.gov/prospectuses/2024/VA-Philadelphia-RFP.pdf",
            status="active"
        )
        
        p3 = Prospectus(
            prospectus_number="GSA-R09-PX-22-000789",
            agency="Internal Revenue Service",
            location="Denver, CO",
            state="CO",
            current_nusf=28000,
            estimated_nusf=30000,
            estimated_rsf=45000,
            expansion_nusf=2000,
            estimated_annual_cost=750000.00,
            rental_rate_per_nusf=25.00,
            current_annual_cost=700000.00,
            current_lease_expiration=datetime.now() + timedelta(days=240),
            prospectus_date=datetime.now() - timedelta(days=45),
            max_lease_term_years=20,
            delineated_area={
                "north": "I-70",
                "south": "I-25 & 6th Ave",
                "east": "I-225",
                "west": "Wadsworth Blvd"
            },
            parking_spaces=125,
            special_requirements="High security requirements, evidence storage capability, 24/7 access control",
            scoring_type="best_value",
            energy_requirements="LEED Silver minimum, renewable energy preferred",
            pdf_url="https://gsa.gov/prospectuses/2024/IRS-Denver-RFP.pdf",
            status="active"
        )
        
        prospectuses = [p1, p2, p3]
        db.add_all(prospectuses)
        db.commit()
        
        # Refresh to get IDs
        for p in prospectuses:
            db.refresh(p)
        
        print(f"✅ Created {len(prospectuses)} prospectuses")
        
        # Create properties
        print("🏘️ Creating sample properties...")
        
        prop1 = Property(
            address="1234 Peachtree Street NE",
            city="Atlanta",
            state="GA",
            zip_code="30309",
            total_sqft=85000,
            available_sqft=75000,
            parking_spaces=250,
            year_built=2018,
            asking_rent_per_sqft=24.50,
            latitude=33.7849,
            longitude=-84.3885,
            source="loopnet",
            source_url="https://loopnet.com/sample-atlanta-property"
        )
        
        prop2 = Property(
            address="5678 Market Street",
            city="Philadelphia",
            state="PA", 
            zip_code="19106",
            total_sqft=60000,
            available_sqft=52500,
            parking_spaces=180,
            year_built=2015,
            asking_rent_per_sqft=26.00,
            latitude=39.9526,
            longitude=-75.1652,
            source="costar",
            source_url="https://costar.com/sample-philadelphia-property"
        )
        
        prop3 = Property(
            address="9012 17th Street",
            city="Denver",
            state="CO",
            zip_code="80202",
            total_sqft=50000,
            available_sqft=45000,
            parking_spaces=140,
            year_built=2020,
            asking_rent_per_sqft=24.00,
            latitude=39.7392,
            longitude=-104.9903,
            source="loopnet",
            source_url="https://loopnet.com/sample-denver-property"
        )
        
        properties = [prop1, prop2, prop3]
        db.add_all(properties)
        db.commit()
        
        # Refresh to get IDs
        for p in properties:
            db.refresh(p)
            
        print(f"✅ Created {len(properties)} properties")
        
        # Create matches
        print("🔗 Creating sample matches...")
        
        matches = []
        for i, prospectus in enumerate(prospectuses):
            if i < len(properties):
                match = Match(
                    prospectus_id=prospectus.id,
                    property_id=properties[i].id,
                    total_score=0.92,
                    size_score=0.95,
                    location_score=0.90,
                    parking_score=0.88,
                    price_score=0.94,
                    notes=f"Excellent match for {prospectus.agency} requirements",
                    compliance_gaps={"security": "Level IV clearance needed"},
                    status="potential"
                )
                matches.append(match)
        
        db.add_all(matches)
        db.commit()
        
        print(f"✅ Created {len(matches)} matches")
        
        print("\n🎉 Neon database seeded successfully!")
        print("\n📊 Sample data summary:")
        print(f"  • {len(prospectuses)} GSA prospectuses")
        print(f"  • {len(properties)} available properties") 
        print(f"  • {len(matches)} potential matches")
        
        total_value = sum(p.estimated_annual_cost for p in prospectuses)
        print(f"  • ${total_value:,.0f} total pipeline value")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🌱 Setting up Neon database with GSA prospectus data...")
    seed_database()