#!/usr/bin/env python3
"""
Deal Calculator - Calculate potential earnings from each opportunity
Analyzes the financial value of GSA lease deals and your potential fees
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import json
from app.database import SessionLocal
from app.models import Prospectus, Property, Match

class DealCalculator:
    def __init__(self):
        self.fee_structures = {
            'finder_fee': 0.02,      # 2% of first year annual rent
            'consulting_fee': 25000,  # Fixed fee for compliance work
            'success_bonus': 0.01,    # 1% success fee
            'ongoing_commission': 0.005  # 0.5% of annual rent for ongoing management
        }
    
    def calculate_deal_value(self, prospectus, detailed=True):
        """Calculate comprehensive deal value and your potential earnings"""
        
        annual_value = prospectus.estimated_annual_cost or 0
        lease_term = prospectus.max_lease_term_years or 10
        sqft = prospectus.estimated_nusf or 0
        
        # Basic calculations
        calculations = {
            'opportunity_overview': {
                'prospectus_number': prospectus.prospectus_number,
                'agency': prospectus.agency,
                'location': f"{prospectus.location}, {prospectus.state}",
                'square_footage': sqft,
                'annual_lease_value': annual_value,
                'lease_term_years': lease_term,
                'total_lease_value': annual_value * lease_term,
                'rent_per_sqft': annual_value / sqft if sqft > 0 else 0
            },
            
            'your_potential_earnings': {
                'finder_fee': annual_value * self.fee_structures['finder_fee'],
                'consulting_fee': self.fee_structures['consulting_fee'],
                'success_bonus': annual_value * self.fee_structures['success_bonus'],
                'ongoing_annual_commission': annual_value * self.fee_structures['ongoing_commission'],
                'total_upfront': 0,  # Will calculate below
                'total_ongoing': 0,  # Will calculate below
                'total_potential': 0  # Will calculate below
            },
            
            'timeline_analysis': self.calculate_timeline_value(prospectus),
            'risk_assessment': self.assess_deal_risk(prospectus),
            'market_comparison': self.compare_to_market(prospectus)
        }
        
        # Calculate totals
        earnings = calculations['your_potential_earnings']
        earnings['total_upfront'] = (
            earnings['finder_fee'] + 
            earnings['consulting_fee'] + 
            earnings['success_bonus']
        )
        earnings['total_ongoing'] = earnings['ongoing_annual_commission'] * lease_term
        earnings['total_potential'] = earnings['total_upfront'] + earnings['total_ongoing']
        
        # Add profitability metrics
        calculations['profitability'] = {
            'roi_percentage': (earnings['total_potential'] / max(earnings['consulting_fee'], 1)) * 100,
            'profit_per_hour': self.estimate_profit_per_hour(earnings['total_potential']),
            'payback_period_months': self.estimate_payback_period(earnings),
            'risk_adjusted_value': earnings['total_potential'] * (1 - calculations['risk_assessment']['overall_risk'])
        }
        
        if detailed:
            self.print_deal_analysis(calculations)
        
        return calculations
    
    def calculate_timeline_value(self, prospectus):
        """Analyze timeline impact on deal value"""
        
        if not prospectus.current_lease_expiration:
            return {
                'urgency_level': 'Unknown',
                'days_until_expiration': None,
                'rfp_timeline': 'TBD',
                'urgency_multiplier': 1.0
            }
        
        days_until = (prospectus.current_lease_expiration - datetime.now()).days
        
        if days_until < 180:
            urgency_level = 'CRITICAL'
            urgency_multiplier = 1.3  # 30% bonus for urgent deals
        elif days_until < 365:
            urgency_level = 'HIGH'
            urgency_multiplier = 1.2  # 20% bonus
        elif days_until < 730:
            urgency_level = 'MEDIUM'
            urgency_multiplier = 1.1  # 10% bonus
        else:
            urgency_level = 'LOW'
            urgency_multiplier = 1.0
        
        return {
            'urgency_level': urgency_level,
            'days_until_expiration': days_until,
            'rfp_expected': prospectus.current_lease_expiration - timedelta(days=270),
            'urgency_multiplier': urgency_multiplier,
            'time_to_prepare': max(days_until - 270, 0)  # Time before RFP
        }
    
    def assess_deal_risk(self, prospectus):
        """Assess risk factors for the deal"""
        
        risk_factors = []
        risk_score = 0.0  # 0 = no risk, 1 = maximum risk
        
        # Size risk
        sqft = prospectus.estimated_nusf or 0
        if sqft > 200000:
            risk_factors.append("Large size increases competition")
            risk_score += 0.2
        elif sqft < 10000:
            risk_factors.append("Very small - may not be worth effort")
            risk_score += 0.1
        
        # Value risk
        annual_value = prospectus.estimated_annual_cost or 0
        if annual_value > 20000000:
            risk_factors.append("High value attracts major players")
            risk_score += 0.3
        elif annual_value < 500000:
            risk_factors.append("Low value - minimal fees")
            risk_score += 0.2
        
        # Location risk
        location = (prospectus.location or '').lower()
        high_competition_areas = ['washington', 'new york', 'los angeles', 'chicago', 'boston', 'san francisco']
        if any(area in location for area in high_competition_areas):
            risk_factors.append("Major metro area - high competition")
            risk_score += 0.3
        
        # Agency risk
        agency = (prospectus.agency or '').lower()
        if 'dod' in agency or 'defense' in agency:
            risk_factors.append("DoD contracts are highly competitive")
            risk_score += 0.2
        elif 'gsa' in agency and annual_value > 10000000:
            risk_factors.append("Large GSA deals attract established players")
            risk_score += 0.2
        
        # Timeline risk
        timeline = self.calculate_timeline_value(prospectus)
        if timeline['days_until_expiration'] and timeline['days_until_expiration'] < 90:
            risk_factors.append("Very short timeline - limited preparation time")
            risk_score += 0.3
        
        risk_level = 'LOW'
        if risk_score > 0.6:
            risk_level = 'HIGH'
        elif risk_score > 0.3:
            risk_level = 'MEDIUM'
        
        return {
            'overall_risk': min(risk_score, 1.0),
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'mitigation_strategies': self.suggest_risk_mitigation(risk_factors)
        }
    
    def suggest_risk_mitigation(self, risk_factors):
        """Suggest strategies to mitigate identified risks"""
        
        strategies = []
        
        for factor in risk_factors:
            if 'competition' in factor.lower():
                strategies.append("Early market entry and relationship building")
                strategies.append("Unique value proposition development")
            elif 'size' in factor.lower() or 'value' in factor.lower():
                strategies.append("Partner with established firms for large deals")
                strategies.append("Focus on specialized requirements")
            elif 'timeline' in factor.lower():
                strategies.append("Immediate action plan with accelerated preparation")
                strategies.append("Pre-qualified property options")
        
        return list(set(strategies))  # Remove duplicates
    
    def compare_to_market(self, prospectus):
        """Compare deal to market standards"""
        
        annual_value = prospectus.estimated_annual_cost or 0
        sqft = prospectus.estimated_nusf or 0
        rent_per_sqft = annual_value / sqft if sqft > 0 else 0
        
        # Market benchmarks (these would come from real data in production)
        market_benchmarks = {
            'average_deal_size': 5000000,
            'average_rent_psf': 25.0,
            'typical_lease_term': 10,
            'average_finder_fee': 100000
        }
        
        return {
            'deal_size_vs_market': annual_value / market_benchmarks['average_deal_size'],
            'rent_vs_market': rent_per_sqft / market_benchmarks['average_rent_psf'] if rent_per_sqft > 0 else 0,
            'deal_attractiveness': self.rate_deal_attractiveness(prospectus),
            'market_position': 'Above Average' if annual_value > market_benchmarks['average_deal_size'] else 'Below Average'
        }
    
    def rate_deal_attractiveness(self, prospectus):
        """Rate the overall attractiveness of the deal"""
        
        score = 0
        annual_value = prospectus.estimated_annual_cost or 0
        
        # Value scoring
        if annual_value > 10000000:
            score += 3
        elif annual_value > 5000000:
            score += 2
        elif annual_value > 2000000:
            score += 1
        
        # Timeline scoring
        timeline = self.calculate_timeline_value(prospectus)
        if timeline['urgency_level'] in ['CRITICAL', 'HIGH']:
            score += 2
        elif timeline['urgency_level'] == 'MEDIUM':
            score += 1
        
        # Agency scoring
        agency = (prospectus.agency or '').lower()
        if 'va' in agency:
            score += 2  # VA deals often have less competition
        elif 'gsa' in agency:
            score += 1
        
        if score >= 7:
            return 'EXCELLENT'
        elif score >= 5:
            return 'GOOD'
        elif score >= 3:
            return 'FAIR'
        else:
            return 'POOR'
    
    def estimate_profit_per_hour(self, total_potential):
        """Estimate profit per hour based on typical effort"""
        
        # Estimate total hours for a deal
        estimated_hours = {
            'research_and_analysis': 20,
            'property_identification': 30,
            'owner_outreach': 40,
            'proposal_preparation': 60,
            'negotiation_and_closing': 30,
            'ongoing_management': 20
        }
        
        total_hours = sum(estimated_hours.values())
        return total_potential / total_hours if total_hours > 0 else 0
    
    def estimate_payback_period(self, earnings):
        """Estimate how long to recoup initial investment"""
        
        # Assume initial investment is mostly time (opportunity cost)
        initial_investment = earnings['consulting_fee']  # Use consulting fee as proxy
        monthly_return = earnings['total_upfront'] / 6  # Assume 6 months to close
        
        if monthly_return > 0:
            return initial_investment / monthly_return
        else:
            return 12  # Default to 12 months if calculation fails
    
    def print_deal_analysis(self, calculations):
        """Print formatted deal analysis"""
        
        overview = calculations['opportunity_overview']
        earnings = calculations['your_potential_earnings']
        timeline = calculations['timeline_analysis']
        risk = calculations['risk_assessment']
        profitability = calculations['profitability']
        
        print(f"\n🎯 DEAL ANALYSIS: {overview['prospectus_number']}")
        print("=" * 60)
        
        print(f"📍 Location: {overview['location']}")
        print(f"🏢 Size: {overview['square_footage']:,} sq ft")
        print(f"💰 Annual Value: ${overview['annual_lease_value']:,.0f}")
        print(f"📅 Lease Term: {overview['lease_term_years']} years")
        print(f"💵 Total Value: ${overview['total_lease_value']:,.0f}")
        print(f"📊 Rate: ${overview['rent_per_sqft']:.2f}/sq ft")
        
        print(f"\n💼 YOUR POTENTIAL EARNINGS:")
        print(f"   Finder's Fee (2%): ${earnings['finder_fee']:,.0f}")
        print(f"   Consulting Fee: ${earnings['consulting_fee']:,.0f}")
        print(f"   Success Bonus (1%): ${earnings['success_bonus']:,.0f}")
        print(f"   ─────────────────────────────────")
        print(f"   UPFRONT TOTAL: ${earnings['total_upfront']:,.0f}")
        print(f"   Ongoing Annual: ${earnings['ongoing_annual_commission']:,.0f}")
        print(f"   GRAND TOTAL: ${earnings['total_potential']:,.0f}")
        
        print(f"\n⏰ TIMELINE ANALYSIS:")
        print(f"   Urgency Level: {timeline['urgency_level']}")
        if timeline['days_until_expiration']:
            print(f"   Days Until Expiration: {timeline['days_until_expiration']}")
        print(f"   Urgency Multiplier: {timeline['urgency_multiplier']:.1f}x")
        
        print(f"\n⚠️  RISK ASSESSMENT: {risk['risk_level']}")
        if risk['risk_factors']:
            print(f"   Risk Factors:")
            for factor in risk['risk_factors']:
                print(f"     • {factor}")
        
        print(f"\n📈 PROFITABILITY METRICS:")
        print(f"   ROI: {profitability['roi_percentage']:.0f}%")
        print(f"   Profit/Hour: ${profitability['profit_per_hour']:,.0f}")
        print(f"   Payback: {profitability['payback_period_months']:.1f} months")
        print(f"   Risk-Adjusted Value: ${profitability['risk_adjusted_value']:,.0f}")
        
        # Deal rating
        market = calculations['market_comparison']
        print(f"\n⭐ DEAL RATING: {market['deal_attractiveness']}")
        
        return calculations
    
    def analyze_portfolio(self):
        """Analyze entire portfolio of opportunities"""
        
        print("🦅 PORTFOLIO ANALYSIS - ALL OPPORTUNITIES")
        print("=" * 60)
        
        db = SessionLocal()
        
        try:
            prospectuses = db.query(Prospectus).filter(
                Prospectus.status == 'active'
            ).all()
            
            if not prospectuses:
                print("❌ No active prospectuses found")
                return
            
            portfolio_data = []
            total_potential = 0
            
            print(f"📊 Analyzing {len(prospectuses)} opportunities...\n")
            
            for prospectus in prospectuses:
                deal_calc = self.calculate_deal_value(prospectus, detailed=False)
                portfolio_data.append(deal_calc)
                total_potential += deal_calc['your_potential_earnings']['total_potential']
            
            # Sort by potential earnings
            portfolio_data.sort(
                key=lambda x: x['your_potential_earnings']['total_potential'], 
                reverse=True
            )
            
            # Print summary table
            print(f"{'Rank':<4} {'Prospectus':<15} {'Location':<20} {'Annual Value':<12} {'Your Fee':<12} {'Rating':<10}")
            print("-" * 85)
            
            for i, deal in enumerate(portfolio_data, 1):
                overview = deal['opportunity_overview']
                earnings = deal['your_potential_earnings']
                rating = deal['market_comparison']['deal_attractiveness']
                
                print(f"{i:<4} {overview['prospectus_number'][:14]:<15} "
                      f"{overview['location'][:19]:<20} "
                      f"${overview['annual_lease_value']/1000000:.1f}M{'':<6} "
                      f"${earnings['total_potential']/1000:.0f}K{'':<7} "
                      f"{rating:<10}")
            
            # Portfolio summary
            print(f"\n💰 PORTFOLIO SUMMARY:")
            print(f"   Total Opportunities: {len(portfolio_data)}")
            print(f"   Total Potential Earnings: ${total_potential:,.0f}")
            print(f"   Average per Deal: ${total_potential/len(portfolio_data):,.0f}")
            
            # Top opportunities
            top_5 = portfolio_data[:5]
            top_5_total = sum(d['your_potential_earnings']['total_potential'] for d in top_5)
            
            print(f"\n🎯 TOP 5 OPPORTUNITIES (${top_5_total:,.0f} potential):")
            for i, deal in enumerate(top_5, 1):
                overview = deal['opportunity_overview']
                earnings = deal['your_potential_earnings']
                timeline = deal['timeline_analysis']
                
                print(f"{i}. {overview['prospectus_number']} - {overview['location']}")
                print(f"   Potential: ${earnings['total_potential']:,.0f} | "
                      f"Urgency: {timeline['urgency_level']}")
            
            # Risk analysis
            high_risk = [d for d in portfolio_data if d['risk_assessment']['risk_level'] == 'HIGH']
            low_risk = [d for d in portfolio_data if d['risk_assessment']['risk_level'] == 'LOW']
            
            print(f"\n⚠️  RISK DISTRIBUTION:")
            print(f"   Low Risk: {len(low_risk)} deals")
            print(f"   Medium Risk: {len(portfolio_data) - len(high_risk) - len(low_risk)} deals")
            print(f"   High Risk: {len(high_risk)} deals")
            
            # Action recommendations
            print(f"\n🚀 RECOMMENDED ACTION PLAN:")
            print(f"1. Focus on top 3 opportunities: ${sum(d['your_potential_earnings']['total_potential'] for d in top_5[:3]):,.0f}")
            print(f"2. Prioritize {len([d for d in top_5 if d['timeline_analysis']['urgency_level'] in ['CRITICAL', 'HIGH']])} urgent deals")
            print(f"3. Target low-risk, high-value opportunities first")
            
            # Save portfolio analysis
            self.save_portfolio_analysis(portfolio_data, total_potential)
            
        finally:
            db.close()
    
    def save_portfolio_analysis(self, portfolio_data, total_potential):
        """Save portfolio analysis to file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"data/portfolio_analysis_{timestamp}.json"
        
        os.makedirs("data", exist_ok=True)
        
        analysis_summary = {
            'timestamp': timestamp,
            'total_opportunities': len(portfolio_data),
            'total_potential_earnings': total_potential,
            'average_per_deal': total_potential / len(portfolio_data) if portfolio_data else 0,
            'deals': []
        }
        
        for deal in portfolio_data:
            deal_summary = {
                'prospectus_number': deal['opportunity_overview']['prospectus_number'],
                'location': deal['opportunity_overview']['location'],
                'annual_value': deal['opportunity_overview']['annual_lease_value'],
                'potential_earnings': deal['your_potential_earnings']['total_potential'],
                'risk_level': deal['risk_assessment']['risk_level'],
                'deal_rating': deal['market_comparison']['deal_attractiveness'],
                'urgency_level': deal['timeline_analysis']['urgency_level']
            }
            analysis_summary['deals'].append(deal_summary)
        
        with open(filename, 'w') as f:
            json.dump(analysis_summary, f, indent=2, default=str)
        
        print(f"\n💾 Portfolio analysis saved: {filename}")

def main():
    """Main calculator function"""
    
    import argparse
    parser = argparse.ArgumentParser(description="Calculate deal values")
    parser.add_argument("--prospectus-id", type=int, help="Calculate for specific prospectus")
    parser.add_argument("--portfolio", action="store_true", help="Analyze entire portfolio")
    parser.add_argument("--top", type=int, default=10, help="Show top N opportunities")
    
    args = parser.parse_args()
    
    calculator = DealCalculator()
    
    if args.prospectus_id:
        db = SessionLocal()
        prospectus = db.query(Prospectus).filter(Prospectus.id == args.prospectus_id).first()
        if prospectus:
            calculator.calculate_deal_value(prospectus, detailed=True)
        else:
            print(f"❌ Prospectus ID {args.prospectus_id} not found")
        db.close()
    
    elif args.portfolio:
        calculator.analyze_portfolio()
    
    else:
        # Show top opportunities by default
        db = SessionLocal()
        prospectuses = db.query(Prospectus).filter(
            Prospectus.status == 'active'
        ).order_by(Prospectus.estimated_annual_cost.desc()).limit(args.top).all()
        
        print(f"🎯 TOP {len(prospectuses)} OPPORTUNITIES BY VALUE")
        print("=" * 60)
        
        for prospectus in prospectuses:
            calculator.calculate_deal_value(prospectus, detailed=True)
            print("\n" + "-" * 60 + "\n")
        
        db.close()

if __name__ == "__main__":
    main()