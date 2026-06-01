# Visualizations.ipynb Rebuild Plan

The notebook was reverted to its git state after a failed edit. The following
changes need to be re-applied in a fresh session.


## Bundle plot cell changes

1. **Data source selector** — prompt user for redux/pp01/pp02/pp05. When pp05
   selected, load the manifest CSV and set DATA_BASE to redux (files are read
   from redux, filtered by manifest).

2. **Sensor slider fix** — the update callbacks for sensor low/high sliders must
   use "widen first, set values, then tighten" pattern to handle density
   (1024–1028) and other sensors with ranges far from zero.

3. **SENSORS dict updates:**
   - `cdom`: high → 20.0 (was 2.5)
   - `chlora`: high → 20.0 (was 1.5)
   - `backscatter`: high → 0.01 (was 0.002)

4. **Exclusion filter toggle** — add an "Exclusions: OFF" button. When ON, skip
   profiles within `sensor_exclusions.csv` windows. Default OFF.

5. **Time-aligned indexing (NEW, not yet implemented):**
   - Sensor 1 drives navigation (slider = position in sensor 1 file list)
   - Sensor 2 finds co-temporal files by matching day-of-year within ±1 day
   - For each sensor 1 file at position N, extract year+doy from filename
   - Find sensor 2 files with same year+doy (or nearest day)
   - If no match found, show nothing for sensor 2 at that position
   - This ensures pCO2/nitrate data appears when co-temporal with temperature

6. **Nitrate diagnostic** — when nitrate is selected, print the filename at
   the current index position (for debugging). Can be removed once time-alignment
   is confirmed working.


## Curtain plot cell changes

1. **Complete rewrite** — the cell was rewritten from scratch. Key features:
   - User input: start date, end date (manual text input with defaults)
   - User input: "All" or "Select" sensors (numbered list for selection)
   - All 8 HSD sensors available
   - Source selector (redux/pp01/pp02/pp05 with manifest support)
   - Sensor exclusions loaded from `sensor_exclusions.csv`
   - Per-sensor contour configuration: `n_contours`, `contour_pcts`, `contour_colors`
   - Temperature: 4 contours at [20,40,60,80] pcts, colors ["white","white","black","black"]
   - All contours rendered as smoothed line segments (no markers)
   - Temperature contour linewidth: 0.9
   - Saves PNG to `~/ooi/visualizations/CurtainPlots_{Location}_{start}_{end}.png`
   - Saves CSV to `~/ooi/metadata/curtain_contour_values_{Location}_{start}_{end}.csv`
   - Only two print statements: the PNG path and CSV path
   - No other diagnostic output

2. **Colormaps:**
   - Temperature: inferno
   - Salinity: viridis
   - DO: cividis
   - Density: plasma
   - CDOM: YlOrBr
   - ChlorA: GnBu
   - Backscatter: Greys
   - PAR: YlOrRd


## Animation cell changes

1. **Data source selector** — same pattern as bundle/curtain cells.


## General notes

- All cells should have outputs cleared after editing (set outputs=[], execution_count=None)
- Validate JSON after every edit: `python -c "import json; json.load(open('path'))"`
- Validate Python syntax: parse each cell with `ast.parse()` (strip `%matplotlib inline`)
- The pp05 manifest path: `~/ooi/metadata/pp05_manifest.csv`
- When pp05 is selected as source, the code reads the manifest and uses the
  filepath column to load files directly from redux. Exclusion checking is
  skipped (manifest already filtered). Time-range filtering still applies.
