This folder `~/argosy/plume/` contains files for the **plume study**: detecting the Columbia
River freshwater plume in the shallow profiler near-surface record, cross-compared with
satellite SST and SSS.

Plan, status, data sources, and ideation: **`ColumbiaPlumePlan.md`** (in this folder; part of
the Jupyter Book). Book notebook: `chapters/ColumbiaPlume.ipynb` (runs the scripts below via
`%run`).

- `ColumbiaPlumePlan.md` — the plume study plan: hypothesis, 6-step analysis plan, status,
  satellite data sources (CRW SST, SMAP SSS), SST cross-comparison to-dos, eddy-movie extension.
- `surface_extract.py` — per-profile near-surface statistics from pp06 (mean/std of the
  shallowest 10 valid S, T, DO, CDOM points; shallowest depth; dS/dz) →
  `~/ooi/<site>/metadata/features/surface_extract_slopebase.csv`.
- `fetch_sst.py` — CRW SST (NOAA Coral Reef Watch daily 5 km, `noaacrwsstDaily`) point time
  series via NOAA CoastWatch ERDDAP, no auth → `~/ooi/<site>/metadata/external/satellite_sst_slopebase.csv`.
- `fetch_sss.py` — SMAP SSS (`noaacwSMAPsssDaily`, 0.25°) point time series via CoastWatch
  ERDDAP, no auth, plus 8-day rolling mean → `~/ooi/<site>/metadata/external/satellite_sss_slopebase.csv`.
- `surface_plot.py` — stacked near-surface panels (S, SMAP SSS, T vs CRW SST, DO, CDOM, depth,
  std, dS/dz) for a chosen date range → PNG in `~/ooi/<site>/visualizations/`. Runs standalone
  (`python surface_plot.py`, headless Agg) or via `%run` in the notebook.
- `smap_download.py` — **LEGACY.** Earlier combined SSS + SST fetch to
  `smap_sss_slopebase.csv`; superseded by `fetch_sst.py` + `fetch_sss.py`. `surface_plot.py`
  reads it only as a fallback.

Current limitation: all scripts are hardcoded to Slope Base (`slopebase`, 44.53 N −125.39 W);
generalizing to the 2-letter site code (oo, ab) is an open to-do in `ColumbiaPlumePlan.md`.
