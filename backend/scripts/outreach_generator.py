#!/usr/bin/env python3
"""
Outreach Generator - Create personalized outreach for property owners
Generates emails, cold call scripts, and follow-up sequences
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import json
from app.database import SessionLocal
from app.models import Prospectus, Property, Match

class OutreachGenerator:
    def __init__(self):
        self.templates = {}
        self.load_templates()
    
    def load_templates(self):
        """Load email and script templates"""
        
        self.templates = {
            'initial_email': {
                'subject': 'Federal Government Seeks {sqft:,} sq ft - Your Property at {address} Matches',
                'body': '''Dear Property Owner,

I represent LeaseHawk, a specialized firm that matches federal government lease requirements with commercial properties.

The {agency} has announced a requirement for {sqft:,} square feet in {location} with an annual lease value of ${annual_value:,.0f}.

Your property at {address} appears to meet their requirements:
✓ Size: Your {available_sqft:,} sq ft (needs {sqft:,})
✓ Location: Within the designated area  
✓ Parking: {parking} spaces available (needs {required_parking})

The government will pay up to ${rent_per_sqft:.2f} per square foot.

This is a {lease_term}-year lease opportunity with the full backing of the U.S. Government - the most creditworthy tenant possible.

TIMELINE:
• Current lease expires: {expiration_date}
• RFP expected: 6-9 months before expiration
• We need to start preparing NOW

This represents ${total_lease_value:,.0f} in total lease value over {lease_term} years.

Would you be interested in a brief call to discuss positioning your property for this opportunity?

Best regards,
{your_name}
LeaseHawk - Government Lease Intelligence
{your_phone} | {your_email}

P.S. The government is actively seeking properties NOW. First movers have the advantage.'''
            },
            
            'follow_up_email': {
                'subject': 'Re: ${potential_fee:,.0f} opportunity - {agency} lease requirement',
                'body': '''Hi {owner_name},

Following up on the federal government lease opportunity I mentioned.

Quick recap:
• {agency} needs {sqft:,} sq ft in {location}
• Annual value: ${annual_value:,.0f}
• Your property: {address} - {match_score}% match
• Potential lease value: ${total_lease_value:,.0f}

I've identified only 3 properties in the area that meet their requirements. Yours is the best match.

The selection process is competitive, but properties that prepare early have a significant advantage.

Can we schedule 15 minutes this week to discuss:
1. Government lease requirements and compliance
2. Property modifications that might be needed
3. How to position your property to win

Available: {availability}

Best regards,
{your_name}
{your_phone}'''
            },
            
            'cold_call_script': {
                'opening': '''Hi, is this the owner of {address}?

Great! I'm calling because the federal government just announced they need {sqft:,} square feet in your exact area, and your property appears to be a perfect match.''',
                
                'value_prop': '''This is a {lease_term}-year lease worth ${annual_value:,.0f} per year - that's ${total_lease_value:,.0f} in total lease value.

The {agency} has specific requirements, and your property at {available_sqft:,} sq ft is within their size range, and the location is perfect.''',
                
                'urgency': '''The current lease expires {expiration_date}, and they typically issue RFPs 6-9 months before. We need to start preparing now to have the best chance of winning.''',
                
                'credibility': '''We specialize in GSA lease requirements and know exactly what they're looking for. We've helped property owners win government contracts worth over $50 million.''',
                
                'close': '''Can we schedule 15 minutes this week to discuss the specific requirements and what modifications might be needed to win this contract?

I have availability {availability}. What works better for you?'''
            },
            
            'urgent_follow_up': {
                'subject': 'URGENT: {agency} RFP timeline moved up - {address}',
                'body': '''URGENT UPDATE - {owner_name}

The {agency} has moved up their timeline for the {location} requirement.

New timeline:
• RFP Release: {rfp_date}  
• Proposals Due: {proposal_deadline}
• Award Expected: {award_date}

This is 2-3 months earlier than expected.

Your property at {address} is still our top recommendation, but we need to move quickly on:

1. Property compliance assessment
2. Modification planning  
3. Proposal preparation

Can you take a call TODAY to discuss next steps?

This is a ${annual_value:,.0f}/year opportunity - we can't afford to miss it.

Call me: {your_phone}
Email: {your_email}

Best regards,
{your_name}'''
            }
        }
    
    def generate_owner_email(self, prospectus, property, template_type='initial_email', **kwargs):
        """Generate personalized email to property owner"""
        
        template = self.templates.get(template_type, self.templates['initial_email'])
        
        # Calculate values
        total_lease_value = (prospectus.estimated_annual_cost or 0) * (prospectus.max_lease_term_years or 10)
        potential_fee = (prospectus.estimated_annual_cost or 0) * 0.02
        
        # Format expiration date
        exp_date = "TBD"
        if prospectus.current_lease_expiration:
            exp_date = prospectus.current_lease_expiration.strftime("%B %Y")
        
        # Default values
        defaults = {
            'agency': prospectus.agency or 'Federal Agency',
            'sqft': prospectus.estimated_nusf or 0,
            'location': f"{prospectus.location}, {prospectus.state}",
            'annual_value': prospectus.estimated_annual_cost or 0,
            'address': property.address,
            'available_sqft': property.available_sqft or property.total_sqft or 0,
            'parking': property.parking_spaces or 0,
            'required_parking': prospectus.parking_spaces or 0,
            'rent_per_sqft': prospectus.rental_rate_per_nusf or 20.0,
            'lease_term': prospectus.max_lease_term_years or 10,
            'expiration_date': exp_date,
            'total_lease_value': total_lease_value,
            'potential_fee': potential_fee,
            'your_name': kwargs.get('your_name', '[Your Name]'),
            'your_phone': kwargs.get('your_phone', '[Your Phone]'),
            'your_email': kwargs.get('your_email', '[Your Email]'),
            'match_score': kwargs.get('match_score', 95),
            'owner_name': kwargs.get('owner_name', 'Property Owner'),
            'availability': kwargs.get('availability', 'Monday-Friday 9am-5pm'),
            'rfp_date': kwargs.get('rfp_date', 'Within 60 days'),
            'proposal_deadline': kwargs.get('proposal_deadline', '30 days after RFP'),
            'award_date': kwargs.get('award_date', '90 days after RFP')
        }
        
        # Merge with any additional kwargs
        defaults.update(kwargs)
        
        try:
            subject = template['subject'].format(**defaults)
            body = template['body'].format(**defaults)
            
            return {
                'subject': subject,
                'body': body,
                'recipient_info': {
                    'property_address': property.address,
                    'prospectus_number': prospectus.prospectus_number,
                    'potential_value': potential_fee
                }
            }
        except KeyError as e:
            return {
                'error': f"Template formatting error: {e}",
                'subject': f"Government Lease Opportunity - {property.address}",
                'body': f"Error generating template for {property.address}"
            }
    
    def generate_cold_call_script(self, prospectus, property, **kwargs):
        """Generate cold call script"""
        
        template = self.templates['cold_call_script']
        
        # Calculate values (same as email)
        total_lease_value = (prospectus.estimated_annual_cost or 0) * (prospectus.max_lease_term_years or 10)
        
        exp_date = "TBD"
        if prospectus.current_lease_expiration:
            exp_date = prospectus.current_lease_expiration.strftime("%B %Y")
        
        defaults = {
            'address': property.address,
            'agency': prospectus.agency or 'Federal Agency',
            'sqft': prospectus.estimated_nusf or 0,
            'lease_term': prospectus.max_lease_term_years or 10,
            'annual_value': prospectus.estimated_annual_cost or 0,
            'total_lease_value': total_lease_value,
            'available_sqft': property.available_sqft or property.total_sqft or 0,
            'expiration_date': exp_date,
            'availability': kwargs.get('availability', 'this week'),
        }
        
        defaults.update(kwargs)
        
        script_parts = {}
        for section, text in template.items():
            try:
                script_parts[section] = text.format(**defaults)
            except KeyError as e:
                script_parts[section] = f"[Template error: {e}]"
        
        return {
            'opening': script_parts['opening'],
            'value_prop': script_parts['value_prop'],
            'urgency': script_parts['urgency'], 
            'credibility': script_parts['credibility'],
            'close': script_parts['close'],
            'full_script': '\n\n'.join(script_parts.values())
        }
    
    def generate_outreach_campaign(self, prospectus_id, limit=20):
        """Generate complete outreach campaign for a prospectus"""
        
        print(f"🎯 Generating Outreach Campaign for Prospectus ID: {prospectus_id}")
        print("=" * 60)
        
        db = SessionLocal()
        
        try:
            # Get prospectus
            prospectus = db.query(Prospectus).filter(Prospectus.id == prospectus_id).first()
            if not prospectus:
                print(f"❌ Prospectus ID {prospectus_id} not found")
                return
            
            print(f"📋 Prospectus: {prospectus.prospectus_number}")
            print(f"   Agency: {prospectus.agency}")
            print(f"   Location: {prospectus.location}, {prospectus.state}")
            print(f"   Annual Value: ${prospectus.estimated_annual_cost:,.0f}")
            
            # Get top matching properties
            matches = db.query(Match).filter(
                Match.prospectus_id == prospectus_id
            ).order_by(Match.total_score.desc()).limit(limit).all()
            
            if not matches:
                print("❌ No property matches found. Run property matching first.")
                return
            
            print(f"\n🏢 Generating outreach for top {len(matches)} property matches")
            
            outreach_items = []
            
            for i, match in enumerate(matches, 1):
                property = db.query(Property).filter(Property.id == match.property_id).first()
                if not property:
                    continue
                
                # Generate email
                email = self.generate_owner_email(
                    prospectus, 
                    property,
                    your_name="[Your Name Here]",
                    your_phone="[Your Phone]", 
                    your_email="[Your Email]",
                    match_score=int(match.total_score)
                )
                
                # Generate call script
                script = self.generate_cold_call_script(prospectus, property)
                
                outreach_item = {
                    'rank': i,
                    'property': property,
                    'match_score': match.total_score,
                    'email': email,
                    'call_script': script,
                    'potential_fee': (prospectus.estimated_annual_cost or 0) * 0.02
                }
                
                outreach_items.append(outreach_item)
                
                print(f"✅ [{i:2d}] {property.address} - {match.total_score:.0f}% match")
            
            # Save to file
            self.save_outreach_campaign(outreach_items, prospectus)
            
            # Print summary and next steps
            self.print_campaign_summary(outreach_items, prospectus)
            
        finally:
            db.close()
    
    def save_outreach_campaign(self, outreach_items, prospectus):
        """Save outreach campaign to files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"outreach_{prospectus.prospectus_number}_{timestamp}"
        
        # Create outreach directory
        os.makedirs("data/outreach", exist_ok=True)
        
        # Save as JSON for programmatic use
        json_data = []
        for item in outreach_items:
            json_item = {
                'rank': item['rank'],
                'property_address': item['property'].address,
                'match_score': item['match_score'],
                'email_subject': item['email']['subject'],
                'email_body': item['email']['body'],
                'call_script': item['call_script']['full_script'],
                'potential_fee': item['potential_fee']
            }
            json_data.append(json_item)
        
        json_file = f"data/outreach/{base_filename}.json"
        with open(json_file, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        # Save as readable text file
        text_file = f"data/outreach/{base_filename}.txt"
        with open(text_file, 'w') as f:
            f.write(f"OUTREACH CAMPAIGN\n")
            f.write(f"Prospectus: {prospectus.prospectus_number}\n")
            f.write(f"Agency: {prospectus.agency}\n")
            f.write(f"Location: {prospectus.location}, {prospectus.state}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write("=" * 80 + "\n\n")
            
            for item in outreach_items:
                f.write(f"PROPERTY #{item['rank']:02d} - MATCH SCORE: {item['match_score']:.0f}%\n")
                f.write(f"Address: {item['property'].address}\n")
                f.write(f"Potential Fee: ${item['potential_fee']:,.0f}\n")
                f.write("-" * 40 + "\n")
                
                f.write("EMAIL:\n")
                f.write(f"Subject: {item['email']['subject']}\n\n")
                f.write(f"{item['email']['body']}\n\n")
                
                f.write("COLD CALL SCRIPT:\n")
                f.write(f"{item['call_script']['full_script']}\n\n")
                f.write("=" * 80 + "\n\n")
        
        print(f"\n💾 Campaign saved to:")
        print(f"   📄 {text_file}")
        print(f"   📊 {json_file}")
    
    def print_campaign_summary(self, outreach_items, prospectus):
        """Print campaign summary and action items"""
        
        total_potential = sum(item['potential_fee'] for item in outreach_items)
        top_5 = outreach_items[:5]
        
        print(f"\n📊 CAMPAIGN SUMMARY")
        print(f"   Properties: {len(outreach_items)}")
        print(f"   Total Potential Fees: ${total_potential:,.0f}")
        print(f"   Average Per Property: ${total_potential/len(outreach_items):,.0f}")
        
        print(f"\n🎯 TOP 5 TARGETS:")
        for item in top_5:
            print(f"   {item['rank']}. {item['property'].address}")
            print(f"      Match: {item['match_score']:.0f}% | Fee: ${item['potential_fee']:,.0f}")
        
        print(f"\n🚀 ACTION PLAN:")
        print(f"1. START WITH TOP 5 - highest probability of success")
        print(f"2. Send emails to top 10 properties today")
        print(f"3. Follow up with calls within 24-48 hours")
        print(f"4. Schedule property visits for interested owners")
        print(f"5. Prepare GSA compliance packages for top 3 matches")
        
        print(f"\n📞 DAILY CALL TARGETS:")
        print(f"   Monday: Properties 1-4")
        print(f"   Tuesday: Properties 5-8") 
        print(f"   Wednesday: Properties 9-12")
        print(f"   Thursday: Properties 13-16")
        print(f"   Friday: Properties 17-20 + follow-ups")
        
        print(f"\n💡 SUCCESS TIPS:")
        print(f"   • Call between 9-11am or 2-4pm")
        print(f"   • Lead with the dollar amount: '${prospectus.estimated_annual_cost:,.0f} opportunity'")
        print(f"   • Emphasize government creditworthiness")
        print(f"   • Create urgency with timeline")
        print(f"   • Follow up within 48 hours of first contact")

def main():
    """Main outreach generation function"""
    
    import argparse
    parser = argparse.ArgumentParser(description="Generate outreach campaigns")
    parser.add_argument("--prospectus-id", type=int, help="Generate for specific prospectus")
    parser.add_argument("--all-high-value", action="store_true", help="Generate for all high-value prospectuses")
    parser.add_argument("--limit", type=int, default=20, help="Limit number of properties per campaign")
    
    args = parser.parse_args()
    
    generator = OutreachGenerator()
    
    if args.prospectus_id:
        generator.generate_outreach_campaign(args.prospectus_id, args.limit)
    
    elif args.all_high_value:
        db = SessionLocal()
        high_value = db.query(Prospectus).filter(
            Prospectus.estimated_annual_cost > 3000000,
            Prospectus.status == 'active'
        ).all()
        
        print(f"🎯 Generating campaigns for {len(high_value)} high-value prospectuses")
        
        for prospectus in high_value:
            generator.generate_outreach_campaign(prospectus.id, args.limit)
            print("\n" + "="*60 + "\n")
        
        db.close()
    
    else:
        print("📋 Available Commands:")
        print("   --prospectus-id 1    Generate for specific prospectus")
        print("   --all-high-value     Generate for all high-value prospectuses")
        print("   --limit 10           Limit properties per campaign")

if __name__ == "__main__":
    main()