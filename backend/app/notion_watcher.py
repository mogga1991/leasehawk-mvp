"""
Background task to watch Notion for changes and trigger alerts
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict
import schedule
from .notion_sync import NotionSync
from .database import SessionLocal
from .models import Prospectus, Property
from .matchers.property_matcher import PropertyMatcher

class NotionWatcher:
    def __init__(self):
        self.notion = NotionSync()
        self.matcher = PropertyMatcher()
        self.last_check = datetime.now()
        
    def check_for_updates(self):
        """Check Notion for new or updated prospectuses"""
        print(f"🔍 Checking Notion for updates at {datetime.now()}")
        
        db = SessionLocal()
        
        try:
            # Get all prospectuses from Notion
            prospectuses = self.notion.get_prospectuses()
            
            new_count = 0
            updated_count = 0
            high_value_alerts = []
            
            for p in prospectuses:
                if not p.get("prospectus_number"):
                    continue
                    
                existing = db.query(Prospectus).filter(
                    Prospectus.prospectus_number == p["prospectus_number"]
                ).first()
                
                if not existing:
                    # New prospectus found!
                    new_count += 1
                    self.send_new_prospectus_alert(p)
                    
                    # Check if it's high value
                    if self.is_high_value_opportunity(p):
                        high_value_alerts.append(p)
                    
                    # Add to database
                    prospectus_data = {k: v for k, v in p.items() if k != "notion_id" and v is not None}
                    new_prospectus = Prospectus(**prospectus_data)
                    db.add(new_prospectus)
                    
                    # Auto-run matching for new prospectus
                    self.auto_match_new_prospectus(p, db)
                    
                else:
                    # Check if significantly updated
                    if self.has_significant_update(existing, p):
                        updated_count += 1
                        self.send_update_alert(existing, p)
                        
                        # Update existing record
                        for key, value in p.items():
                            if key != "notion_id" and hasattr(existing, key):
                                setattr(existing, key, value)
            
            db.commit()
            
            # Send summary if there were changes
            if new_count > 0 or updated_count > 0:
                self.send_summary_alert(new_count, updated_count, high_value_alerts)
            
            self.last_check = datetime.now()
            print(f"✅ Notion Check Complete: {new_count} new, {updated_count} updated")
            
        except Exception as e:
            print(f"❌ Error checking Notion: {e}")
            db.rollback()
        finally:
            db.close()
    
    def auto_match_new_prospectus(self, prospectus_data: Dict, db):
        """Automatically run matching for new prospectus"""
        try:
            # Get all properties
            properties = db.query(Property).all()
            property_dicts = [p.__dict__ for p in properties]
            
            # Find matches
            matches = self.matcher.find_matches(prospectus_data, property_dicts)
            
            # Send alert for high-scoring matches
            high_score_matches = [m for m in matches if m['scores']['total_score'] > 85]
            
            if high_score_matches:
                self.send_high_match_alert(prospectus_data, high_score_matches)
                
        except Exception as e:
            print(f"Error auto-matching prospectus: {e}")
    
    def is_high_value_opportunity(self, prospectus: Dict) -> bool:
        """Determine if this is a high-value opportunity"""
        annual_cost = prospectus.get("estimated_annual_cost", 0)
        sqft = prospectus.get("estimated_nusf", 0)
        
        # High value criteria
        return (
            annual_cost > 5000000 or  # $5M+ annual value
            sqft > 100000 or          # 100k+ sq ft
            prospectus.get("agency") in ["GSA", "DoD", "VA"]  # Major agencies
        )
    
    def has_significant_update(self, existing: Prospectus, new_data: Dict) -> bool:
        """Check if prospectus has significant updates"""
        significant_fields = [
            "estimated_annual_cost", 
            "estimated_nusf", 
            "current_lease_expiration",
            "status"
        ]
        
        for field in significant_fields:
            if hasattr(existing, field):
                old_value = getattr(existing, field)
                new_value = new_data.get(field)
                
                if old_value != new_value:
                    return True
        
        return False
    
    def send_new_prospectus_alert(self, prospectus: Dict):
        """Send alert for new prospectus"""
        print(f"\n🚨 NEW PROSPECTUS ALERT!")
        print(f"Agency: {prospectus.get('agency', 'Unknown')}")
        print(f"Location: {prospectus.get('location', 'Unknown')}")
        print(f"Prospectus #: {prospectus.get('prospectus_number', 'Unknown')}")
        
        if prospectus.get('estimated_nusf'):
            print(f"Size: {prospectus['estimated_nusf']:,} sq ft")
        
        if prospectus.get('estimated_annual_cost'):
            print(f"Annual Value: ${prospectus['estimated_annual_cost']:,.0f}")
            potential_fee = prospectus['estimated_annual_cost'] * 0.02
            print(f"Potential Fee (2%): ${potential_fee:,.0f}")
        
        if prospectus.get('current_lease_expiration'):
            print(f"Lease Expires: {prospectus['current_lease_expiration']}")
        
        # In production, send email/SMS/Slack notification
    
    def send_update_alert(self, existing: Prospectus, new_data: Dict):
        """Send alert for prospectus updates"""
        print(f"\n📝 PROSPECTUS UPDATE: {new_data.get('prospectus_number')}")
        print(f"Location: {new_data.get('location')}")
        # Add specific change details here
    
    def send_high_match_alert(self, prospectus: Dict, matches: List[Dict]):
        """Send alert for high-scoring property matches"""
        print(f"\n🎯 HIGH-SCORE MATCHES FOUND!")
        print(f"Prospectus: {prospectus.get('prospectus_number')} - {prospectus.get('location')}")
        print(f"Found {len(matches)} properties with 85%+ match scores:")
        
        for match in matches[:3]:  # Top 3 matches
            prop = match['property']
            score = match['scores']['total_score']
            print(f"  • {prop.get('address', 'Unknown Address')} - {score:.1f}% match")
    
    def send_summary_alert(self, new_count: int, updated_count: int, high_value: List[Dict]):
        """Send daily summary alert"""
        print(f"\n📊 DAILY NOTION SYNC SUMMARY")
        print(f"New Prospectuses: {new_count}")
        print(f"Updated Prospectuses: {updated_count}")
        print(f"High-Value Opportunities: {len(high_value)}")
        
        if high_value:
            total_potential = sum([p.get('estimated_annual_cost', 0) * 0.02 for p in high_value])
            print(f"Total Potential Fees: ${total_potential:,.0f}")
    
    def start_watching(self, check_interval_minutes: int = 15):
        """Start the background watcher"""
        print(f"🦅 LeaseHawk Notion Watcher Started")
        print(f"Checking every {check_interval_minutes} minutes...")
        
        # Schedule regular checks
        schedule.every(check_interval_minutes).minutes.do(self.check_for_updates)
        
        # Run initial check
        self.check_for_updates()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute for scheduled tasks
    
    def run_single_check(self):
        """Run a single check (useful for testing)"""
        print("🔍 Running single Notion check...")
        self.check_for_updates()
        print("✅ Single check complete")

# Convenience function to start watcher
def start_notion_watcher(interval_minutes: int = 15):
    """Start the Notion watcher with specified interval"""
    watcher = NotionWatcher()
    watcher.start_watching(interval_minutes)