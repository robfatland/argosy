# Development Log


This document:


- expands on project scope (see Red Zone and Umbrella sections)
- tracks progress
- is used for "what next?" content in three sections
    - Open Topics: Reminder list for this very complex project
    - Pending: Items to get too in the soon but not now time frame
    - Next: The now time frame


For observatory background see `OOIObservatory.md`. For workflow detail 
see `FileSystemWorkflow.md`.


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


- TODO: Describe the tidal model data


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


## Pending To Do


- Run the full re-shard (all 6 instruments, all years) from clean source data
- Regenerate noon/midnight metadata CSVs (`profile_duration_histograms.py`)
- Regenerate pp01/pp02 (`postprocess_special_profiles.py noon` and `midnight`)
- Add pCO2, nitrate, PAR to bundle plot SENSORS dict once sharded
- Check the `argo-env2` installed libraries against those listed in `ArgosyOverview.md`
- LegacyCode/ directory: Review for archival or deletion (entirely superseded by current code)
- TMLD/ directory: Decide whether to keep `tmld_estimates.csv` as historical data; delete the empty `tmld_selector.py`
- Order VELPT data for 2018–present (lower priority; deferred for SGA feature vector)
- Update `CodeManifest.md` to reflect the documentation refactor
- Copy updated `pre_shard_data_availability.png` to `~/argosy/images/` after each regeneration
- Concerning NOON / MIDNIGHT determination:
    - Both NOON and MIDNIGHT profiles are distinct from the other seven possible profiles
in that the descent stage (between time `peak` and time `end` in profileIndices) takes
longer in order to allow for sensor equilibration, specifically for the pCO2 and pH 
sensors that operate on descent only. 
- redo backscatter shard: optical_backscatter, not total_volume_scattering_etcetera
- revamp animations
- add curtain plots: See e.g. ~/OceanRepos/notebooks/dev_notebooks/keenan/3d_DO.ipynb
- clear identification of which profiles are midnight, which are noon, which are neither~~ DONE: `profile_duration_histograms.py` and `~/ooi/metadata/`
- fix PAR in the Sensor Table~~ DONE: `par_counts_output`
- 2020 T vs S has some odd behaviors
    - seems like a Wide Aneurism appears in salinity but + / - buttons do not behave as expected
        - some kind of hysteresis where there should not be any
    - suggest making mean/std box width a slider
- Add nitrate, pco2, and par to the sharding pipeline in DataSharding.ipynb (code ready; awaiting data order)
- Re-run sharding for those instruments (awaiting data)
- Run pp01/02 for not-yet-done instruments (awaiting sharding)
- Add pCO2, nitrate, PAR to bundle plot SENSORS dict once those sensors are sharded
- Check the `argo-env2` installed libraries against the libraries listed at the top of this file
- LegacyCode/ directory: Review for archival or deletion (entirely superseded by current code)
- TMLD/ directory: Decide whether to keep tmld_estimates.csv as historical data; delete the empty tmld_selector.py
- `20xx_do` folder: 33 DOFSTA files (2014-2025) from a separate fast-response DO instrument (DOFSTA102), NOT redundant with CTD-derived DO. 
    - Decide: distribute into year folders and integrate into sharding pipeline as a second DO source, or leave as-is?


## Next
- Run and verify shard
