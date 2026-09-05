# Code Manifest

Inventory of code and data files in the `~/argosy` repository.

Last refreshed: 2026-06-26


## Root directory (`~/argosy`)


### Python scripts

| File | Description |
|------|-------------|
| `ooipaths.py` | Single source of truth for the `~/ooi` data filesystem layout (per-site, Aug 2026). Site registry (`sb`/`oo`/`ab` → OOI designators) and path accessors (`redux_dir`, `postproc_dir`, `metadata_dir`, `profile_index_dir`, `analysis_dir`, `ooinet_dir`, `shard_glob`, etc.), all taking a `site` arg. Layout: `~/ooi/<site>/{ooinet, redux/<yyyy>, postproc/<pp>/<yyyy>, ...}`. |
| `postprocess_pp05.py` | Generates pp05 manifest (QC-filtered analysis dataset). Manifest-based: writes `~/ooi/<site>/metadata/pp05_manifest.csv`. Resumable per-year. |
| `postprocess_pp06.py` | Builds pp06 physical dataset from pp05-qualified shards. Filter 0 (baseline copy) + Filter 1 (MRA walk on salinity/density). Includes 8 HSD + 3 LSD sensors. Output: `~/ooi/<site>/postproc/pp06/`. |
| `postprocess_pp06_filter2.py` | Savitzky-Golay smoothing (Filter 2) for CDOM, ChlorA, Backscatter quantization noise. Operates in-place on pp06 shards. |
| `postprocess_pp06_filter3.py` | Rolling-minimum baseline despiking (Filter 3) for backscatter (Briggs et al. 2011). Operates in-place on pp06 shards. |
| `postprocess_special_profiles.py` | Generates pp01 (noon) and pp02 (midnight) subsets. HSD via noon/midnight metadata; LSD via daily_index 4/9 with min-points filter. |
| `profile_duration_histograms.py` | Computes profile duration histograms from profileIndices. Classifies noon/midnight profiles. Writes to `~/ooi/<site>/metadata/` and `~/ooi/<site>/visualizations/`. |
| `TimeSeriesProfileCorrelation.py` | Cross-correlation between adjacent profiles on a regular depth grid. Produces vertical offset time series (tidal/current displacement). |


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


## SGA directory (`~/argosy/sga`)

| File | Description |
|------|-------------|
| `sga_config.py` | Configuration parameters for SGA pipeline (sensors, depth grid 27–185m, σ², k-NN). |
| `sga_module1.py` | Module 1: Data loading from redux shards. |
| `sga_module2.py` | Module 2: Feature matrix construction (depth-binned sensor profiles). |
| `sga_module3.py` | Module 3: Z-score normalization of feature matrix. |
| `sga_module4.py` | Module 4: Distance, similarity, and adjacency (k-NN) matrices. |
| `sga_module5.py` | Module 5: Eigenvalue/eigenvector analysis of graph Laplacian. |
| `sga_module6.py` | Module 6: Spectral clustering. |
| `sga_module7.py` | Module 7: Follow-on analysis and visualization. |
| `sga_depth_analysis.py` | Depth range analysis for SGA grid selection. |
| `sga_sensor_presence.py` | Sensor presence/availability analysis across profiles. |


## IW directory (`~/argosy/iw`)

| File | Description |
|------|-------------|
| `internal_wave_physics.py` | Shared physics module. Stream function formulation guaranteeing divergence-free displacement fields. |
| `internal_wave.py` | Generates internal wave animation (particles, pycnocline boundary, orbit ellipses). Output: `~/ooi/<site>/visualizations/internal_wave.mp4`. |
| `TestInternalWaveIncompressibility.py` | Validates incompressibility: tracks area of 3 rectangular cells over one period. Pass: <3% variation. |


## Vis directory (`~/argosy/vis`)

| File | Description |
|------|-------------|
| `bundle_chart.py` | Standalone interactive bundle chart. Global-index navigation, dynamic data source (redux/pp01–pp06), persistent range memory, display names, nav buttons. |
| `curtain_plot.py` | Interactive curtain plot for HSD sensors. Source selector, sensor exclusions, contour overlays. Outputs PNG + contour CSV to `~/ooi/<site>/`. |
| `bundle_animation.py` | Bundle animation: sliding-window temperature profile time-lapse. Mean±std or overlay mode. Output: `~/ooi/<site>/visualizations/bundle_animation.mp4`. |


## Chapters directory (`~/argosy/chapters`)

| File | Description |
|------|-------------|
| `DataDownload.ipynb` | Downloads NetCDF source files from OOINET staging URLs. |
| `DataSharding.ipynb` | Shards source files into single-sensor single-profile NetCDF files in `~/ooi/<site>/redux/<yyyy>`. |
| `Visualizations.ipynb` | Bundle plots, curtain plots, and bundle animations. Source selector (redux/pp01/pp02/pp05). |
| `MidnightNoon.ipynb` | Midnight/noon profile exploration. |
| `SpectralGraphAnalysis.ipynb` | Spectral graph analysis of profile data (runs the sga/ modules). |
| `TidalSignal.ipynb` | Tidal signal analysis: profile start-depth variation over time, correlation with tidal prediction. |
| `StubWork.ipynb` | Stub/scratch notebook. |


## TMLD directory (`~/argosy/TMLD`)

| File | Description |
|------|-------------|
| `tmld_selector.py` | Interactive tool for manually selecting Temperature Mixed Layer Depth. |
| `tmld_estimates.csv` | Human-generated TMLD estimates from the interactive selector. |


## LegacyCode directory (`~/argosy/LegacyCode`)

| File | Description |
|------|-------------|
| `legacy_spectrophotometer.py` | Earlier OPTAA spectrophotometer processing. Retained as only reference for vector sensor (OA/BA) data handling. |


## Documentation files (`~/argosy`)

See also `ArgosyOverview.md` → "Documentation Files" for a narrative-style index
of these same files.

| File | Description |
|------|-------------|
| `ArgosyOverview.md` | Entry point. Pointers to Key Actions, documentation index, AI guidelines, PDF build. |
| `OOIObservatory.md` | OOI background, glossary, sites, challenges. |
| `SensorTable.md` | Sensor table, HSD/LSD categories, sampling details, vector sensor specs. |
| `DeveloperGuide.md` | Technical map for collaborators/reusers: filesystem layout, workflow tasks 0–6, OOINET ordering + download, raw filename anatomy, shard convention. Absorbs the former `Workflow.md`. |
| `Sharding.md` | Shard filename conventions, profile metadata, sensor operation modes. |
| `Visualization.md` | Bundle plots, curtain plots, animations, midnight/noon annotation. |
| `PostProcessing.md` | redux → ppNN pipeline: pp01/pp02 generation, pp05/pp06 filters, sensor exclusions workflow, QC flags. |
| `DataOps.md` | Data operations: S3 backup/sync/restore, localhost WSL vhdx disk management. |
| `PP05_QCAnalysis.md` | pp05 methodology: three-tier exclusion, suspect ranges, manifest design. |
| `SpectralGraphAnalysis.md` | Module-by-module guide for the SGA notebook (rehearsal script, diagnostics, known issues). |
| `TidalAnalysis.md` | Tidal prediction (TPXO10), start-depth correlation, blowdown events, further work. |
| `CoincidencePlans.md` | Anomaly detection: auto-coincidence and hetero-coincidence plans. |
| `InternalWaves.md` | Internal wave analysis: terminology, file inventory, stream function physics, plan. |
| `VectorData.md` | Vector sensor integration (velocity, spectral irradiance, spectrophotometer). |
| `Analysis.md` | Derived oceanographic parameters, data exploration ideas, SGA methodology. |
| `Umbrella.md` | Expansion beyond shallow profiler: other data resources. |
| `ColumbiaPlumePlan.md` | Columbia River plume detection plan; satellite (PO.DAAC) cross-comparison. |
| `RCAWritLarge.md` | Broader Regional Cabled Array context. |
| `OOIFAQandGeneralInfoSummary.md` | OOI FAQ / general information summary. |
| `OOINETSlopeBaseDataStatus.md` | OOINET data availability status for Slope Base. |
| `Testing.md` | Test definitions: SGA synthetic validation, internal wave incompressibility check. |
| `VisQC.md` | Visual QC workflow design (cline review; Inspector + planned Corrector). |
| `Publishing.md` | Open-science / DOI archiving plan (Zenodo, Figshare, OSF; postproc subset). |
| `SessionState.md` | Machine-readable session state for AI continuity (last updated, in-progress, blocked). |
| `pp06ErraticFilterPrompt.md` | Design notes/prompt for pp06 erratic filter system. |
| `DevelopmentLog.md` | Development narrative, open topics, pending items, Next prompt section. |
| `CodeManifest.md` | This file. |
| `SETUP.md` | Collaboration setup: environment installation, S3 data access, getting started. |


## Supporting files

| File | Description |
|------|-------------|
| `_config.yml` | Jupyter Book configuration. |
| `_toc.yml` | Jupyter Book table of contents. |
| `_header.tex` | LaTeX header for pandoc PDF generation. |
| `intro.md` | Jupyter Book landing page. |
| `markdown-notebooks.md` | Jupyter Book MyST markdown notebook example. |
| `slides.md` | Marp slide deck. Render with `marp slides.md -o slides.html`. |
| `environment.yml` | Conda environment snapshot (`argosy` env). |
| `download_link_list.txt` | OOINET download URLs for data retrieval. |
| `downlinklist_completed.txt` | Record of completed downloads. |
| `.gitignore` | Git ignore rules. |
