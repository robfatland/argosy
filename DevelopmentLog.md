# Development Log


This document:


- expands on project scope (see Red Zone and Umbrella sections)
- tracks progress
- is used for "what next?" content in three sections
    - Open Topics: Reminder list for this very complex project
    - Pending: Items to get too in the soon but not now time frame
    - Next: The now time frame


For observatory background see `OOIObservatory.md`. For workflow detail 
see `Workflow.md`.


## Red Zone


The red zone is metaphorically getting from clean data to data analysis.


- Starting point: A spatiotemporal dataset to pave the way
    - OOI observatory (many arrays)
    - Regional Cabled Array (RCA): Northeast Pacific off the coast of Oregon
    - Single site/platform: Oregon Slope Base shallow profiler
    - One instrument: CTD
    - One sensor: Temperature
    - Full-resolution data from OOINET (legacy data system) in NetCDF format
    - Time series boxed by year
    - Profiles time-boxed using metadata (up to 9 per day)
        - Mostly using *ascent* with two exceptions for other sensors
    - 2015 through 2025
    - Result: A `redux` temperature profile dataset (comparatively low data volume)
        - Profiles index to dimension `time` (replacing `obs`) with associated `depth`
        - Back this up to AWS S3 object storage
        - Data folder is external to the `argosy` repo 
- Create visualization tools based on `matplotlib` residing in a notebook in this Argosy Jupyter Book
    - Plots tend to set up with temperature (etcetera) variation on the x-axis and depth on the y-axis
    - Plots can be single profile or bundled (an overlay of many related profiles)
        - Interactive bundle plots select time window width and starting point via two sliders
        - This uses the interactive widget
    - Create time-series animations of this data
    - From this start to formulate how to build a persistent anomaly dataset
- Add 10 more scalar sensors following these guidelines
    - Dissolved Oxygen, Salinity, Density, Backscatter, FDOM, Chlorophyll A
    - pCO2, pH, PAR, Nitrate
    - Follows the temperature plan
- Add four vector sensors
    - Point current measurement: east, north, up
    - spectral irradiance: 7 wavelengths, downwelling
    - instrument: spectrophotometer
        - sensor: optical absorbance
        - sensor: beam attenuation
        - 73 elements (wavelengths)
- For specs on the project file system see `FileSystemWorkflow.md`)
    - source data
    - metadata including profile time boundaries
    - separated sensor+profile data files ("sharding" (`redux`))
    - post-processing versions of the sharded data
- Build out analysis machinery

    

## Umbrella


The umbrella is abstractly "incorporating other data resources beyond the shallow profiler sensors
found at the Oregon Slope Base site". This term comes from considering remote sensing time series
data (with some geospatial extent) as the umbrella canopy; where the shallow profiler sensors 
comprise the umbrella pole.  


### Done: Data already incorporated


- **Tidal model predictions**: Harmonic constituents for the three RCA shallow profiler sites
  (Oregon Offshore, Oregon Slope Base, Axial Base) were extracted from the TPXO10-atlas-v2
  global tidal model. The extracted data is stored in `tidal_constituents.json` — self-contained
  for predicting tidal height at any time. Extraction scripts retired after producing the JSON.
  Analysis of start-depth vs tidal prediction documented in `TidalAnalysis.md`.


### Instruments/sensors/data streams beyond the shallow profiler 


This is at much lower task resolution.


- Use current sensors (ADCP etcetera) on the profiler platform for current
- Extend the Oregon Slope Base workflow to the other two shallow profilers in the RCA
- Incorporate NOAA sea surface state buoy data
- Apply the methodology to the shallow profiler platform moored at 200 meters
- Extend focus within RCA to other sensors
    - Horizontal Electrometer Pressure Inverted Echosounders (HPIES; 2 sites)
    - Broadband Hydrophone and other acoustic sensors as directed (see WL, SA)
    - Axial tilt meters, seismometers etcetera
- Glider data from Coastal Endurance
- NANOOS installations
- ARGO
- Global ocean dataset formerly known as GLODAP
- PO-DAAC data including 
- Inferred ocean surface chlorophyll (LANDSAT, MODIS etcetera) 
- Publish the pipeline and output results to be openly available
    - Includes appraisal of working on the OOI-hosted Jupyter Hub
    - Includes containerization as appropriate



## Open Topics


- Inquire about a shallow profiler conversation with A.Gray
- Bundle plot "Scanning redux folders" message counts shard files rather than unique profiles.
  Replace with profile count from `profileIndices` plus maximum possible.
- 2020 T vs S has odd behaviors: Wide aneurism in salinity; +/- buttons don't behave as expected.
  Suggest making mean/std box width a slider.
- Backscatter shard: Verify using `optical_backscatter` not `total_volume_scattering_etcetera`.
- Revamp animations (frame timing, hold time per frame).
- Add curtain plots: See e.g. `~/OceanRepos/notebooks/dev_notebooks/keenan/3d_DO.ipynb`.
- Axis offset calculation for dual-sensor bundle plots: Verify the math with a worked example.
- DO streams: Confirmed CTD-derived DO is identical to DOFSTA; using CTD as single source.
- Revalidate that DO data is identical to the DO sensor data found in the CTD instrument file (side-by-side value comparison still pending).
- Is there a means of automated data retrieval from OOINET (eliminating the manual order step)?
- Proper use of engineering / metadata to validate a sensor time series: Use data quality flags (qartod) to disqualify certain segments automatically.
- Profile count calculation confusion (line ~1050):
    - The diagnostic shows "4394 profiles" for 2015 but then says it should show "578 profiles (3285 possible)"
    - The document correctly identifies this as counting shard files (4 sensors × ~1100 profiles ≈ 4400)
    - But the logic needs clarification: Are you counting unique profiles or total shard files?
- Time zone handling ambiguity:
    - Mentions UTC-8/UTC-7 for standard/daylight time
    - Doesn't specify when DST transitions occur (important for the NOON/MIDNIGHT logic)
    - Consider adding explicit DST transition dates or using a timezone library
-Gripes section (line ~180):
    - Mentions "two streams for DO" plus a third - this unresolved question could affect the dissolved oxygen processing
    - Should be investigated before finalizing the sensor variable names
- Animation frame timing (line ~450):
    - Says "If possible: Add in a 'hold time' per frame of d seconds"
    - This uncertainty should be resolved - matplotlib animations support frame duration
- Axis offset calculation (lines ~900-920):
    - The formula for offsetting two sensor ranges is clever but could use a worked example
    - The concrete example helps but doesn't match the formula exactly (should verify the math)
- Terminology for indexing profiles:
    - "global profile index" means the ordinal global index across all time: From profileIndices
    - "daily profile number" refers to a particular day: Which profile this is in the range 1 -- 9
- Finding and using QC flags (qartod) for data exclusion filter: See `PostProcessing.md` QC Filter section.
  Initial study shows 0.11% suspect temperature and 9.38% suspect conductivity in a 2018 CTD file.
  Need to determine if flagged data falls within profiles (actionable) or at rest (ignorable).
- Validation test: Calculate contour lines with independent code and compare with Vis.ipynb notebook
  values produced for curtain plots. Reference data: `~/ooi/metadata/curtain_contour_values.csv`.
- Revisit ChlorA and CDOM curtain plots: Can they be redeemed? (Dynamic range shifts across time make
  single-colormap representation poor. Consider per-segment normalization or log scale.)
- Place curtain plot at the top of the Vis notebook; and set up a control in the interactive bundle
  chart to launch a bundle chart animation run.
- Consolidate the bundle animation cells in Vis.ipynb (see analysis below).
- **Testing follow-up (high priority)**: Implement and run the tests defined in `Testing.md`
  (SGA synthetic validation, internal wave incompressibility check). Failed tests go to Open Topics.
  - Internal wave incompressibility: DONE. Stream function formulation passes at <3%.
    Remaining error is finite-amplitude (Lagrangian vs Eulerian). See `Testing.md` for details.
- **SGA depth grid range**: Does expanding the SGA depth quantization range add any value to
  the analysis? e.g. 185m - 27m becomes 195m - 5m; see png of histograms at
  `~/ooi/analysis/sga/depth_range_histograms.png`. Also consider depth bin width as a
  hyperparameter: 2m (current, 80 bins) vs 1m (160 bins, doubles feature dimension). Finer bins
  may resolve thin layers but risk curse-of-dimensionality effects in the SGA distance metric.
- **Deep profiler O₂ integration**: Combine shallow profiler (RS01SBPS, 0–200m) with deep profiler
  (RS01SBPD, 200–2900m) to visualize the full water column oxygen structure including the OMZ core
  and deep recovery. See `Umbrella.md` → "Deep Profiler: Full Water Column Oxygen Structure".
- **SGA two-cluster problem**: Multi-year runs converge to k=2 (seasonal dominance). Need diagnostic
  plan: try per-year analysis, force higher k, vary σ², examine outlier cluster composition,
  consider sub-annual windowing. See `SpectralGraphAnalysis.md` → "Known Issues / History".
- Erratics filter: Identify and suppress spurious profile data (e.g. salinity bundles with 180 profiles
  frequently show 1–2 profiles with clearly non-physical values). Could operate as a pp05-level filter
  or a runtime toggle in the bundle chart. Needs a detection heuristic (e.g. profile mean outside
  N sigma of bundle mean, or individual points beyond physical bounds).
- CDOM quantization/smoothing: The WET Labs ECO FLORT sensor digitizes CDOM fluorescence from
  raw counts with coarse ADC resolution, producing a staircase-like profile that obscures real
  structure. References for smoothing approaches:
  - **Savitzky-Golay filter** (Savitzky & Golay 1964; scipy.signal.savgol_filter): Fits local
    polynomials via least squares. Preserves peak width and position better than moving average.
    Standard choice in spectroscopy for quantized/noisy data. Window size = depth span (~5–11
    points at 2m bins = 10–22m smoothing window). Polynomial order 2 or 3.
  - **LOWESS/LOESS** (Cleveland 1979; statsmodels.nonparametric.lowess): Locally weighted
    regression, robust to outliers. More computationally expensive but handles irregular
    spacing well. `frac` parameter controls smoothing bandwidth.
  - **Median filter** (scipy.ndimage.median_filter): Non-linear, good for removing single-point
    spikes while preserving step edges. Less good for quantization noise specifically.
  - Recommendation: Start with Savitzky-Golay (window=11, polyorder=2) as Filter 2 for CDOM
    in pp06. Compare visually with raw data in bundle chart. Same filter likely applicable to
    ChlorA and backscatter.


## Completed (June 2026)

- Full re-shard complete (all instruments, all years 2015–2025). Redux data in `~/ooi/redux/`.
- `~/ooi/ooinet/` (204 GB source NetCDF) synced to `s3://s3ooi/ooinet/` and deleted locally.
- pCO2, nitrate, PAR, pH added to sharding pipeline and sharded.
- NOON/MIDNIGHT identification: DONE via `profile_duration_histograms.py` → `~/ooi/metadata/`.
- PAR fixed in Sensor Table.
- Bundle plot SENSORS dict already includes all 11 scalar sensors (temperature, salinity,
  density, dissolvedoxygen, cdom, chlora, backscatter, ph, pco2, nitrate, par).
- Vis notebook bundle chart: Modifications attempted (slider fix, CDOM/ChlorA/backscatter
  range updates, exclusion filter, time-aligned indexing). Changes proved fragile; notebook
  was reverted to git state. Rebuild plan documented in `~/argosy/VisNotebookRebuild.md`.


## Pending To Do

- **pp06 filters for all 8 HDS sensors**: Filter 1 (salinity/density MRA) is implemented.
  Remaining sensors need their own filters:
  - CDOM: quantized signal, needs smoothing filter (see below)
  - ChlorA: likely similar quantization issues to CDOM
  - Backscatter: may have spike/erratic issues
  - Temperature: generally clean but check for rare spikes
  - Dissolved Oxygen: check for conductivity-coupled artifacts
  - PAR: high dynamic range, check for saturation/zeroing
- **CDOM smoothing research**: The FLORT ECO sensor outputs digitized counts with
  coarse resolution (quantization noise). Candidate filters:
  - Savitzky-Golay (polynomial local regression, preserves peaks/shape)
  - LOWESS/LOESS (locally weighted regression, robust to outliers)
  - Median filter (good for spike removal, preserves edges)
  - Depth-binned averaging (simple, interpretable)
  See references in Open Topics below.
- **Vis notebook rebuild**: Apply changes from `VisNotebookRebuild.md` (bundle plot slider fix,
  SENSORS dict range updates, exclusion filter, time-aligned indexing, curtain plot rewrite,
  animation data source selector).
- Regenerate noon/midnight metadata CSVs (`profile_duration_histograms.py`)
- Regenerate pp01/pp02 (`postprocess_special_profiles.py noon` and `midnight`)
- Check the `argosy` environment installed libraries against `environment.yml`
- LegacyCode/ directory: Review for archival or deletion (entirely superseded by current code)
- TMLD/ directory: Decide whether to keep `tmld_estimates.csv` as historical data; delete the empty `tmld_selector.py`
- Order VELPT data for 2018–present (lower priority; deferred for SGA feature vector)
- Update `CodeManifest.md` to reflect the documentation refactor
- Copy updated `pre_shard_data_availability.png` to `~/argosy/images/` after each regeneration
- Backscatter shard: Verify using `optical_backscatter` not `total_volume_scattering_etcetera`
- Revamp animations (frame timing, hold time per frame)
- 2020 T vs S odd behaviors: Wide aneurism in salinity; suggest making mean/std box width a slider
- `20xx_do` folder: 33 DOFSTA files (2014-2025) from a separate fast-response DO instrument
  (DOFSTA102), NOT redundant with CTD-derived DO. Decide: integrate as second DO source or leave?
- Concerning NOON / MIDNIGHT determination:
    - From 2017 onward, three sensors operate exclusively on daily_index 4 (midnight)
      and 9 (post-noon, ~13:40 local):
        - **Nitrate**: ascent data, ~150 points/profile, full depth range
        - **pCO2**: descent data, ~10 points/profile
        - **pH**: descent data, ~10 points/profile (files exist for all 9 but only 4 and 9 usable)
    - In 2015–2016 these sensors operated on more/all profiles before being restricted.


## Next

- **Bundle chart terminology**: Clarify the meaning of `nProfiles` in the UI. Currently it means
  "number of consecutive global index positions to scan" not "number of profile traces drawn."
  If 3 of 27 positions have no data, you see 24 traces. Options: rename the slider (e.g.
  `nPositions` or `window`), add a display showing actual traces drawn, or change the docs.
  Resolve before sharing with collaborators.
- Finish writing `pp06ErraticFilterPrompt.md`
- Apply Vis notebook rebuild (see `VisNotebookRebuild.md`)


## Bundle Chart applied to pp06

`nProfiles` is the nominal number of consecutive GPI-assigned profiles to render in bundle
mode or use for the meanstd calculation. This is a **maximum**: the bundle chart renders at
most this many traces. It renders fewer when filtering operations (pp05 exclusions, pp06
filters) have removed GPI-assigned profiles from the shard pool.

The implication: because of profile dropouts, the bundle chart's time window varies in
duration as the slider is moved. Two adjacent slider positions (e.g. index0=1000 vs
index0=1001) with the same nProfiles may span different calendar durations, since gaps
in the shard pool compress time coverage.

Example with nProfiles=10, index0=1000 on pp06:
- Global indices scanned: 1000, 1001, 1002, ..., 1009 (always 10 consecutive integers)
- If GPIs 1003 was removed by a pp06 filter: 9 traces rendered (not 10)
- The title shows the index range scanned: `(Global indices 1000 - 1009)`
- The actual data range (first to last trace) is read from the title date fields
