# MLD Annotation Plan

Design spec for a two-program workflow that builds a **human-labeled MLD (mixed-layer
depth) training dataset** from the pp06 shallow-profiler data. The labels are the ground
truth for a later ML model that will estimate MLD across the entire shard dataset (see
`Analysis.md` and the "annotation problem" note in `argosy-conventions.md`).

Status: **implemented (Sep 2026).** Two programs, both in the repo root:
1. `PreSelectProfiles.py` — selects candidate profiles (reproducible sampling).
2. `MLD.py` — interactive standalone GUI to hand-label MLD on those candidates.

Modeled on the existing standalone annotator `iw/VisQCInspector.py` (TkAgg, per-decision
rows written to a CSV under `metadata/annotations/`). All paths via `ooipaths` (`op`).


## 1. PreSelectProfiles.py — candidate selection

### Purpose
Produce an even, reproducible sample of profiles across the full pp06 time span for each
site, so the training set spans seasons / conditions / mission epochs rather than clustering
where casts are dense.

### Method
- Runs for **all three sites** (sb, oo, ab), reading pp06 shards.
- **Blocks:** fixed-width time windows, width = **parameter in days (default 5)**. For each
  site, block 0 starts on the **date of that site's first GPI** (no shared calendar anchor);
  blocks tile forward to the last available profile. A 5-day block spans at most 45 profiles
  (5 days × 9 daily profiles).
- **Per block:**
  1. Count profiles present in the block by global profile index (a profile "exists" if its
     **T shard file exists** — presence = file exists, not valid-data check). Call this `N`.
  2. Build the eligible pool: profiles with **all four** of T/S/ρ/DO shard files present
     (`all4`). If that pool is empty, fall back to the **T-only** pool (`T_only`).
  3. If the chosen pool is non-empty, select **one profile at random** (seeded RNG) from it.
     If the block has no profiles at all, select nothing.
- **LSD sensors (nitrate/pCO2/pH) are not involved.** Daily indices 4 and 9 are ordinary,
  equally-likely candidates like any other index.
- **Determinism:** fixed **random seed** (parameter) so re-runs reproduce the candidate list.

### Output (working copy + blessed shared copy)
- **Working copy** (regenerable): one CSV per site at
  `~/ooi/<site>/metadata/annotations/mld_candidates_<site>_block<NN>.csv` — block width baked
  into the name (zero-padded), so different block sizes coexist. **Create the folder if absent.**
- **Blessed shared copy** (canonical): `PreSelectProfiles.py --bless` copies the working CSVs
  into the repo folder **`~/argosy/mld_candidates/`** (small, committable manifests — a deliberate
  exception to "no data in `~/argosy`", like `sensor_exclusions.csv`). `MLD.py` reads the
  **blessed** copies, and both files are committed to git.
- **Why bless instead of re-run:** selection draws at random from the profiles present in each
  block, so it is only reproducible if the local pp06 set is identical across machines — which is
  NOT guaranteed (partial syncs, newer data). Blessing one person's run and sharing it via git
  guarantees Chuck and Rob label the SAME profiles (the whole point of inter-annotator agreement).

Columns:

| column | meaning |
|---|---|
| `site` | 2-letter site code |
| `block_id` | 0-based block index from the site's first-GPI day |
| `block_start`, `block_end` | block boundary dates |
| `N` | count of profiles found in the block (pre-selection) |
| `selection_tier` | `all4`, `T_only`, or empty (for N=0 blocks) |
| `gpi` | global profile index of the selected profile (empty for N=0 blocks) |
| `timestamp` | selected profile timestamp |
| `daily_index` | 1–9 |
| `has_temperature`, `has_salinity`, `has_density`, `has_dissolvedoxygen` | per-sensor presence flags |
| `seed`, `block_width_days` | provenance |

- **Empty blocks are kept** as rows with `N=0` and no `gpi` (complete coverage/diagnostic
  record).


## 2. MLD.py — interactive annotation tool

Standalone TkAgg GUI (matplotlib), following the `VisQCInspector.py` lineage. Reads a site's
candidate list, lets a human place an MLD on a profile, writes one label row per
(gpi, sensor).

### Invocation
- `--site <sb|oo|ab>` — default `sb` (overrides the default; analogous to `ARGOSY_SITE`).
- `--year <yyyy>` — start point, **not** a hard filter: the tool begins at the first candidate
  whose timestamp falls in that year and continues **past** it into later profiles. Default
  start = first profile in the candidate list for the site.
- `--who <A|C|R|X>` — labeler identity for the whole session; **default `C`** (Chuck). Fixed at
  launch — there is **no who-chooser in the UI** (avoids mid-session mislabeling and keeps the
  per-who output file consistent). Determines both the `who` value written to every row and the
  output filename.

### Display
- **Single-sensor view:** show only the **active sensor's** trace for the current profile
  (T selected → temperature only). Switching the active sensor swaps the displayed trace.
- **Active sensor:** one of T / S / ρ / DO. **T is the default operational sensor;** a UI
  control selects which of the four is active. **Only one MLD is recorded per interaction.**
  The ρ trace is the pp06 `density` shard (potential density σ₀ is deferred).
- **Depth axis:** 0 m at top to 100 m at bottom.
- **Per-sensor color:** trace and MLD marker share one color per sensor — **temperature = red,
  salinity = green, density = gold, DO = blue** — so a sensor reads the same everywhere.
- **Labeled-profile cue:** returning to an already-labeled (gpi, sensor) shows the committed
  MLD as a dashed line plus a dot on the trace **in the sensor's color** (with a black edge),
  so the User can see it is labeled, for which sensor, and where. A no-MLD record draws no
  marker (there is no depth). The just-clicked pick is the same color/size marker.

#### Two binary display states
- **State 1 — filter application:** `file data` (default) OR `file data with the active filter
  applied`.
- **State 2 — raw overlay** (only meaningful when State 1 = "filter applied"): the unfiltered
  file data is *also* drawn in **gray** behind the filtered trace, or not shown. Filtered data
  always renders in **black**. (Gray avoids colliding with the per-sensor marker colors, e.g.
  the red temperature marker.) Default **on**.

### Filters
A small, extensible registry. Initial set of **four**:

| filter key | description | sliders |
|---|---|---|
| `None` | raw pp06 file data, no smoothing (default) | — |
| `savgol` | Savitzky-Golay smoothing (`scipy.signal.savgol_filter`), fixed window | window length (odd, ≥3), polyorder (< window) |
| `adaptive_savgol_std` | σ-modulated Savitzky-Golay: window widened locally where the profile is rough, using local **standard deviation** as the roughness metric; minimal smoothing where smooth | base window, adaptivity/σ-sensitivity |
| `adaptive_savgol_mad` | same adaptive scheme but roughness measured by local **median absolute deviation (MAD)** instead of σ — more robust to isolated spikes | base window, adaptivity/MAD-sensitivity |

- The two adaptive filters are **identical except for the roughness metric** (σ vs. MAD). Keeping
  them as separate selectable keys makes the metric an explicit, recorded experimental variable —
  later analysis can test whether MAD's spike-robustness yields better human picks than σ.
- Filter key + slider values are recorded per label (structured columns, see schema).
- **Minor open item:** exact adaptive formulation (how the local roughness metric maps to window
  width) — start with a reasonable default shared by both adaptive filters, expose one adaptivity
  slider, treat as tunable.
- **Slider bounds (as built):** savgol window 3–101 odd; polyorder 1–5 and always < window
  (enforced in code). Adaptive filters: base window 3–101 odd; adaptivity 0–3 (headroom past 1,
  where 1 tracks normalized local roughness and >1 pushes more of the profile toward the heavy
  trace, per-point weight clipped to 1).

### Advance / commit model (as built)
A **click always COMMITS a real MLD** for the current (gpi, sensor, who), overwriting any prior
value — in **both** modes. So a pick (marker + line + table row) **persists when the User
switches Active sensor and returns**, which is the point: cross-sensor comparison with no extra
clicks. The click marker uses the sensor color at the same size as the committed marker. The two
modes differ only in what happens *after* the commit:
- **Stay on click (default):** commit, then remain on the profile (click again to reposition —
  each reposition overwrites the same row).
- **Advance on click:** commit, then advance to the next candidate.

**`<Advance>` button** keys on the **committed table state, not the transient marker** (the
marker is cleared by sensor switches / navigation while the committed row survives — the earlier
bug was Advance overwriting a real pick with no-MLD because it consulted the marker). Behavior:
- a **real MLD already committed** for (gpi, sensor, who) → **left untouched**, just advance;
- **no real MLD** (never clicked, or clicked then `<Clear pick>`) → record an explicit
  **"no MLD recorded"** and advance.

**`<Clear pick>`** resets the current profile's active sensor to **untouched**: clears any
pending marker and **deletes the committed row** for (gpi, sensor, who), so it re-registers as
unlabeled (Fwd/Rev-to-Null will find it again).

**Recording no-MLD** (a necessary annotation — many profiles have no clear mixed layer): in Stay
mode, either never click then `<Advance>`, or click then `<Clear pick>` then `<Advance>`.

**Descent overlay (planned):** a "Descent" button will overlay the descent trace for the current
(sensor, gpi) as visual context for water-column stability/distortion. Context only — not pickable.
Requires pre-sharded descent data; full design in `DescentData.md`.

- A **UI toggle** ("Advance on click") switches the two modes; default is **Stay on click**
  (toggle off).

### Navigation
- Standard next/previous through the candidate list.
- **Forward to Null / Reverse to Null:** two dedicated buttons that jump to the next / previous
  candidate profile that has **no recorded label for the currently active sensor by the current
  `who`**. Since the running tool only sees its own per-who file, "null" means "unlabeled by me" —
  each labeler fills their own gaps independently (no cross-machine coupling). Surfaces gaps so
  coverage for a given sensor can be filled efficiently.

### Session settings persistence
Active sensor, who-code, filter key, filter slider values, and both display states **persist
across advances** (sticky session configuration). A labeler configures once and grinds.

### Re-labeling
Navigating back to an already-labeled (gpi, sensor, who) and clicking **overwrites** that row
(one row per (gpi, sensor, who); `who` is fixed for the session, so within one file it reduces
to (gpi, sensor)). A different sensor can be labeled on the same profile in a later interaction,
adding a new row.

### The "who" code
Provenance of the labeler; set once via `--who` at launch (default **`C`** = Chuck); **no UI control**:

| code | labeler |
|---|---|
| `A` | TBD person |
| `C` | Chuck (collaborator) — **default** |
| `R` | Rob (project lead) |
| `X` | TBD person |

Because each running tool instance writes only its own `who`, the `who` column is constant
within a file — the value's real purpose is disambiguating rows once per-who files are combined.


## 3. Label output schema

**One CSV per site per labeler** at
`~/ooi/<site>/metadata/annotations/mld_labels_<site>_<who>.csv` (create folder if absent).
The label filename should also carry the candidate block tag (e.g.
`mld_labels_<site>_block05_<who>.csv`) so a label set is traceable to the candidate set it
was made against.
Baking `who` into the filename means each running tool instance writes/overwrites **only its own
labeler's file** — no collision when Chuck and Rob work on separate computers and combine later.

**Key = (gpi, sensor, who).** Sparse: a sensor gets a row only when it is labeled (e.g. GPI 6000
gets a temperature row when T is labeled; a salinity row is added below only when S is chosen).
Re-labeling overwrites the matching (gpi, sensor, who) row. Since `who` is constant within a
file, in-file this behaves as one row per (gpi, sensor); the `who` column keeps the combined
multi-labeler table well-formed.

### Combining & agreement
Combine the per-who files with a simple `pd.concat`. Because the key includes `who`, the merged
table has one row per (gpi, sensor, who) — grouping by (gpi, sensor) then yields inter-annotator
agreement (e.g. Chuck's vs. Rob's temperature MLD on the same profile), the core signal for
training against a label distribution rather than a point estimate.

Columns (structured; not a packed string):

| column | meaning |
|---|---|
| `site` | 2-letter site code |
| `gpi` | global profile index |
| `timestamp` | profile timestamp |
| `sensor` | `temperature` / `salinity` / `density` / `dissolvedoxygen` |
| `mld_depth` | **continuous click depth** (interpolated, not snapped to a sample) |
| `value_raw` | raw file-data sensor value interpolated at `mld_depth` |
| `value_filtered` | filtered-trace sensor value interpolated at `mld_depth` (equals `value_raw` when filter = None) |
| `who` | `A` / `C` / `R` / `X` (`C` = Chuck, default; `R` = Rob) |
| `filter_key` | `None` / `savgol` / `adaptive_savgol_std` / `adaptive_savgol_mad` |
| `filter_p1`, `filter_p2` | structured filter slider settings (e.g. window, polyorder); empty when `None` |
| `no_mld_recorded` | `True` for an explicit "no MLD here" record (no depth); `mld_depth`/values empty |
| `reviewed_at` | UTC timestamp of the decision |

- **Both** raw and filtered values are stored (per decision), so a label is interpretable
  regardless of the filter that was active.
- Depth is the continuous click depth; both values are interpolated at that depth.


## 4. MLDTimeSeries.py — MLD time-series viewer

Standalone TkAgg GUI (repo root, beside `MLD.py`; reuses its `build_gpi_file_index`,
`load_profile`, `science_labels_path`). Purpose: look at the human-labeled MLD as a TIME SERIES
(diurnal / seasonal / event structure) and at the sensor value found at the MLD, to compare
against external forcing (see `Umbrella.md` -> "ERA5 sea state").

### Charts
Two charts stacked, one shared time axis:
- **Upper:** MLD depth (m, axis inverted) for temperature (red), salinity (green), DO (blue).
- **Lower:** the sensor value AT the MLD (the label's `value_raw`): T at MLD (left axis, red),
  S at MLD (first twin axis, right, green), DO at MLD (second twin axis, right, offset spine,
  blue). Three y-axes via `twinx`.
- All series: filled circle markers joined by lines. **No connector line** across a gap of more
  than 1 day between successive points of a series (NaN break).
- Y limits auto-fit the visible window each time the time range changes.

### Controls (bottom of window)
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

### Science vs training data
- **Science** (`mld_labels_<site>_science_<who>.csv`): filled circles joined by lines.
- **Training** (`mld_labels_<site>_block05_<who>.csv`, ~1 profile in 45): filled TRIANGLES,
  markers only (they are too sparse to join). Rows whose (gpi, sensor) already appear in the
  science file are skipped, because the science set was seeded from the training labels and
  they would just overlap.
- Profiles flagged unusable (`xud_recorded`) are never plotted. No-MLD profiles add nothing to
  the upper chart in either mode.

### Invocation
- `--site <sb|oo|ab>` default `sb`.
- `--start`, `--end` default 2024-01-01 / 2024-01-31 (`--end` is inclusive of that day). These
  only set the initial window; the sliders reach anywhere in the label file's time span.
- `--who` default `R` (reads `mld_labels_<site>_science_<who>.csv`).
- `--local` starts in Pacific local time (America/Los_Angeles); default is UTC. The same switch
  is the "Local time" checkbox in the window.
- `--size WxH` initial window size in pixels (e.g. `1500x850`); default auto-fits the screen
  (92% of screen width, 85% of height). Under WSLg a "full screen" click can size to the whole
  Windows desktop rather than one monitor; if so, un-maximize and use `--size`.

### Notes
- Value at MLD is `value_raw`, never the filtered value; the O-mode shallowest value is also
  raw. Density labels are ignored.
- Layout: all axes are placed in figure fractions, so the layout scales with the window.

## Conventions honored
- Standalone GUI uses **TkAgg** (genuinely interactive; needs a display) — contrast the headless
  `Agg` scripts. Requires `python3-tk`. See `operational-recipes` steering §3.
- All data/paths via `ooipaths`; outputs under `~/ooi/<site>/metadata/annotations/` (never in
  `~/argosy`). Folder is created if missing.
- `input()`-free (GUI), so the cloud-stdin convention doesn't apply here.


## Resolved decisions (for the record)
- **Density trace = pp06 `density` shard** (not gsw potential density σ₀; σ₀ deferred).
- **"No MLD recorded" = `no_mld_recorded` flag column** (not an empty `mld_depth`).
- **Chuck's who-code = `C`** (was `I`; changed for readability); default `--who` = `C`.
- **Four filters** including both σ- and MAD-based adaptive savgol (see filter table).

## Open / deferred items
- Exact adaptive local-roughness → window mapping, shared by `adaptive_savgol_std` and
  `adaptive_savgol_mad` (default proposed; tunable).
- Final savgol slider ranges/defaults (proposed above; confirm at build).
- Whether a combined all-sites label file is ever needed (per-site is primary; easy to
  concatenate later).


## Implementation status
Both programs are built and committed in the repo root. `PreSelectProfiles.py` produces the
per-site block candidate lists (working copies under
`~/ooi/<site>/metadata/annotations/`, blessed copies committed to `~/argosy/mld_candidates/`);
`MLD.py` reads the blessed lists and writes labels to
`~/ooi/<site>/metadata/annotations/mld_labels_<site>_<who>.csv`.

## Collaborator setup (running MLD.py on another machine)

`MLD.py` needs a small subset of the `argosy` env, so a portable minimal spec is provided as
**`environment-mld.yml`** (NOT the full `environment.yml` snapshot, which is pinned to exact
Linux build hashes for Rob's machine and carries hundreds of unrelated packages — see the
"environment sprawl" entry in `DevelopmentLog.md` → Open Topics). Dependencies: `numpy`,
`pandas`, `scipy`, `xarray`, `netcdf4`, `matplotlib`, `tk` on `python=3.11`.

```bash
git pull                                   # get MLD.py, environment-mld.yml, mld_candidates/
conda env create -f environment-mld.yml    # creates a conda env named "argosy"
conda activate argosy
sudo apt install python3-tk                # OS Tk bindings for the TkAgg GUI (WSL/Debian/Ubuntu)
python MLD.py --site sb --who C            # C = Chuck (default); see MLD.py header for switches
```

Caveats: TkAgg needs a working display (an X server under WSL2) — headless will not work
(see `operational-recipes` §3). The tool reads the **blessed** candidate lists in
`~/argosy/mld_candidates/`, which is what guarantees Chuck and Rob label the same profiles.
