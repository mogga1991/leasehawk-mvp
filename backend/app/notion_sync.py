"""
Notion Integration for LeaseHawk MVP
Syncs prospectuses and properties between Notion and local database
"""
import os
from typing import List, Dict, Any
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

class NotionSync:
    def __init__(self):
        self.notion_token = os.getenv("NOTION_TOKEN")
        if self.notion_token:
            self.headers = {
                "Authorization": f"Bearer {self.notion_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
        else:
            self.headers = None
        self.base_url = "https://api.notion.com/v1"
        
        # Database IDs - will be set from environment
        self.prospectus_db_id = os.getenv("NOTION_PROSPECTUS_DB")
        self.property_db_id = os.getenv("NOTION_PROPERTY_DB")
        
    def get_prospectuses(self) -> List[Dict[str, Any]]:
        """Fetch all prospectuses from Notion database"""
        if not self.prospectus_db_id:
            raise ValueError("NOTION_PROSPECTUS_DB environment variable not set")
            
        url = f"{self.base_url}/databases/{self.prospectus_db_id}/query"
        
        response = requests.post(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Notion API error: {response.text}")
            
        data = response.json()
        
        prospectuses = []
        for page in data.get("results", []):
            props = page["properties"]
            prospectuses.append({
                "notion_id": page["id"],
                "prospectus_number": self._get_title(props.get("Prospectus Number")),
                "agency": self._get_select(props.get("Agency")),
                "location": self._get_text(props.get("Location")),
                "state": self._get_select(props.get("State")),
                "estimated_nusf": self._get_number(props.get("Square Footage (NUSF)")),
                "estimated_annual_cost": self._get_number(props.get("Annual Value")),
                "rental_rate_per_nusf": self._get_number(props.get("Rate per NUSF")),
                "parking_spaces": self._get_number(props.get("Parking Spaces")),
                "current_lease_expiration": self._get_date(props.get("Lease Expiration")),
                "delineated_area": self._get_text(props.get("Delineated Area")),
                "special_requirements": self._get_text(props.get("Special Requirements")),
                "pdf_url": self._get_url(props.get("PDF URL")),
                "status": self._get_select(props.get("Status")) or "active"
            })
        
        return prospectuses
    
    def get_properties(self) -> List[Dict[str, Any]]:
        """Fetch all properties from Notion database"""
        if not self.property_db_id:
            raise ValueError("NOTION_PROPERTY_DB environment variable not set")
            
        url = f"{self.base_url}/databases/{self.property_db_id}/query"
        
        response = requests.post(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Notion API error: {response.text}")
            
        data = response.json()
        
        properties = []
        for page in data.get("results", []):
            props = page["properties"]
            properties.append({
                "notion_id": page["id"],
                "address": self._get_title(props.get("Property Address")),
                "city": self._get_text(props.get("City")),
                "state": self._get_select(props.get("State")),
                "available_sqft": self._get_number(props.get("Available SQFT")),
                "total_sqft": self._get_number(props.get("Total SQFT")),
                "asking_rent_per_sqft": self._get_number(props.get("Asking Rent")),
                "parking_spaces": self._get_number(props.get("Parking Spaces")),
                "year_built": self._get_number(props.get("Year Built")),
                "source": self._get_select(props.get("Source")),
                "source_url": self._get_url(props.get("Source URL"))
            })
        
        return properties
    
    def update_match_score(self, prospectus_notion_id: str, property_notion_id: str, score: float):
        """Update match score in Notion when a match is found"""
        
        # Update prospectus with best match score if higher
        prospectus_url = f"{self.base_url}/pages/{prospectus_notion_id}"
        prospectus_data = {
            "properties": {
                "Best Match Score": {
                    "number": score
                }
            }
        }
        requests.patch(prospectus_url, headers=self.headers, json=prospectus_data)
        
        # Update property with match scores
        property_url = f"{self.base_url}/pages/{property_notion_id}"
        
        # First get existing scores
        existing_scores_response = requests.get(property_url, headers=self.headers)
        if existing_scores_response.status_code == 200:
            existing_data = existing_scores_response.json()
            existing_scores = self._get_text(existing_data["properties"].get("Match Scores", {})) or ""
            
            # Add new score entry
            new_score_entry = f"Prospectus {prospectus_notion_id[:8]}: {score:.1f}%"
            updated_scores = f"{existing_scores}\n{new_score_entry}" if existing_scores else new_score_entry
            
            property_data = {
                "properties": {
                    "Match Scores": {
                        "rich_text": [{
                            "text": {
                                "content": updated_scores
                            }
                        }]
                    }
                }
            }
            requests.patch(property_url, headers=self.headers, json=property_data)
    
    def add_property_from_search(self, property_data: Dict[str, Any]) -> str:
        """Add a new property found from web search to Notion"""
        url = f"{self.base_url}/pages"
        
        data = {
            "parent": {"database_id": self.property_db_id},
            "properties": {
                "Property Address": {
                    "title": [{
                        "text": {"content": property_data.get("address", "Unknown")}
                    }]
                },
                "City": {
                    "rich_text": [{
                        "text": {"content": property_data.get("city", "")}
                    }]
                },
                "State": {
                    "select": {"name": property_data.get("state", "XX")}
                },
                "Available SQFT": {
                    "number": property_data.get("available_sqft")
                },
                "Total SQFT": {
                    "number": property_data.get("total_sqft")
                },
                "Asking Rent": {
                    "number": property_data.get("asking_rent_per_sqft")
                },
                "Parking Spaces": {
                    "number": property_data.get("parking_spaces")
                },
                "Source": {
                    "select": {"name": property_data.get("source", "LoopNet")}
                },
                "Source URL": {
                    "url": property_data.get("source_url")
                }
            }
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code == 200:
            return response.json().get("id")
        else:
            raise Exception(f"Failed to create property in Notion: {response.text}")
    
    def add_prospectus(self, prospectus_data: Dict[str, Any]) -> str:
        """Add a new prospectus to Notion"""
        url = f"{self.base_url}/pages"
        
        data = {
            "parent": {"database_id": self.prospectus_db_id},
            "properties": {
                "Prospectus Number": {
                    "title": [{
                        "text": {"content": prospectus_data.get("prospectus_number", "")}
                    }]
                },
                "Agency": {
                    "select": {"name": prospectus_data.get("agency", "GSA")}
                },
                "Location": {
                    "rich_text": [{
                        "text": {"content": prospectus_data.get("location", "")}
                    }]
                },
                "State": {
                    "select": {"name": prospectus_data.get("state", "XX")}
                },
                "Square Footage (NUSF)": {
                    "number": prospectus_data.get("estimated_nusf", 0)
                },
                "Annual Value": {
                    "number": prospectus_data.get("estimated_annual_cost", 0)
                },
                "Rate per NUSF": {
                    "number": prospectus_data.get("rental_rate_per_nusf", 0)
                },
                "Parking Spaces": {
                    "number": prospectus_data.get("parking_spaces", 0)
                },
                "Status": {
                    "select": {"name": prospectus_data.get("status", "active")}
                }
            }
        }
        
        # Add lease expiration date if available
        if prospectus_data.get("current_lease_expiration"):
            lease_exp = prospectus_data["current_lease_expiration"]
            if isinstance(lease_exp, datetime):
                data["properties"]["Lease Expiration"] = {
                    "date": {"start": lease_exp.isoformat()}
                }
        
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code == 200:
            return response.json().get("id")
        else:
            raise Exception(f"Failed to create prospectus in Notion: {response.text}")
    
    # Helper methods to extract data from Notion properties
    def _get_title(self, prop):
        if not prop or "title" not in prop:
            return None
        return prop["title"][0]["text"]["content"] if prop["title"] else None
    
    def _get_text(self, prop):
        if not prop:
            return None
        if "rich_text" in prop:
            return prop["rich_text"][0]["text"]["content"] if prop["rich_text"] else None
        return None
    
    def _get_number(self, prop):
        if not prop or "number" not in prop:
            return None
        return prop["number"]
    
    def _get_select(self, prop):
        if not prop or "select" not in prop:
            return None
        return prop["select"]["name"] if prop["select"] else None
    
    def _get_date(self, prop):
        if not prop or "date" not in prop:
            return None
        if prop["date"] and prop["date"].get("start"):
            return datetime.fromisoformat(prop["date"]["start"].replace("Z", "+00:00"))
        return None
    
    def _get_url(self, prop):
        if not prop or "url" not in prop:
            return None
        return prop["url"]