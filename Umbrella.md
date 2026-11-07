# Umbrella

This file describes the 'umbrella' askpect of this OOI project. For a definition
of umbrella in this context: See `~/argosy/AIPrompt.md`. This markdown file 
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

NDBC 46015 is roughly 200 km south of sb (not adjacent). A 2019 NWS service notice said it was
inoperable pending replacement; current status not verified. The closer, more useful buoy is
**46050 Stonewall Bank** (44.68°N, 124.54°W): ~70 km from sb, ~50 km from oo. Others: 46029
(Columbia River Bar), 46089 (Tillamook offshore); for ab the nearest is probably 46005 (verify).
This topic is relegated to `~/argosy/NDBC` for the time being.


[46015 dedicated web page](https://www.ndbc.noaa.gov/station_page.php?station=46015)


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


I downloaded and placed an example text table file: 
Standard Meteorological Data, NDBC Buoy 46015, hourly for 2016. 
This is placed for scrutiny in` ~/argosy/NDBC` with filename `NDBC46015h2016.txt`. 
The first two rows act as type/units doubled column headers:


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

Next steps: fetch; build a daily/lagged series per site; compare against the MLD label set
(`MLDDataRelease.md`, `MLD.py` label CSVs) season by season.


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



