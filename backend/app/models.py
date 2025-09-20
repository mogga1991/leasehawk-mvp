from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Prospectus(Base):
    __tablename__ = "prospectuses"
    
    id = Column(Integer, primary_key=True, index=True)
    prospectus_number = Column(String, unique=True, index=True)
    agency = Column(String, index=True)
    location = Column(String, index=True)
    state = Column(String, index=True)
    
    # Space Requirements
    current_nusf = Column(Integer)
    estimated_nusf = Column(Integer)
    estimated_rsf = Column(Integer)
    expansion_nusf = Column(Integer)
    
    # Financial
    estimated_annual_cost = Column(Float)
    rental_rate_per_nusf = Column(Float)
    current_annual_cost = Column(Float)
    
    # Timing
    current_lease_expiration = Column(DateTime)
    prospectus_date = Column(DateTime)
    max_lease_term_years = Column(Integer)
    
    # Location Requirements
    delineated_area = Column(JSON)  # Store as JSON with north, south, east, west
    parking_spaces = Column(Integer)
    
    # Additional Requirements
    special_requirements = Column(Text)
    scoring_type = Column(String)
    energy_requirements = Column(Text)
    
    # Metadata
    pdf_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")  # active, awarded, cancelled
    notion_id = Column(String)  # Store Notion page ID for sync
    
class Property(Base):
    __tablename__ = "properties"
    
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String)
    city = Column(String, index=True)
    state = Column(String, index=True)
    zip_code = Column(String)
    
    # Property Details
    total_sqft = Column(Integer)
    available_sqft = Column(Integer)
    parking_spaces = Column(Integer)
    year_built = Column(Integer)
    
    # Financial
    asking_rent_per_sqft = Column(Float)
    
    # Location
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Source
    source = Column(String)  # loopnet, costar, etc.
    source_url = Column(String)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    notion_id = Column(String)  # Store Notion page ID for sync
    
class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    prospectus_id = Column(Integer)
    property_id = Column(Integer)
    
    # Scoring
    total_score = Column(Float)
    size_score = Column(Float)
    location_score = Column(Float)
    parking_score = Column(Float)
    price_score = Column(Float)
    
    # Analysis
    notes = Column(Text)
    compliance_gaps = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="potential")  # potential, contacted, pursuing, won, lost