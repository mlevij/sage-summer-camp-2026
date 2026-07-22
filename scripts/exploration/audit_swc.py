import csv
import glob
import os
import sys

base = r"C:\Users\mlevij\OneDrive - Colostate\Levi\NEON\NEON_conc-h2o-soil-salinity"
out_path = r"C:\Users\mlevij\AppData\Local\Temp\claude\C--Users-mlevij\506a9e3e-2cc2-424c-bea3-00a1bc6d9347\scratchpad\cper_swc_audit.csv"

pattern = os.path.join(base, "NEON.D10.CPER.DP1.00094.001.*", "NEON.D10.CPER.DP1.00094.001.*.030.SWS_30_minute.*.csv")
files = sorted(glob.glob(pattern))

with open(out_path, "w", newline="") as out:
    writer = csv.writer(out)
    writer.writerow(["file", "month", "horPos", "verPos", "total_rows", "nonnull_vswc", "pct_filled", "qf_pass_rows", "qf_fail_rows"])
    for i, fp in enumerate(files):
        name = os.path.basename(fp)
        parts = name.split(".")
        # NEON.D10.CPER.DP1.00094.001.001.501.030.SWS_30_minute.2024-01.basic...
        hor = parts[6]
        ver = parts[7]
        month = parts[10]
        total = 0
        nonnull = 0
        qf_pass = 0
        qf_fail = 0
        with open(fp, newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            vswc_idx = header.index("VSWCMean")
            qf_idx = header.index("VSWCFinalQF")
            for row in reader:
                total += 1
                if row[vswc_idx].strip() != "":
                    nonnull += 1
                if row[qf_idx].strip() == "0":
                    qf_pass += 1
                elif row[qf_idx].strip() == "1":
                    qf_fail += 1
        pct = round(100 * nonnull / total, 1) if total else 0
        writer.writerow([name, month, hor, ver, total, nonnull, pct, qf_pass, qf_fail])
        out.flush()
        print(f"[{i+1}/{len(files)}] {name}: {nonnull}/{total} filled ({pct}%)", file=sys.stderr)

print(f"Done. {len(files)} files processed. Summary written to {out_path}", file=sys.stderr)
