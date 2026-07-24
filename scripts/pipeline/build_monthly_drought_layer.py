import csv
import io
import os
import zipfile
import urllib.request

import geopandas as gpd
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DROUGHT_MONITOR_DIR = os.path.abspath(os.path.join(BASE, "..", "..", "drought-monitor"))
PEAK_WEEKS_CSV = os.path.join(BASE, "peak_weeks.csv")
COUNTY_GEOJSON = os.path.join(DROUGHT_MONITOR_DIR, "wise_county.geojson")
CACHE_DIR = os.path.join(BASE, "shapefile_cache")
OUT_PATH = os.path.join(DROUGHT_MONITOR_DIR, "wise_drought_monthly.geojson")

os.makedirs(CACHE_DIR, exist_ok=True)

CATEGORY_NAMES = {0: "D0", 1: "D1", 2: "D2", 3: "D3", 4: "D4"}

county = gpd.read_file(COUNTY_GEOJSON)
assert county.crs.to_epsg() == 4326
county_geom = county.geometry.iloc[0]

with open(PEAK_WEEKS_CSV, newline="") as f:
    months = list(csv.DictReader(f))

print(f"{len(months)} months to process")

all_features = []

for i, row in enumerate(months):
    month = row["month"]
    date = row["peak_date"]
    date_compact = date.replace("-", "")
    zip_path = os.path.join(CACHE_DIR, f"USDM_{date_compact}_M.zip")
    shp_path = os.path.join(CACHE_DIR, f"USDM_{date_compact}.shp")

    if not os.path.exists(shp_path):
        url = f"https://droughtmonitor.unl.edu/data/shapefiles_m/USDM_{date_compact}_M.zip"
        if not os.path.exists(zip_path):
            urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(CACHE_DIR)

    national = gpd.read_file(shp_path)
    if national.crs is None or national.crs.to_epsg() != 4326:
        national = national.to_crs(epsg=4326)

    # Clip each DM level to the county first
    clipped = {}
    for dm in sorted(national["DM"].unique()):
        sub = national[national["DM"] == dm]
        try:
            clip = gpd.clip(sub, county_geom)
        except Exception:
            clip = sub.iloc[0:0]
        if len(clip) and not clip.union_all().is_empty:
            clipped[dm] = clip.union_all()

    levels = sorted(clipped.keys())
    exclusive_geoms = {}
    for idx, dm in enumerate(levels):
        geom = clipped[dm]
        if idx + 1 < len(levels):
            next_geom = clipped[levels[idx + 1]]
            geom = geom.difference(next_geom)
        if geom and not geom.is_empty:
            exclusive_geoms[dm] = geom

    # "None" (no drought) region = county minus the D0-or-worse extent
    if 0 in clipped:
        none_geom = county_geom.difference(clipped[0])
    else:
        none_geom = county_geom
    if none_geom and not none_geom.is_empty:
        all_features.append({"month": month, "date": date, "category": "None", "geometry": none_geom})

    for dm, geom in exclusive_geoms.items():
        all_features.append({"month": month, "date": date, "category": CATEGORY_NAMES[dm], "geometry": geom})

    print(f"[{i+1}/{len(months)}] {month} ({date}): categories present = {['None'] + [CATEGORY_NAMES[d] for d in exclusive_geoms]}")

result = gpd.GeoDataFrame(all_features, crs="EPSG:4326")
result.to_file(OUT_PATH, driver="GeoJSON")
print(f"\nWrote {OUT_PATH} -- {len(result)} total features across {len(months)} months")
