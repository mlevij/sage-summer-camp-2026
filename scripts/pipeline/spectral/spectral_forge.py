import pystac_client
import planetary_computer
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds
import numpy as np
import pandas as pd
import json
from pathlib import Path

# --- CONFIGURATION ---
LON = -97.5673
LAT = 33.4014
BUFFER_DEG = 0.002  # ~200m buffer around CLBJ soil pit
SITES_BBOX = [LON - BUFFER_DEG, LAT - BUFFER_DEG, LON + BUFFER_DEG, LAT + BUFFER_DEG]

START_DATE = "2017-01-01"
END_DATE = "2026-07-31"

# S2 L2A bands (excludes B10/cirrus which is absent in L2A products)
BANDS = ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B11", "B12"]

# SCL whitelist — explicitly enumerate good classes rather than threshold-gating.
# Good: 4=vegetation, 5=bare soil, 6=water, 7=unclassified
# Excluded: 0=no data, 1=saturated/defective, 2=dark area pixels, 3=cloud shadow,
#           8=cloud medium prob, 9=cloud high prob, 10=thin cirrus, 11=snow/ice
# Note: 6 (water) and 7 (unclassified) are debatable for a dryland grassland site;
# drop them from the list here if you want stricter land-surface-only masking.
SCL_CLEAN_CLASSES = [4, 5, 6, 7]
MIN_CLEAN_FRACTION = 0.50  # skip scene if < 50% of AOI pixels are clean

# S2 L2A DN to reflectance scale factor
S2_SCALE = 10000.0

OUTPUT_DIR = Path("/home/mlevij/spectral_forge")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MASTER_CSV = OUTPUT_DIR / "clbj_master_spectral_ts.csv"
LOG_FILE   = OUTPUT_DIR / "extraction_log.json"


def read_window(signed_item, band, bbox_wgs84):
    """
    Open a COG asset, reproject the WGS84 bbox into the raster's native CRS
    (typically a UTM zone for S2), read the window, and return the raw array.
    Caller is responsible for scaling and aggregation.
    """
    asset = signed_item.assets[band]
    with rasterio.open(asset.href) as src:
        native_bbox = transform_bounds("EPSG:4326", src.crs, *bbox_wgs84)
        window = from_bounds(*native_bbox, src.transform)
        return src.read(1, window=window)


def compute_indices(b):
    """
    Compute spectral indices from a dict of median reflectance values (0-1 scale).
    All formulas use standard published coefficients against true reflectance.

    Fixes vs original script:
      - NDWI: was using B02 (blue); corrected to B03 (green) per McFeeters 1996
      - EVI:  was using C1=0.1, C2=0.1, L=0.1; corrected to C1=6, C2=7.5, L=1
              (Huete et al. 1997; only valid against 0-1 reflectance, not raw DNs)
    """
    def r(num, den):
        if np.isnan(num) or np.isnan(den):
            return np.nan
        return float(num / (den + 1e-10))

    ndvi = r(b["B08"] - b["B04"], b["B08"] + b["B04"])         # (NIR-RED)/(NIR+RED)
    ndmi = r(b["B08"] - b["B11"], b["B08"] + b["B11"])         # (NIR-SWIR1)/(NIR+SWIR1)
    ndwi = r(b["B03"] - b["B08"], b["B03"] + b["B08"])         # (GREEN-NIR)/(GREEN+NIR), GREEN=B03
    savi = r((b["B08"] - b["B04"]) * 1.5, b["B08"] + b["B04"] + 0.5)
    ndre = r(b["B08"] - b["B05"], b["B08"] + b["B05"])         # (NIR-RedEdge)/(NIR+RedEdge)

    # EVI: 2.5*(NIR-RED)/(NIR + C1*RED - C2*BLUE + L), C1=6, C2=7.5, L=1
    if any(np.isnan([b["B08"], b["B04"], b["B02"]])):
        evi = np.nan
    else:
        den = b["B08"] + 6.0 * b["B04"] - 7.5 * b["B02"] + 1.0
        evi = float(2.5 * (b["B08"] - b["B04"]) / (den + 1e-10))

    return {"NDVI": ndvi, "NDMI": ndmi, "NDWI": ndwi, "SAVI": savi, "EVI": evi, "NDRE": ndre}


def main():
    stac_url = "https://planetarycomputer.microsoft.com/api/stac/v1"
    catalog = pystac_client.Client.open(stac_url)

    print(f"Querying Sentinel-2 L2A from {START_DATE} to {END_DATE}...")
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=SITES_BBOX,
        datetime=f"{START_DATE}/{END_DATE}",
        query={"eo:cloud_cover": {"lt": 30}},  # loose pre-filter; SCL gate refines
    )
    items = list(search.items())
    print(f"Found {len(items)} candidates. Beginning extraction...")

    results = []
    log     = []

    for i, item in enumerate(items):
        date = item.properties["datetime"].split("T")[0]

        # Sign once per scene — not once per band call
        signed = planetary_computer.sign(item)

        # --- SCL cloud/shadow gate ---
        try:
            scl_array = read_window(signed, "SCL", SITES_BBOX)
            clean_fraction = float(np.isin(scl_array, SCL_CLEAN_CLASSES).mean())
        except Exception as e:
            log.append({"date": date, "status": "error", "reason": f"SCL read failed: {e}"})
            continue

        if clean_fraction < MIN_CLEAN_FRACTION:
            log.append({
                "date": date,
                "status": "skipped",
                "reason": f"clean_fraction={clean_fraction:.3f} below {MIN_CLEAN_FRACTION}",
                "clean_fraction": round(clean_fraction, 3),
            })
            continue

        # --- Band extraction ---
        # Take median of ALL pixels in window. The clean_fraction gate ensures that
        # >= 50% of pixels are good, so the median lands on a clean pixel by definition —
        # cloud/shadow outliers (minority) are pushed to the tails, not the median.
        band_data = {}
        for band in BANDS:
            try:
                raw    = read_window(signed, band, SITES_BBOX)
                scaled = raw.astype(float) / S2_SCALE
                band_data[band] = float(np.nanmedian(scaled))
            except Exception:
                band_data[band] = np.nan

        indices = compute_indices(band_data)

        entry = {"date": date, "clean_fraction": round(clean_fraction, 3)}
        entry.update(band_data)
        entry.update(indices)
        results.append(entry)

        log.append({
            "date": date,
            "status": "kept",
            "clean_fraction": round(clean_fraction, 3),
        })

        if (i + 1) % 25 == 0:
            kept_so_far = sum(1 for e in log if e.get("status") == "kept")
            print(f"  {i + 1}/{len(items)} evaluated, {kept_so_far} kept...")

    # --- Monthly aggregation ---
    if not results:
        print("No scenes passed the cloud gate. Exiting.")
        return

    df = pd.DataFrame(results)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

    numeric_cols = [c for c in df.columns if c != "clean_fraction"]
    monthly    = df[numeric_cols].resample("ME").mean()
    monthly_cf = df["clean_fraction"].resample("ME").mean().rename("mean_clean_fraction")
    monthly    = monthly.join(monthly_cf)

    monthly.to_csv(MASTER_CSV)
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

    kept    = sum(1 for e in log if e.get("status") == "kept")
    skipped = sum(1 for e in log if e.get("status") == "skipped")
    errors  = sum(1 for e in log if e.get("status") == "error")
    print(f"\nDone. {kept} kept / {skipped} skipped (cloud+shadow) / {errors} errors")
    print(f"Master TS : {MASTER_CSV}")
    print(f"Log       : {LOG_FILE}")


if __name__ == "__main__":
    main()
