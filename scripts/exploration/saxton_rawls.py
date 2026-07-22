import csv
import json

# Horizon texture (%) and estimated organic carbon (%) from the CPER Megapit
horizons = {}
with open(r"C:\Users\mlevij\OneDrive - Colostate\Levi\NEON\CPER_Megapit\filesToStack00096\unzipped\NEON.D10.CPER.DP1.00096.001.mgp_perbiogeosample.2012-08.basic.20251204T185221Z.csv", newline="") as f:
    for row in csv.DictReader(f):
        horizons[row["horizonName"]] = {
            "top": float(row["biogeoTopDepth"]),
            "bottom": float(row["biogeoBottomDepth"]),
            "sand": float(row["sandTotal"]),
            "clay": float(row["clayTotal"]),
            "oc": float(row["estimatedOC"]),
        }

# Our 8 SWC sensor depths (cm below surface, from swc_depthsV2.csv D10/CPER)
SENSOR_DEPTHS_CM = {"501": 6, "502": 16, "503": 26, "504": 56, "505": 96, "506": 116, "507": 166, "508": 196}

def find_horizon(depth_cm):
    for name, h in horizons.items():
        if h["top"] <= depth_cm < h["bottom"]:
            return name, h
    return None, None

def saxton_rawls(sand_pct, clay_pct, oc_pct):
    S = sand_pct / 100.0
    C = clay_pct / 100.0
    OM = oc_pct * 1.72  # Van Bemmelen factor, OC% -> OM%

    t1500 = -0.024*S + 0.487*C + 0.006*OM + 0.005*(S*OM) - 0.013*(C*OM) + 0.068*(S*C) + 0.031
    wp = t1500 + (0.14*t1500 - 0.02)

    t33 = -0.251*S + 0.195*C + 0.011*OM + 0.006*(S*OM) - 0.027*(C*OM) + 0.452*(S*C) + 0.299
    fc = t33 + (1.283*t33**2 - 0.374*t33 - 0.015)

    tS33 = 0.278*S + 0.034*C + 0.022*OM - 0.018*(S*OM) - 0.027*(C*OM) - 0.584*(S*C) + 0.078
    S33 = tS33 + (0.636*tS33 - 0.107)

    sat = fc + S33 - 0.097*S + 0.043

    return round(wp*100, 1), round(fc*100, 1), round(sat*100, 1)

result = {}
for ver, depth_cm in SENSOR_DEPTHS_CM.items():
    name, h = find_horizon(depth_cm)
    if h is None:
        print(f"WARNING: no horizon found for {ver} ({depth_cm} cm)")
        continue
    wp, fc, sat = saxton_rawls(h["sand"], h["clay"], h["oc"])
    result[ver] = {"horizon": name, "sand": h["sand"], "clay": h["clay"], "oc": h["oc"], "wp": wp, "fc": fc, "sat": sat}
    print(f"{ver} ({depth_cm} cm) -> horizon {name} [{h['top']:.0f}-{h['bottom']:.0f} cm], "
          f"sand={h['sand']}% clay={h['clay']}% OC={h['oc']}% => WP={wp}% FC={fc}% Sat={sat}%")

with open(r"C:\Users\mlevij\AppData\Local\Temp\claude\C--Users-mlevij\506a9e3e-2cc2-424c-bea3-00a1bc6d9347\scratchpad\cper_saxton_rawls.json", "w") as f:
    json.dump(result, f, indent=1)
