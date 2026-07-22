import csv
import json
from collections import defaultdict

base = r"C:\Users\mlevij\OneDrive - Colostate\Levi\NEON\CPER_SWC_5yr_30min"
out_path = r"C:\Users\mlevij\repos\sage-summer-camp-2026\drought-monitor\data.json"

DEPTH_M = {  # from swc_depthsV2.csv, D10/CPER shallow-to-deep, negative = below surface (m)
    "501": -0.06, "502": -0.16, "503": -0.26, "504": -0.56,
    "505": -0.96, "506": -1.16, "507": -1.66, "508": -1.96,
}

def weighted_agg(rows_by_key):
    # rows_by_key: key -> list of (n, mean, mn, mx)
    out = {}
    for key, rows in rows_by_key.items():
        total_n = sum(r[0] for r in rows)
        if total_n == 0:
            continue
        w_mean = sum(r[0] * r[1] for r in rows) / total_n
        w_min = min(r[2] for r in rows)
        w_max = max(r[3] for r in rows)
        out[key] = (total_n, w_mean, w_min, w_max)
    return out

def load(path, period_key):
    by_depth_period = defaultdict(lambda: defaultdict(list))
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            n = int(row["n_readings"])
            if n == 0:
                continue
            ver = row["verPos"]
            period = row[period_key]
            by_depth_period[ver][period].append(
                (n, float(row["VSWC_mean"]), float(row["VSWC_min"]), float(row["VSWC_max"]))
            )
    result = {}
    for ver, periods in by_depth_period.items():
        agg = weighted_agg(periods)
        series = []
        for period in sorted(agg):
            n, mean, mn, mx = agg[period]
            series.append({"period": period, "mean": round(mean, 4), "min": round(mn, 4), "max": round(mx, 4), "n": n})
        result[ver] = series
    return result

weekly = load(f"{base}\\cper_swc_weekly.csv", "weekStart")
monthly = load(f"{base}\\cper_swc_monthly.csv", "month")

with open(r"C:\Users\mlevij\repos\sage-summer-camp-2026\drought-monitor\wfp_fc_sat.json") as f:
    wp_fc_sat = json.load(f)

data = {
    "site": "CPER",
    "product": "DP1.00094.001",
    "units": "VWC (m3/m3)",
    "depths_m": DEPTH_M,
    "wp_fc_sat": wp_fc_sat,
    "wp_fc_sat_source": "SSURGO (Ascalon series, dominant component, CPER soil pit 40.81297,-104.74455) + Saxton-Rawls 2006",
    "weekly": weekly,
    "monthly": monthly,
}

with open(out_path, "w") as f:
    json.dump(data, f, indent=1)

print(f"Wrote {out_path}")
print("Depths present:", sorted(weekly.keys()))
