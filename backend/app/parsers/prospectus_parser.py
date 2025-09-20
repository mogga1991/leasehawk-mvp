import PyPDF2
import re
from datetime import datetime
from openai import OpenAI
import json
import os
from typing import Dict, Any

class ProspectusParser:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract raw text from PDF"""
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    
    def parse_with_llm(self, text: str) -> Dict[str, Any]:
        """Use GPT-4 to extract structured data from prospectus text"""
        
        if not self.client:
            raise Exception("OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")
        
        prompt = """
        Extract the following information from this GSA prospectus text.
        Return as JSON with these exact keys:
        
        {
            "prospectus_number": "string",
            "agency": "string",
            "location": "city, state",
            "state": "XX",
            "current_nusf": integer or null,
            "estimated_nusf": integer,
            "estimated_rsf": integer,
            "expansion_nusf": integer or null,
            "estimated_annual_cost": float,
            "rental_rate_per_nusf": float,
            "current_annual_cost": float or null,
            "current_lease_expiration": "YYYY-MM-DD" or null,
            "max_lease_term_years": integer,
            "delineated_area": {
                "north": "description",
                "south": "description",
                "east": "description",
                "west": "description"
            },
            "parking_spaces": integer,
            "special_requirements": "string with key requirements",
            "scoring_type": "Operating Lease or Capital Lease"
        }
        
        Prospectus text:
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a GSA prospectus data extraction expert. Extract data precisely as it appears in the document."},
                {"role": "user", "content": prompt + text[:4000]}  # Limit text for token management
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def quick_parse(self, text: str) -> Dict[str, Any]:
        """Fallback regex parser for quick extraction"""
        data = {}
        
        # Extract prospectus number
        prospectus_match = re.search(r'Prospectus Number:\s*([A-Z0-9-]+)', text)
        if prospectus_match:
            data['prospectus_number'] = prospectus_match.group(1)
        
        # Extract NUSF
        nusf_match = re.search(r'Estimated Maximum NUSF:\s*([\d,]+)', text)
        if nusf_match:
            data['estimated_nusf'] = int(nusf_match.group(1).replace(',', ''))
        
        # Extract annual cost
        cost_match = re.search(r'Estimated Total Unserviced Annual Cost:\s*\$([\d,]+)', text)
        if cost_match:
            data['estimated_annual_cost'] = float(cost_match.group(1).replace(',', ''))
        
        # Extract parking
        parking_match = re.search(r'Parking Spaces:\s*([\d,]+)', text)
        if parking_match:
            data['parking_spaces'] = int(parking_match.group(1).replace(',', ''))
        
        return data
