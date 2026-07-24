import os
import urllib.request

import geopandas as gpd

# --- site config -- edit these for a new county ---
COUNTY_FIPS = "48497"  # Wise County, TX
OUT = r"C:\Users\mlevij\repos\sage-summer-camp-2026\drought-monitor\wise_county.geojson"
# --------------------------------------------------

CENSUS_URL = "https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_us_county_20m.zip"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cb_2022_us_county_20m.zip")

if not os.path.exists(CACHE):
    urllib.request.urlretrieve(CENSUS_URL, CACHE)

gdf = gpd.read_file(f"zip://{CACHE}")
print("Total counties:", len(gdf))
print("Columns:", list(gdf.columns))

wise = gdf[gdf["GEOID"] == COUNTY_FIPS]
print("Matched rows:", len(wise))
print(wise[["NAME", "STATEFP", "COUNTYFP", "GEOID"]].to_string())

wise = wise.to_crs(epsg=4326)
wise.to_file(OUT, driver="GeoJSON")
print("Bounds (lon/lat):", wise.total_bounds)
print(f"Wrote {OUT}")
