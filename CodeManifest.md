# Code Manifest


Inventory of code files in the `~/argosy` repository.


## Root directory (`~/argosy`)


| File | Type | Description |
|------|------|-------------|
| `bundlechart05.py` | Module | Interactive bundle plot visualization with dual-sensor display, slider navigation, noon/midnight annotation, and mean±std mode. Runs in a Jupyter cell. |
| `profile_duration_histograms.py` | Module | Computes ascent/descent/total duration histograms from profileIndices. Classifies noon and midnight profiles. Writes results to `~/ooi/metadata` and `~/ooi/visualizations`. |
| `postprocess_special_profiles.py` | Module | Generates pp01 (noon) and pp02 (midnight) post-processed subsets from redux. Copies qualifying shards with V1→V2 rename, applies depth filter, generates depth histograms. |
| `assess_synch.py` | Module | Compares file counts between local redux folders and S3 mirror by sensor and year. Flags mismatches. |
| `redux_s3_synch.py` | Module | Syncs redux NetCDF shard files from localhost to the `epipelargosy` S3 bucket using AWS CLI. Logs progress; stops after 20 cumulative errors. |
| `sensortable.csv` | Data | Sensor table CSV: sensor name, instrument, key, data variable, shard name, acquisition side, extreme low/high. |
| `vcurrent.csv` | Data | Vector sensor channel enumeration for velocity (3 channels: east, north, up). |
| `vspectralirr.csv` | Data | Vector sensor channel enumeration for spectral irradiance (7 wavelength channels). |
| `vopticalabsorb.csv` | Data | Vector sensor channel enumeration for optical absorption (73 channels). |
| `vbeamatten.csv` | Data | Vector sensor channel enumeration for beam attenuation (73 channels). |


## Chapters directory (`~/argosy/chapters`)


| File | Type | Description |
|------|------|-------------|
| `DataDownload.ipynb` | Notebook | Downloads NetCDF source files from OOINET staging URLs. Handles restart tolerance, degenerate file detection, and redundant file cleanup. |
| `DataSharding.ipynb` | Notebook | Shards multi-sensor continuous-time source files into single-sensor single-profile NetCDF files in `~/ooi/redux/redux<YYYY>`. Also contains exploratory cells for pH, DO, and profile status tracking. |
| `Visualizations.ipynb` | Notebook | Interactive bundle plots (dual sensor, slider navigation), curtain plots, and related visualizations of redux data. |
| `SpectralGraphAnalysis.ipynb` | Notebook | Spectral graph analysis of profile data. |
| `curtain_plot.py` | Module | Generates curtain plots (time × depth × color-encoded sensor value) for salinity and temperature. Runs in a Jupyter cell within `Visualizations.ipynb`. |


## TMLD directory (`~/argosy/TMLD`)


| File | Type | Description |
|------|------|-------------|
| `tmld_selector.py` | Module | Interactive tool for manually selecting Temperature Mixed Layer Depth by clicking on profile charts. |
| `tmld_estimates.csv` | Data | Human-generated TMLD estimates from the interactive selector. |


## LegacyCode directory (`~/argosy/LegacyCode`)


| File | Type | Description |
|------|------|-------------|
| `legacy_charts.py` | Module | Earlier chart generation code (superseded by bundlechart05 and curtain_plot). |
| `legacy_shallowprofiler.py` | Module | Earlier shallow profiler data processing including spectral irradiance reformatting. |
| `legacy_spectrophotometer.py` | Module | Earlier spectrophotometer (OPTAA) data processing. |
| `legacy_data.py` | Module | Earlier general data loading and profile extraction utilities. |
| `legacy_ShallowProfiler.ipynb` | Notebook | Earlier notebook version of shallow profiler workflow. |


## Markdown / documentation files


| File | Description |
|------|-------------|
| `AIPrompt.md` | Project documentation and CA prompt composition. Contains sensor table, workflow, file system description, and development log. |
| `Analysis.md` | Data exploration and analysis method ideas. |
| `Umbrella.md` | Expansion perspective: extending beyond Oregon Slope Base shallow profiler. |
| `PostProcessing.md` | Post-processing documentation: pp01 (noon) and pp02 (midnight) subset generation, filters, results. |
| `Asta.md` | Notes (TBD). |
| `shard_code_updated.md` | Notes on sharding code updates. |
| `intro.md` | Jupyter Book introduction page. |
| `markdown.md` | Jupyter Book markdown example page. |
| `markdown-notebooks.md` | Jupyter Book MyST notebook example page. |
| `README.md` | Repository README. |


## Supporting files


| File | Description |
|------|-------------|
| `_config.yml` | Jupyter Book configuration. |
| `_toc.yml` | Jupyter Book table of contents. |
| `requirements.txt` | Python package dependencies. |
| `references.bib` | Bibliography for Jupyter Book. |
| `logo.png` | Jupyter Book logo image. |
| `download_link_list.txt` | OOINET download URLs for data retrieval. |
| `downlinklist_completed.txt` | Record of completed downloads. |
| `.gitignore` | Git ignore rules. |
