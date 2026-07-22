import json

with open(r"C:\Users\mlevij\AppData\Local\Temp\claude\C--Users-mlevij\506a9e3e-2cc2-424c-bea3-00a1bc6d9347\scratchpad\cper_ssurgo_horizons.json") as f:
    d = json.load(f)

horizons = d["horizons"]

SENSOR_DEPTHS_CM = {"501": 6, "502": 16, "503": 26, "504": 56, "505": 96, "506": 116, "507": 166, "508": 196}

def find_horizon(depth_cm):
    for h in horizons:
        if h["hzdept_r"] <= depth_cm < h["hzdepb_r"]:
            return h
    return None

def saxton_rawls(sand_pct, clay_pct, om_pct):
    S = sand_pct / 100.0
    C = clay_pct / 100.0
    OM = om_pct  # SSURGO om_r is already a raw percent -- do NOT divide by 100 (corrected formula, see AES/soil/index.html comments)

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
    h = find_horizon(depth_cm)
    if h is None:
        print(f"WARNING: no horizon found for {ver} ({depth_cm} cm)")
        continue
    wp, fc, sat = saxton_rawls(h["sandtotal_r"], h["claytotal_r"], h["om_r"])
    result[ver] = {
        "horizon": h["hzname"], "sand": h["sandtotal_r"], "clay": h["claytotal_r"], "om": h["om_r"],
        "wp": wp, "fc": fc, "sat": sat,
    }
    print(f"{ver} ({depth_cm} cm) -> horizon {h['hzname']} [{h['hzdept_r']:.0f}-{h['hzdepb_r']:.0f} cm], "
          f"sand={h['sandtotal_r']}% clay={h['claytotal_r']}% OM={h['om_r']}% => WP={wp}% FC={fc}% Sat={sat}%")

with open(r"C:\Users\mlevij\repos\sage-summer-camp-2026\drought-monitor\wfp_fc_sat.json", "w") as f:
    json.dump(result, f, indent=1)
print("\nWrote wfp_fc_sat.json")
