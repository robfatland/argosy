This folder `~/argosy/seastate` contains files for retrieving and using ERA5 reanalysis
sea-state, wind-stress and surface-flux series at the three shallow-profiler sites, and the
Endurance surface mooring, as an independent (non-OOI-profiler) check on the winter-deep /
summer-shallow MLD seasonality.

- **Status:** active (reviewed Nov 2026)
- **Purpose:** independent sea-state, wind and heat-flux data (ERA5, Endurance surface mooring) compared with the human-labeled MLD
- **Next:** run the ERA5-vs-mooring comparison; test why December flips sign; repeat for all months once 2024 labeling is complete; add NDBC 46050 as a second check

## Files

- `fetch_era5.py` -- downloads hourly ERA5 POINT time-series (CDS dataset
  `reanalysis-era5-single-levels-timeseries`) at each site's exact lon/lat, one file per
  site-year, into `~/ooi/<site>/metadata/external/era5/`. One request carries waves + wind +
  heat-flux variables; CDS may return a ZIP of several tables because the wave grid (0.5 deg)
  and the atmospheric grid (0.25 deg) differ. Skips existing files; `--dry-run` lists requests.
  Licence: on the dataset page click "Accept terms" once (free, tied to the account the API uses).
- `fetch_era5_radiation.py` -- downloads net surface solar (`ssr`) and thermal (`str`) radiation
  from the GRIDDED dataset `reanalysis-era5-single-levels` (the point product omits radiation).
  Requires its own "Accept terms" click. Gridded requests are slow (~20 min each), so one shared
  box covers all 3 sites (one file per year, `~/ooi/era5_shared/era5rad_shared_<yyyy>.nc`) and
  several years are submitted concurrently (`--workers`, default 3).
- `load_era5.py` -- opens a site-year payload, merges the wave and surface members, and adds
  derived fields: wind speed/direction, wind stress `tau` and friction velocity `ustar` (constant
  bulk Cd), turbulent heat fluxes (`qlat`, `qsens`, `qturb`) and, when the shared radiation files
  exist, the nearest-cell solar/longwave (`qsw`, `qlw`, `qrad`) and the full net surface heat flux
  `qnet` (W/m^2, positive = ocean gains heat). API: `load_site_year`, `load_site`, `daily`.
  CLI: `python load_era5.py --site oo --year 2024 [--plot]`.
- `compare_mld.py` -- first-look comparison for one site-month: human-labeled MLD (science set,
  per sensor) against ERA5 wind, Hs, ustar^3 and heat flux; Spearman correlations of MLD vs
  trailing-window (6/24/72/168 h) forcing means. `python compare_mld.py --site sb --month 2024-01`.
- `rolling_corr.py` -- sliding-window version: rho of MLD vs trailing q_net and ustar^3 (72 h and
  168 h lags) as a function of DATE (21-day window), per sensor, with 90% day-block bootstrap
  bands, partial correlations, and the q_net-vs-ustar^3 correlation. Writes CSVs and three PNGs.
  `python rolling_corr.py --site sb --start 2024-08-01 --end 2024-12-31` (`--boot 0` skips the bootstrap).
- `compare_era5_mooring.py` -- validates ERA5 against the Oregon Offshore surface mooring CE04OSSM
  (waves from WAVSS; wind, stress, radiation and heat fluxes from METBK), using NetCDF fetched
  from the OOI M2M API into `~/ooi/oo/metadata/external/endurance/`. Prints bias, RMSE,
  correlation and slope; saves scatter and time-series PNGs. `--inspect` lists variable names.

What the ERA5 POINT product serves (confirmed Nov 2026): wave file = swh, mwp, mwd; surface
file = u10, v10, slhf, sshf. Peak period, wind-wave/swell Hs and the turbulent-stress pair are
NOT served, so stress/u* are derived from u10, v10; radiation comes from the gridded product.

Results and caveats are in `../Umbrella.md` -> "ERA5 sea state".


## NDBC: NOAA National Data Buoy Center (unused resource; former folder `NDBC/`, retired Nov 2026)

- **Status:** stub. No code was ever written and no analysis done. The folder `~/argosy/NDBC/` was
removed; its one data file now lives at `~/ooi/sb/metadata/external/ndbc/NDBC46015h2016.txt`.

**What it is.** NOAA's National Data Buoy Center runs moored buoys and coastal stations and
publishes their observations free on the web (station pages, real-time files, yearly archives). The
standard meteorological file is hourly: wind direction, speed and gust; significant wave height
(WVHT), dominant and average wave period (DPD, APD) and mean wave direction (MWD); pressure; air,
water and dew-point temperature; visibility; tide. Some stations also publish wave spectra.

**Purpose for argosy.** Independent, in-situ wind and wave data to check ERA5 (waves are on a coarse
0.5 degree grid) and to compare with the human-labeled MLD. The original idea (Umbrella.md): wave
height and wind versus MLD; wave direction versus velocity at the profile apex; buoy water
temperature versus profile-top temperature.

**Stations near our sites** (distances computed from the profiler coordinates):

| Station | Where | Distance | Note |
|---|---|---|---|
| 46050 Stonewall Bank | 44.68 N 124.54 W, off Newport | ~48 km from oo, ~70 km from sb | best candidate |
| 46029 | Columbia River Bar | far north of oo | Columbia plume context |
| 46089 | Tillamook, offshore | | |
| 46015 Port Orford | 42.75 N 124.84 W | ~200 km south of sb | a 2019 NWS notice said inoperable pending replacement; current status NOT verified |
| 46005 | offshore Washington/Oregon | probably the nearest to ab | NOT verified |

Earlier versions of `Umbrella.md` mistook station 46015's coordinates for Slope Base's; corrected.

**Utility, honestly.** Modest. No NDBC station sits at a profiler, and none is near Axial Base. The
Endurance surface mooring CE04OSSM at the Oregon Offshore site (waves and meteorology, via the OOI
M2M API) is a much closer local check and is used first (`compare_era5_mooring.py`). Station 46050
remains a worthwhile second, independent check for oo and sb. Not used yet.

**Sources.** Station pages: `https://www.ndbc.noaa.gov/station_page.php?station=46050` (and the
other station numbers); field definitions: `https://www.ndbc.noaa.gov/faq/measdes.shtml`.
