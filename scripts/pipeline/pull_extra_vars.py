import os
import urllib.request

# --- site config -- edit these for a new site/dataset ---
HF_BASE = "https://huggingface.co/datasets/johnnybwell/neon_CLBJ/resolve/main/raw"
OUT_DIR = r"C:\Users\mlevij\OneDrive - Colostate\Levi\NEON\CLBJ_extra_vars"
FILES = [
    ("soil_temperature/CLBJ_soil_temperature_2021-07_2026-07.csv", "soil_temperature.csv"),
    ("precipitation/CLBJ_precipitation_2021-07_2026-07.csv", "precipitation.csv"),
    ("air_temperature/CLBJ_air_temperature_2021-07_2026-07.csv", "air_temperature.csv"),
    ("radiation/CLBJ_radiation_net_2021-07_2026-07.csv", "radiation_net.csv"),
]
# ---------------------------------------------------------

os.makedirs(OUT_DIR, exist_ok=True)

for rel_path, out_name in FILES:
    url = f"{HF_BASE}/{rel_path}"
    out_path = os.path.join(OUT_DIR, out_name)
    print(f"Downloading {url} -> {out_path}")
    urllib.request.urlretrieve(url, out_path)
    size_mb = os.path.getsize(out_path) / 1e6
    print(f"  done ({size_mb:.1f} MB)")

print("All files downloaded.")
