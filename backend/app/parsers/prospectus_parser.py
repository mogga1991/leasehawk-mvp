import PyPDF2
import re
from datetime import datetime
import google.generativeai as genai
import json
import os
from typing import Dict, Any

class ProspectusParser:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        try:
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-pro')
            else:
                self.model = None
        except Exception as e:
            print(f"Warning: Failed to initialize Gemini client: {e}")
            self.model = None
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract raw text from PDF"""
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    
    def parse_with_llm(self, text: str) -> Dict[str, Any]:
        """Use Gemini to extract structured data from prospectus text"""
        
        if not self.model:
            raise Exception("Gemini API key not configured. Set GEMINI_API_KEY environment variable.")
        
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
        
        full_prompt = "You are a GSA prospectus data extraction expert. Extract data precisely as it appears in the document.\n\n" + prompt + "\n\nProspectus text:\n" + text[:4000]
        
        response = self.model.generate_content(full_prompt)
        
        # Extract JSON from the response
        response_text = response.text
        # Find JSON content between ```json and ``` or just parse the whole response
        try:
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_content = response_text[json_start:json_end].strip()
            else:
                json_content = response_text.strip()
            
            return json.loads(json_content)
        except json.JSONDecodeError:
            # Fallback to regex parsing if JSON parsing fails
            raise Exception(f"Failed to parse JSON from Gemini response: {response_text[:200]}...")
    
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
