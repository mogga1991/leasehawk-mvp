#!/usr/bin/env python3
"""
Daily Intelligence Brief - Your Secret Weapon Command
Combines all LeaseHawk tools for comprehensive daily intelligence
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import json
from app.database import SessionLocal
from app.models import Prospectus, Property, Match

# Import our custom scripts
from complete_workflow import run_complete_workflow
from win_strategy import WinningStrategy
from deal_calculator import DealCalculator
from property_hunter import PropertyHunter
from outreach_generator import OutreachGenerator

class DailyIntelligenceBrief:
    def __init__(self):
        self.strategy = WinningStrategy()
        self.calculator = DealCalculator()
        self.hunter = PropertyHunter()
        self.outreach = OutreachGenerator()
        self.brief_data = {}
        
    def generate_daily_brief(self):
        """Generate complete daily intelligence brief"""
        
        print("🦅 LEASEHAWK DAILY INTELLIGENCE BRIEF")
        print(f"📅 {datetime.now().strftime('%A, %B %d, %Y')}")
        print("=" * 60)
        
        # 1. Market Intelligence Update
        print("\n📊 MARKET INTELLIGENCE UPDATE")
        print("-" * 40)
        self.market_intelligence_update()
        
        # 2. New Opportunities Alert
        print("\n🚨 NEW OPPORTUNITIES ALERT")
        print("-" * 40)
        new_opps = self.check_new_opportunities()
        
        # 3. Top 5 Easiest Wins
        print("\n🎯 TOP 5 EASIEST WINS TODAY")
        print("-" * 40)
        easy_wins = self.get_easiest_wins()
        
        # 4. Urgent Actions Required
        print("\n⚠️  URGENT ACTIONS REQUIRED")
        print("-" * 40)
        urgent_actions = self.identify_urgent_actions()
        
        # 5. Portfolio Performance
        print("\n💰 PORTFOLIO PERFORMANCE")
        print("-" * 40)
        portfolio_summary = self.portfolio_performance()
        
        # 6. Today's Action Plan
        print("\n📋 TODAY'S ACTION PLAN")
        print("-" * 40)
        action_plan = self.create_daily_action_plan(easy_wins, urgent_actions)
        
        # 7. Intelligence Summary
        print("\n🧠 INTELLIGENCE SUMMARY")
        print("-" * 40)
        self.intelligence_summary(new_opps, easy_wins, urgent_actions, portfolio_summary)
        
        # Save brief
        self.save_daily_brief()
        
        return self.brief_data
    
    def market_intelligence_update(self):
        """Update on overall market conditions"""
        
        db = SessionLocal()
        
        try:
            # Count active opportunities
            total_active = db.query(Prospectus).filter(Prospectus.status == 'active').count()
            
            # New this week
            week_ago = datetime.now() - timedelta(days=7)
            new_this_week = db.query(Prospectus).filter(
                Prospectus.created_at >= week_ago
            ).count()
            
            # Expiring soon (next 6 months)
            six_months = datetime.now() + timedelta(days=180)
            expiring_soon = db.query(Prospectus).filter(
                Prospectus.current_lease_expiration <= six_months,
                Prospectus.current_lease_expiration > datetime.now(),
                Prospectus.status == 'active'
            ).count()
            
            # High value opportunities (>$5M annual)
            high_value = db.query(Prospectus).filter(
                Prospectus.estimated_annual_cost > 5000000,
                Prospectus.status == 'active'
            ).count()
            
            print(f"📈 Total Active Opportunities: {total_active}")
            print(f"🆕 New This Week: {new_this_week}")
            print(f"⏰ Expiring <6 Months: {expiring_soon}")
            print(f"💎 High Value (>$5M): {high_value}")
            
            self.brief_data['market_intelligence'] = {
                'total_active': total_active,
                'new_this_week': new_this_week,
                'expiring_soon': expiring_soon,
                'high_value': high_value
            }
            
        finally:
            db.close()
    
    def check_new_opportunities(self):
        """Check for new opportunities since last check"""
        
        db = SessionLocal()
        
        try:
            # New opportunities in last 24 hours
            yesterday = datetime.now() - timedelta(days=1)
            new_prospects = db.query(Prospectus).filter(
                Prospectus.created_at >= yesterday
            ).all()
            
            if not new_prospects:
                print("🔍 No new opportunities in last 24 hours")
                print("💡 Consider running: python scripts/load_all_gsa.py")
                return []
            
            new_opportunities = []
            
            for prospect in new_prospects:
                # Calculate potential value
                potential_fee = (prospect.estimated_annual_cost or 0) * 0.02
                
                new_opportunities.append({
                    'prospectus': prospect,
                    'potential_fee': potential_fee,
                    'urgency': self.calculate_urgency_days(prospect)
                })
                
                print(f"🆕 {prospect.agency} - {prospect.location}")
                print(f"   Annual Value: ${prospect.estimated_annual_cost:,.0f}")
                print(f"   Your Potential Fee: ${potential_fee:,.0f}")
                print(f"   Prospectus: {prospect.prospectus_number}")
            
            # Auto-trigger property hunting for high-value new opportunities
            high_value_new = [o for o in new_opportunities if o['potential_fee'] > 50000]
            if high_value_new:
                print(f"\n🎯 AUTO-TRIGGERING property hunt for {len(high_value_new)} high-value opportunities")
                for opp in high_value_new:
                    try:
                        self.hunter.hunt_for_prospectus(opp['prospectus'])
                    except Exception as e:
                        print(f"❌ Hunt failed for {opp['prospectus'].prospectus_number}: {e}")
            
            self.brief_data['new_opportunities'] = len(new_opportunities)
            return new_opportunities
            
        finally:
            db.close()
    
    def get_easiest_wins(self):
        """Get today's easiest wins"""
        
        try:
            easy_wins = self.strategy.identify_easiest_wins(5)
            
            if not easy_wins:
                print("🔍 No opportunities analyzed yet")
                print("💡 Run: python scripts/complete_workflow.py --full")
                return []
            
            total_potential = sum(w['potential_fee'] for w in easy_wins)
            
            print(f"💰 Total Potential from Top 5: ${total_potential:,.0f}")
            print()
            
            for i, win in enumerate(easy_wins, 1):
                p = win['prospectus']
                print(f"{i}. {p.agency} - {p.location}")
                print(f"   Win Probability: {win['win_probability']:.0f}%")
                print(f"   Potential Fee: ${win['potential_fee']:,.0f}")
                print(f"   Urgency: {win['urgency_days']} days")
                print(f"   Why Easy: {win['reasoning'][0] if win['reasoning'] else 'Strategic advantage'}")
                print()
            
            self.brief_data['easiest_wins'] = easy_wins
            return easy_wins
            
        except Exception as e:
            print(f"❌ Error getting easiest wins: {e}")
            return []
    
    def identify_urgent_actions(self):
        """Identify actions that need immediate attention"""
        
        db = SessionLocal()
        urgent_actions = []
        
        try:
            # 1. Opportunities expiring in <90 days
            ninety_days = datetime.now() + timedelta(days=90)
            urgent_expiring = db.query(Prospectus).filter(
                Prospectus.current_lease_expiration <= ninety_days,
                Prospectus.current_lease_expiration > datetime.now(),
                Prospectus.status == 'active'
            ).all()
            
            for prospect in urgent_expiring:
                days_left = (prospect.current_lease_expiration - datetime.now()).days
                urgent_actions.append({
                    'type': 'EXPIRING_SOON',
                    'priority': 'CRITICAL' if days_left < 60 else 'HIGH',
                    'prospectus': prospect,
                    'action': f'RFP expected within {90 - days_left} days',
                    'deadline': prospect.current_lease_expiration - timedelta(days=270)
                })
            
            # 2. High-value opportunities without properties matched
            high_value_unmatched = db.query(Prospectus).filter(
                Prospectus.estimated_annual_cost > 3000000,
                Prospectus.status == 'active'
            ).all()
            
            for prospect in high_value_unmatched:
                match_count = db.query(Match).filter(Match.prospectus_id == prospect.id).count()
                if match_count == 0:
                    urgent_actions.append({
                        'type': 'NO_PROPERTIES',
                        'priority': 'HIGH',
                        'prospectus': prospect,
                        'action': 'Run property hunting immediately',
                        'potential_lost': (prospect.estimated_annual_cost or 0) * 0.02
                    })
            
            # 3. Properties found but no outreach generated
            prospects_with_matches = db.query(Prospectus).join(Match).filter(
                Prospectus.estimated_annual_cost > 2000000
            ).distinct().all()
            
            for prospect in prospects_with_matches:
                # Check if outreach was generated (this would need tracking in production)
                urgent_actions.append({
                    'type': 'OUTREACH_NEEDED',
                    'priority': 'MEDIUM',
                    'prospectus': prospect,
                    'action': 'Generate and execute outreach campaign',
                    'matches_available': db.query(Match).filter(Match.prospectus_id == prospect.id).count()
                })
            
            # Sort by priority and potential value
            urgent_actions.sort(key=lambda x: (
                0 if x['priority'] == 'CRITICAL' else 1 if x['priority'] == 'HIGH' else 2,
                -(x['prospectus'].estimated_annual_cost or 0)
            ))
            
            # Display urgent actions
            if not urgent_actions:
                print("✅ No urgent actions identified")
            else:
                for action in urgent_actions[:5]:  # Top 5 most urgent
                    p = action['prospectus']
                    print(f"🚨 {action['priority']}: {action['type']}")
                    print(f"   {p.agency} - {p.location}")
                    print(f"   Action: {action['action']}")
                    print(f"   Value: ${p.estimated_annual_cost:,.0f}")
                    print()
            
            self.brief_data['urgent_actions'] = len(urgent_actions)
            return urgent_actions
            
        finally:
            db.close()
    
    def portfolio_performance(self):
        """Analyze overall portfolio performance"""
        
        try:
            db = SessionLocal()
            
            # Total potential value
            all_prospects = db.query(Prospectus).filter(Prospectus.status == 'active').all()
            total_annual_value = sum((p.estimated_annual_cost or 0) for p in all_prospects)
            total_potential_fees = total_annual_value * 0.02
            
            # Properties matched
            total_matches = db.query(Match).count()
            
            # High-scoring matches (>80%)
            high_score_matches = db.query(Match).filter(Match.total_score > 80).count()
            
            print(f"💼 Total Portfolio Value: ${total_annual_value:,.0f}")
            print(f"💰 Total Potential Fees: ${total_potential_fees:,.0f}")
            print(f"🏢 Properties Matched: {total_matches}")
            print(f"⭐ High-Score Matches: {high_score_matches}")
            
            # Calculate success metrics
            if all_prospects:
                avg_value = total_annual_value / len(all_prospects)
                match_rate = total_matches / len(all_prospects) if all_prospects else 0
                
                print(f"📊 Average Deal Size: ${avg_value:,.0f}")
                print(f"📈 Match Rate: {match_rate:.1f} properties per prospectus")
            
            portfolio_summary = {
                'total_value': total_annual_value,
                'potential_fees': total_potential_fees,
                'total_matches': total_matches,
                'high_score_matches': high_score_matches,
                'opportunities': len(all_prospects)
            }
            
            self.brief_data['portfolio'] = portfolio_summary
            db.close()
            
            return portfolio_summary
            
        except Exception as e:
            print(f"❌ Error analyzing portfolio: {e}")
            return {}
    
    def create_daily_action_plan(self, easy_wins, urgent_actions):
        """Create specific action plan for today"""
        
        actions = []
        
        # Priority 1: Handle urgent items
        critical_urgent = [a for a in urgent_actions if a['priority'] == 'CRITICAL'][:3]
        for urgent in critical_urgent:
            actions.append(f"🚨 URGENT: {urgent['action']} - {urgent['prospectus'].prospectus_number}")
        
        # Priority 2: Work on easiest wins
        if easy_wins:
            top_win = easy_wins[0]
            actions.append(f"🎯 START: Generate outreach for {top_win['prospectus'].prospectus_number} (${top_win['potential_fee']:,.0f} potential)")
            
            if len(easy_wins) > 1:
                second_win = easy_wins[1]
                actions.append(f"🏢 HUNT: Find properties for {second_win['prospectus'].prospectus_number}")
        
        # Priority 3: Maintenance tasks
        actions.append("📥 SYNC: Run Notion sync to check for new opportunities")
        actions.append("📞 FOLLOW-UP: Contact property owners from yesterday's outreach")
        
        # Priority 4: Pipeline development
        actions.append("🔍 RESEARCH: Check GSA prospectus library for new releases")
        
        print("📝 Today's Priority Actions:")
        for i, action in enumerate(actions, 1):
            print(f"{i}. {action}")
        
        # Specific time blocks
        print(f"\n⏰ SUGGESTED SCHEDULE:")
        print(f"9:00-10:00 AM  🚨 Handle critical urgent items")
        print(f"10:00-12:00 PM 🎯 Work on top easiest win")
        print(f"1:00-3:00 PM   📞 Outreach calls and follow-ups")
        print(f"3:00-4:00 PM   🏢 Property hunting and research")
        print(f"4:00-5:00 PM   📥 Admin and pipeline development")
        
        self.brief_data['daily_actions'] = actions
        return actions
    
    def intelligence_summary(self, new_opps, easy_wins, urgent_actions, portfolio):
        """Provide strategic intelligence summary"""
        
        # Calculate key metrics
        if easy_wins:
            top_3_potential = sum(w['potential_fee'] for w in easy_wins[:3])
        else:
            top_3_potential = 0
        
        critical_count = len([a for a in urgent_actions if a['priority'] == 'CRITICAL'])
        
        print(f"🧠 KEY INTELLIGENCE:")
        print(f"   New Opportunities: {len(new_opps)} (last 24h)")
        print(f"   Critical Actions: {critical_count}")
        print(f"   Top 3 Win Potential: ${top_3_potential:,.0f}")
        print(f"   Portfolio Value: ${portfolio.get('total_value', 0):,.0f}")
        
        # Strategic recommendations
        print(f"\n💡 STRATEGIC INSIGHTS:")
        
        if critical_count > 3:
            print(f"   ⚠️  High urgency load - prioritize critical items")
        elif critical_count == 0:
            print(f"   ✅ Good pipeline health - focus on growth")
        
        if len(new_opps) > 2:
            print(f"   📈 Strong opportunity flow - scale outreach")
        elif len(new_opps) == 0:
            print(f"   🔍 Opportunity gap - increase sourcing efforts")
        
        if top_3_potential > 200000:
            print(f"   💰 High-value pipeline - excellent potential")
            print(f"   🎯 Focus on conversion for maximum impact")
        
        # Market intelligence
        market_trend = "GROWING" if len(new_opps) > 1 else "STABLE" if len(new_opps) == 1 else "DECLINING"
        print(f"   📊 Market Trend: {market_trend}")
        
        # Success probability
        if easy_wins and easy_wins[0]['win_probability'] > 70:
            print(f"   🏆 High win probability on top opportunity")
        
        self.brief_data['intelligence_summary'] = {
            'new_opportunities': len(new_opps),
            'critical_actions': critical_count,
            'top_3_potential': top_3_potential,
            'market_trend': market_trend
        }
    
    def calculate_urgency_days(self, prospectus):
        """Calculate days until action needed"""
        if not prospectus.current_lease_expiration:
            return 999
        return (prospectus.current_lease_expiration - datetime.now()).days - 270  # 9 months before exp
    
    def save_daily_brief(self):
        """Save daily brief to file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"data/daily_brief_{timestamp}.json"
        
        os.makedirs("data", exist_ok=True)
        
        self.brief_data['timestamp'] = datetime.now().isoformat()
        self.brief_data['generated_by'] = 'LeaseHawk Daily Intelligence'
        
        with open(filename, 'w') as f:
            json.dump(self.brief_data, f, indent=2, default=str)
        
        print(f"\n💾 Daily brief saved: {filename}")
        
        # Also save a latest.json for easy access
        latest_file = "data/daily_brief_latest.json"
        with open(latest_file, 'w') as f:
            json.dump(self.brief_data, f, indent=2, default=str)

def run_morning_brief():
    """Run the morning intelligence brief"""
    brief = DailyIntelligenceBrief()
    return brief.generate_daily_brief()

def run_full_workflow_with_brief():
    """Run complete workflow followed by intelligence brief"""
    
    print("🔄 Running Complete Workflow...")
    try:
        run_complete_workflow()
    except Exception as e:
        print(f"⚠️  Workflow error: {e}")
    
    print("\n" + "="*60 + "\n")
    
    print("🧠 Generating Intelligence Brief...")
    return run_morning_brief()

def main():
    """Main function with command options"""
    
    import argparse
    parser = argparse.ArgumentParser(description="LeaseHawk Daily Intelligence Brief")
    parser.add_argument("--brief-only", action="store_true", help="Generate brief only (skip workflow)")
    parser.add_argument("--full", action="store_true", help="Run complete workflow + brief")
    
    args = parser.parse_args()
    
    if args.brief_only:
        run_morning_brief()
    elif args.full:
        run_full_workflow_with_brief()
    else:
        # Default: brief only
        run_morning_brief()

if __name__ == "__main__":
    main()