import pystac_client
import planetary_computer
from datetime import datetime

# Target coordinates for CLBJ
LON = -97.5673
LAT = 33.4014
BBOX = [LON - 0.01, LAT - 0.01, LON + 0.01, LAT + 0.01]

def test_satellite_access():
    print("Attempting to query Microsoft Planetary Computer for Sentinel-2...")
    
    # The correct STAC URL for MPC is usually a hardcoded string if not in the Catalog class
    stac_url = "https://planetarycomputer.microsoft.com/api/stac/v1"

    # Initialize the catalog
    catalog = pystac_client.Client.open(stac_url)

    # Search for Sentinel-2 L2A (surface reflectance)
    search = catalog.search(
        collections=["sentinel-2-l2a"], 
        bbox=BBOX,
        datetime="2023-06-01/2023-07-01", # Small window in early summer
        max_items=5,
        query={"eo:cloud_cover": {"lt": 10}} # Low cloud cover
    )

    items = search.item_collection()
    print(f"Found {len(items)} items matching criteria.")

    if len(items) > 0:
        # Sign the assets for access (this is the "magic" tokenless part of MPC)
        signed_item = planetary_computer.sign(items[0])
        asset_url = signed_item.assets["B04"].href # Red band
        print(f"Successfully obtained signed asset URL: {asset_url[:60]}...")
        print("\nSUCCESS: Satellite access verified without manual tokens.")
    else:
        print("No items found for the given window and cloud cover threshold.")

if __name__ == "__main__":
    test_satellite_access()
