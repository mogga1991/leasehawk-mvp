from typing import List, Dict
import math
from geopy.distance import geodesic

class PropertyMatcher:
    def __init__(self):
        self.weights = {
            'size': 0.35,
            'location': 0.30,
            'parking': 0.20,
            'price': 0.15
        }
    
    def calculate_match_score(self, prospectus: Dict, property: Dict) -> Dict:
        """Calculate match score between prospectus and property"""
        
        scores = {}
        
        # Size score (how close is the available space to requirement)
        size_diff_pct = abs(property['available_sqft'] - prospectus['estimated_nusf']) / prospectus['estimated_nusf']
        scores['size'] = max(0, 100 - (size_diff_pct * 100))
        
        # Parking score
        if prospectus.get('parking_spaces') and property.get('parking_spaces'):
            parking_ratio = property['parking_spaces'] / prospectus['parking_spaces']
            scores['parking'] = min(100, parking_ratio * 100)
        else:
            scores['parking'] = 50  # Neutral if unknown
        
        # Price score (if property is at or below GSA rate)
        if property.get('asking_rent_per_sqft') and prospectus.get('rental_rate_per_nusf'):
            if property['asking_rent_per_sqft'] <= prospectus['rental_rate_per_nusf']:
                scores['price'] = 100
            else:
                overage = (property['asking_rent_per_sqft'] - prospectus['rental_rate_per_nusf']) / prospectus['rental_rate_per_nusf']
                scores['price'] = max(0, 100 - (overage * 100))
        else:
            scores['price'] = 50
        
        # Location score (simplified - would need geofencing for delineated area)
        scores['location'] = 75  # Placeholder - implement proper geographic matching
        
        # Calculate weighted total
        total_score = sum(scores[key] * self.weights[key] for key in self.weights)
        
        return {
            'total_score': total_score,
            'size_score': scores['size'],
            'parking_score': scores['parking'],
            'price_score': scores['price'],
            'location_score': scores['location']
        }
    
    def find_matches(self, prospectus: Dict, properties: List[Dict], min_score: float = 60) -> List[Dict]:
        """Find all properties that match prospectus requirements"""
        matches = []
        
        for property in properties:
            scores = self.calculate_match_score(prospectus, property)
            if scores['total_score'] >= min_score:
                matches.append({
                    'property': property,
                    'scores': scores
                })
        
        # Sort by total score
        matches.sort(key=lambda x: x['scores']['total_score'], reverse=True)
        return matches
