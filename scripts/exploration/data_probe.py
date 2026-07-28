import pandas as pd
from huggingface_hub import hf_hub_download
import os

def analyze_and_discard(repo_id, filename):
    print(f"\n--- Analyzing {filename} ---")
    try:
        # Download the file
        local_path = hf_hub_download(repo_id=repo_id, filename=filename, repo_type="dataset")
        
        # Load into pandas
        df = pd.read_csv(local_path)
        
        # Analyse
        print(f"Shape: {df.shape}")
        print("\nColumns:")
        print(df.columns.tolist())
        
        if not df.empty:
            print("\nHead:")
            print(df.head(3))
            
            # Check for date/time column to get range
            date_cols = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()]
            if date_cols:
                col = date_cols[0]
                print(f"\nDate Range ({col}): {df[col].min()} to {df[col].max()}")
            
            print("\nMissing values:")
            print(df.isna().sum())
            
            num_cols = df.select_dtypes(include=['number']).columns
            if len(num_cols) > 0:
                print("\nBasic Stats for numeric columns:")
                print(df[num_cols].describe().loc[['mean', 'std', 'min', 'max']])

        # Discard
        os.remove(local_path)
        print(f"\nSuccessfully discarded {local_path}")
        
    except Exception as e:
        print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    repo = "johnnybwell/neon_CLBJ"
    files_to_check = [
        "raw/soil_moisture/CLBJ_soil_moisture_2021-07_2026-07.csv",
        "raw/precipitation/CLBJ_precipitation_2021-07_2026-07.csv",
        "raw/air_temperature/CLBJ_air_temperature_2021-07_2026-07.csv",
        "raw/radiation/CLBJ_radiation_par_2021-07_2026-07.csv"
    ]
    
    for f in files_to_check:
        analyze_and_discard(repo, f)
