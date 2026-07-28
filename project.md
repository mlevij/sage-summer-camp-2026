# Validating Remote Sensing Products with In Situ Environmental Monitoring

**Author:** Levi Johnson & Claude
**Affiliation:** Department of Soil and Crop Sciences, Colorado State University
**Workshop:** Sage Grande — Summer of AI, July 20–28, 2026, UIC Electronic Visualization Laboratory, Chicago, IL

## Big Question

How can AI at the edge inform an effort to validate remote sensing products with in situ environmental monitoring?

## Background

My work sits at the intersection of two things I already maintain independently:

- **In situ sensor networks**: an existing pipeline pulling and mapping live data from CoAgMET, RAWS, SNOTEL, and Zentra soil moisture stations across Colorado (ArcGIS/R/Python, automated via GitHub Actions).
- **Remote sensing / soil science**: SSURGO-based soil property estimation, including field capacity modeling (Saxton-Rawls, Bagnall) and work with satellite-derived land/soil products via Google Earth Engine.

My thesis direction is validating remote sensing soil moisture products against in situ monitoring — i.e., how well do satellite-derived estimates track what ground sensors actually measure, and where/why do they diverge.

## Why Sage

Sage/Waggle nodes are edge-AI platforms with real onboard compute (not just low-power sensors) sitting in the field. That raises a concrete question for this workshop: can edge inference be used to add context, QA, or derived products to a remote-sensing-validation pipeline in near real time, rather than validation only happening after the fact in a downstream analysis?

## Workshop Progress Log

### Day 0 prep (June 29 – July 18, 2026)
Completed a self-directed 4-phase syllabus ahead of the workshop: Linux/SSH fundamentals, Docker, running AI models locally (Ollama, quantization, Hugging Face `transformers`), and a Sage platform preview (`sage_data_client`, live queries against Sage's public API). Also completed the pre-arrival checklist, including installing and configuring **Hermes** (Nous Research's agent shell) on node **H02E**, wired to NVIDIA NIM (`z-ai/glm-5.2`).

### Day 1 (July 20, 2026)
Verified the full node-access loop end to end: SSH into H02E → tmux session → Hermes agent running and taking real actions on the node. Used Hermes to run a live sensor inventory on H02E — confirmed the node's onboard sensing is currently limited to power/thermal monitoring (no registered soil, weather, or camera sensors in `node-manifest-v2.json`), with a still-unidentified FT232 serial device on `/dev/ttyUSB0` (possibly GPS) worth following up on.

### Day 2 (July 21, 2026)
Completed the Sage "edge app" tutorial end to end — built a mean-color plugin, deployed it to H02E via `pluginctl`, and confirmed real published output on Sage's public data API. Swapped it over to pull from a live workshop RTSP camera feed instead of a static test image.

Kicked off a second, larger workstream: a NEON drought-monitor project with fellow participants John Blackwell, Di Fan and Atefah Hosseini, targeting NEON's CPER field site initially. Goal: pull sensor (and eventually imagery) data, train a multimodal drought-early-warning model, and deploy it for edge inference on a Sage Thor Blade node already placed at CPER (currently blocked by a node connectivity issue, unrelated to this workshop's own H02E/H037/H019 access). Scoped the data-acquisition approach (rate limits, resolution/size tradeoffs) and read the Thor Blade deployment spec to confirm the target node has enough onboard storage/compute for the full pipeline.

### Day 3 (July 22, 2026)
Built a dashboard showing NEON soil water content by depth with per-depth wilting point / field capacity / saturation reference zones. First attempt used NEON's own Megapit soil-pit product for the underlying texture data — abandoned after the results proved physically implausible (organic matter far outside the Saxton-Rawls formula's valid domain). Pivoted to SSURGO texture data at the site's exact soil-pit coordinates instead, which produced sane, physically plausible values. Shipped the first working dashboard, live on mlevij.com.

Mid-session, the target site changed from CPER (Colorado) to **CLBJ** (Lyndon B. Johnson National Grassland, Texas). Rebuilt the pipeline end to end against CLBJ's own coordinates, soil series, and sensor depths — including switching from a Colorado-only SSURGO geopackage to USDA's national Soil Data Access API — and added daily-resolution aggregation and a date-range selector, both explicit workshop-adjacent asks for a broader "soil health monitor" concept.

### Day 4 (July 23, 2026)
Published the CLBJ dashboard live on mlevij.com in place of the original CPER page, plus a round of UI polish (clearer WP/FC/saturation zone shading, a site-metadata banner with CLBJ's location and coordinates). Lighter day overall — mostly consolidation before the next push into cross-referencing the sensor data against independent drought data sources.

### Day 5 (July 24, 2026)
Cross-checked the site's own sensor data against the official NIDIS/USDM drought classification for Wise County, TX — caught and corrected an early misreading of USDM's cumulative (not exclusive) percent-area columns before trusting any conclusions about the site's drought history. Built a Leaflet timelapse map of the county's actual drought history, with real per-category polygons spatially clipped to the county boundary rather than a single flat color per week. Added four more environmental charts (soil temperature, precipitation, air temperature, incoming solar radiation) sourced from a colleague's broader NEON data pull, plus min/max bands around the sensor chart to surface precipitation-driven spikes.

### Day 6 (July 25, 2026)
Reconfigured the Hermes agent on **H037**, the actual assigned workshop node (previous setup had been on H02E). Discovered a pre-existing NEON phenocam imagery pipeline already built and run on that node from earlier work — a ready-made imagery source for future multimodal modeling, not previously connected to this project's own tracking.

### Day 7 (July 26, 2026)
Set up durable, off-node project storage (a private Hugging Face dataset repo) so Hermes and the wider project context can persist independent of any one node or session — replacing an earlier, more fragile local-file approach. Set up a Telegram gateway for the agent (currently blocked on a shared-node permissions issue, not yet resolved). Added **CoCoRaHS** (a volunteer precipitation/drought-observation network) as a candidate ground-truth data source alongside USDM and NEON.

Built and successfully ran a Sentinel-2 spectral-extraction pipeline for the CLBJ site (2017–2026, all 12 usable bands, cloud-masked, six candidate vegetation/moisture indices) — explicitly scoped to run genuine empirical feature selection against real ground-truth data, rather than assuming standard indices like NDVI are automatically the most informative for this site.

### Day 8 (July 27, 2026)
Continuing the empirical feature-selection step: merging the Sentinel-2 spectral time series with NEON sensor and USDM drought data to determine which indices actually correlate with observed drought conditions at CLBJ. Began evaluating **domain-adapted remote-sensing vision-language models** (e.g., a Qwen2.5-VL checkpoint specifically fine-tuned on remote-sensing visual instructions) as a stronger, better-targeted alternative to the originally-proposed generic Qwen-VL for the eventual multimodal fusion model.

A code review before trusting the pipeline's first "success" claim caught a real bug: a coordinate-reference-system mismatch (WGS84 lat/lon passed directly into a raster window expecting native UTM coordinates) had silently produced 100% NaN output across every band. Fixed (reprojection, a DN-to-reflectance scale factor, and two further formula errors — a wrong band in the NDWI calculation and non-standard EVI coefficients, both caught in the same pass), verified on individual test scenes before re-running the full extraction, then correlated against bulk soil moisture: nothing reached statistical significance (n=48 months), with red-edge/green bands (B06, B03) the closest at p≈0.06.

### Day 9 (July 28, 2026)
Re-ran the correlation against individual sensor depths instead of the bulk soil-moisture average, on the hypothesis that averaging across all 8 depths (down to 196cm) was diluting a real surface-driven signal. Result: the opposite of that hypothesis, and more interesting — the strongest correlation (rho≈0.60) showed up between NDMI/EVI and the **deepest** sensors, not the shallowest, with near-surface soil moisture behaving more like noise.

The explanation ties back to the site's actual vegetation: CLBJ ("National Grassland" is a land-management designation, not a vegetation description) sits in the Cross Timbers ecoregion, a post oak/blackjack oak woodland-prairie mosaic, not open grassland. Deep-rooted oaks draw water from 1-2m depth, so canopy water content (what NDMI and EVI actually measure) tracks deep soil moisture rather than the surface-rainfall-driven shallow layer; NDVI stays comparatively flat because it saturates quickly in closed woody canopy. A literature check the same day supported the core mechanism — NDMI's NIR+SWIR design is specifically built to isolate vegetation water content, EVI is an established strong performer against in-situ soil moisture in prior studies, and root-zone soil moisture literature specifically recommends *integrated deep* moisture products (rather than shallow-sensitive ones) for sites with mixed deep-rooted woody vegetation over a shallow-rooted understory — while also flagging that the deep-root/deep-moisture relationship is not universally clean across ecosystems, so this is treated as a well-supported site-specific finding rather than an assumed general rule for future NEON sites.

## Open Questions

- Ground-truth/drought-label source for model training: USDM categories, computed SPI/SPEI, soil-moisture percentile thresholds, and/or CoCoRaHS — not yet decided.
- Multimodal fusion architecture: how to combine dense sensor/spectral time series with image-based (phenocam/satellite) inputs — including whether a domain-adapted remote-sensing VLM is a better foundation than a generic vision-language model.
- What would a minimal edge plugin look like that flags or contextualizes disagreement between a remote sensing product and a nearby in situ reading?
- How does Sage's data model (published measurements + Beehive) fit alongside an existing non-Sage pipeline (CoAgMET/RAWS/SNOTEL/Zentra)?
- Resolving the CPER Thor Blade node's connectivity issue, which blocks real end-to-end edge deployment testing for the drought-monitor model specifically.
