# Argosy Project Conventions

## Project structure

- Repository: `~/argosy` — code, markdown, Jupyter Book. No data files here.
- Data: `~/ooi` — all NetCDF source files, redux shards, postproc, analysis outputs, visualizations.
- The two are mirrored independently: `argosy` to GitHub, `ooi` to S3 (`epipelargosy` bucket).

## Documentation

- Primary docs are split across focused markdown files (each < 400 lines).
- Entry point: `ArgosyOverview.md`. Lists all companion files.
- Development log, to-do list, and prompt staging: `DevelopmentLog.md` (last in sequence).
- The `## Next` section at the end of `DevelopmentLog.md` is where complex prompts are staged.
- PDF build: `pandoc` with `_header.tex`, command documented in `ArgosyOverview.md`.

## Coding conventions

- Python environment: `argo-env2` (miniconda). Activate with `source ~/miniconda3/etc/profile.d/conda.sh && conda activate argo-env2`.
- Timezone handling: Use `zoneinfo.ZoneInfo('America/Los_Angeles')`. Do not use `pytz`.
- Matplotlib in standalone scripts: Use `matplotlib.use('Agg')` for headless execution.
- Matplotlib in Jupyter cells: Do not set backend; use `%matplotlib inline` if needed.
- Temporary scripts: Name with `_` prefix (e.g. `_check_something.py`). Delete after use.
- Notebook edits: After editing `.ipynb` files, validate JSON with `python -c "import json; json.load(open('path'))"`.

## Sensor table

- Authoritative source: `~/argosy/sensortable.csv`
- Folder naming in `~/ooi/ooinet/rca/SlopeBase/scalar/` uses the `key` column: `<year>_<key>` (e.g. `2018_ctd`, `2022_nitr`, `2015_par`).
- Vector channel files: `vcurrent.csv`, `vspectralirr.csv`, `vopticalabsorb.csv`, `vbeamatten.csv`.
- When the sensor table changes, update both `sensortable.csv` and `SensorReference.md`.

## Data pipeline

- Download: `chapters/DataDownload.ipynb`. URLs in `~/argosy/download_link_list.txt` (lines starting with `#` are ignored).
- Sharding: `chapters/DataSharding.ipynb`. Reads from `~/ooi/ooinet/...`, writes to `~/ooi/redux/redux<yyyy>/`.
- Post-processing: `~/argosy/postprocess_special_profiles.py`. Reads redux, writes to `~/ooi/postproc/pp01/` or `pp02/`.
- Profile metadata: `~/ooi/profileIndices/` (read-only clone from GitHub). Derived metadata goes to `~/ooi/metadata/`.
- Visualizations saved to disk go to `~/ooi/visualizations/`. Copies for the repo go to `~/argosy/images/`.

## Shard filename convention

`RCA_sb_sp_<sensor>_<yyyy>_<ddd>_<global_index>_<daily_index>_<version>.nc`

- `<sensor>`: from `shard` column of sensor table (e.g. `temperature`, `dissolvedoxygen`, `nitrate`)
- `<global_index>`: from `profileIndices` (starts at 1 in July 2015, exceeds 20000 by 2026)
- `<daily_index>`: 1–9 (which profile of the day)
- `<version>`: `V1` for redux, `V2` for postproc subsets

## Key rules

- Never write data or generated files to `~/argosy`. Output goes to `~/ooi`.
- Exception: `~/argosy/images/` holds copies of key charts for the PDF/repo.
- Do not run long-running code without asking. Describe what will happen and get confirmation.
- When editing notebook cells, preserve existing outputs unless asked to clear them.
- CTD is the single source for temperature, salinity, density, AND dissolved oxygen.
- pCO2 and pH operate on descent only (noon/midnight profiles). All other scalars operate on ascent (all 9 profiles).
