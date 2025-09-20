import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from typing import List, Dict

class GSAScraper:
    def __init__(self):
        self.base_url = "https://www.gsa.gov"
        self.prospectus_url = "/real-estate/gsa-properties/capital-investment-and-leasing-prospectus-library/2025-prospectus"
        
    def get_prospectus_list(self) -> List[Dict]:
        """Scrape list of current prospectuses from GSA website"""
        response = requests.get(self.base_url + self.prospectus_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        prospectuses = []
        
        # Find all prospectus links (adjust selectors based on actual HTML)
        for link in soup.find_all('a', href=True):
            if '.pdf' in link['href'] and 'lease' in link.text.lower():
                prospectuses.append({
                    'title': link.text.strip(),
                    'url': self.base_url + link['href'] if not link['href'].startswith('http') else link['href'],
                    'date_found': datetime.utcnow().isoformat()
                })
        
        return prospectuses
    
    def get_pipeline_data(self) -> List[Dict]:
        """Get data from d2d.gsa.gov pipeline"""
        # This would need proper API access or scraping strategy
        # For MVP, you might manually download and parse the Excel file
        pass
