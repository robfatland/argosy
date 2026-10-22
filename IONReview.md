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

## FLO module facts (from the ION landing page, fetched Sep 2026)

ION's **FLO** family = the two OOI fluorometer classes:
- **FLORD** — 2-wavelength fluorometer (Chl-a, backscatter)
- **FLORT** — 3-wavelength fluorometer (Chl-a, CDOM, backscatter)  ← the SP sensor argosy uses

FLO data products (the L1/L2 variable codes): **CHLAFLO** (chlorophyll-a fluorescence),
**CDOMFLO** (CDOM fluorescence), **FLUBSCT** (optical backscatter).

ION processing levels: **L0** raw (counts/volts), **L1** calibrated physical quantity from one
sensor channel, **L2** derived product from ≥2 L1/L2 inputs. Algorithms are drawn from OOI Data
Product Specifications (DPS), vendor docs, and peer-reviewed literature; source discrepancies are
noted in-module. (So CHLAFLO/CDOMFLO/FLUBSCT are the L1 calibrated outputs — ION takes raw counts
→ these, applying the vendor dark-count + scale-factor cal.)

Argosy relevance: these are exactly argosy's `chlora`, `cdom`, `backscatter` shard variables. The
argosy pp06 filter2 (Savitzky-Golay) / filter3 (backscatter despike) work operates DOWNSTREAM of
this L1 calibration — on the quantization/noise problem, not the raw→physical conversion. (See the
"bridging" discussion in DeveloperGuide/BR; ION = L0→L1/L2, argosy pp05/pp06 = QC + conditioning on
top of the delivered product.)

## Review notes (to fill in)

Reviewing FLO from a user standpoint — clarity, completeness, accessibility of the documentation.
Open the FLORD/FLORT module page from the sign-up spreadsheet link.

- Access / can a user find and open it: _TBD_
- Is the purpose / what-it-does clear: _TBD_
- Are inputs (raw units, calibration coefficients) and outputs (product, processing level) clear: _TBD_
- Worked example / usage intelligible: _TBD_
- Gaps, ambiguities, or confusing points: _TBD_
- Overall verdict (and explicit approval if warranted): _TBD_
