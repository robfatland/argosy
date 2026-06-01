# Code Manifest


Inventory of code and data files in the `~/argosy` repository.


## Root directory (`~/argosy`)


### Python scripts

| File | Description |
|------|-------------|
| `postprocess_pp05.py` | Generates pp05 manifest (QC-filtered analysis dataset). Manifest-based: writes `~/ooi/metadata/pp05_manifest.csv`. Resumable per-year. |
| `postprocess_special_profiles.py` | Generates pp01 (noon) and pp02 (midnight) subsets. HSD via noon/midnight metadata; LSD via daily_index 4/9 with min-points filter. |
| `profile_duration_histograms.py` | Computes profile duration histograms from profileIndices. Classifies noon/midnight profiles. Writes to `~/ooi/metadata/` and `~/ooi/visualizations/`. |
| `redux_s3_synch.py` | Syncs redux shard files to S3 (`epipelargosy` bucket). Logs progress; stops after 20 errors. |
| `tidal_extract.py` | Extracts tidal harmonic constituents from TPXO10 at 3 profiler sites, saves to `tidal_constituents.json`. |
| `tidal_plot_may2026.py` | Plots predicted tidal height for 3 sites over May 2026. |


### Data files

| File | Description |
|------|-------------|
| `sensortable.csv` | Sensor table: sensor name, instrument, key, data variable, shard name, side, extreme low/high. |
| `sensor_exclusions.csv` | Manual QC embargo list: sensor, start date, end date, reason. Consumed by curtain plot and postprocess scripts. |
| `tidal_constituents.json` | Extracted tidal harmonic constituents (amplitude, phase, frequency) for 3 sites, 14 constituents. |
| `vcurrent.csv` | Vector sensor channels for velocity (3: east, north, up). |
| `vspectralirr.csv` | Vector sensor channels for spectral irradiance (7 wavelengths). |
| `vopticalabsorb.csv` | Vector sensor channels for optical absorption (73 channels). |
| `vbeamatten.csv` | Vector sensor channels for beam attenuation (73 channels). |


## Chapters directory (`~/argosy/chapters`)

| File | Description |
|------|-------------|
| `DataDownload.ipynb` | Downloads NetCDF source files from OOINET staging URLs. |
| `DataSharding.ipynb` | Shards source files into single-sensor single-profile NetCDF files in `~/ooi/redux/redux<yyyy>`. |
| `Visualizations.ipynb` | Bundle plots, curtain plots, and bundle animations. Source selector (redux/pp01/pp02/pp05). |
| `MidnightNoon.ipynb` | Midnight/noon profile exploration. |
| `SpectralGraphAnalysis.ipynb` | Spectral graph analysis of profile data. |
| `StubWork.ipynb` | Stub/scratch notebook. |


## LegacyCode directory (`~/argosy/LegacyCode`)

| File | Description |
|------|-------------|
| `legacy_spectrophotometer.py` | Earlier OPTAA spectrophotometer processing. Retained as only reference for vector sensor (OA/BA) data handling. |


## TMLD directory (`~/argosy/TMLD`)

| File | Description |
|------|-------------|
| `tmld_selector.py` | Interactive tool for manually selecting Temperature Mixed Layer Depth. |
| `tmld_estimates.csv` | Human-generated TMLD estimates from the interactive selector. |


## Documentation files (`~/argosy`)

| File | Description |
|------|-------------|
| `ArgosyOverview.md` | Entry point. Pointers to Key Actions, documentation index, AI guidelines, PDF build. |
| `OOIObservatory.md` | OOI background, glossary, sites, challenges. |
| `SensorTable.md` | Sensor table, HSD/LSD categories, sampling details, vector sensor specs. |
| `Sharding.md` | Shard filename conventions, profile metadata, sensor operation modes. |
| `Visualization.md` | Bundle plots, curtain plots, animations, midnight/noon annotation. |
| `PostProcessing.md` | pp01/pp02 generation, sensor exclusions workflow, QC flags, S3 backup procedure. |
| `PP05_QCAnalysis.md` | pp05 methodology: three-tier exclusion, suspect ranges, manifest design. |
| `VectorData.md` | Vector sensor integration (velocity, spectral irradiance, spectrophotometer). |
| `Analysis.md` | Data exploration ideas. |
| `CoincidencePlans.md` | Anomaly detection: auto-coincidence and hetero-coincidence plans. |
| `Umbrella.md` | Expansion beyond shallow profiler: other data resources. |
| `OOINETSlopeBaseDataStatus.md` | OOINET data availability status for Slope Base. |
| `DevelopmentLog.md` | Development narrative, open topics, pending items, Next prompt section. |
| `CodeManifest.md` | This file. |


## Supporting files

| File | Description |
|------|-------------|
| `_config.yml` | Jupyter Book configuration. |
| `_toc.yml` | Jupyter Book table of contents. |
| `_header.tex` | LaTeX header for pandoc PDF generation. |
| `download_link_list.txt` | OOINET download URLs for data retrieval. |
| `downlinklist_completed.txt` | Record of completed downloads. |
| `.gitignore` | Git ignore rules. |
