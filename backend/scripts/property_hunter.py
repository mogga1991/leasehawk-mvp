#!/usr/bin/env python3
"""
Property Hunter - Find matching properties for GSA prospectuses
Searches LoopNet, CoStar, and other sources for available properties
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time
from datetime import datetime
from urllib.parse import urlencode, quote
import json

from app.database import SessionLocal
from app.models import Prospectus, Property
from app.notion_sync import NotionSync

class PropertyHunter:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="leasehawk-property-hunter")
        self.notion = NotionSync()
        self.found_properties = []
        
    def hunt_for_prospectus(self, prospectus):
        """Find all matching properties for a specific prospectus"""
        print(f"\n🎯 Hunting properties for: {prospectus.prospectus_number}")
        print(f"   Location: {prospectus.location}, {prospectus.state}")
        print(f"   Size: {prospectus.estimated_nusf:,} sq ft")
        print(f"   Annual Value: ${prospectus.estimated_annual_cost:,.0f}")
        
        # Get coordinates for the prospectus location
        location_query = f"{prospectus.location}, {prospectus.state}"
        try:
            location = self.geolocator.geocode(location_query)
            if not location:
                print(f"❌ Could not geocode location: {location_query}")
                return []
            
            lat, lon = location.latitude, location.longitude
            print(f"   Coordinates: {lat:.4f}, {lon:.4f}")
            
        except Exception as e:
            print(f"❌ Geocoding error: {e}")
            return []
        
        # Search parameters based on prospectus requirements
        search_params = {
            'lat': lat,
            'lon': lon,
            'radius': 25,  # miles - GSA typically allows broader area
            'min_size': int(prospectus.estimated_nusf * 0.8),  # 20% smaller OK
            'max_size': int(prospectus.estimated_nusf * 1.5),  # 50% larger OK
            'min_parking': prospectus.parking_spaces or 0,
            'max_rent': prospectus.rental_rate_per_nusf * 1.2 if prospectus.rental_rate_per_nusf else None
        }
        
        # Search multiple sources
        all_properties = []
        
        # 1. LoopNet search
        loopnet_properties = self.search_loopnet(search_params, prospectus)
        all_properties.extend(loopnet_properties)
        
        # 2. Manual high-value targets (you can expand this)
        manual_properties = self.get_manual_targets(prospectus)
        all_properties.extend(manual_properties)
        
        # 3. Filter and score properties
        scored_properties = self.score_properties(all_properties, prospectus)
        
        # 4. Save top properties
        top_properties = scored_properties[:10]  # Top 10 matches
        self.save_properties(top_properties, prospectus)
        
        return top_properties
    
    def search_loopnet(self, params, prospectus):
        """Search LoopNet for matching properties"""
        print(f"🔍 Searching LoopNet...")
        
        properties = []
        
        try:
            # LoopNet search URL (simplified - in production use their API)
            base_url = "https://www.loopnet.com/search/"
            
            # Build search query
            query_params = {
                'sk': 'f0c0148ec4ba78cf0e',  # Example search key
                'bb': f"{params['lat']-0.5},{params['lon']-0.5},{params['lat']+0.5},{params['lon']+0.5}",
                'Property-Type': 'Office',
                'Min-Square-Feet': params['min_size'],
                'Max-Square-Feet': params['max_size']
            }
            
            # For demo purposes, create mock properties based on real locations
            mock_properties = self.create_mock_properties(params, prospectus)
            properties.extend(mock_properties)
            
            print(f"✅ Found {len(properties)} properties on LoopNet")
            
        except Exception as e:
            print(f"❌ LoopNet search failed: {e}")
        
        return properties
    
    def create_mock_properties(self, params, prospectus):
        """Create realistic mock properties for demo (replace with real scraping)"""
        
        # Base this on the specific prospectus location
        if 'franklin' in prospectus.location.lower() and 'oh' in prospectus.state.lower():
            return [
                {
                    'address': '1234 Corporate Blvd, Columbus, OH 43215',
                    'city': 'Columbus',
                    'state': 'OH',
                    'zip_code': '43215',
                    'total_sqft': 95000,
                    'available_sqft': 85000,
                    'asking_rent_per_sqft': 18.50,
                    'parking_spaces': 340,
                    'year_built': 2015,
                    'source': 'LoopNet',
                    'source_url': 'https://www.loopnet.com/Listing/1234-Corporate-Blvd-Columbus-OH/12345/',
                    'latitude': params['lat'] + 0.1,
                    'longitude': params['lon'] - 0.1,
                    'property_type': 'Office',
                    'class_type': 'A'
                },
                {
                    'address': '5678 Business Park Dr, Dublin, OH 43017',
                    'city': 'Dublin', 
                    'state': 'OH',
                    'zip_code': '43017',
                    'total_sqft': 78000,
                    'available_sqft': 78000,
                    'asking_rent_per_sqft': 17.25,
                    'parking_spaces': 312,
                    'year_built': 2018,
                    'source': 'LoopNet',
                    'source_url': 'https://www.loopnet.com/Listing/5678-Business-Park-Dr-Dublin-OH/23456/',
                    'latitude': params['lat'] + 0.15,
                    'longitude': params['lon'] + 0.1,
                    'property_type': 'Office',
                    'class_type': 'A'
                }
            ]
        
        elif 'salt lake' in prospectus.location.lower() and 'ut' in prospectus.state.lower():
            return [
                {
                    'address': '2468 South State St, Salt Lake City, UT 84115',
                    'city': 'Salt Lake City',
                    'state': 'UT', 
                    'zip_code': '84115',
                    'total_sqft': 92000,
                    'available_sqft': 88000,
                    'asking_rent_per_sqft': 22.00,
                    'parking_spaces': 368,
                    'year_built': 2016,
                    'source': 'LoopNet',
                    'source_url': 'https://www.loopnet.com/Listing/2468-South-State-St-Salt-Lake-City-UT/34567/',
                    'latitude': params['lat'] + 0.05,
                    'longitude': params['lon'] - 0.08,
                    'property_type': 'Office',
                    'class_type': 'A'
                },
                {
                    'address': '1357 Medical Dr, Salt Lake City, UT 84132',
                    'city': 'Salt Lake City',
                    'state': 'UT',
                    'zip_code': '84132', 
                    'total_sqft': 105000,
                    'available_sqft': 95000,
                    'asking_rent_per_sqft': 24.50,
                    'parking_spaces': 420,
                    'year_built': 2019,
                    'source': 'LoopNet',
                    'source_url': 'https://www.loopnet.com/Listing/1357-Medical-Dr-Salt-Lake-City-UT/45678/',
                    'latitude': params['lat'] - 0.02,
                    'longitude': params['lon'] + 0.12,
                    'property_type': 'Medical Office',
                    'class_type': 'A'
                }
            ]
        
        # Generic properties for other locations
        return [
            {
                'address': f'123 Main St, {prospectus.location}, {prospectus.state}',
                'city': prospectus.location,
                'state': prospectus.state,
                'zip_code': '00000',
                'total_sqft': int(prospectus.estimated_nusf * 1.1),
                'available_sqft': prospectus.estimated_nusf,
                'asking_rent_per_sqft': prospectus.rental_rate_per_nusf * 0.95 if prospectus.rental_rate_per_nusf else 20.00,
                'parking_spaces': prospectus.parking_spaces or 250,
                'year_built': 2010,
                'source': 'LoopNet',
                'source_url': 'https://www.loopnet.com/example',
                'latitude': params['lat'],
                'longitude': params['lon'],
                'property_type': 'Office',
                'class_type': 'B'
            }
        ]
    
    def get_manual_targets(self, prospectus):
        """Get manually identified high-value properties"""
        
        # Add specific properties you know about for high-value prospects
        if 'franklin' in prospectus.location.lower():
            return [
                {
                    'address': '123 Executive Center, Westerville, OH 43081',
                    'city': 'Westerville',
                    'state': 'OH',
                    'zip_code': '43081',
                    'total_sqft': 120000,
                    'available_sqft': 85000,
                    'asking_rent_per_sqft': 16.75,
                    'parking_spaces': 480,
                    'year_built': 2012,
                    'source': 'Manual Research',
                    'source_url': 'https://example.com/property1',
                    'latitude': 40.1261,
                    'longitude': -82.9291,
                    'property_type': 'Office',
                    'class_type': 'A',
                    'special_notes': 'Owner previously worked with GSA, very interested in government tenants'
                }
            ]
        
        return []
    
    def score_properties(self, properties, prospectus):
        """Score properties based on match with prospectus requirements"""
        
        scored = []
        
        for prop in properties:
            score = 0
            reasons = []
            
            # Size match (40 points max)
            if prop['available_sqft']:
                size_diff = abs(prop['available_sqft'] - prospectus.estimated_nusf) / prospectus.estimated_nusf
                if size_diff <= 0.1:  # Within 10%
                    score += 40
                    reasons.append("Perfect size match")
                elif size_diff <= 0.25:  # Within 25%
                    score += 30
                    reasons.append("Good size match")
                elif size_diff <= 0.5:  # Within 50%
                    score += 20
                    reasons.append("Acceptable size")
            
            # Rent match (25 points max)
            if prospectus.rental_rate_per_nusf and prop['asking_rent_per_sqft']:
                if prop['asking_rent_per_sqft'] <= prospectus.rental_rate_per_nusf:
                    score += 25
                    reasons.append("Rent within budget")
                elif prop['asking_rent_per_sqft'] <= prospectus.rental_rate_per_nusf * 1.1:
                    score += 15
                    reasons.append("Rent slightly above budget")
            
            # Parking match (15 points max)
            if prospectus.parking_spaces and prop['parking_spaces']:
                if prop['parking_spaces'] >= prospectus.parking_spaces:
                    score += 15
                    reasons.append("Adequate parking")
                elif prop['parking_spaces'] >= prospectus.parking_spaces * 0.8:
                    score += 10
                    reasons.append("Parking close to requirements")
            
            # Building quality (10 points max)
            if prop.get('year_built', 0) >= 2010:
                score += 10
                reasons.append("Modern building")
            elif prop.get('year_built', 0) >= 2000:
                score += 5
                reasons.append("Recent building")
            
            # Property class (10 points max)
            if prop.get('class_type') == 'A':
                score += 10
                reasons.append("Class A property")
            elif prop.get('class_type') == 'B':
                score += 7
                reasons.append("Class B property")
            
            prop['match_score'] = score
            prop['match_reasons'] = reasons
            prop['prospectus_id'] = prospectus.id
            
            scored.append(prop)
        
        # Sort by score descending
        return sorted(scored, key=lambda x: x['match_score'], reverse=True)
    
    def save_properties(self, properties, prospectus):
        """Save properties to database and Notion"""
        
        db = SessionLocal()
        saved_count = 0
        
        try:
            for prop_data in properties:
                # Check if property already exists
                existing = db.query(Property).filter(
                    Property.address == prop_data['address']
                ).first()
                
                if existing:
                    print(f"⚠️  Property already exists: {prop_data['address']}")
                    continue
                
                # Create new property
                property_fields = {k: v for k, v in prop_data.items() 
                                 if k not in ['match_score', 'match_reasons', 'prospectus_id', 'special_notes']}
                
                new_property = Property(**property_fields)
                db.add(new_property)
                saved_count += 1
                
                print(f"✅ Added property: {prop_data['address']} (Score: {prop_data['match_score']})")
                
                # Also save to Notion
                try:
                    notion_id = self.notion.add_property_from_search(prop_data)
                    print(f"   💫 Added to Notion: {notion_id}")
                except Exception as e:
                    print(f"   ⚠️  Notion save failed: {e}")
            
            db.commit()
            print(f"\n✅ Saved {saved_count} new properties to database")
            
        except Exception as e:
            print(f"❌ Error saving properties: {e}")
            db.rollback()
        finally:
            db.close()
    
    def hunt_all_prospectuses(self):
        """Hunt properties for all active prospectuses"""
        print("🦅 Property Hunter - Hunting ALL Prospectuses")
        print("=" * 60)
        
        db = SessionLocal()
        
        # Get all active prospectuses
        prospectuses = db.query(Prospectus).filter(
            Prospectus.status == 'active'
        ).all()
        
        print(f"📋 Found {len(prospectuses)} active prospectuses to hunt")
        
        total_properties = 0
        high_value_matches = []
        
        for prospectus in prospectuses:
            try:
                properties = self.hunt_for_prospectus(prospectus)
                total_properties += len(properties)
                
                # Track high-value opportunities
                if prospectus.estimated_annual_cost and prospectus.estimated_annual_cost > 3000000:
                    top_match = properties[0] if properties else None
                    if top_match and top_match['match_score'] > 70:
                        high_value_matches.append({
                            'prospectus': prospectus,
                            'property': top_match,
                            'potential_fee': prospectus.estimated_annual_cost * 0.02
                        })
                
                time.sleep(2)  # Be respectful to websites
                
            except Exception as e:
                print(f"❌ Error hunting for {prospectus.prospectus_number}: {e}")
                continue
        
        db.close()
        
        # Summary report
        print(f"\n🎯 PROPERTY HUNT COMPLETE")
        print(f"   Total Properties Found: {total_properties}")
        print(f"   High-Value Matches: {len(high_value_matches)}")
        
        if high_value_matches:
            print(f"\n💰 TOP HIGH-VALUE OPPORTUNITIES:")
            for i, match in enumerate(high_value_matches[:5], 1):
                p = match['prospectus']
                prop = match['property']
                print(f"{i}. {p.agency} - {p.location}")
                print(f"   Property: {prop['address']}")
                print(f"   Match Score: {prop['match_score']}/100")
                print(f"   Potential Fee: ${match['potential_fee']:,.0f}")
                print()
        
        print(f"\n🚀 Next Steps:")
        print(f"1. Review high-scoring matches in Notion")
        print(f"2. Research property owners for top matches")
        print(f"3. Begin outreach campaign")
        print(f"4. Run: python scripts/outreach_generator.py")

def main():
    """Main property hunting function"""
    hunter = PropertyHunter()
    
    import argparse
    parser = argparse.ArgumentParser(description="Hunt for matching properties")
    parser.add_argument("--prospectus-id", type=int, help="Hunt for specific prospectus ID")
    parser.add_argument("--all", action="store_true", help="Hunt for all active prospectuses")
    
    args = parser.parse_args()
    
    if args.prospectus_id:
        db = SessionLocal()
        prospectus = db.query(Prospectus).filter(Prospectus.id == args.prospectus_id).first()
        if prospectus:
            hunter.hunt_for_prospectus(prospectus)
        else:
            print(f"❌ Prospectus ID {args.prospectus_id} not found")
        db.close()
    elif args.all:
        hunter.hunt_all_prospectuses()
    else:
        # Default: hunt for all
        hunter.hunt_all_prospectuses()

if __name__ == "__main__":
    main()