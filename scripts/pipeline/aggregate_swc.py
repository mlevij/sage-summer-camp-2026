import csv
import glob
import os
import sys
from collections import defaultdict
from datetime import datetime

# --- site config -- edit these three for a new site ---
SITE = "CLBJ"
DOMAIN = "D11"
BASE_DIR = r"C:\Users\mlevij\OneDrive - Colostate\Levi\NEON\CLBJ_SWC_5yr_30min\filesToStack00094"
OUT_DIR = r"C:\Users\mlevij\OneDrive - Colostate\Levi\NEON\CLBJ_SWC_5yr_30min"
# --------------------------------------------------------

daily_path = os.path.join(OUT_DIR, f"{SITE.lower()}_swc_daily.csv")
weekly_path = os.path.join(OUT_DIR, f"{SITE.lower()}_swc_weekly.csv")
monthly_path = os.path.join(OUT_DIR, f"{SITE.lower()}_swc_monthly.csv")

pattern = os.path.join(BASE_DIR, f"NEON.{DOMAIN}.{SITE}.DP1.00094.001.*", f"NEON.{DOMAIN}.{SITE}.DP1.00094.001.*.030.SWS_30_minute.*.csv")
files = sorted(glob.glob(pattern))
print(f"Found {len(files)} 30-minute files to aggregate", file=sys.stderr)

with open(daily_path, "w", newline="") as df, open(weekly_path, "w", newline="") as wf, open(monthly_path, "w", newline="") as mf:
    dwriter = csv.writer(df)
    wwriter = csv.writer(wf)
    mwriter = csv.writer(mf)
    dwriter.writerow(["horPos", "verPos", "date", "n_readings", "VSWC_mean", "VSWC_min", "VSWC_max"])
    wwriter.writerow(["horPos", "verPos", "isoYear", "isoWeek", "weekStart", "n_readings", "VSWC_mean", "VSWC_min", "VSWC_max"])
    mwriter.writerow(["horPos", "verPos", "month", "n_readings", "VSWC_mean", "VSWC_min", "VSWC_max"])

    for i, fp in enumerate(files):
        name = os.path.basename(fp)
        parts = name.split(".")
        hor = parts[6]
        ver = parts[7]
        month = parts[10]

        day_bins = defaultdict(list)
        week_bins = defaultdict(list)
        month_vals = []

        with open(fp, newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            vswc_idx = header.index("VSWCMean")
            start_idx = header.index("startDateTime")
            for row in reader:
                val = row[vswc_idx].strip()
                if val == "":
                    continue
                v = float(val)
                dt = datetime.strptime(row[start_idx], "%Y-%m-%dT%H:%M:%SZ")
                iso_year, iso_week, _ = dt.isocalendar()
                day_bins[dt.date().isoformat()].append(v)
                week_bins[(iso_year, iso_week)].append(v)
                month_vals.append(v)

        for date_str, vals in sorted(day_bins.items()):
            dwriter.writerow([hor, ver, date_str, len(vals),
                               round(sum(vals) / len(vals), 4), round(min(vals), 4), round(max(vals), 4)])

        for (iso_year, iso_week), vals in sorted(week_bins.items()):
            week_start = datetime.strptime(f"{iso_year}-W{iso_week}-1", "%G-W%V-%u").strftime("%Y-%m-%d")
            wwriter.writerow([hor, ver, iso_year, iso_week, week_start, len(vals),
                               round(sum(vals) / len(vals), 4), round(min(vals), 4), round(max(vals), 4)])

        if month_vals:
            mwriter.writerow([hor, ver, month, len(month_vals),
                               round(sum(month_vals) / len(month_vals), 4),
                               round(min(month_vals), 4), round(max(month_vals), 4)])
        else:
            mwriter.writerow([hor, ver, month, 0, "", "", ""])

        df.flush()
        wf.flush()
        mf.flush()
        if (i + 1) % 20 == 0 or i + 1 == len(files):
            print(f"[{i+1}/{len(files)}] processed {name}", file=sys.stderr)

print(f"Done. Daily -> {daily_path}", file=sys.stderr)
print(f"Done. Weekly -> {weekly_path}", file=sys.stderr)
print(f"Done. Monthly -> {monthly_path}", file=sys.stderr)
