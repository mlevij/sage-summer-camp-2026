import csv
import json
from collections import defaultdict

# --- site config -- edit these for a new site ---
SITE = "CLBJ"
SITE_LOWER = "clbj"
CSV_DIR = r"C:\Users\mlevij\OneDrive - Colostate\Levi\NEON\CLBJ_SWC_5yr_30min"
WP_FC_SAT_PATH = r"C:\Users\mlevij\repos\sage-summer-camp-2026\drought-monitor\clbj_wfp_fc_sat.json"
WP_FC_SAT_SOURCE = "SSURGO (Duffau series, dominant component, CLBJ soil pit 33.4014,-97.5673) + Saxton-Rawls 2006"
OUT_PATH = r"C:\Users\mlevij\repos\sage-summer-camp-2026\drought-monitor\clbj_data.json"
DEPTH_M = {  # from swc_depthsV2.csv, D11/CLBJ shallow-to-deep, negative = below surface (m)
    "501": -0.06, "502": -0.16, "503": -0.26, "504": -0.56,
    "505": -0.76, "506": -1.06, "507": -1.36, "508": -1.96,
}
# --------------------------------------------------

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

daily = load(f"{CSV_DIR}\\{SITE_LOWER}_swc_daily.csv", "date")
weekly = load(f"{CSV_DIR}\\{SITE_LOWER}_swc_weekly.csv", "weekStart")
monthly = load(f"{CSV_DIR}\\{SITE_LOWER}_swc_monthly.csv", "month")

with open(WP_FC_SAT_PATH) as f:
    wp_fc_sat = json.load(f)

data = {
    "site": SITE,
    "product": "DP1.00094.001",
    "units": "VWC (m3/m3)",
    "depths_m": DEPTH_M,
    "wp_fc_sat": wp_fc_sat,
    "wp_fc_sat_source": WP_FC_SAT_SOURCE,
    "daily": daily,
    "weekly": weekly,
    "monthly": monthly,
}

with open(OUT_PATH, "w") as f:
    json.dump(data, f, indent=1)

print(f"Wrote {OUT_PATH}")
print("Depths present:", sorted(weekly.keys()))
print("Daily points (dep 501):", len(daily.get("501", [])))
