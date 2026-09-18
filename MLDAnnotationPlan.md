# MLD Annotation Plan

Design spec for a two-program workflow that builds a **human-labeled MLD (mixed-layer
depth) training dataset** from the pp06 shallow-profiler data. The labels are the ground
truth for a later ML model that will estimate MLD across the entire shard dataset (see
`Analysis.md` and the "annotation problem" note in `argosy-conventions.md`).

Status: **spec only — not yet implemented.** Two programs:
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

### Output
One CSV per site at `~/ooi/<site>/metadata/annotations/mld_candidates_<site>.csv`.
**Create the target folder if it does not exist** (test-and-create).

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

#### Two binary display states
- **State 1 — filter application:** `file data` (default) OR `file data with the active filter
  applied`.
- **State 2 — raw overlay** (only meaningful when State 1 = "filter applied"): the unfiltered
  file data is *also* drawn faintly in **light blue** behind the filtered trace, or not shown.
  Filtered data always renders in **black**.

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
- **Slider bounds (proposed):** savgol window 3–51 odd; polyorder 1–5 and always < window
  (enforce in UI).

### Advance modes
- **Mode 1 — Auto-advance (default):** clicking in the profile chart records the depth for the
  current profile+sensor and immediately generates the next profile view.
- **Mode 2 — Manual advance:** clicking marks the point with a **large blue dot** but records
  nothing yet. Re-clicking relocates the dot freely (as many times as desired). The
  **`<Advance>`** button commits the label and moves on. `<Advance>` with **no point placed**
  saves **"no MLD recorded"** (an explicit skip) and advances.
- A **UI toggle** switches between Mode 1 and Mode 2 (default Mode 1).

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
Provenance of the labeler; set once via `--who` at launch (default **`I`**); **no UI control**:

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
| `who` | `A` / `I` / `R` / `X` |
| `filter_key` | `None` / `savgol` / `adaptive_savgol_std` / `adaptive_savgol_mad` |
| `filter_p1`, `filter_p2` | structured filter slider settings (e.g. window, polyorder); empty when `None` |
| `no_mld_recorded` | flag/marker for an explicit Mode-2 skip (no depth chosen) |
| `reviewed_at` | UTC timestamp of the decision |

- **Both** raw and filtered values are stored (per decision), so a label is interpretable
  regardless of the filter that was active.
- Depth is the continuous click depth; both values are interpolated at that depth.


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


## Next step
Build `PreSelectProfiles.py` first (candidate lists are the input to the tool), then `MLD.py`.
When implementation begins, add pointers in `ArgosyOverview.md` → "Pointers to Key Actions"
and note the tool in `CodeManifest.md`.
