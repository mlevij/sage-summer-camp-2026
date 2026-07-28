import pandas as pd
import numpy as np

SPECTRAL_CSV = "/home/mlevij/spectral_forge/clbj_master_spectral_ts.csv"
SOIL_CSV = "/home/mlevij/clbj_data/soil_moisture.csv"

def main():
    # Inspect Spectral Data
    spec = pd.read_csv(SPECTRAL_CSV, index_col='date', parse_dates=True)
    print("--- Spectral Data Stats ---")
    print(f"Shape: {spec.shape}")
    print(spec.isna().mean() * 100) # % of NaNs per column
    print("\nSample data (2023):")
    print(spec.loc['2023-01-01':'2023-12-31'].head())

    # Inspect Soil Data
    soil = pd.read_csv(SOIL_CSV, usecols=['startDateTime', 'VSWCMean'])
    soil['startDateTime'] = pd.to_datetime(soil['startDateTime']).dt.tz_localize(None)
    print("\n--- Soil Moisture Data Stats ---")
    print(f"Shape: {soil.shape}")
    print(f"NaNs in VSWCMean: {soil['VSWCMean'].isna().sum()}")
    print(soil.head())

if __name__ == "__main__":
    main()