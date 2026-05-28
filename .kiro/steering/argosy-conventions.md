# Argosy Project Conventions

## Project structure

- Repository: `~/argosy` — code, markdown, Jupyter Book. No data files here.
- Data: `~/ooi` — all NetCDF source files, redux shards, postproc, analysis outputs, visualizations.
- The two are mirrored independently: `argosy` to GitHub, `ooi` to S3 (`s3ooi` bucket).

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
- Sensor exclusions: `~/argosy/sensor_exclusions.csv`. Manual QC embargo list (sensor, start, end, reason). Consumed by the curtain plot and the postprocess script. Add entries when fouling or anomalies are observed.
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
- Sensor profile operation modes (post-2016):
  - **All 9 profiles, ascent**: temperature, salinity, density, DO, chlorA, CDOM, backscatter, PAR (~full depth, dense data)
  - **Daily index 4 and 9 only, ascent**: nitrate (~150 points/profile, full depth)
  - **Daily index 4 and 9 only, descent**: pCO2 (~10 points/profile), pH (~10 points/profile)
  - Daily index 4 = midnight profile; daily index 9 = post-noon profile (~13:40 local)
  - In 2015–2016 all three restricted sensors operated on more/all profiles; the 4-and-9 restriction began in 2017.
  - pH has shard files for all 9 daily indices but only indices 4 and 9 contain usable data (others have too few valid points).
- When appropriate: Finish a response with what the user should do next. This avoids forcing them to scan back up for action items.
- When starting a new chat (usually due to context window full) be sure to read `ArgosyOverview.md` and any other markdown in the ~/argosy folder (repo root) to get up to speed on the project.
- Before running any long-running process that writes significant data (pp05, sharding, etc.), check Windows C: drive free space with `Get-PSDrive C`. If free space is 2GB or less, STOP and notify the user that the Windows drive is critically low — WSL will fail if the vhdx cannot grow.
