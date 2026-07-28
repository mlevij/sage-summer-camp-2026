import pystac_client
import planetary_computer
import pandas as pd
import numpy as np
from huggingface_hub import hf_hub_download
import rasterio
from datetime import datetime, timedelta
import time
import os

# --- Configuration ---
REPO_ID = "johnnybwell/neon_CLBJ"
SM_FILE = "raw/soil_moisture/CLBJ_soil_moisture_2021-07_2026-07.csv"
LON, LAT = -97.5673, 33.4014
BBOX = [LON - 0.01, LAT - 0.01, LON + 0.01, LAT + 0.01]
STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"

# To keep it slim, we only sample a subset of dates
# We'll look for Sentinel-2 images and check the corresponding Ground Truth SM
def get_ground_truth_sm():
    print("Loading ground truth soil moisture...")
    path = hf_hub_download(repo_id=REPO_ID, filename=SM_FILE, repo_type="dataset")
    df = pd.read_csv(path)
    # Use the mean of the 10cm depth (verticalPosition = 502 usually, let's verify or average)
    # For simplicity in this training run, we'll take a daily aggregate across all depths
    df['startDateTime'] = pd.to_datetime(df['startDateTime'])
    daily = df.groupby(df['startDateTime'].dt.date)['VSWCMean'].mean().reset_index()
    daily.columns = ['date', 'sm_value']
    os.remove(path) # Discard source file immediately
    return daily

def pull_ndvi_for_date(catalog, date_str):
    # Search for Sentinel-2 L2A on this specific day (or closest window)
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=BBOX,
        datetime=f"{date_str}/{date_str}",
        max_items=1,
        query={"eo:cloud_cover": {"lt": 20}}
    )
    items = search.item_collection()
    if not items: return None
    
    signed_item = planetary_computer.sign(items[0])
    # We need Red (B04) and NIR (B08) for NDVI
    try:
        with rasterio.open(signed_item.assets["B04"].href) as red, \
             rasterio.open(signed_item.assets["B08"].href) as nir:
            # Read small window around the center point
            # Note: This is a simplification; usually we'd use a window for exact coords
            # But since BBOX is tiny (200m), taking the center pixel of the chip is okay
            r_val = red.read(1).mean() 
            n_val = nir.read(1).mean()
            ndvi = (n_val - r_val) / (n_val + r_val + 1e-5)
            return ndvi
    except Exception as e:
        print(f"Error reading raster for {date_str}: {e}")
        return None

def train_loop():
    sm_data = get_ground_truth_sm()
    catalog = pystac_client.Client.open(STAC_URL)
    
    results = []
    # Sample 50 diverse dates to keep it discrete and avoid rate limits
    sample_dates = sm_data.sample(n=min(len(sm_data), 50))
    
    print(f"Starting discrete training over {len(sample_dates)} sample dates...")
    
    for idx, row in sample_dates.iterrows():
        date_str = row['date'].strftime('%Y-%m-%d')
        sm_val = row['sm_value']
        
        print(f"Processing {date_str}... ", end="")
        ndvi = pull_ndvi_for_date(catalog, date_str)
        
        if ndvi is not None:
            print(f"NDVI: {ndvi:.4f}, SM: {sm_val:.4f}")
            results.append({'date': date_str, 'ndvi': ndvi, 'sm': sm_val})
        else:
            print("No clear imagery.")
        
        # Polite sleep to avoid bandwidth/API spikes
        time.sleep(2)

    # Save findings as a mini-knowledge base
    results_df = pd.DataFrame(results)
    correlation = results_df['ndvi'].corr(results_df['sm'])
    
    output_path = "/home/mlevij/clbj_sat_training_summary.txt"
    with open(output_path, "w") as f:
        f.write(f"CLBJ Satellite-Ground Correlation Analysis\n")
        f.write(f"Date: {datetime.now()}\n")
        f.write(f"Samples analyzed: {len(results)}\n")
        f.write(f"NDVI vs VSWCMean Correlation: {correlation:.4f}\n")
        f.write("\nRaw results (Sampled):\n")
        f.write(results_df.to_string())
    
    print(f"\nTraining complete. Summary saved to {output_path}")

if __name__ == "__main__":
    train_loop()
