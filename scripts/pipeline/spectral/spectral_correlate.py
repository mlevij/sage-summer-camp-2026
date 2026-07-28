"""
CLBJ Spectral vs Soil Moisture Correlation
Spearman rho between each monthly band/index and NEON SWC (VSWCMean),
aggregated to monthly means and aligned on overlapping dates.

Outputs:
  spectral_forge/correlation_results.txt  — ranked feature table
"""
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
import os

SPECTRAL_CSV  = "/home/mlevij/spectral_forge/clbj_master_spectral_ts.csv"
SOIL_CSV      = "/home/mlevij/clbj_data/soil_moisture.csv"
OUTPUT_REPORT = "/home/mlevij/spectral_forge/correlation_results.txt"

def main():
    # --- Load spectral TS ---
    spec = pd.read_csv(SPECTRAL_CSV, index_col="date", parse_dates=True)
    # Drop bookkeeping column — not a spectral feature
    feature_cols = [c for c in spec.columns if c != "mean_clean_fraction"]
    spec = spec[feature_cols]
    print(f"Spectral data: {spec.shape[0]} months, {spec.shape[1]} features")
    print(f"  Date range: {spec.index.min().date()} to {spec.index.max().date()}")
    print(f"  Months with data: {spec['NDVI'].notna().sum()}")

    # --- Load soil moisture, aggregate to monthly means ---
    print("\nLoading soil moisture (this may take a moment — 535 MB CSV)...")
    soil = pd.read_csv(SOIL_CSV, usecols=["startDateTime", "VSWCMean"])
    soil["startDateTime"] = pd.to_datetime(soil["startDateTime"]).dt.tz_localize(None)
    soil = soil.set_index("startDateTime")
    soil_monthly = soil["VSWCMean"].resample("ME").mean().rename("SWC")
    soil_monthly = soil_monthly.dropna()
    print(f"Soil moisture: {len(soil_monthly)} months after aggregation")
    print(f"  Date range: {soil_monthly.index.min().date()} to {soil_monthly.index.max().date()}")

    # --- Align on overlapping dates ---
    combined = spec.join(soil_monthly, how="inner")
    combined = combined.dropna(subset=["SWC"])
    print(f"\nOverlap window: {combined.index.min().date()} to {combined.index.max().date()}")
    print(f"Aligned months: {len(combined)}")

    if len(combined) < 10:
        print("ERROR: fewer than 10 overlapping months — cannot correlate.")
        return

    # --- Spearman correlation of each feature vs SWC ---
    results = []
    for feat in feature_cols:
        valid = combined[[feat, "SWC"]].dropna()
        n = len(valid)
        if n >= 10:
            rho, p = spearmanr(valid[feat], valid["SWC"])
            results.append({"Feature": feat, "Rho": rho, "PValue": p, "N": n})
        else:
            results.append({"Feature": feat, "Rho": np.nan, "PValue": np.nan, "N": n})

    res = (pd.DataFrame(results)
             .sort_values("Rho", key=abs, ascending=False)
             .reset_index(drop=True))

    # --- Print summary ---
    print("\n=== TOP 10 FEATURES BY |Rho| ===")
    print(f"{'Feature':<8} {'Rho':>8} {'PValue':>10} {'N':>5}  Sig?")
    print("-" * 45)
    for _, row in res.head(10).iterrows():
        if np.isnan(row["Rho"]):
            print(f"  {row['Feature']:<8}    NaN")
            continue
        sig = "**" if row["PValue"] < 0.01 else ("*" if row["PValue"] < 0.05 else "")
        print(f"  {row['Feature']:<8} {row['Rho']:>8.4f} {row['PValue']:>10.4f} {int(row['N']):>5}  {sig}")

    print("\n=== ALL FEATURES ===")
    print(res.to_string(index=False, float_format="{:.4f}".format))

    # --- Write report ---
    with open(OUTPUT_REPORT, "w") as f:
        f.write("=== CLBJ Spectral vs Soil Moisture Correlation (Spearman) ===\n")
        f.write(f"Overlap Window: {combined.index.min().date()} to {combined.index.max().date()}\n")
        f.write(f"Sample Size: {len(combined)} months\n\n")
        f.write(res.to_string(index=False, float_format="{:.4f}".format))
    print(f"\nReport saved to: {OUTPUT_REPORT}")

if __name__ == "__main__":
    main()
