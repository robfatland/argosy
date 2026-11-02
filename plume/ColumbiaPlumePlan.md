# Columbia River Plume Detection Plan

Hypothesis: The Columbia River freshwater plume reaches the Oregon Offshore and
Slope Base shallow profiler sites seasonally, producing detectable multi-sensor
anomalies in the upper 15–40 m of the profiler record.

This is the **plume study**. Code lives alongside this document in `~/argosy/plume/`
(see `plume/README.md`); the Book notebook is `chapters/ColumbiaPlume.ipynb`.


## Status (Nov 2026)

**Built (Slope Base only):**

- `surface_extract.py` — per-profile near-surface statistics from pp06 (mean/std of the
  shallowest 10 valid points for S, T, DO, CDOM; shallowest observation depth; dS/dz).
  Output: `~/ooi/sb/metadata/features/surface_extract_slopebase.csv` (20,447 profiles,
  2015-07-09 → 2025-12-31).
- `fetch_sst.py` — **CRW SST** point time series at SB. Output:
  `~/ooi/sb/metadata/external/satellite_sst_slopebase.csv` (4,231 daily values,
  2015-01-01 → 2026-08-01, no gaps).
- `fetch_sss.py` — **SMAP SSS** point time series at SB (+ 8-day rolling mean). Output:
  `~/ooi/sb/metadata/external/satellite_sss_slopebase.csv` (2015-04 → 2026-08, with gaps —
  e.g. no rows for Jan–Mar 2025).
- `surface_plot.py` — stacked near-surface panels; profiler T vs CRW SST and profiler S vs
  SMAP SSS are **visual overlays only**. Runs standalone (`python surface_plot.py`, Agg) or
  via `%run` in the notebook.

**Satellite data sources (as actually implemented):** both via NOAA CoastWatch ERDDAP
griddap, single-pixel point query at 44.53 N, −125.39 W, **no authentication**.

| Short term | Dataset | ERDDAP id / variable | Grid (pixel at SB) | Time step |
|---|---|---|---|---|
| **CRW SST** | NOAA Coral Reef Watch daily global 5 km SST (analysed, gap-filled) | `noaacrwsstDaily` / `analysed_sst` | 0.05° (≈ 5.6 × 4.0 km) | daily, 12:00 UTC |
| **SMAP SSS** | SMAP sea surface salinity, daily global 0.25° | `noaacwSMAPsssDaily` / `sss` | 0.25° (≈ 28 × 20 km; radiometer footprint ~40 km) | daily (+ our 8-day mean) |

Use "CRW SST" / "SMAP SSS" vs "SP T" / "SP S" to distinguish satellite from profiler values.
(Older docs say "NASA PO.DAAC SST" — that wording is wrong for SST; see the cross-comparison
section below.)

**Plan step status:**

| Step | Status |
|---|---|
| 1. Profiler near-surface time series | Done for sb (10-point mean, not single shallowest point). oo not done. |
| 2. Low-salinity event detection | Not started |
| 3. SMAP SSS | Implemented via CoastWatch ERDDAP (not the PO.DAAC/Earthdata route below) |
| 4. Satellite ↔ profiler correlation | Visual only (`surface_plot.py`); quantitative fit not started |
| 5. Multi-sensor coincidence characterization | Not started |
| 6. Columbia River discharge (USGS) | Not started |

**Known issues / caveats:**

- Everything is hardcoded to Slope Base (`slopebase`, sb lat/lon); oo (and ab) need the
  fetchers/extractor generalized to the 2-letter site code.
- The profiler "surface" is the shallowest reached point: median 8.5 m (10th–90th pct
  5.2–21.6 m), up to ~198 m on profiles that didn't ascend. Filter on `obs_depth_m` before any
  satellite comparison.
- ~9 profiles/day vs one satellite value/day — collapse to a daily SP value (mean of shallow
  profiles, or nearest-in-time) before quantitative comparison.
- Satellites see the top ~mm (SST) to ~cm (SSS); the SP surface is 5–20 m. Agreement should
  degrade under strong near-surface stratification — i.e. precisely during plume events.
- Check whether `noaacwSMAPsssDaily` is itself a multi-day running mean; if so our extra 8-day
  rolling mean double-smooths.


## Rationale

- The plume extends 270–310 km offshore in summer (glider observations). Oregon
  Offshore is ~65 km and Slope Base ~100 km from coast — both well within reach.
- The far-field plume layer thickens to 30–40 m depth at distance, overlapping
  with the shallow profiler's ascent range (surface to ~200 m, top ~5–15 m).
- Expected multi-sensor signature: low salinity, elevated temperature, elevated
  CDOM fluorescence, possibly elevated backscatter — simultaneous anomalies
  constituting inter-sensor coincidence.


## Analysis plan

### Step 1: Extract profiler near-surface salinity time series

From pp06 temperature and salinity shards, extract the shallowest valid measurement
from each profile (typically 5–15 m depth). Build a time series:
- profile timestamp (from shard metadata)
- shallowest salinity value
- shallowest temperature value
- depth of shallowest measurement

Do this for Oregon Offshore and Slope Base (2015–2025).

*Implemented (sb) as `surface_extract.py`, using the mean of the shallowest 10 valid points
rather than the single shallowest point, and adding DO and CDOM.*

### Step 2: Identify low-salinity events

Define a baseline: median salinity in the 5–20 m layer, computed per month from
the full record. Flag profiles where near-surface salinity drops more than 1 PSU
below the monthly median. These are candidate plume detection events.

Characterize each event:
- Duration (how many consecutive profiles show the anomaly)
- Depth penetration (how deep does the fresh layer extend)
- Coincident signals (is CDOM elevated? temperature elevated? backscatter elevated?)

### Step 3: Download SMAP SSS satellite data

**As implemented:** `fetch_sss.py` pulls the SMAP SSS point time series from NOAA CoastWatch
ERDDAP (`noaacwSMAPsssDaily`, variable `sss`) — public, no authentication — and adds an 8-day
rolling mean (`sss_8day`). See the Status section for resolution and coverage.

**Alternative route (original plan, not used):** the RSS SMAP L3 8-day running-mean product
from PO.DAAC, which requires a NASA Earthdata login.

NASA's SMAP satellite provides 8-day running-mean sea surface salinity at ~40 km
resolution from April 2015 to present.

**Dataset:** SMAP RSS L3 SSS 8-Day Running Mean V6.0
**Access:** PO.DAAC via OPeNDAP or Earthdata download
**URL:** https://podaac.jpl.nasa.gov/dataset/SMAP_RSS_L3_SSS_SMI_8DAY-RUNNINGMEAN_V6

**How to download:**

1. Create a free NASA Earthdata account: https://urs.earthdata.nasa.gov
2. Install earthaccess: `pip install earthaccess`
3. Use this Python script to extract a time series at the profiler locations:

```python
import earthaccess
import xarray as xr
import numpy as np

# Authenticate
earthaccess.login()

# Search for SMAP SSS granules
results = earthaccess.search_data(
    short_name="SMAP_RSS_L3_SSS_SMI_8DAY-RUNNINGMEAN_V6",
    temporal=("2015-04-01", "2025-12-31"),
)

# Open as xarray (streaming via OPeNDAP — no bulk download needed)
ds = xr.open_mfdataset(earthaccess.open(results), combine='by_coords')

# Extract time series at profiler locations
# Oregon Offshore: ~44.66N, 124.95W
# Slope Base: ~44.53N, 125.39W
offshore_sss = ds['sss_smap'].sel(latitude=44.66, longitude=-124.95, method='nearest')
slopebase_sss = ds['sss_smap'].sel(latitude=44.53, longitude=-125.39, method='nearest')

# Save to CSV
offshore_sss.to_dataframe().to_csv('~/ooi/oo/metadata/smap_sss_offshore.csv')
slopebase_sss.to_dataframe().to_csv('~/ooi/sb/metadata/smap_sss_slopebase.csv')
```

Note: Variable names and coordinate names may differ slightly. Check with
`ds.data_vars` and `ds.coords` after opening. The SMAP grid may use
`longitude` in 0–360 range (so -124.95 becomes 235.05).

### Step 4: Correlate satellite and profiler time series

Overlay the SMAP SSS time series with the profiler near-surface salinity time series.
Look for:
- Do low-SSS events in satellite data align temporally with low-salinity profiles?
- Is there a lag (satellite sees the plume before the profiler, or vice versa)?
- Seasonal pattern: are detections concentrated in summer (upwelling-favorable winds
  push plume offshore/southward)?

The temperature analogue (CRW SST vs SP T) and its quantification plan are in
"Satellite cross-comparison: CRW SST vs top-of-profile SP temperature" below.

### Step 5: Multi-sensor coincidence characterization

For confirmed plume events (satellite + profiler agreement):
- Plot T, S, CDOM, backscatter profiles together
- Compute the depth of the fresh layer (depth where S returns to background)
- Check if temperature is anomalously warm (river water in summer)
- Check if CDOM is anomalously high (terrigenous organic matter)
- This is inter-sensor coincidence: multiple sensors responding to the same
  coherent water mass intrusion

### Step 6: Contextualize with Columbia River discharge

USGS gauge 14246900 (Columbia River at Beaver Army Terminal) provides daily
discharge. Available at: https://waterdata.usgs.gov/monitoring-location/14246900/

Overlay discharge with plume detection events. High spring discharge (May–June
freshet) should correlate with more/stronger plume detections at the profilers,
with a lag of days to weeks depending on wind regime.


## Expected outcomes

- A catalog of plume incursion events at each profiler site (dates, duration, intensity)
- Validation of profiler-detected freshwater events against satellite observations
- Demonstration of "corroborated coincidence" for the AGU framework
- Quantification of plume depth at the profiler sites (satellite gives surface only;
  profiler reveals vertical extent)


## Data requirements

| Source | Location | Status |
|--------|----------|--------|
| pp06 salinity/temperature shards | ~/ooi/sb/postproc/pp06/ | Available |
| pp06 CDOM/backscatter shards | ~/ooi/sb/postproc/pp06/ | Available |
| SMAP SSS (CoastWatch ERDDAP `noaacwSMAPsssDaily`) | ~/ooi/sb/metadata/external/satellite_sss_slopebase.csv | Available (sb); public, no auth |
| CRW SST (CoastWatch ERDDAP `noaacrwsstDaily`) | ~/ooi/sb/metadata/external/satellite_sst_slopebase.csv | Available (sb); public, no auth |
| SMAP SSS V6.0 (RSS, PO.DAAC) | PO.DAAC (NASA) | Alternative only; needs Earthdata account |
| USGS Columbia River discharge | waterdata.usgs.gov | Free, public; not yet fetched |
| Profile metadata (timestamps) | ~/ooi/sb/profileIndices/ | Available |


## References

- Palacios et al. (2009). "Development of synthetic salinity from remote sensing
  for the Columbia River plume." JGR. doi:10.1029/2008JC004895
- Saldias et al. (2016). "Optics of the offshore Columbia River plume from glider
  observations and satellite imagery." JGR. doi:10.1002/2015JC011431
- Liu et al. (2009). "Seasonal and interannual variability of the Columbia River
  plume." JGR. doi:10.1029/2008JC004964
- Adams et al. (2015). "Anomalous near-surface low-salinity pulses off the central
  Oregon coast." Scientific Reports. doi:10.1038/srep17145
- Nash & Moum (2005). "River plumes as a source of large-amplitude internal waves
  in the coastal ocean." Nature, 437, 400–403. doi:10.1038/nature03936


## ERDDAP data access URLs

Interactive map (SSS, regional, change dates as needed):
```
https://coastwatch.noaa.gov/erddap/griddap/noaacwSMAPsssDaily.graph?sss[(2020-06-15T00:00:00Z):1:(2020-07-05T00:00:00Z)][(0)][(42.0):(49.0)][(-130.0):(-122.0)]
```

Interactive map (SST, regional):
```
https://coastwatch.noaa.gov/erddap/griddap/noaacrwsstDaily.graph?analysed_sst[(2020-06-15T00:00:00Z):1:(2020-07-05T00:00:00Z)][(42.0):(49.0)][(-130.0):(-122.0)]
```

Point time series (as used by `plume/fetch_sst.py` / `plume/fetch_sss.py`):
```
SSS: https://coastwatch.noaa.gov/erddap/griddap/noaacwSMAPsssDaily.csv?sss[(2024-01-01T00:00:00Z)][(0)][(44.53)][(-125.39)]
SST: https://coastwatch.noaa.gov/erddap/griddap/noaacrwsstDaily.csv?analysed_sst[(2024-01-01T12:00:00Z)][(44.53)][(-125.39)]
```


## Satellite cross-comparison: CRW SST vs top-of-profile SP temperature

*(Moved from `BR.md`, Nov 2026.)*

**Current state (verified Sep 2026):** the SST↔SP-surface comparison exists but is VISUAL ONLY —
`plume/surface_plot.py` Panel 3 overlays profiler `temp_mean` (shallowest-10-point mean from
`surface_extract.py`, on pp06) against satellite SST (from `fetch_sst.py`). No quantitative fit.
**Also:** the "SST" is actually **NOAA Coral Reef Watch** (`noaacrwsstDaily` via CoastWatch
ERDDAP), NOT literally PO.DAAC — reconcile the "NASA PO.DAAC SST" wording in DeveloperGuide/MOAR.
And the plume fetchers hardcode `slopebase` + sb lat/lon (same stale-naming pattern fixed elsewhere).

**Data available for the comparison (sb, verified Nov 2026):** 2,435 overlap days (every SP
profile day has a CRW SST value), 20,447 profiles. Overlap days per year: 2015: 82,
2016: 303, 2017: 124, 2018: 207, 2019: 241, 2020: 146, 2021: 324, 2022: 267, 2023: 162,
2024: 264, 2025: 315.

**To do:**
- Add a QUANTITATIVE SST-vs-SP-surface analysis: time-align satellite SST with per-profile surface
  temp, compute correlation / RMSE / bias (and seasonal breakdown), to substantiate the MOAR claim
  "SST tracks SP surface well" (currently flagged as an unverified project observation).
- Demonstrate fidelity **better than an uninformed baseline** ("random SST") — e.g. a skill
  score against time-shuffled or off-site SST, or against climatology/persistence — not just
  correlation/RMSE/bias in isolation. (Top of `DevelopmentLog.md` → Pending To Do.)
- Reconcile provider wording (NOAA CRW vs PO.DAAC) across code + docs.
- Generalize plume fetchers to the 2-letter site code + per-site lat/lon (retire `slopebase`).
- (Ties to G3: this cross-comparison is exactly what standardized metadata + a satellite "external"
  product should make routine rather than bespoke.)


## Extension: regional CRW SST heatmap time-series movie (eddy structure)

*(Moved from `BR.md` → "Analysis topic: harmonizing data to scale water-mass emplacement
anomalies", sub-topic A, Nov 2026. Sub-topic B — SP velocity + ADCP fusion, S = V·T — remains in
`BR.md`.)*

Extend the current POINT SST fetch (`plume/fetch_sst.py`, single lat/lon) to a REGIONAL BOX fetch
(`SST[time, lat, lon]`) — the ERDDAP griddap box-query form already appears above in "ERDDAP data
access URLs" (`[(42):(49)][(-130):(-122)]`). Animate frames over time (reuse `vis/bundle_animate.py`
machinery) to SEE a mesoscale feature approach/pass a SP site, then check whether top-of-profile
temperature registers it at the matching time — turning "2-month anomaly" into "here is the feature
responsible."
- Caveats: NOAA CRW ~5 km resolves mesoscale eddies (tens of km) but NOT submesoscale filaments;
  IR SST has cloud gaps (analysed products gap-fill/smooth); SST is surface-only (corroborates
  top-of-profile T, says nothing direct about the subsurface salinity lens).
- Upgrade path if eddies become central: sea-surface-height / geostrophic velocity (AVISO/Copernicus)
  detects eddies DIRECTLY (closed SSH contours + rotation) — a stronger eddy detector than SST.
