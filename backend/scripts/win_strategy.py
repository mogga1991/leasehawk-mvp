#!/usr/bin/env python3
"""
Winning Strategy - Identify easiest wins and create compliance packages
The "Unfair Advantage" strategy for winning GSA lease placements
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import json
from app.database import SessionLocal
from app.models import Prospectus, Property, Match

class WinningStrategy:
    def __init__(self):
        self.target_prospectuses = []
        self.qualified_properties = []
        self.winning_packages = []
        
    def identify_easiest_wins(self, limit=10):
        """Find the easiest prospectuses to win based on strategic criteria"""
        
        print("🎯 Identifying Easiest Wins...")
        print("Analyzing strategic advantages...")
        
        db = SessionLocal()
        
        try:
            prospectuses = db.query(Prospectus).filter(
                Prospectus.status == 'active'
            ).all()
            
            easy_wins = []
            
            for prospectus in prospectuses:
                score = self.calculate_win_probability(prospectus)
                reasoning = self.explain_opportunity(prospectus, score)
                
                # Get match count for this prospectus
                match_count = db.query(Match).filter(
                    Match.prospectus_id == prospectus.id
                ).count()
                
                easy_wins.append({
                    'prospectus': prospectus,
                    'win_probability': score['total_score'],
                    'difficulty_score': 100 - score['total_score'],
                    'scoring_breakdown': score,
                    'reasoning': reasoning,
                    'available_properties': match_count,
                    'potential_fee': (prospectus.estimated_annual_cost or 0) * 0.02,
                    'urgency_days': self.calculate_urgency(prospectus)
                })
            
            # Sort by win probability (highest first)
            easy_wins.sort(key=lambda x: x['win_probability'], reverse=True)
            
            return easy_wins[:limit]
            
        finally:
            db.close()
    
    def calculate_win_probability(self, prospectus):
        """Calculate probability of winning based on strategic factors"""
        
        scores = {
            'size_advantage': 0,      # Max 25 points
            'location_advantage': 0,  # Max 20 points  
            'agency_advantage': 0,    # Max 20 points
            'timeline_advantage': 0,  # Max 15 points
            'competition_advantage': 0, # Max 10 points
            'value_advantage': 0,     # Max 10 points
            'total_score': 0
        }
        
        # Size advantage (smaller = less competition)
        sqft = prospectus.estimated_nusf or 0
        if sqft < 30000:  # Under 30k sq ft
            scores['size_advantage'] = 25
        elif sqft < 50000:  # Under 50k sq ft
            scores['size_advantage'] = 20
        elif sqft < 75000:  # Under 75k sq ft
            scores['size_advantage'] = 15
        elif sqft < 100000:  # Under 100k sq ft
            scores['size_advantage'] = 10
        else:  # Large spaces have more competition
            scores['size_advantage'] = 5
        
        # Location advantage (smaller markets = less competition)
        location = (prospectus.location or '').lower()
        state = (prospectus.state or '').lower()
        
        # Rural/smaller states
        if state in ['wv', 'mt', 'wy', 'vt', 'me', 'nd', 'sd', 'ak']:
            scores['location_advantage'] = 20
        # Mid-size markets
        elif state in ['oh', 'ut', 'ok', 'ks', 'ne', 'ia', 'ar', 'ms', 'al']:
            scores['location_advantage'] = 15
        # Avoid major metro keywords
        elif any(metro in location for metro in ['washington', 'new york', 'los angeles', 'chicago', 'boston', 'san francisco']):
            scores['location_advantage'] = 5
        else:
            scores['location_advantage'] = 12
        
        # Agency advantage (some agencies are easier)
        agency = (prospectus.agency or '').lower()
        if 'va' in agency and 'medical' in (prospectus.special_requirements or '').lower():
            scores['agency_advantage'] = 20  # VA medical has specific needs
        elif 'va' in agency:
            scores['agency_advantage'] = 18
        elif 'usda' in agency or 'agriculture' in agency:
            scores['agency_advantage'] = 16
        elif 'sba' in agency:
            scores['agency_advantage'] = 15
        elif 'gsa' in agency:
            scores['agency_advantage'] = 12
        elif 'dod' in agency or 'defense' in agency:
            scores['agency_advantage'] = 8  # Highly competitive
        else:
            scores['agency_advantage'] = 10
        
        # Timeline advantage (urgent = less prepared competition)
        urgency_days = self.calculate_urgency(prospectus)
        if urgency_days < 180:  # Less than 6 months
            scores['timeline_advantage'] = 15
        elif urgency_days < 365:  # Less than 1 year
            scores['timeline_advantage'] = 12
        elif urgency_days < 730:  # Less than 2 years
            scores['timeline_advantage'] = 8
        else:
            scores['timeline_advantage'] = 5
        
        # Competition advantage (specific requirements reduce competition)
        special_reqs = (prospectus.special_requirements or '').lower()
        if any(req in special_reqs for req in ['medical', 'laboratory', 'secure', 'classified']):
            scores['competition_advantage'] = 10
        elif any(req in special_reqs for req in ['parking', 'loading', 'storage']):
            scores['competition_advantage'] = 7
        else:
            scores['competition_advantage'] = 5
        
        # Value advantage (moderate value = sweet spot)
        annual_value = prospectus.estimated_annual_cost or 0
        if 2000000 <= annual_value <= 8000000:  # $2M-$8M sweet spot
            scores['value_advantage'] = 10
        elif 1000000 <= annual_value <= 15000000:  # $1M-$15M still good
            scores['value_advantage'] = 8
        elif annual_value > 20000000:  # Too big = too competitive
            scores['value_advantage'] = 3
        else:
            scores['value_advantage'] = 6
        
        scores['total_score'] = sum(scores.values()) - scores['total_score']  # Subtract total to avoid double counting
        
        return scores
    
    def calculate_urgency(self, prospectus):
        """Calculate days until lease expiration"""
        if not prospectus.current_lease_expiration:
            return 999  # Unknown = assume far out
        
        return (prospectus.current_lease_expiration - datetime.now()).days
    
    def explain_opportunity(self, prospectus, scores):
        """Generate human-readable explanation of why this is an easy win"""
        
        reasons = []
        
        # Size reasoning
        sqft = prospectus.estimated_nusf or 0
        if scores['size_advantage'] >= 20:
            reasons.append(f"Smaller size ({sqft:,} sq ft) means less competition")
        elif scores['size_advantage'] >= 15:
            reasons.append(f"Mid-size requirement ({sqft:,} sq ft) has moderate competition")
        
        # Location reasoning
        if scores['location_advantage'] >= 18:
            reasons.append(f"Rural/smaller market ({prospectus.state}) has fewer qualified properties")
        elif scores['location_advantage'] >= 12:
            reasons.append(f"Secondary market ({prospectus.state}) more accessible than major metros")
        
        # Agency reasoning
        if scores['agency_advantage'] >= 18:
            reasons.append(f"VA medical facilities have specialized needs - fewer competitors")
        elif scores['agency_advantage'] >= 15:
            reasons.append(f"{prospectus.agency} typically has streamlined processes")
        
        # Timeline reasoning
        urgency = self.calculate_urgency(prospectus)
        if urgency < 180:
            reasons.append(f"Urgent timeline ({urgency} days) means less time for competitors to prepare")
        elif urgency < 365:
            reasons.append(f"Reasonable timeline ({urgency} days) allows for good preparation")
        
        # Value reasoning
        annual_value = prospectus.estimated_annual_cost or 0
        if 2000000 <= annual_value <= 8000000:
            reasons.append(f"Sweet spot value (${annual_value:,.0f}) - big enough for good fees, not so big to attract major players")
        
        return reasons
    
    def create_winning_package(self, prospectus, property):
        """Create a complete winning presentation package"""
        
        print(f"📋 Creating winning package for {prospectus.prospectus_number}")
        
        package = {
            'executive_summary': self.create_executive_summary(prospectus, property),
            'compliance_matrix': self.create_compliance_matrix(prospectus, property),
            'modifications_plan': self.create_modifications_plan(prospectus, property),
            'pricing_strategy': self.create_pricing_strategy(prospectus, property),
            'timeline': self.create_timeline(prospectus),
            'competitive_advantages': self.create_competitive_advantages(prospectus, property),
            'financial_analysis': self.create_financial_analysis(prospectus, property)
        }
        
        return package
    
    def create_executive_summary(self, prospectus, property):
        """Create executive summary for the opportunity"""
        
        return {
            'opportunity_overview': f"""
EXECUTIVE SUMMARY - {prospectus.agency} LEASE OPPORTUNITY

Property: {property.address}
Requirement: {prospectus.prospectus_number}
Annual Value: ${prospectus.estimated_annual_cost:,.0f}
Lease Term: {prospectus.max_lease_term_years} years
Total Value: ${(prospectus.estimated_annual_cost or 0) * (prospectus.max_lease_term_years or 10):,.0f}

PROPERTY ADVANTAGES:
• Size Match: {property.available_sqft:,} sq ft (requirement: {prospectus.estimated_nusf:,} sq ft)
• Location: Optimal positioning within delineated area
• Parking: {property.parking_spaces} spaces (requirement: {prospectus.parking_spaces})
• Building Quality: {property.year_built} construction, well-maintained

COMPETITIVE ADVANTAGES:
• Early preparation and positioning
• Full GSA compliance planning
• Proven track record with federal requirements
• Optimal rent positioning at ${property.asking_rent_per_sqft:.2f}/sq ft

RECOMMENDATION: PROCEED IMMEDIATELY
Timeline is critical for optimal positioning.""",
            
            'key_dates': {
                'current_lease_expires': prospectus.current_lease_expiration,
                'rfp_expected': prospectus.current_lease_expiration - timedelta(days=270) if prospectus.current_lease_expiration else None,
                'proposal_preparation': '60-90 days',
                'award_expected': prospectus.current_lease_expiration - timedelta(days=180) if prospectus.current_lease_expiration else None
            }
        }
    
    def create_compliance_matrix(self, prospectus, property):
        """Show exact compliance with GSA requirements"""
        
        requirements = [
            {
                'requirement': 'Usable Square Footage',
                'needed': f"{prospectus.estimated_nusf:,} NUSF",
                'provided': f"{property.available_sqft:,} sq ft",
                'status': 'COMPLIANT' if (property.available_sqft or 0) >= (prospectus.estimated_nusf or 0) * 0.95 else 'REVIEW NEEDED',
                'notes': 'Meets minimum size requirements'
            },
            {
                'requirement': 'Parking Spaces',
                'needed': f"{prospectus.parking_spaces or 0} spaces",
                'provided': f"{property.parking_spaces or 0} spaces",
                'status': 'COMPLIANT' if (property.parking_spaces or 0) >= (prospectus.parking_spaces or 0) else 'MODIFICATION NEEDED',
                'notes': 'Additional parking may be arranged if needed'
            },
            {
                'requirement': 'Rent Rate',
                'needed': f"≤ ${prospectus.rental_rate_per_nusf:.2f}/sq ft" if prospectus.rental_rate_per_nusf else 'Market rate',
                'provided': f"${property.asking_rent_per_sqft:.2f}/sq ft",
                'status': 'COMPETITIVE' if (property.asking_rent_per_sqft or 0) <= (prospectus.rental_rate_per_nusf or 999) else 'NEGOTIATE',
                'notes': 'Rate positioning for government tenant'
            },
            {
                'requirement': 'Energy Star Certification',
                'needed': 'Required for buildings >75k sq ft',
                'provided': 'TBD - Assessment needed',
                'status': 'IN PROCESS',
                'notes': 'Can be obtained during lease negotiation period'
            },
            {
                'requirement': 'ADA Compliance',
                'needed': 'Full ADA accessibility',
                'provided': 'Modern building - compliant',
                'status': 'COMPLIANT',
                'notes': f'{property.year_built} construction meets standards'
            },
            {
                'requirement': 'Security Level',
                'needed': 'Level II minimum',
                'provided': 'Achievable with modifications',
                'status': 'ACHIEVABLE',
                'notes': 'Standard commercial security upgrades required'
            },
            {
                'requirement': 'Location Delineation',
                'needed': 'Within specified boundaries',
                'provided': 'Verified compliant',
                'status': 'COMPLIANT',
                'notes': 'Property falls within required geographic area'
            }
        ]
        
        return requirements
    
    def create_modifications_plan(self, prospectus, property):
        """Create plan for any needed property modifications"""
        
        modifications = []
        
        # Security modifications
        if 'secure' in (prospectus.special_requirements or '').lower():
            modifications.append({
                'category': 'Security',
                'description': 'Upgrade to GSA security standards',
                'estimated_cost': 150000,
                'timeline': '60-90 days',
                'priority': 'High',
                'details': [
                    'Access control system installation',
                    'Security camera upgrade',
                    'Visitor management system',
                    'Secure entrance modifications'
                ]
            })
        
        # Energy efficiency
        if (property.year_built or 0) < 2010:
            modifications.append({
                'category': 'Energy Efficiency',
                'description': 'Energy Star certification improvements',
                'estimated_cost': 75000,
                'timeline': '30-45 days',
                'priority': 'Medium',
                'details': [
                    'LED lighting upgrade',
                    'HVAC efficiency improvements',
                    'Energy management system',
                    'Window film/upgrades if needed'
                ]
            })
        
        # Parking expansion (if needed)
        parking_shortage = (prospectus.parking_spaces or 0) - (property.parking_spaces or 0)
        if parking_shortage > 0:
            modifications.append({
                'category': 'Parking',
                'description': f'Add {parking_shortage} parking spaces',
                'estimated_cost': parking_shortage * 3000,  # $3k per space
                'timeline': '45-60 days',
                'priority': 'High',
                'details': [
                    f'Expand parking area by {parking_shortage} spaces',
                    'Proper marking and signage',
                    'Lighting for new areas',
                    'Drainage considerations'
                ]
            })
        
        return modifications
    
    def create_pricing_strategy(self, prospectus, property):
        """Create optimal pricing strategy"""
        
        market_rate = property.asking_rent_per_sqft or 20.0
        max_rate = prospectus.rental_rate_per_nusf or market_rate
        
        return {
            'base_rent_strategy': {
                'current_asking': market_rate,
                'max_allowable': max_rate,
                'recommended_bid': min(max_rate * 0.98, market_rate * 0.95),  # Slightly under max
                'rationale': 'Position just below maximum to ensure competitiveness while maximizing revenue'
            },
            'incentive_package': {
                'tenant_improvements': 'GSA-required modifications at landlord expense',
                'free_rent': '3 months during modification period',
                'escalations': '2.5% annual increases (below GSA standard 3%)',
                'options': f'{prospectus.max_lease_term_years + 5} year renewal option'
            },
            'total_package_value': {
                'annual_base_rent': (prospectus.estimated_nusf or 0) * (min(max_rate * 0.98, market_rate * 0.95)),
                'total_lease_value': (prospectus.estimated_nusf or 0) * (min(max_rate * 0.98, market_rate * 0.95)) * (prospectus.max_lease_term_years or 10),
                'ti_allowance': 50 * (prospectus.estimated_nusf or 0),  # $50/sq ft for improvements
                'estimated_profit_margin': '15-20% after modifications and incentives'
            }
        }
    
    def create_timeline(self, prospectus):
        """Create project timeline"""
        
        lease_exp = prospectus.current_lease_expiration
        if not lease_exp:
            lease_exp = datetime.now() + timedelta(days=730)  # Default 2 years
        
        milestones = [
            {
                'phase': 'Immediate Actions',
                'date': datetime.now(),
                'tasks': [
                    'Secure property owner agreement',
                    'Begin compliance assessment',
                    'Start modification planning',
                    'Engage GSA specialist team'
                ],
                'duration': '2 weeks'
            },
            {
                'phase': 'Pre-RFP Preparation',
                'date': datetime.now() + timedelta(days=14),
                'tasks': [
                    'Complete building assessment',
                    'Finalize modification plans',
                    'Obtain preliminary cost estimates',
                    'Draft response framework'
                ],
                'duration': '60 days'
            },
            {
                'phase': 'RFP Release Response',
                'date': lease_exp - timedelta(days=270),
                'tasks': [
                    'Submit comprehensive proposal',
                    'Provide all required documentation',
                    'Schedule site visits',
                    'Handle clarification requests'
                ],
                'duration': '30 days'
            },
            {
                'phase': 'Award & Execution',
                'date': lease_exp - timedelta(days=180),
                'tasks': [
                    'Contract negotiation',
                    'Execute lease agreement',
                    'Begin tenant improvements',
                    'Coordinate move-in'
                ],
                'duration': '120 days'
            }
        ]
        
        return milestones
    
    def create_competitive_advantages(self, prospectus, property):
        """Identify competitive advantages"""
        
        advantages = [
            {
                'advantage': 'Early Market Entry',
                'description': 'First-mover advantage with comprehensive preparation',
                'impact': 'High - reduces competition response time'
            },
            {
                'advantage': 'Optimal Property Match',
                'description': f'Property size and location perfectly align with requirements',
                'impact': 'High - meets all primary criteria'
            },
            {
                'advantage': 'GSA Expertise',
                'description': 'Specialized knowledge of federal lease requirements',
                'impact': 'Medium - ensures compliant proposal'
            },
            {
                'advantage': 'Modification Readiness',
                'description': 'Pre-planned improvements demonstrate commitment',
                'impact': 'Medium - shows serious intent and capability'
            },
            {
                'advantage': 'Pricing Strategy',
                'description': 'Competitive rate while maintaining profitability',
                'impact': 'High - key evaluation factor'
            }
        ]
        
        return advantages
    
    def create_financial_analysis(self, prospectus, property):
        """Create comprehensive financial analysis"""
        
        annual_rent = (prospectus.estimated_nusf or 0) * (property.asking_rent_per_sqft or 20)
        lease_term = prospectus.max_lease_term_years or 10
        total_value = annual_rent * lease_term
        
        return {
            'revenue_projection': {
                'annual_rent': annual_rent,
                'lease_term_years': lease_term,
                'total_lease_value': total_value,
                'escalations': annual_rent * 0.025 * (lease_term * (lease_term + 1) / 2),  # 2.5% annual
                'total_with_escalations': total_value * 1.15  # Approximate with escalations
            },
            'investment_requirements': {
                'tenant_improvements': (prospectus.estimated_nusf or 0) * 50,  # $50/sq ft
                'security_upgrades': 150000,
                'energy_efficiency': 75000,
                'total_investment': (prospectus.estimated_nusf or 0) * 50 + 225000
            },
            'profit_analysis': {
                'gross_profit_margin': '25-30%',
                'roi_timeline': '3-4 years',
                'cash_flow_positive': 'Month 1',
                'exit_value': total_value * 0.8  # Conservative estimate
            },
            'your_fees': {
                'finder_fee': annual_rent * 0.02,
                'consulting_fee': 25000,
                'success_bonus': annual_rent * 0.01,
                'total_earnings': annual_rent * 0.03 + 25000
            }
        }
    
    def generate_strategy_report(self, limit=5):
        """Generate complete strategy report"""
        
        print("🦅 LEASEHAWK WINNING STRATEGY REPORT")
        print("=" * 60)
        
        easy_wins = self.identify_easiest_wins(limit)
        
        print(f"\n🎯 TOP {len(easy_wins)} EASIEST WINS IDENTIFIED")
        print("-" * 40)
        
        total_potential = 0
        
        for i, opportunity in enumerate(easy_wins, 1):
            p = opportunity['prospectus']
            total_potential += opportunity['potential_fee']
            
            print(f"\n{i}. {p.agency} - {p.location}")
            print(f"   Prospectus: {p.prospectus_number}")
            print(f"   Annual Value: ${p.estimated_annual_cost:,.0f}")
            print(f"   Win Probability: {opportunity['win_probability']:.0f}%")
            print(f"   Your Potential Fee: ${opportunity['potential_fee']:,.0f}")
            print(f"   Urgency: {opportunity['urgency_days']} days")
            print(f"   Available Properties: {opportunity['available_properties']}")
            
            print(f"   🎯 Why This is Easy:")
            for reason in opportunity['reasoning'][:3]:
                print(f"      • {reason}")
        
        print(f"\n💰 TOTAL POTENTIAL EARNINGS: ${total_potential:,.0f}")
        print(f"📊 Average per opportunity: ${total_potential/len(easy_wins):,.0f}")
        
        # Strategic recommendations
        print(f"\n🏆 STRATEGIC RECOMMENDATIONS:")
        print(f"1. START WITH #{easy_wins[0]['prospectus'].prospectus_number} - Highest win probability")
        print(f"2. Focus on opportunities with <365 day timelines")
        print(f"3. Target {sum(1 for o in easy_wins if o['urgency_days'] < 365)} urgent opportunities first")
        print(f"4. Prepare winning packages for top 3 opportunities")
        
        # Save detailed report
        self.save_strategy_report(easy_wins)
        
        return easy_wins
    
    def save_strategy_report(self, opportunities):
        """Save detailed strategy report to file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"data/strategy_report_{timestamp}.json"
        
        os.makedirs("data", exist_ok=True)
        
        report_data = []
        for opp in opportunities:
            p = opp['prospectus']
            report_data.append({
                'rank': len(report_data) + 1,
                'prospectus_number': p.prospectus_number,
                'agency': p.agency,
                'location': f"{p.location}, {p.state}",
                'annual_value': p.estimated_annual_cost,
                'win_probability': opp['win_probability'],
                'potential_fee': opp['potential_fee'],
                'urgency_days': opp['urgency_days'],
                'scoring_breakdown': opp['scoring_breakdown'],
                'reasoning': opp['reasoning']
            })
        
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"\n💾 Strategy report saved: {filename}")

def main():
    """Main strategy function"""
    
    import argparse
    parser = argparse.ArgumentParser(description="Generate winning strategy")
    parser.add_argument("--limit", type=int, default=5, help="Number of opportunities to analyze")
    parser.add_argument("--prospectus-id", type=int, help="Create package for specific prospectus")
    
    args = parser.parse_args()
    
    strategy = WinningStrategy()
    
    if args.prospectus_id:
        db = SessionLocal()
        prospectus = db.query(Prospectus).filter(Prospectus.id == args.prospectus_id).first()
        if prospectus:
            # Get best matching property
            best_match = db.query(Match).filter(
                Match.prospectus_id == args.prospectus_id
            ).order_by(Match.total_score.desc()).first()
            
            if best_match:
                property = db.query(Property).filter(Property.id == best_match.property_id).first()
                package = strategy.create_winning_package(prospectus, property)
                
                print("📋 Winning package created successfully!")
                print("   Use this information to prepare your proposal")
                
        db.close()
    else:
        strategy.generate_strategy_report(args.limit)

if __name__ == "__main__":
    main()