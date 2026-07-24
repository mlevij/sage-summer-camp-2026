# Drought monitor data pipeline

Scripts used to build the CPER Drought Monitor dashboard (`../drought-monitor/`). Saved here 2026-07-22 from a session temp scratchpad so they aren't lost.

**Not yet a generic multi-site tool** — these are a snapshot of what was actually run for CPER, with `CPER` and its coordinates hardcoded in several places (`pipeline/pull_5yr_swc.py`'s `site="CPER"`, `pipeline/cper_ssurgo_lookup.R`'s soil-pit lat/long, `pipeline/saxton_rawls_ssurgo.py`'s sensor-depth table). Adapting for another site (e.g. CLBJ) means editing those values directly, not passing a parameter.

All scripts expect a NEON API token at `C:\Users\mlevij\OneDrive - Colostate\Levi\NEON\NEON API.txt` (read from disk at runtime, never hardcoded into the script itself). `upload_to_hf.py` similarly expects a Hugging Face access token at `C:\Users\mlevij\OneDrive - Colostate\Levi\Hugging Face\.huggingface_token` (Write-scoped, personal account).

## pipeline/ — the actual chain that built the dashboard, in order
1. `pull_5yr_swc.py` — downloads DP1.00094.001 (soil water content) via `neonutilities`, 30-min resolution, 5 years.
2. `aggregate_swc.py` — aggregates the raw 30-min CSVs into weekly/monthly CSVs.
3. `cper_ssurgo_lookup.R` — point lookup against `CO_SSURGO.gpkg` at the site's soil pit coordinates; returns the dominant SSURGO component's horizons (sand/clay/om_r).
4. `saxton_rawls_ssurgo.py` — computes wilting point/field capacity/saturation per sensor depth from the SSURGO horizons (Saxton-Rawls 2006, OM as raw percent per the corrected formula documented in `AES/soil/index.html`).
5. `build_json.py` — combines the aggregated CSVs + WP/FC/Sat into `data.json`, the file the dashboard actually fetches.
6. `upload_to_hf.py` — uploads the daily/weekly/monthly CSVs plus both JSON outputs to a Hugging Face dataset repo (repo ID + file list configured at the top of the script — currently `mlevij/neon_CLBJ`), so acquired data can be shared with the rest of the team/used to train a model, per workshop instruction (2026-07-23). Idempotent — re-running when nothing's actually changed (e.g. NEON hasn't published a new month yet) correctly no-ops instead of creating empty commits.

## Shipped since the note above was written
- **Daily aggregation** and a **date-range selector** (both originally listed here as "planned") are live on `../drought-monitor/clbj.html` — `aggregate_swc.py` now outputs a daily tier alongside weekly/monthly, and the dashboard has From/To date inputs plus a Daily/Weekly/Monthly resolution toggle that auto-adjusts based on the selected range's width.
- The site itself pivoted from CPER to **CLBJ** — the stale original CPER page (`../drought-monitor/index.html`, `data.json`, `wfp_fc_sat.json`) has been deleted; `clbj.html`/`clbj_data.json`/`clbj_wfp_fc_sat.json` are the only working copies now (also mirrored to the live site at `mlevij.com/drought-monitor/`, and to `mlevij/neon_CLBJ` on Hugging Face).
- `clbj.html` now opens with a **Leaflet USDM drought timelapse map** for Wise County, TX (real clipped drought-category polygons, not a flat per-county color — see the new `pipeline/` entries below) as the first thing visible on page load, with the existing VWC-by-depth chart below it on scroll. Same page, two data sources.

## pipeline/ — Wise County USDM drought timelapse (feeds the map on `clbj.html`, separate chain)
1. `extract_wise_county.py` — downloads Census's `cb_2022_us_county_20m` cartographic boundary file, filters to Wise County TX (FIPS `48497`), writes `../../drought-monitor/wise_county.geojson`.
2. `analyze_peak_weeks.py` — pulls Wise County's full weekly USDM percent-area history from `usdmdataservices.unl.edu`'s CountyStatistics API, converts the cumulative D0-D4 percentages to exclusive per-category percentages, computes an area-weighted severity score per week, and picks the single worst week per calendar month. Writes `peak_weeks.csv` (month → representative date).
3. `build_monthly_drought_layer.py` — for each of those representative dates, downloads the real USDM shapefile (`droughtmonitor.unl.edu/data/shapefiles_m/USDM_YYYYMMDD_M.zip`, cached in `shapefile_cache/`, gitignored), clips each drought-category polygon to Wise County's boundary, and converts the cumulative clipped shapes into exclusive per-category regions (same cumulative→exclusive logic as step 2, but on real geometry via `geopandas`/`shapely` difference operations, not just percentages) — this is what preserves genuine within-county spatial variation instead of flattening each month to one dominant color. Writes `../../drought-monitor/wise_drought_monthly.geojson`.

Needs `geopandas`, `shapely`, `fiona`, `pyproj` (not part of the base pipeline's dependencies — installed separately for this).

## exploration/ — abandoned or one-off, kept for reference
- `pull_megapit.py` / `saxton_rawls.py` — the first WP/FC/Sat attempt, using NEON's own Megapit product (DP1.00096.001) instead of SSURGO. Abandoned: NEON's field-estimated organic carbon was far outside Saxton-Rawls' valid domain (implied ~13.8% OM vs. the formula's 8% ceiling), producing implausible saturation values (58-73%). See `saxton_rawls_ssurgo.py` for the working replacement.
- `audit_swc.py` — one-off data-quality audit (fill rate / QF-flag distribution) run against the original 6-month CPER test download, not part of the ongoing pipeline.
