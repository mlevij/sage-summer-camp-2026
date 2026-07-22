# Drought monitor data pipeline

Scripts used to build the CPER Drought Monitor dashboard (`../drought-monitor/`). Saved here 2026-07-22 from a session temp scratchpad so they aren't lost.

**Not yet a generic multi-site tool** — these are a snapshot of what was actually run for CPER, with `CPER` and its coordinates hardcoded in several places (`pipeline/pull_5yr_swc.py`'s `site="CPER"`, `pipeline/cper_ssurgo_lookup.R`'s soil-pit lat/long, `pipeline/saxton_rawls_ssurgo.py`'s sensor-depth table). Adapting for another site (e.g. CLBJ) means editing those values directly, not passing a parameter.

All scripts expect a NEON API token at `C:\Users\mlevij\OneDrive - Colostate\Levi\NEON\NEON API.txt` (read from disk at runtime, never hardcoded into the script itself).

## pipeline/ — the actual chain that built the dashboard, in order
1. `pull_5yr_swc.py` — downloads DP1.00094.001 (soil water content) via `neonutilities`, 30-min resolution, 5 years.
2. `aggregate_swc.py` — aggregates the raw 30-min CSVs into weekly/monthly CSVs.
3. `cper_ssurgo_lookup.R` — point lookup against `CO_SSURGO.gpkg` at the site's soil pit coordinates; returns the dominant SSURGO component's horizons (sand/clay/om_r).
4. `saxton_rawls_ssurgo.py` — computes wilting point/field capacity/saturation per sensor depth from the SSURGO horizons (Saxton-Rawls 2006, OM as raw percent per the corrected formula documented in `AES/soil/index.html`).
5. `build_json.py` — combines the aggregated CSVs + WP/FC/Sat into `data.json`, the file the dashboard actually fetches.

## Planned, not yet built
- **Daily aggregation** — `aggregate_swc.py` currently only outputs weekly and monthly CSVs; add a daily tier alongside them (same weighted-mean/min/max-per-period pattern already used for weekly/monthly).
- **Date-range selector** — the dashboard (`../drought-monitor/index.html`) currently only offers a Weekly/Monthly resolution toggle over the full fixed date range; add a UI control to pick a custom start/end range.
- Explicit context from the user: these two are a proof-of-concept for a separate, broader "soil health monitor" initiative — not needed for the current CPER/CLBJ drought-monitor work specifically, but should be built as part of this same pipeline when that work resumes.

## exploration/ — abandoned or one-off, kept for reference
- `pull_megapit.py` / `saxton_rawls.py` — the first WP/FC/Sat attempt, using NEON's own Megapit product (DP1.00096.001) instead of SSURGO. Abandoned: NEON's field-estimated organic carbon was far outside Saxton-Rawls' valid domain (implied ~13.8% OM vs. the formula's 8% ceiling), producing implausible saturation values (58-73%). See `saxton_rawls_ssurgo.py` for the working replacement.
- `audit_swc.py` — one-off data-quality audit (fill rate / QF-flag distribution) run against the original 6-month CPER test download, not part of the ongoing pipeline.
