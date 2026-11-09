# Umbrella

This file describes the 'umbrella' askpect of this OOI project. For a definition
of umbrella in this context: See the glossary in `~/argosy/OOIObservatory.md`. This markdown file 
primarily concerns non-OOI data resources, the most important aspect of the umbrella 
concept. The scientific objective is to use this profusion of data to better characterize 
the upper water column (photic zone) in the northeast Pacific, particularly in 
the vicinity of the Regional Cabled Array.


## List of umbrella data resources outside of the OOI program


- National Data Buoy Center (NDBC)
- PO-DAAC


## National Data Buoy Center (NDBC)


Oregon Slope Base (informal abbreviation in this book "sb") is located at 44.529°N, 125.390°W
(table below). An earlier version of this file gave sb as 42.754°N, 124.839°W; those are in fact
the coordinates of NDBC station 46015 "Port Orford", not of sb. Corrected Nov 2026.

**NDBC status: stub (Nov 2026).** The `NDBC/` folder was retired; nothing was ever built on it. The
program summary, station list (46050 Stonewall Bank is the best candidate, ~70 km from sb and ~50 km
from oo; 46015 is ~200 km south and possibly out of service) and honest utility assessment are in
`seastate/README.md` -> "NDBC". The one downloaded file (46015, 2016) is at
`~/ooi/sb/metadata/external/ndbc/`. The buoy comparison is now part of the `seastate` work below.


Shallow profiler coordinates:


```
Site name             Abbreviation     Latitude          Longitude
------------------    ------------     --------          ---------
Oregon Offshore         OOF            44.37415          -124.95648
Oregon Slope Base       OSB            44.52897          -125.38966 
Axial Base              AXB            45.83049          -129.75326
```   


#### Distance calculation


```
from math import pi, cos, sqrt
def distance_approximate(lat_a_dd, lon_a_dd, lat_b_dd = 44.6, lon_b_dd = -124.):
    '''
    A very coarse distance local distance estimation in km.
    The default lat/lon is Newport Oregon.
    '''
    conversion = pi/180
    lat_a_rad = lat_a_dd * conversion
    lon_a_rad = lon_a_dd * conversion
    lat_b_rad = lat_b_dd * conversion
    lon_b_rad = lon_b_dd * conversion
    re        = 6378.                        # earth radius, km
    mean_lat  = (lat_a_rad + lat_b_rad)*0.5
    dx_km     = (lon_a_rad - lon_b_rad)*cos(mean_lat)*re
    dy_km     = (lat_a_rad - lat_b_rad)*re
    return sqrt(dx_km**2 + dy_km**2)
```


[46015 historic data dedicated page](https://www.ndbc.noaa.gov/station_history.php?station=46015)


[Descriptions of data fields in NDBC historical data files](https://www.ndbc.noaa.gov/faq/measdes.shtml)


An example text table file was downloaded: Standard Meteorological Data, NDBC Buoy 46015, hourly
for 2016. It now lives at `~/ooi/sb/metadata/external/ndbc/NDBC46015h2016.txt` (moved from the
retired `~/argosy/NDBC/` folder in Nov 2026). The first two rows act as type/units doubled column headers:


```
#YY  MM DD hh mm WDIR WSPD GST  WVHT   DPD   APD MWD   PRES  ATMP  WTMP  DEWP  VIS  TIDE
#yr  mo dy hr mn degT m/s  m/s     m   sec   sec degT   hPa  degC  degC  degC   mi    ft
```


These 18 columns are interpreted in order from left to right:


- Year (Note: Date is UTC)
- Month
- Day
- Hour
- Minute
- Wind Direction (degrees true north)
- Wind speed (meters per second)
- Wind gust (meters per second)
- Wave height (meters)
- DPD = Dominant Wave Period in seconds
- APD = Average Wave Period in seconds
- MWD = Mean Wave Direction (degrees true north)
- Pressure (hectoPascal, equivalent to millibars)
- Air Temperature (deg C)
- Water Temperature (deg C)
- Dewpoint (deg C) NODATA = 999
- Visibility (miles) NODATA = 99
- Tide (feet) NODATA = 99


There are 8307 rows of actual data starting December 31 2015 at 23:50 UTC.
The possible number of rows is 366 x 24 = 8784 so we expect about 480
missing entries corresponding to 20 days.


### Comparing NDBC buoy data with Slope Base shallow profiler data



data that are comparable to shallow profiler data include...


- Wave height + Wind + Wave Periods: compare to mixed layer depth
- Wave Direction compare to velocity at profile apex
- Water temperature compare to temperature at profile apex



Other data types beyond standard meteorological are: 


- Continuous winds data
- Five types of wave data
- Supplemental measurement data (certain years only)


## ERA5 sea state (MLD seasonality check)

Question: summer MLD is shallower than winter. Is that explained by mixing energy (storms,
waves, wind stress) or by stratification (surface heating)? Plan agreed Nov 2026: start with
ERA5 (all three sites, no OOI streams yet). Platform ADCP/VELPT wave estimation is deferred.

- Code: `~/argosy/seastate/fetch_era5.py` (see `seastate/README.md`). CDS dataset
  `reanalysis-era5-single-levels-timeseries` (the POINT product: give it a lon/lat, get a
  ready-made series at the nearest grid cell -- no area box). Output:
  `~/ooi/<site>/metadata/external/era5/era5_<site>_<yyyy>.nc` (one per site-year; may be a
  `.zip` of several tables when the wave 0.5 deg and atmospheric 0.25 deg grids differ).
- Fields: waves (Hs, mean/peak period, mean direction, wind-wave and swell Hs); 10 m wind;
  turbulent surface stress; latent/sensible/shortwave/longwave heat flux.
- Caveats: wave grid is 0.5 deg (a +/-0.5 deg box gives only a few cells); stress and heat flux are
  hourly ACCUMULATIONS (divide by 3600 s); heat flux sign is positive downward.
- Hs is probably not the best MLD predictor. Prefer wind stress / friction velocity and net
  surface heat flux, accumulated over a lag window (e.g. integrated u*^3 over the prior N days).
- Validation anchor: OOI Endurance surface mooring CE04OSSM (Axys TriAxys wave sensor) is at oo;
  compare ERA5 Hs there, and NDBC 46050, to establish model skill before trusting it at sb and ab.

### Status (2026-11-06)

- Data: ERA5 point series (waves, wind, latent/sensible flux) for sb/oo/ab 2014-2026, plus gridded
  net solar/longwave radiation in one shared box (`~/ooi/era5_shared/`). `seastate/load_era5.py`
  merges them and derives wind stress, u*, and the full net surface heat flux `q_net`
  (= solar + longwave + latent + sensible, W/m^2, positive downward).
- Method (`seastate/compare_mld.py`): for each human-labeled MLD (science set, `value`-bearing
  labels only; No-MLD and unusable profiles are excluded), take the TRAILING mean of each forcing
  over 6/24/72/168 h before the profile and compute the Spearman correlation with MLD, separately
  per sensor (T/S/DO label the same profiles, so pooling would triple-count). Per-month results are
  saved to `~/ooi/sb/analysis/seastate/mld_forcing_corr_sb_<yyyy-mm>.csv`; plots to
  `~/ooi/sb/visualizations/mld_vs_era5_sb_<yyyy-mm>.png`.

### Results: sb, 2024 (Spearman rho, MLD vs trailing-window forcing)

rho > 0 means stronger / more-downward forcing goes with a DEEPER MLD. Columns are T / S / DO.
`q_net` is net heat flux (negative = ocean losing heat); `ustar^3` is the wind mixing-energy index.

| Month | usable n (T/S/DO) | q_net 72 h | q_net 168 h | ustar^3 72 h | ustar^3 168 h |
|---|---|---|---|---|---|
| Jan | 259 / 262 / 263 | -0.31 / -0.56 / -0.27 | -0.38 / -0.61 / -0.38 | 0.16 / 0.08 / 0.18 | 0.07 / 0.05 / 0.03 |
| Aug | 49 / 46 / 56 | -0.69 / -0.69 / -0.64 | -0.68 / -0.64 / -0.60 | 0.69 / 0.69 / 0.56 | 0.64 / 0.56 / 0.52 |
| Sep | 210 / 196 / 220 | -0.21 / -0.22 / -0.33 | 0.05 / 0.02 / -0.13 | 0.18 / 0.19 / 0.27 | -0.17 / -0.10 / 0.02 |
| Oct | 216 / 195 / 251 | -0.43 / -0.48 / -0.42 | -0.50 / -0.60 / -0.58 | 0.35 / 0.44 / 0.36 | 0.25 / 0.32 / 0.40 |
| Nov | 214 / 218 / 231 | -0.33 / -0.40 / -0.42 | -0.27 / -0.30 / -0.28 | 0.12 / 0.21 / 0.42 | 0.30 / 0.32 / 0.41 |
| Dec | 241 / 224 / 229 | +0.20 / +0.58 / +0.43 | +0.20 / +0.39 / +0.35 | 0.44 / 0.26 / 0.37 | 0.43 / 0.30 / 0.42 |

Other notable entries: Hs tracks wind (Aug 72 h: 0.66 / 0.65 / 0.53; otherwise weak, 0 to 0.3);
solar `q_sw` is positive in Aug (168 h: +0.61 / +0.47 / +0.55) but negative in Nov and Dec
(168 h about -0.3 to -0.4); Dec turbulent flux alone is strongly positive (72 h salinity +0.61).

### Reading (tentative)

- **Heat loss is the most consistent driver.** Net heat loss over the prior 3 to 7 days goes with a
  deeper MLD in Jan, Aug, Oct and Nov (rho about -0.3 to -0.7), weakly in Sep.
- **Wind work is positive but modest** in Aug through Dec (rho about 0.2 to 0.7) and near zero in
  January. So storms matter, but less consistently than heat loss.
- **The signs are not stable across months.** December reverses the heat-flux relationship
  (positive), and solar flips sign between Aug and Nov/Dec. A single monotonic "forcing drives MLD"
  story does not fit; lateral advection, the plume, or covarying forcings (clear, windy,
  upwelling-favorable northerlies in summer) probably matter. Not tested.
- **Caveats.** (1) These are rank correlations, not causal. (2) Profiles are ~9 per day and the
  trailing means are strongly autocorrelated, so the effective sample size is closer to the number
  of independent days than to n. (3) August has only 46 to 56 usable labels per sensor out of 429
  rows, because No-MLD and unusable profiles are excluded, so it is both small and selected.
  (4) One year, one site (sb). (5) ERA5 grid cell is ~15 to 20 km from the profiler.
- **This does not yet test the seasonal question** (summer shallow vs winter deep). That needs the
  full-year record (the labeling in progress for 2024 sb/oo/ab) and a seasonal-cycle comparison,
  not within-month correlations.

### What the quantities mean

- **q_net** (net surface heat flux, W/m^2, positive = ocean gains heat) = absorbed sunlight
  (shortwave) + net infrared (longwave, usually negative) + evaporation (latent, negative) +
  conduction (sensible, usually negative). Negative q_net cools the surface water, which sinks and
  mixes the layer deeper; positive q_net stabilizes it and the MLD shoals. Expected sign of the MLD
  correlation: negative.
- **ustar^3** = (friction velocity)^3, with u* = sqrt(wind stress / water density). The rate of
  wind stirring work scales with u*^3, so storms dominate (a 20 m/s wind gives ~8x the stirring of
  10 m/s). Here u* uses a constant drag coefficient, so ustar^3 is essentially (wind speed)^3.
  Expected sign of the MLD correlation: positive.
- **The 72 h and 168 h numbers** (3 and 7 days) are Spearman rank correlations between a profile's
  MLD and the AVERAGE of the forcing over the preceding 72 or 168 hours (a trailing window ending at
  the profile time). The MLD remembers past forcing: it deepens in storms and cold spells and stays
  deep. 3 days captures individual storms; 7 days captures slower build-up. rho = -0.5 for q_net at
  7 days means profiles that followed colder weeks tended to have deeper mixed layers (rho^2 ~ 0.25
  of the rank variance). It is order-only and not causal.

### Sliding-window results: sb, Aug to Dec 2024 (`seastate/rolling_corr.py`)

Method: a centered 21-day window slid by 1 day (133 windows); per sensor; trailing 72 h and 168 h
forcing means; 90% bands from a bootstrap that resamples whole label-days; partial correlations; and
the correlation between the two forcings. Figures: `~/ooi/sb/visualizations/mld_forcing_rolling_*_sb_2024-08-01_2024-12-31.png`
(plain, `_ci_`, `_partial_`); tables in `~/ooi/sb/analysis/seastate/`.

| Month | q_net rho, 168 h (T / S / DO) | Windows with q_net band < 0 (T / S / DO) | ustar^3 rho, 168 h (T / S / DO) | rho(q_net, ustar^3) between forcings, 168 h |
|---|---|---|---|---|
| Aug | -0.28 / -0.27 / -0.24 | 43% / 54% / 40% | 0.22 / 0.28 / 0.10 | -0.49 |
| Sep | -0.03 / -0.02 / -0.11 | 17% / 10% / 27% | -0.01 / 0.04 / 0.07 | -0.71 |
| Oct | -0.42 / -0.43 / -0.51 | 84% / 74% / 97% | 0.30 / 0.33 / 0.41 | -0.77 |
| Nov | -0.17 / -0.15 / -0.17 | 47% / 50% / 43% | 0.19 / 0.16 / 0.30 | -0.70 |
| Dec | 0.11 / 0.41 / 0.24 | 0% / 0% / 0% (positive in 14% / 81% / 29%) | 0.16 / 0.03 / 0.13 | 0.01 |

Findings:

- **October is the clearest month.** The q_net band excludes zero on the negative side in 74 to 97%
  of windows, and the partial correlation of MLD with q_net, controlling for ustar^3, stays near -0.3.
- **From August through November the two forcings are the same events.** rho(q_net, ustar^3) is
  -0.5 to -0.8: windy weeks are the cold weeks (frontal passages). Hence the plain wind correlation
  (0.2 to 0.4, positive in many windows) is mostly the cooling effect seen through a second variable:
  the wind partial correlation (ustar^3 given q_net) is about 0 in Aug to Oct. Only DO in November
  retains an independent wind signal (+0.25). The data cannot separate wind from cooling in these
  months; heat loss is the better-supported driver, and wind may still contribute.
- **December is a different regime.** The two forcings decouple (rho about 0), but the q_net
  relationship flips positive (band entirely above 0 in 81% of salinity windows) and ustar^3 is
  positive in about half of the windows (it dips to about -0.5 near Dec 1). Warmer, windier weeks
  go with deeper MLD. The earlier suggestion that warm south-west storms (wind and weaker cooling
  together) cause the flip is NOT supported: the forcings are uncorrelated in December, not
  positively correlated. Cause unknown.
- **September is weak** for both forcings (q_net significant in only 10 to 27% of windows).
- **August** is low-n before about Aug 25 (fewer than ~10 label days in the window); read the early
  values as unreliable.
- **Caveats.** The bands treat days as independent, but the forcing is autocorrelated across days,
  so the bands are too narrow: a band excluding zero means "robust sign", not a formal test. The
  three sensors label the same profiles, so they are not independent confirmations. One year, one
  site.

### Next steps

1. Check why December flips: (a) are December MLDs deep enough to meet the bottom of the profile
   range? (b) are the excluded "no MLD" and "unusable" labels unevenly distributed across months
   (selection)? (c) does the pattern survive daily-mean MLD?
2. Validate ERA5 against the Oregon Offshore surface mooring CE04OSSM (done below as data are
   fetched: `seastate/compare_era5_mooring.py`); NDBC 46050 as a second check.
3. Finish labeling 2024 for sb, oo, ab, then repeat for all months and the other two sites.
4. Seasonal cycle: monthly-mean MLD vs monthly-mean forcing (heat flux, wind work, Hs).
5. If this grows, split it into its own named project folder (idea: "mldforcing") out of this file.


## Task list


## Deep Profiler: Full Water Column Oxygen Structure


The Oregon Slope Base shallow profiler (RS01SBPS) covers ~0–200m depth. At the same
site, the **deep profiler** (RS01SBPD, McLane Moored Profiler) operates between
approximately 200m and 2900m (near the seafloor at ~2900m bottom depth). The deep
profiler carries a CTD with dissolved oxygen and profiles once or twice per day.

### Motivation: The Oxygen Minimum Zone

Dissolved oxygen profiles from the shallow profiler consistently show decreasing O₂
with depth despite cold water having higher oxygen solubility. This seeming paradox
reflects the balance between supply and consumption:

- **Near-surface O₂ is high** because of atmospheric gas exchange and photosynthesis
  (active in the photic zone, upper ~50m).
- **O₂ decreases with depth** because respiration and decomposition of sinking organic
  matter consume oxygen continuously, while no resupply mechanisms exist at depth (no
  light for photosynthesis, no contact with the atmosphere).

The result is an **Oxygen Minimum Zone (OMZ)**, typically at 200–1000m in the northeast
Pacific. Below the OMZ core, O₂ partially recovers because deep water masses (originating
at polar surfaces — North Atlantic Deep Water, Antarctic Bottom Water) were oxygen-saturated
when they sank. These deep waters are relatively "young" (less time for respiration to
deplete their O₂), so the vertical oxygen profile has a characteristic "C" shape: high at
surface, minimum at mid-depth, partial recovery in the abyss.

### Opportunity

Combining the shallow profiler (0–200m, 9 profiles/day) with the deep profiler
(200–2900m, 1–2 profiles/day) would reveal:

- The complete vertical O₂ structure from surface to near-bottom
- The depth and intensity of the OMZ core at this site
- Seasonal and interannual variability in OMZ depth and intensity
- Potential shoaling of the OMZ (a climate-change indicator in the northeast Pacific)

The deep profiler data is available on OOI under site code **RS01SBPD**. Integration
would require downloading SBPD CTD data, applying a similar sharding pipeline, and
developing a stitched visualization that spans both profiler ranges.

### References

- The OMZ in the northeast Pacific is well-documented; it is one of the most
  intense in the global ocean due to high surface productivity (fueling respiration
  at depth) and sluggish deep ventilation.
- Recent literature reports OMZ expansion and shoaling in this region, potentially
  linked to warming and altered circulation patterns.



