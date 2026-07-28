import requests
import xml.etree.ElementTree as ET
from math import radians, cos, sin, asin, sqrt
import pandas as pd

def haversine(lon1, lat1, lon2, lat2):
    """Calculate the great circle distance between two points on the earth (km)."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # Radius of earth in kilometers.
    return c * r

# Target CLBJ Site
TARGET_LAT = 33.4014
TARGET_LON = -97.5673
MAX_DIST_KM = 25 # Maximum distance to consider a station "local"

def main():
    # We'll pull data for the last month to see current active reporters in TX
    url = "https://data.cocorahs.org/export/exportreports.aspx?ReportType=Daily&Format=XML&State=TX&StartDate=2026-07-01&EndDate=2026-07-26"
    print(f"Fetching CoCoRaHS data from {url}...")
    
    response = requests.get(url)
    root = ET.fromstring(response.content)
    
    stations = {} # Store unique stations and their proximity
    
    for report in root.findall('.//DailyPrecipReport'):
        s_num = report.find('StationNumber').text
        if s_num not in stations:
            name = report.find('StationName').text
            lat = float(report.find('Latitude').text)
            lon = float(report.find('Longitude').text)
            
            dist = haversine(TARGET_LON, TARGET_LAT, lon, lat)
            stations[s_num] = {
                'name': name,
                'lat': lat,
                'lon': lon,
                'dist': dist
            }

    # Filter for local stations
    local_stations = {k: v for k, v in stations.items() if v['dist'] <= MAX_DIST_KM}
    
    print(f"Total TX reporters found: {len(stations)}")
    print(f"Reporters within {MAX_DIST_KM}km of CLBJ: {len(local_stations)}")
    
    if local_stations:
        print("\nLocal Stations Found:")
        df = pd.DataFrame.from_dict(local_stations, orient='index')
        print(df.sort_values('dist'))
    else:
        print("\nNo reporters found within the specified radius of CLBJ.")

if __name__ == "__main__":
    main()