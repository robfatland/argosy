# MLDTimeSeries.py: MLD time-series viewer

This file describes `MLDTimeSeries.py` (repo root, beside `MLD.py`), a viewer for the human-labeled MLD written by the annotation suite (design in `MLDAnnotationPlan.md`). Label sharing with collaborators: `DeveloperGuide.md` -> "Sharing small datasets". Related analysis: `Umbrella.md` -> "ERA5 sea state".


Standalone TkAgg GUI (repo root, beside `MLD.py`; reuses its `build_gpi_file_index`,
`load_profile`, `science_labels_path`). Purpose: look at the human-labeled MLD as a TIME SERIES
(diurnal / seasonal / event structure) and at the sensor value found at the MLD, to compare
against external forcing (see `Umbrella.md` -> "ERA5 sea state").

## Charts
Two charts stacked, one shared time axis:
- **Upper:** MLD depth (m, axis inverted) for temperature (red), salinity (green), DO (blue).
- **Lower:** the sensor value AT the MLD (the label's `value_raw`): T at MLD (left axis, red),
  S at MLD (first twin axis, right, green), DO at MLD (second twin axis, right, offset spine,
  blue). Three y-axes via `twinx`.
- All series: filled circle markers joined by lines. **No connector line** across a gap of more
  than 1 day between successive points of a series (NaN break).
- Y limits auto-fit the visible window each time the time range changes.

## Controls (bottom of window)
- **start coarse** slider: global window start over 2014-01-01 .. 2027-12-31, continuous (not
  quantized by year, so it spans year boundaries gracefully).
- **start fine** slider: a day OFFSET added to the coarse start (0 .. 45 d, constant
  `FINE_MAX_DAYS`). **Window start = coarse + fine.** The window label under the lower chart
  shows the resulting start and end.
- **width (d)** slider: window width in days, 0.25 to 400.
- One compact **checkbox panel** to the right of the sliders, four boxes:
  - **Adaptive y** (default ON). ON: all y axes re-fit to the visible window on every pan/zoom.
    OFF: fixed WIDE limits so any start time is directly comparable. Wide limits are the full
    range of all loaded labels over all times (science, plus training if shown; plus the
    Faux No-MLD shallow values when on) with the same padding, for each of the three lower-chart
    axes (T, S, DO) and the upper depth axis (0 m to deepest MLD).
  - **Training (^)** (default ON when the training file exists): show/hide training labels.
  - **Faux No-MLD** (default OFF) — how a profile labeled *No MLD* for a sensor is shown.
    OFF = `X`: a cross in the sensor's color near the TOP of the lower chart (one row per
    sensor so the three do not overlap). ON: read that profile's pp06 shard, take the SHALLOWEST
    valid sample, and plot it as an OPEN marker in that sensor's lower-chart series (circle for
    science, joined by the line; triangle for training). First use indexes the pp06 shards, so
    it pauses briefly once.
  - **Local time** (default OFF = UTC). Switches the time axis, the window label and the day
    gridlines between UTC and Pacific local time. The vertical gridlines fall at midnight of the
    displayed zone. Toggling keeps the same instant at the window start (the coarse slider is
    reset to it and the fine offset to 0).

## Science vs training data
- **Science** (`mld_labels_<site>_science_<who>.csv`): filled circles joined by lines.
- **Training** (`mld_labels_<site>_block05_<who>.csv`, ~1 profile in 45): filled TRIANGLES,
  markers only (they are too sparse to join). Rows whose (gpi, sensor) already appear in the
  science file are skipped, because the science set was seeded from the training labels and
  they would just overlap.
- Profiles flagged unusable (`xud_recorded`) are never plotted. No-MLD profiles add nothing to
  the upper chart in either mode.

## Invocation
- `--site <sb|oo|ab>` default `sb`.
- `--start`, `--end` default 2024-01-01 / 2024-01-31 (`--end` is inclusive of that day). These
  only set the initial window; the sliders reach anywhere in the label file's time span.
- `--who` default `R` (reads `mld_labels_<site>_science_<who>.csv`).
- `--local` starts in Pacific local time (America/Los_Angeles); default is UTC. The same switch
  is the "Local time" checkbox in the window.
- `--size WxH` initial window size in pixels (e.g. `1500x850`); default auto-fits the screen
  (92% of screen width, 85% of height). Under WSLg a "full screen" click can size to the whole
  Windows desktop rather than one monitor; if so, un-maximize and use `--size`.

## Notes
- Value at MLD is `value_raw`, never the filtered value; the O-mode shallowest value is also
  raw. Density labels are ignored.
- Layout: all axes are placed in figure fractions, so the layout scales with the window.
