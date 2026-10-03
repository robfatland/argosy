# ION Functions Review (DSC task)

Task-specific working doc. Rob is reviewing an OOI ION Functions module as a member of the
OOI Data Systems Committee (DSC), at NSF's request. Repo-only (not in the Jupyter Book).

## The request (paraphrased)

At the OOIFB web conference, George Voulgaris (NSF OOI program manager; also the driver behind
synchronizing argosy with Zenodo) asked the DSC/OOIFB to help review **ION Functions** before it
goes live. Relayed by Holly (OOIFB administrative lead, URI). ION technical/data lead is
**Chris Wingard** (OSU; background in the vector sensors identified for the shallow profiler).

**What ION Functions is:** a Python library of oceanographic data-processing algorithms. OOI
instruments output raw L0 data in native units (counts, voltages, proprietary binary); ION
Functions applies vendor calibration coefficients and documented algorithms to convert L0 →
calibrated physical quantities (L1) → derived scientific products (L2), per the OOI project
science team's data-product specifications. Covers CTD, dissolved oxygen, CO2, fluorometry, pH,
nitrate, velocity, passive acoustics, seismology, optics, pressure, meteorology, and more.
Organized as standalone modules under `ion_functions/data/`; each holds pure, stateless functions
taking NumPy arrays in and returning NumPy arrays out. Output products each carry a processing
level reflecting distance from raw.

**The ask (what we are and are NOT doing):** 15 draft modules now have documentation. Each
DSC/OOIFB member picks one to review **from the USER's perspective** — is it understandable and
well-documented? **Do NOT question the method/algorithm itself**; assess only whether the
description and instructions are clear and intelligible for someone to access and understand. If
it looks good, say so.

## Rob's assignment

- **Module: FLO** — the two fluorometer types used in OOI (FLOR / fluorometry family). Chosen for
  argosy relevance: CDOM, chlorophyll-a, and backscatter all come from the FLORT sensor, which the
  pipeline already shards and filters (pp06 filter2 Savitzky-Golay on CDOM/chlorA; filter3
  backscatter despike). So Rob has hands-on user context for exactly this data product.

## Key facts / deadlines

- **Go-live:** ION Functions public on oceanobservatories.org by **Oct 30, 2026**.
- **Comments due:** **Oct 28, 2026** — email to George (gvoulgar@nsf.gov), CC Holly.
- Express approval explicitly if the module reads well.

## Links

- ION Functions (Chris Wingard, GitHub docs): https://cwingard.github.io/ion-functions/
- Module sign-up spreadsheet (each ION function linked to its GitHub page):
  https://docs.google.com/spreadsheets/d/1ilYS7E-_fQKiwHaZqZ8hHothuPULATTPxHIUIMD6QU0/edit?usp=sharing

## Review notes (to fill in)

Reviewing FLO from a user standpoint — clarity, completeness, accessibility of the documentation.

- Access / can a user find and open it: _TBD_
- Is the purpose / what-it-does clear: _TBD_
- Are inputs (raw units, calibration coefficients) and outputs (product, processing level) clear: _TBD_
- Worked example / usage intelligible: _TBD_
- Gaps, ambiguities, or confusing points: _TBD_
- Overall verdict (and explicit approval if warranted): _TBD_
