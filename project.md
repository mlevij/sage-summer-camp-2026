# Validating Remote Sensing Products with In Situ Environmental Monitoring

**Author:** Levi Johnson & Claude
**Affiliation:** Department of Soil and Crop Sciences, Colorado State University
**Workshop:** Sage Grande — Summer of AI, July 20–28, 2026, UIC Electronic Visualization Laboratory, Chicago, IL

This project is my own thread within a larger team effort — see below for the group's work, and how mine builds on it. (Full day-by-day session logs live in private project notes, not here — this is the condensed version.)

## The Group's Project

Along with John Blackwell, Di Fan, and Atefah Hosseini, we built [**"Multimodal Drought Early Warning at the Edge"**](https://github.com/difan1995/sage-summer-camp-2026/blob/main/sage_drought_early_warning_public_draft.md) — a research prototype that fuses NEON sensor histories with PhenoCam imagery to estimate current drought conditions at NEON's CLBJ site (Texas) and produce short-term outlooks. The real design constraint the team built around: sensors and images don't all arrive at the same time, so the system tracks what's actually present, what's delayed, and updates its read as new data comes in — rather than requiring a fully synced record before it'll say anything. A vision-language model handles the natural-language explanation layer, kept deliberately separate from the numerical forecast itself, so the science doesn't depend on the LLM to be right. It's running on a Thor edge node now, with historical replay and live-forecast modes.

Early result: environmental sensors carry more weight for straightforward meteorological (precipitation-defined) drought, while imagery earns its keep more when sensor coverage is thin or the question shifts toward vegetation/ecosystem response rather than rainfall alone. Full details in the team's own writeup: 

## My Piece: Does the Satellite Signal Actually Track the Ground Truth?

The team's system leans on PhenoCam imagery for its visual read. My own background is the other half of that same question — I already run an in-situ sensor pipeline (CoAgMET/RAWS/SNOTEL/Zentra soil moisture across Colorado) and do SSURGO-based soil modeling with satellite land/soil products via Google Earth Engine. So off the back of the team's CLBJ work, I asked a narrower question: **before you trust a satellite-derived signal as a stand-in for ground sensors, does it actually track them — and where does it not?**

**What I built:**
- A dashboard of CLBJ's own NEON soil water content by depth, with wilting point/field capacity/saturation reference zones computed via SSURGO + Saxton-Rawls (an earlier attempt using NEON's own Megapit soil data gave physically implausible results — its organic-matter estimate was outside the formula's valid range — so I pivoted to SSURGO instead). Live at [mlevij.com](https://mlevij.com/soil/), plus a [Leaflet](https://mlevij.com/drought-monitor/) timelapse of the county's real USDM drought history (spatially clipped, not flattened to one color per week) and four more environmental charts.
- A Sentinel-2 spectral-extraction pipeline (2017–2026, all 12 usable bands, cloud-masked, six vegetation/moisture indices) built specifically to let the data tell me which bands/indices actually predict drought at this site, instead of assuming NDVI is automatically the right answer. Caught and fixed a real bug along the way — a coordinate-system mismatch was silently producing 100% empty output on the first run, plus a couple of formula errors (wrong band in the NDWI calc, non-standard EVI coefficients) found in the same pass.

**What I found, and why it's actually interesting:** correlating against bulk soil moisture (averaged across all 8 depths) turned up nothing significant. But re-running against individual sensor depths flipped the story — NDMI and EVI correlate with the **deepest** sensors (rho≈0.60), not the shallow ones, with near-surface moisture behaving like noise. The reason ties back to the site itself: CLBJ isn't open grassland despite the "National Grassland" name — it's Cross Timbers, an oak woodland-prairie mosaic. Deep-rooted oaks pull water from 1-2m down, so canopy water content (what NDMI/EVI actually measure) tracks deep soil moisture, not the surface layer that responds to individual rain events. NDVI stays flat because it saturates fast under closed woody canopy. A literature check backs the mechanism (NDMI's NIR+SWIR design is built for exactly this, EVI is an established strong performer against in-situ soil moisture, and root-zone literature specifically recommends deep/integrated moisture products for mixed woody-vegetation sites like this one) — with the honest caveat that the deep-root/deep-moisture relationship isn't universally clean across ecosystems, so I'm treating this as a well-explained finding at CLBJ specifically, not a rule to assume carries over to the next NEON site.

**Where this is headed**: lag analysis next (soil moisture typically peaks a week or two after the rain event that also greens up the canopy), then feeding whichever spectral features actually earn their place into the team's fusion model as a validated input, rather than a hand-picked one.

## Open Questions

- Ground-truth/drought-label source for model training: USDM categories, computed SPI/SPEI, soil-moisture percentile thresholds, and/or CoCoRaHS — not yet decided.
- Whether a domain-adapted remote-sensing vision-language model (vs. a generic one) is the better foundation for the team's fusion model, given how narrow NDVI's blind spot turned out to be at this specific site.
- Resolving the CPER Thor Blade node's connectivity issue, which blocks real end-to-end edge deployment testing for the remote-sensing-validation side specifically.
