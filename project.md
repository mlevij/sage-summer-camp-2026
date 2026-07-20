# Validating Remote Sensing Products with In Situ Environmental Monitoring

**Author:** Levi (Michael) Johnson
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

## Open Questions

- Which (if any) Sage nodes have, or could be outfitted with, soil moisture or relevant environmental sensors?
- What would a minimal edge plugin look like that flags or contextualizes disagreement between a remote sensing product and a nearby in situ reading?
- How does Sage's data model (published measurements + Beehive) fit alongside an existing non-Sage pipeline (CoAgMET/RAWS/SNOTEL/Zentra)?
