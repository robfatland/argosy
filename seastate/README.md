This folder `~/argosy/seastate` contains files for retrieving and using ERA5 reanalysis
sea-state, wind-stress and surface-flux series at the three shallow-profiler sites, as an
independent (non-OOI) check on the winter-deep / summer-shallow MLD seasonality.

- `fetch_era5.py` -- downloads hourly ERA5 POINT time-series (CDS dataset
  `reanalysis-era5-single-levels-timeseries`) at each site's exact lon/lat, one file per
  site-year, into `~/ooi/<site>/metadata/external/era5/`. One request carries waves + wind +
  stress + heat-flux variables; CDS may return a ZIP of several tables because the wave grid
  (0.5 deg) and the atmospheric grid (0.25 deg) differ. Skips existing files; `--dry-run` lists
  requests. Licence: on the dataset page click "Accept terms" once (free, tied to the account
  the API uses).

- `load_era5.py` -- opens a site-year payload (plain `.nc`, or the `.zip` of wave + surface
  members), merges on `valid_time`, and adds derived fields: wind speed/direction, wind stress
  `tau` and friction velocity `ustar` (constant bulk Cd), and turbulent heat fluxes in W/m^2
  (`qlat`, `qsens`, `qturb`). `daily()` gives daily means plus `wind_work` = daily integral of
  ustar^3 (a mixing-energy index for lagged MLD regressions). When the shared radiation files
  (`~/ooi/era5_shared/`) exist it also crops each site's nearest cell and adds `qsw`, `qlw`,
  `qrad` and the full net surface heat flux `qnet` (W/m^2, + down). API: `load_site_year`,
  `load_site`, `daily`. CLI: `python load_era5.py --site oo --year 2024 [--plot]`.

- `fetch_era5_radiation.py` -- downloads net surface solar (`ssr`) and thermal (`str`)
  radiation from the GRIDDED dataset `reanalysis-era5-single-levels`. Needed because the point
  product omits radiation; with slhf/sshf it completes the net surface heat budget. Requires its
  own "Accept terms" click. SPEED: gridded requests take ~20 min each, so one shared box covers
  all 3 sites (one file per year, `~/ooi/era5_shared/era5rad_shared_<yyyy>.nc`) and several
  years are submitted concurrently (`--workers`, default 3). Not yet merged by `load_era5.py`;
  the loader will crop each site's nearest cell. (A one-off `era5rad_oo_2024.nc` exists under
  `~/ooi/oo/metadata/external/era5/` from the earlier per-site design; use it as a cross-check.)

- `compare_mld.py` -- first-look comparison for one site-month: plots human-labeled MLD (science
  label set, per sensor) against ERA5 wind, Hs, ustar^3 and turbulent heat flux, and prints
  Spearman correlations of MLD vs trailing-window (6/24/72/168 h) forcing means.
  `python compare_mld.py --site sb --month 2024-01`.

What this POINT product actually serves (confirmed Nov 2026): wave file = swh, mwp, mwd;
surface file = u10, v10, slhf, sshf. Peak period, wind-wave/swell Hs, the turbulent-stress
pair, and net radiation are NOT served -- so stress/u* are derived from u10,v10, and the heat
budget is the TURBULENT part only (no radiation).

Design notes and caveats are in `Umbrella.md` -> "ERA5 sea state".
