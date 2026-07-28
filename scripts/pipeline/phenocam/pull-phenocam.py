import csv
import os
import requests

SITE = "NEON.D11.CLBJ.DP1.00033"
BASE = f"https://phenocam.nau.edu/data/archive/{SITE}"
OUT_DIR = os.path.expanduser("~/clbj_phenocam_images")
MANIFEST_PATH = os.path.expanduser("~/clbj_phenocam_manifest.csv")

SEGMENTS = [
    ("DB_2000", f"{BASE}/ROI/{SITE}_DB_2000_1day.csv", "2021-07-01", "2024-01-08"),
    ("DB_3000", f"{BASE}/ROI/{SITE}_DB_3000_1day.csv", "2024-01-24", "2026-06-30"),
]

os.makedirs(OUT_DIR, exist_ok=True)

def fetch_rows(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    lines = [l for l in r.text.splitlines() if not l.startswith("#")]
    return list(csv.DictReader(lines))

manifest_rows = []
downloaded = skipped = failed = 0

for roi, csv_url, start, end in SEGMENTS:
    print(f"\n=== {roi}: {start} to {end} ===")
    rows = fetch_rows(csv_url)
    in_range = [row for row in rows if start <= row["date"] <= end]
    print(f"{len(in_range)} days in range")

    for row in in_range:
        date = row["date"]
        filename = row["midday_filename"]
        out_path = os.path.join(OUT_DIR, f"{date}.jpg")

        if not filename or filename == "None":
            skipped += 1
            manifest_rows.append([date, roi, "", "", "", "no_image"])
            continue

        parts = filename.replace(SITE + "_", "").split("_")
        year, month = parts[0], parts[1]
        img_url = f"{BASE}/{year}/{month}/{filename}"

        status = "already_had"
        if not os.path.exists(out_path):
            try:
                resp = requests.get(img_url, timeout=30)
                resp.raise_for_status()
                with open(out_path, "wb") as f:
                    f.write(resp.content)
                downloaded += 1
                status = "downloaded"
                if downloaded % 100 == 0:
                    print(f"  {downloaded} downloaded so far...")
            except Exception as e:
                print(f"  FAILED {date} ({img_url}): {e}")
                failed += 1
                status = "failed"

        manifest_rows.append([date, roi, filename, row.get("midday_gcc", ""), row.get("gcc_mean", ""), status])

with open(MANIFEST_PATH, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "roi", "filename", "midday_gcc", "gcc_mean", "status"])
    w.writerows(manifest_rows)

print(f"\nDone. Downloaded: {downloaded}, Skipped (no image that day): {skipped}, Failed: {failed}")
print(f"Manifest written to {MANIFEST_PATH}")
