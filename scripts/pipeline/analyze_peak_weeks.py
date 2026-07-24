import csv
import io
import os
import urllib.request
from collections import defaultdict

# --- site config -- edit these for a new county/date range ---
COUNTY_FIPS = "48497"  # Wise County, TX
START_DATE = "7/1/2021"
END_DATE = "7/24/2026"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
# ---------------------------------------------------------------

API_URL = (
    "https://usdmdataservices.unl.edu/api/CountyStatistics/GetDroughtSeverityStatisticsByAreaPercent"
    f"?aoi={COUNTY_FIPS}&startdate={START_DATE}&enddate={END_DATE}&statisticsType=1"
)

with urllib.request.urlopen(API_URL) as resp:
    csv_text = resp.read().decode("utf-8")

rows = []
reader = csv.DictReader(io.StringIO(csv_text))
for row in reader:
        # columns are cumulative ("percent area in category X or worse")
        d0c = float(row["D0"])
        d1c = float(row["D1"])
        d2c = float(row["D2"])
        d3c = float(row["D3"])
        d4c = float(row["D4"])
        # exclusive breakdown
        excl = {
            "D0": d0c - d1c,
            "D1": d1c - d2c,
            "D2": d2c - d3c,
            "D3": d3c - d4c,
            "D4": d4c,
        }
        none_pct = 100.0 - d0c
        # area-weighted severity score: weight none=0, D0=1..D4=5
        score = none_pct * 0 + excl["D0"] * 1 + excl["D1"] * 2 + excl["D2"] * 3 + excl["D3"] * 4 + excl["D4"] * 5
        rows.append({
            "date": row["ValidStart"],
            "none": round(none_pct, 2),
            "D0": round(excl["D0"], 2),
            "D1": round(excl["D1"], 2),
            "D2": round(excl["D2"], 2),
            "D3": round(excl["D3"], 2),
            "D4": round(excl["D4"], 2),
            "score": round(score, 2),
            "d4_cum": d4c,
            "d3_cum": d3c,
        })

rows.sort(key=lambda r: r["date"])

print(f"Total weeks: {len(rows)}")
print(f"Date range: {rows[0]['date']} to {rows[-1]['date']}")

# Find the single worst week overall
worst = max(rows, key=lambda r: r["score"])
print(f"\nWorst single week overall: {worst['date']} score={worst['score']}")
print(f"  Exclusive breakdown: None={worst['none']} D0={worst['D0']} D1={worst['D1']} D2={worst['D2']} D3={worst['D3']} D4={worst['D4']}")

# Any week that ever had real D4 presence
d4_weeks = [r for r in rows if r["D4"] > 0.5]
print(f"\nWeeks with real D4 (exclusive) presence: {len(d4_weeks)}")
for r in d4_weeks[:10]:
    print(f"  {r['date']}: D4={r['D4']}")

# Weeks with D3-or-worse (cumulative) > 50%
big_d3 = [r for r in rows if r["d3_cum"] > 50]
print(f"\nWeeks with D3-or-worse (cumulative) > 50%: {len(big_d3)}")
for r in big_d3:
    print(f"  {r['date']}: D3cum={r['d3_cum']} D4cum={r['d4_cum']}")

# Peak week per month
by_month = defaultdict(list)
for r in rows:
    ym = r["date"][:7]
    by_month[ym].append(r)

print(f"\nTotal months: {len(by_month)}")
print("\nPer-month peak week:")
peak_out_path = os.path.join(OUT_DIR, "peak_weeks.csv")
with open(peak_out_path, "w", newline="") as out:
    w = csv.writer(out)
    w.writerow(["month", "peak_date"])
    for ym in sorted(by_month):
        peak = max(by_month[ym], key=lambda r: r["score"])
        print(f"  {ym}: peak week {peak['date']} score={peak['score']} (None={peak['none']} D0={peak['D0']} D1={peak['D1']} D2={peak['D2']} D3={peak['D3']} D4={peak['D4']})")
        w.writerow([ym, peak["date"]])
print(f"\nWrote {peak_out_path}")
