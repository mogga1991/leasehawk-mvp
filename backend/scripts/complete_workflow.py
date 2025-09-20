#!/usr/bin/env python3
"""
Complete LeaseHawk Workflow: Notion → Parse → Match → Alert
This script demonstrates the full end-to-end workflow of the LeaseHawk system
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.notion_sync import NotionSync
from app.matchers.property_matcher import PropertyMatcher
from app.database import SessionLocal, engine
from app.models import Base, Prospectus, Property, Match
from datetime import datetime, timedelta

def setup_database():
    """Ensure database tables exist"""
    Base.metadata.create_all(bind=engine)

def run_complete_workflow():
    """Run the complete LeaseHawk workflow"""
    
    print("🦅 LeaseHawk Complete Workflow Starting...")
    print("=" * 60)
    
    # Setup
    setup_database()
    
    # 1. Sync from Notion
    print("\n📥 Step 1: Syncing from Notion...")
    try:
        notion = NotionSync()
        prospectuses = notion.get_prospectuses()
        properties = notion.get_properties()
        
        print(f"✅ Found {len(prospectuses)} prospectuses and {len(properties)} properties in Notion")
    except Exception as e:
        print(f"❌ Notion sync failed: {e}")
        print("Make sure NOTION_TOKEN and database IDs are set in your .env file")
        return
    
    # 2. Store in local database
    print("\n💾 Step 2: Updating local database...")
    db = SessionLocal()
    
    try:
        # Add/update prospectuses
        local_prospectuses = []
        for p in prospectuses:
            if not p.get("prospectus_number"):
                continue
                
            existing = db.query(Prospectus).filter(
                Prospectus.prospectus_number == p["prospectus_number"]
            ).first()
            
            if existing:
                # Update existing
                for key, value in p.items():
                    if key != "notion_id" and hasattr(existing, key) and value is not None:
                        setattr(existing, key, value)
                local_prospectuses.append(existing)
            else:
                # Create new
                prospectus_data = {k: v for k, v in p.items() if k != "notion_id" and v is not None}
                new_prospectus = Prospectus(**prospectus_data)
                db.add(new_prospectus)
                local_prospectuses.append(new_prospectus)
        
        # Add/update properties
        local_properties = []
        for prop in properties:
            if not prop.get("address"):
                continue
                
            existing = db.query(Property).filter(
                Property.address == prop["address"]
            ).first()
            
            if not existing:
                property_data = {k: v for k, v in prop.items() if k != "notion_id" and v is not None}
                new_property = Property(**property_data)
                db.add(new_property)
                local_properties.append(new_property)
            else:
                local_properties.append(existing)
        
        db.commit()
        print(f"✅ Database updated with {len(local_prospectuses)} prospectuses and {len(local_properties)} properties")
        
    except Exception as e:
        print(f"❌ Database update failed: {e}")
        db.rollback()
        return
    
    # 3. Run property matching
    print("\n🎯 Step 3: Running intelligent property matching...")
    
    matcher = PropertyMatcher()
    total_matches = 0
    high_value_matches = []
    critical_alerts = []
    
    for prospectus in local_prospectuses:
        if not prospectus:
            continue
            
        try:
            # Convert SQLAlchemy objects to dicts for matcher
            prospectus_dict = {c.name: getattr(prospectus, c.name) for c in prospectus.__table__.columns}
            property_dicts = [{c.name: getattr(prop, c.name) for c in prop.__table__.columns} 
                             for prop in local_properties]
            
            # Find matches
            matches = matcher.find_matches(prospectus_dict, property_dicts)
            
            for match in matches:
                total_matches += 1
                score = match['scores']['total_score']
                
                # Save match to database
                db_match = Match(
                    prospectus_id=prospectus.id,
                    property_id=match['property']['id'],
                    total_score=score,
                    size_score=match['scores']['size_score'],
                    parking_score=match['scores']['parking_score'],
                    price_score=match['scores']['price_score'],
                    location_score=match['scores']['location_score']
                )
                db.add(db_match)
                
                # Track high-value opportunities
                annual_cost = prospectus_dict.get('estimated_annual_cost', 0)
                if score > 80 and annual_cost > 2000000:  # $2M+ and 80%+ match
                    high_value_matches.append({
                        'prospectus': prospectus_dict,
                        'property': match['property'],
                        'score': score,
                        'potential_fee': annual_cost * 0.02
                    })
                
                # Track critical alerts (expiring soon + high value)
                if prospectus.current_lease_expiration:
                    days_until_exp = (prospectus.current_lease_expiration - datetime.now()).days
                    if days_until_exp < 180 and annual_cost > 5000000:  # 6 months, $5M+
                        critical_alerts.append({
                            'prospectus': prospectus_dict,
                            'property': match['property'],
                            'score': score,
                            'days_until_expiration': days_until_exp,
                            'potential_fee': annual_cost * 0.02
                        })
        
        except Exception as e:
            print(f"❌ Error matching prospectus {prospectus.prospectus_number}: {e}")
            continue
    
    db.commit()
    print(f"✅ Matching complete: {total_matches} total matches found")
    
    # 4. Generate alerts and reports
    print("\n🚨 Step 4: Generating alerts and opportunities...")
    
    # Critical alerts (expiring soon + high value)
    if critical_alerts:
        print(f"\n🔥 CRITICAL ALERTS ({len(critical_alerts)} items):")
        print("=" * 50)
        for alert in critical_alerts:
            print(f"⚠️  {alert['prospectus']['agency']} - {alert['prospectus']['location']}")
            print(f"   Expires in {alert['days_until_expiration']} days")
            print(f"   Annual Value: ${alert['prospectus']['estimated_annual_cost']:,.0f}")
            print(f"   Best Match: {alert['property']['address']} ({alert['score']:.1f}%)")
            print(f"   Potential Fee: ${alert['potential_fee']:,.0f}")
            print()
    
    # High-value opportunities
    if high_value_matches:
        print(f"\n💰 HIGH-VALUE OPPORTUNITIES ({len(high_value_matches)} items):")
        print("=" * 50)
        
        # Sort by potential fee
        high_value_matches.sort(key=lambda x: x['potential_fee'], reverse=True)
        
        for i, hvm in enumerate(high_value_matches[:10], 1):  # Top 10
            print(f"{i:2d}. {hvm['prospectus']['agency']} - {hvm['prospectus']['location']}")
            print(f"     Annual Value: ${hvm['prospectus']['estimated_annual_cost']:,.0f}")
            print(f"     Property: {hvm['property']['address']}")
            print(f"     Match Score: {hvm['score']:.1f}%")
            print(f"     Potential Fee: ${hvm['potential_fee']:,.0f}")
            print()
    
    # 5. Action items and next steps
    print("\n📋 Step 5: Action Items & Next Steps")
    print("=" * 50)
    
    if critical_alerts:
        print("🔥 IMMEDIATE ACTIONS (Critical - Expiring Soon):")
        for i, alert in enumerate(critical_alerts[:3], 1):
            print(f"{i}. Contact property owner: {alert['property']['address']}")
            print(f"   Prepare GSA compliance package for {alert['prospectus']['prospectus_number']}")
    
    if high_value_matches:
        print("\n💼 HIGH-PRIORITY ACTIONS (This Week):")
        top_matches = sorted(high_value_matches, key=lambda x: x['potential_fee'], reverse=True)[:5]
        for i, match in enumerate(top_matches, 1):
            print(f"{i}. Research property: {match['property']['address']}")
            print(f"   Draft LOI for {match['prospectus']['prospectus_number']}")
    
    print("\n📊 ONGOING TASKS:")
    print("1. Monitor Notion for new prospectus releases")
    print("2. Update property database with new listings")
    print("3. Refine matching algorithms based on wins/losses")
    print("4. Track competitor activity on matched properties")
    
    # 6. Summary metrics
    print("\n📈 Step 6: Performance Summary")
    print("=" * 50)
    
    total_potential_fees = sum([h['potential_fee'] for h in high_value_matches])
    critical_potential = sum([c['potential_fee'] for c in critical_alerts])
    
    print(f"Total Opportunities Identified: {len(high_value_matches)}")
    print(f"Critical Alerts (Expiring <6mo): {len(critical_alerts)}")
    print(f"Total Potential Fees: ${total_potential_fees:,.0f}")
    print(f"Critical Potential Fees: ${critical_potential:,.0f}")
    
    if total_potential_fees > 0:
        print(f"Average Fee per Opportunity: ${total_potential_fees/len(high_value_matches):,.0f}")
    
    # Close database
    db.close()
    
    print("\n🎉 LeaseHawk Workflow Complete!")
    print("=" * 60)

def run_daily_check():
    """Run a lighter daily check for new opportunities"""
    print("🔍 Running daily opportunity check...")
    
    db = SessionLocal()
    
    # Get active prospectuses expiring in next 6 months
    six_months_out = datetime.now() + timedelta(days=180)
    expiring_soon = db.query(Prospectus).filter(
        Prospectus.current_lease_expiration <= six_months_out,
        Prospectus.status == "active"
    ).all()
    
    print(f"📋 {len(expiring_soon)} prospectuses expiring in next 6 months")
    
    # High-value expiring opportunities
    high_value_expiring = [p for p in expiring_soon if (p.estimated_annual_cost or 0) > 2000000]
    
    if high_value_expiring:
        print(f"\n🎯 {len(high_value_expiring)} HIGH-VALUE expiring opportunities:")
        for p in high_value_expiring:
            days_left = (p.current_lease_expiration - datetime.now()).days
            print(f"  • {p.agency} - {p.location} (${p.estimated_annual_cost:,.0f}, {days_left} days)")
    
    db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LeaseHawk Workflow Runner")
    parser.add_argument("--daily", action="store_true", help="Run daily check only")
    parser.add_argument("--full", action="store_true", help="Run complete workflow")
    
    args = parser.parse_args()
    
    if args.daily:
        run_daily_check()
    elif args.full or len(sys.argv) == 1:
        run_complete_workflow()
    else:
        print("Use --full for complete workflow or --daily for daily check")