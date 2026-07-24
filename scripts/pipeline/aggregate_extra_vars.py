import csv
import os
import sys
from collections import defaultdict
from datetime import datetime

# --- site config -- edit these for a new site ---
RAW_DIR = r"C:\Users\mlevij\OneDrive - Colostate\Levi\NEON\CLBJ_extra_vars"
OUT_DIR = RAW_DIR
# --------------------------------------------------

# (raw filename, value column, out prefix, multi-depth?, agg mode)
VARIABLES = [
    ("soil_temperature.csv", "soilTempMean", "soiltemp", True, "mean"),
    ("precipitation.csv", "precipBulk", "precip", False, "sum"),
    ("air_temperature.csv", "tempSingleMean", "airtemp", False, "mean"),
    ("radiation_net.csv", "inSWMean", "radiation", False, "mean"),
]


def aggregate(raw_path, value_col, multi_depth, mode):
    day_bins = defaultdict(list)
    week_bins = defaultdict(list)
    month_bins = defaultdict(list)

    with open(raw_path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        val_idx = header.index(value_col)
        start_idx = header.index("startDateTime")
        ver_idx = header.index("verticalPosition")

        for i, row in enumerate(reader):
            val = row[val_idx].strip()
            if val == "":
                continue
            v = float(val)
            ver = row[ver_idx] if multi_depth else "_"
            dt = datetime.strptime(row[start_idx][:19], "%Y-%m-%d %H:%M:%S")
            iso_year, iso_week, _ = dt.isocalendar()
            day_bins[(ver, dt.date().isoformat())].append(v)
            week_bins[(ver, iso_year, iso_week)].append(v)
            month_bins[(ver, row[start_idx][:7])].append(v)
            if (i + 1) % 500000 == 0:
                print(f"    ...{i+1} rows read", file=sys.stderr)

    def reduce_vals(vals):
        if mode == "sum":
            return round(sum(vals), 4)
        return round(sum(vals) / len(vals), 4)

    daily = defaultdict(list)
    for (ver, date_str), vals in day_bins.items():
        daily[ver].append((date_str, len(vals), reduce_vals(vals), round(min(vals), 4), round(max(vals), 4)))

    weekly = defaultdict(list)
    for (ver, iso_year, iso_week), vals in week_bins.items():
        week_start = datetime.strptime(f"{iso_year}-W{iso_week}-1", "%G-W%V-%u").strftime("%Y-%m-%d")
        weekly[ver].append((week_start, len(vals), reduce_vals(vals), round(min(vals), 4), round(max(vals), 4)))

    monthly = defaultdict(list)
    for (ver, month), vals in month_bins.items():
        monthly[ver].append((month, len(vals), reduce_vals(vals), round(min(vals), 4), round(max(vals), 4)))

    return daily, weekly, monthly


def write_csv(path, data_by_depth):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["verPos", "period", "n", "value", "min", "max"])
        for ver, rows in sorted(data_by_depth.items()):
            for period, n, value, mn, mx in sorted(rows):
                w.writerow([ver, period, n, value, mn, mx])


for fname, value_col, prefix, multi_depth, mode in VARIABLES:
    raw_path = os.path.join(RAW_DIR, fname)
    print(f"Aggregating {fname} (column={value_col}, mode={mode}, multi_depth={multi_depth})...", file=sys.stderr)
    daily, weekly, monthly = aggregate(raw_path, value_col, multi_depth, mode)
    write_csv(os.path.join(OUT_DIR, f"{prefix}_daily.csv"), daily)
    write_csv(os.path.join(OUT_DIR, f"{prefix}_weekly.csv"), weekly)
    write_csv(os.path.join(OUT_DIR, f"{prefix}_monthly.csv"), monthly)
    print(f"  Done: {prefix}_daily/weekly/monthly.csv written ({len(daily)} depth series)", file=sys.stderr)

print("All variables aggregated.", file=sys.stderr)
