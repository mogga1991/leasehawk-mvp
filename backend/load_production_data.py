#!/usr/bin/env python3
"""
Load initial VA prospectus data for production deployment
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import Base, Prospectus
from datetime import datetime

def load_va_opportunities():
    """Load the two high-value VA opportunities"""
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing = db.query(Prospectus).filter(
            Prospectus.prospectus_number.in_(["POH-09-VA25", "PUT-24-VA25"])
        ).count()
        
        if existing > 0:
            print(f"✅ Production data already exists ({existing} prospectuses)")
            return
        
        # Add VA Franklin County
        va_franklin = Prospectus(
            prospectus_number="POH-09-VA25",
            agency="Veterans Affairs",
            location="Franklin County, OH",
            state="OH",
            current_nusf=9365,
            estimated_nusf=84739,
            estimated_rsf=114398,
            expansion_nusf=75374,
            estimated_annual_cost=4230000,
            rental_rate_per_nusf=49.91,
            current_annual_cost=223043,
            current_lease_expiration=datetime(2026, 7, 20),
            max_lease_term_years=20,
            parking_spaces=600,
            scoring_type="Operating Lease",
            special_requirements="VA Mental Health Clinic expansion - 9x current size",
            status="active"
        )
        
        # Add VA Salt Lake City
        va_salt_lake = Prospectus(
            prospectus_number="PUT-24-VA25",
            agency="Veterans Affairs", 
            location="Salt Lake City, UT",
            state="UT",
            estimated_nusf=85046,
            estimated_rsf=114812,
            expansion_nusf=85046,
            estimated_annual_cost=7760000,
            rental_rate_per_nusf=91.24,
            max_lease_term_years=20,
            parking_spaces=600,
            scoring_type="Operating Lease",
            special_requirements="New medical facility near University of Utah",
            status="active"
        )
        
        db.add(va_franklin)
        db.add(va_salt_lake)
        db.commit()
        
        print("🎯 PRODUCTION DATA LOADED SUCCESSFULLY!")
        print("=" * 50)
        print(f"✅ Franklin County VA: ${va_franklin.estimated_annual_cost:,.0f}/year")
        print(f"   Your potential fee: ${va_franklin.estimated_annual_cost * 0.02:,.0f}")
        print(f"✅ Salt Lake City VA: ${va_salt_lake.estimated_annual_cost:,.0f}/year")
        print(f"   Your potential fee: ${va_salt_lake.estimated_annual_cost * 0.02:,.0f}")
        print("=" * 50)
        print(f"💰 Total Annual Value: ${va_franklin.estimated_annual_cost + va_salt_lake.estimated_annual_cost:,.0f}")
        print(f"🏆 Total Potential Fees: ${(va_franklin.estimated_annual_cost + va_salt_lake.estimated_annual_cost) * 0.02:,.0f}")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    load_va_opportunities()