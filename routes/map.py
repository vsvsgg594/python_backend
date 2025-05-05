from fastapi import APIRouter, HTTPException
from base_model import LocationRequest, GeocodeResult
import requests
import math
router = APIRouter()

API_KEY = 'iYm7HlH8BzRNDVcSlqyKf6IAgbZvU7OL9CyNwtlT'
BASE_URL = "https://api.olamaps.io/places/v1/geocode"

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of Earth in kilometers
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Fixed point for distance calculation (example coordinates)
FIXED_LAT, FIXED_LON = 10.000000, 76.300000

@router.post("/geocode/", tags=["Map"])
async def geocode_location(request: LocationRequest) -> GeocodeResult:
    try:
        # Construct the URL with address and API key
        url = f"{BASE_URL}?address={requests.utils.quote(request.address)}&api_key={API_KEY}"
        
        # Make the API request
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Print the response for debugging
        print("API Response:", data)
        
        # Check if the status indicates no results
        if data['status'] == 'zero_results':
            raise HTTPException(status_code=404, detail=f"No geocoding results found for the address: {request.address}")
        
        # Check if 'geocodingResults' exists and is not empty
        if 'geocodingResults' not in data or not data['geocodingResults']:
            raise HTTPException(status_code=404, detail="Invalid response format: 'geocodingResults' key missing or empty")
        
        # Extract the first result
        result = data['geocodingResults'][0]
        
        # Ensure result contains required fields
        if 'formatted_address' not in result or 'geometry' not in result or 'location' not in result['geometry']:
            raise HTTPException(status_code=400, detail="Unexpected response format")
        
        # Extract latitude and longitude
        lat = result['geometry']['location']['lat']
        lon = result['geometry']['location']['lng']
        
        # Calculate distance to the fixed point
        distance = haversine(lat, lon, FIXED_LAT, FIXED_LON)
        
        # Create and return the GeocodeResult object
        geocode_result = GeocodeResult(
            formatted_address=result['formatted_address'],
            latitude=lat,
            longitude=lon,
            distance_to_fixed_point=distance  # Add distance to the response
        )
        
        return geocode_result

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=500, detail=f"KeyError: {str(e)}")
