# Columbia River Plume Detection Plan

Hypothesis: The Columbia River freshwater plume reaches the Oregon Offshore and
Slope Base shallow profiler sites seasonally, producing detectable multi-sensor
anomalies in the upper 15–40 m of the profiler record.


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

### Step 2: Identify low-salinity events

Define a baseline: median salinity in the 5–20 m layer, computed per month from
the full record. Flag profiles where near-surface salinity drops more than 1 PSU
below the monthly median. These are candidate plume detection events.

Characterize each event:
- Duration (how many consecutive profiles show the anomaly)
- Depth penetration (how deep does the fresh layer extend)
- Coincident signals (is CDOM elevated? temperature elevated? backscatter elevated?)

### Step 3: Download SMAP SSS satellite data

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
| SMAP SSS V6.0 | PO.DAAC (NASA) | Free, needs Earthdata account |
| USGS Columbia River discharge | waterdata.usgs.gov | Free, public |
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

Point time series (as used by `plume/smap_download.py`):
```
SSS: https://coastwatch.noaa.gov/erddap/griddap/noaacwSMAPsssDaily.csv?sss[(2024-01-01T00:00:00Z)][(0)][(44.53)][(-125.39)]
SST: https://coastwatch.noaa.gov/erddap/griddap/noaacrwsstDaily.csv?analysed_sst[(2024-01-01T12:00:00Z)][(44.53)][(-125.39)]
```
