import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import Base, Prospectus, Property
from datetime import datetime

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Add the VA prospectuses from your PDFs
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
    scoring_type="Operating Lease"
)

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
    scoring_type="Operating Lease"
)

db.add(va_franklin)
db.add(va_salt_lake)
db.commit()

print("Sample data loaded successfully!")


