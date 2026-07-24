import csv
import json
import os

# --- site config -- edit these for a new site ---
DATA_JSON_PATH = r"C:\Users\mlevij\repos\sage-summer-camp-2026\drought-monitor\clbj_data.json"
RAW_DIR = r"C:\Users\mlevij\OneDrive - Colostate\Levi\NEON\CLBJ_extra_vars"
DEPTHS_TO_KEEP = {"501", "502", "503", "504", "505", "506", "507", "508"}
# --------------------------------------------------

# (out key in JSON, csv prefix, multi_depth?, units)
VARIABLES = [
    ("soilTemp", "soiltemp", True, "degC"),
    ("precip", "precip", False, "mm (sum per period)"),
    ("airTemp", "airtemp", False, "degC"),
    ("radiation", "radiation", False, "W/m2 (incoming shortwave)"),
]


def load_multi_depth(prefix, res):
    path = os.path.join(RAW_DIR, f"{prefix}_{res}.csv")
    by_depth = {}
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            ver = row["verPos"]
            if ver not in DEPTHS_TO_KEEP:
                continue
            by_depth.setdefault(ver, []).append({
                "period": row["period"],
                "mean": float(row["value"]),
                "min": float(row["min"]),
                "max": float(row["max"]),
                "n": int(row["n"]),
            })
    for ver in by_depth:
        by_depth[ver].sort(key=lambda p: p["period"])
    return by_depth


def load_single_series(prefix, res):
    path = os.path.join(RAW_DIR, f"{prefix}_{res}.csv")
    series = []
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            series.append({
                "period": row["period"],
                "mean": float(row["value"]),
                "min": float(row["min"]),
                "max": float(row["max"]),
                "n": int(row["n"]),
            })
    series.sort(key=lambda p: p["period"])
    return series


with open(DATA_JSON_PATH) as f:
    data = json.load(f)

for out_key, prefix, multi_depth, units in VARIABLES:
    entry = {"units": units}
    for res in ("daily", "weekly", "monthly"):
        if multi_depth:
            entry[res] = load_multi_depth(prefix, res)
        else:
            entry[res] = load_single_series(prefix, res)
    data[out_key] = entry
    n_points = len(entry["daily"]) if not multi_depth else sum(len(v) for v in entry["daily"].values())
    print(f"Added {out_key}: {n_points} daily points")

with open(DATA_JSON_PATH, "w") as f:
    json.dump(data, f, indent=1)

print(f"Wrote {DATA_JSON_PATH}")
