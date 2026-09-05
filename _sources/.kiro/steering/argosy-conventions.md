# Argosy Project Conventions

## Prompt shorthands

- `sa` appended to a prompt: Short answer only, at most five lines of text.

## Project structure

- Repository: `~/argosy` — code, markdown, Jupyter Book. No data files here.
- Data: `~/ooi` — all NetCDF source files, redux shards, postproc, analysis outputs, visualizations.
  Per-site layout: `~/ooi/<site>/{ooinet, redux/<yyyy>, postproc/<pp>/<yyyy>, profileIndices, metadata, analysis, visualizations}`
  where `<site>` is a 2-letter code (`sb`=Slope Base, `oo`=Oregon Offshore, `ab`=Axial Base).
  All path knowledge is centralized in `~/argosy/ooipaths.py` — code MUST obtain paths from it
  (e.g. `op.redux_dir(year, site)`, `op.postproc_dir(pp, year, site)`) rather than hardcoding.
- The two are mirrored independently: `argosy` to GitHub, `ooi` to S3 (`s3ooi` bucket).
  S3 mirrors the per-site layout: `s3://s3ooi/<site>/redux/<yyyy>/`, `s3://s3ooi/<site>/postproc/<pp>/<yyyy>/`.
  Exception: `s3://s3ooi/ooinet/rca/...` (204 GB raw archive) retains legacy keys, not re-keyed.

## Documentation

- Primary docs are split across focused markdown files (each < 400 lines).
- Entry point: `ArgosyOverview.md`. Lists all companion files.
- Development log, to-do list, and prompt staging: `DevelopmentLog.md` (last in sequence).
- The `## Next` section at the end of `DevelopmentLog.md` is where complex prompts are staged.
- PDF build: `pandoc` with `_header.tex`, command documented in `ArgosyOverview.md`.
- Slide deck: `slides.md` (Marp format). Render with `marp slides.md -o slides.html`. Marp CLI is installed.

## Coding conventions

- Python environment: `argosy` (miniconda). Activate with `source ~/miniconda3/etc/profile.d/conda.sh && conda activate argosy`.
- Timezone handling: Use `zoneinfo.ZoneInfo('America/Los_Angeles')`. Do not use `pytz`.
- Matplotlib in standalone scripts: Use `matplotlib.use('Agg')` for headless execution. Always set this
  before importing `matplotlib.pyplot`. This avoids Qt/xcb errors in WSL2 where no display server is available.
- Matplotlib in Jupyter cells: Do not set backend; use `%matplotlib inline` if needed.
- Temporary scripts: Name with `_` prefix (e.g. `_check_something.py`). Delete after use.
- Notebook edits: After editing `.ipynb` files, validate JSON with `python -c "import json; json.load(open('path'))"`.
- `input()` fallback: Cloud JupyterHubs commonly disable stdin. Any `%run` module that uses
  `input()` should wrap it in try/except and fall back to defaults silently. Use this pattern:
  ```python
  def get_input_with_default(prompt, default):
      try:
          response = input(f"{prompt} ").strip()
          return response if response else str(default)
      except (EOFError, OSError, Exception):
          return str(default)
  ```
## Sensor table

- Authoritative source: `~/argosy/sensortable.csv`
- Folder naming in `~/ooi/<site>/ooinet/scalar/` uses the `key` column: `<year>_<key>` (e.g. `2018_ctd`, `2022_nitr`, `2015_par`). For Slope Base: `~/ooi/sb/ooinet/scalar/`.
- Vector channel files: `vcurrent.csv`, `vspectralirr.csv`, `vopticalabsorb.csv`, `vbeamatten.csv`.
- When the sensor table changes, update both `sensortable.csv` and `SensorTable.md`.

## Data pipeline

- Download: `chapters/DataDownload.ipynb`. URLs in `~/argosy/download_link_list.txt` (lines starting with `#` are ignored).
- Sharding: `chapters/DataSharding.ipynb`. Reads from `~/ooi/<site>/ooinet/...`, writes to `~/ooi/<site>/redux/<yyyy>/`.
- Post-processing: `~/argosy/postprocess_special_profiles.py`. Reads redux, writes to `~/ooi/<site>/postproc/pp01/<yyyy>/` or `pp02/`.
- Sensor exclusions: `~/argosy/sensor_exclusions.csv`. Manual QC embargo list (sensor, start, end, reason). Consumed by the curtain plot and the postprocess script. Add entries when fouling or anomalies are observed.
- Profile metadata: `~/ooi/<site>/profileIndices/` (from GitHub clone; designator-keyed CSVs placed per site — an explicit ingest step). Derived metadata goes to `~/ooi/<site>/metadata/`.
- Visualizations saved to disk go to `~/ooi/<site>/visualizations/`. Copies for the repo go to `~/argosy/images/`.

## Shard filename convention

`RCA_<site>_sp_<sensor>_<yyyy>_<ddd>_<global_index>_<daily_index>_<version>.nc`
(e.g. `RCA_sb_sp_temperature_2022_043_13614_1_V1.nc`)

- `<site>`: 2-letter site token, matches the site directory (`sb`/`oo`/`ab`). Filenames were
  NOT changed by the per-site restructure — the site appears in both the path and this token.
- `<sensor>`: from `shard` column of sensor table (e.g. `temperature`, `dissolvedoxygen`, `nitrate`)
- `<global_index>`: from `profileIndices` (starts at 1 in July 2015, exceeds 20000 by 2026)
- `<daily_index>`: 1–9 (which profile of the day)
- `<version>`: `V1` for redux, `V2` for postproc subsets

## Session continuity

These conventions ensure smooth handoff between kiro sessions (context window full, chat restart, etc.).

### Status snapshot: `SessionState.md`

- Location: `~/argosy/SessionState.md`
- Purpose: Machine-readable summary of what the *last* session accomplished, what's in progress, and what's blocked.
- **When to write/update:** At the end of every session (when the user says goodbye, when context is getting long, or after completing a significant milestone). Also update when reverting work or leaving something incomplete.
- **When to read:** At the start of every new session, read `SessionState.md` *before* reading `DevelopmentLog.md`. This is the fastest path to orientation.
- Format (maintain these headings exactly):

```markdown
# Session State

## Last updated
<date and brief session description>

## Completed this session
- <bullet list of what was accomplished>

## In progress / partially done
- <what was started but not finished, with enough detail to resume>

## Reverted / needs redo
- <what was attempted, why it failed, where the rebuild notes live>

## Blocked / waiting on user
- <anything that requires user decision or external action>

## Next action
- <the single most important next step>
```

### Rebuild notes for reverted work

- When work is reverted (notebook cell, script, etc.), write a rebuild plan to `~/argosy/<Feature>Rebuild.md`.
- Name the file after the feature (e.g. `VisNotebookRebuild.md`, `ShardingRebuild.md`).
- Include: what was attempted, why it failed, what changes to re-apply, and any constraints discovered.
- Reference the rebuild file from `SessionState.md` → "Reverted / needs redo" section.
- Once the rebuild is successfully applied, delete the rebuild file and remove the reference.

### Documentation hygiene at session end

- Update `DevelopmentLog.md` → "Completed" section with anything newly done.
- Remove completed items from "Pending To Do".
- Update "## Next" to reflect the actual next priority.
- If a new operational procedure was added to any doc, add the pointer in `ArgosyOverview.md` → "Pointers to Key Actions".

### Self-documenting subfolders (README on creation)

When creating a subfolder to hold an existing set of files, create a `README.md` in that
subfolder that begins:

> This folder `<path>` contains files for `<short purpose statement>`.

Append a bullet list of the source files (scripts that produce or consume the folder's
contents, e.g. `VisQCInspector.py`) with one-line summaries of what each does. The goal is
to make data folders (especially `metadata/` and its subfolders) somewhat self-documenting.

## Key rules

- Never write data or generated files to `~/argosy`. Output goes to `~/ooi`.
- Exception: `~/argosy/images/` holds copies of key charts for the PDF/repo.
- Do not run long-running code without asking. Describe what will happen and get confirmation.
- When editing notebook cells, preserve existing outputs unless asked to clear them.
- **Environment stability**: The `argosy` conda environment should be pinned. After any
  `pip install --upgrade` or `conda update`, run `conda env export > ~/argosy/environment.yml`
  to snapshot the working state. Before running a notebook after a long hiatus, compare
  current versions against `environment.yml` and flag discrepancies. Key packages to watch:
  scipy, scikit-learn, networkx, xarray, threadpoolctl, pandas.
- **Notebook pre-flight check**: After any gap of >2 weeks since last notebook run, read
  the module descriptions (in the SGA markdown or cell comments) and verify that file paths,
  column names, and library APIs still match. Run a quick dry/sanity check on Module 1
  before committing to a full pipeline run.
- CTD is the single source for temperature, salinity, density, AND dissolved oxygen.
- Sensor profile operation modes (post-2016):
  - **All 9 profiles, ascent**: temperature, salinity, density, DO, chlorA, CDOM, backscatter, PAR (~full depth, dense data)
  - **Daily index 4 and 9 only, ascent**: nitrate (~150 points/profile, full depth)
  - **Daily index 4 and 9 only, descent**: pCO2 (~10 points/profile), pH (~10 points/profile)
  - Daily index 4 = midnight profile; daily index 9 = post-noon profile (~13:40 local)
  - In 2015–2016 all three restricted sensors operated on more/all profiles; the 4-and-9 restriction began in 2017.
  - pH has shard files for all 9 daily indices but only indices 4 and 9 contain usable data (others have too few valid points).
- When appropriate: Finish a response with what the user should do next. This avoids forcing them to scan back up for action items.
- When starting a new chat (usually due to context window full) read `SessionState.md` first for immediate orientation, then `ArgosyOverview.md` and `DevelopmentLog.md` as needed.
- Operational procedures are indexed in `ArgosyOverview.md` → "Pointers to Key Actions". When adding a new procedure to any doc, also add a one-line pointer there.
- **Cross-document references**: When an item in one document is addressed or elaborated in another, add a pointer (e.g. "See `Testing.md` for details"). This applies to Open Topics referencing Testing.md, DevelopmentLog referencing Analysis.md, etc. Keeps navigation efficient across the doc set.
- Before running any long-running process that writes significant data (pp05, sharding, etc.), check Windows C: drive free space with `Get-PSDrive C`. If free space is 2GB or less, STOP and notify the user that the Windows drive is critically low — WSL will fail if the vhdx cannot grow.
