# Descent Data

Design note for recovering **descent** profile data as a second-class companion to the primary
**ascent** dataset. Status: **create machinery implemented (Sep 2026); EC2 run + MLD button pending.**

Implemented: `ooipaths` direction support (`redux_dir`/`postproc_dir`/`pp05_manifest`/`shard_glob`
take `direction=`, plus `ARGOSY_DIRECTION` env + `redux_version`); `pipeline/shard.py --direction
descent` (8 HSD sensors, peak→end, `redux_descent`, `V1D`); pp05/pp06/filter2/filter3 honor
`ARGOSY_DIRECTION=descent` (→ `pp05_descent_manifest.csv`, `postproc/pp06_descent/`);
`run_pipeline.sh <site> descent` stage (shard → pp chain → sync). Ascent paths unchanged
(verified). **Not yet run** on EC2; the MLD Descent button is not yet wired (deliberate — a
test-app conversation comes first).

## Motivation

The shallow profiler ascends (mooring → near-surface) and then descends back. The scalar sensors
sit at the top of the science pod, so on **ascent** they enter relatively undisturbed ("pristine")
water — this is why ascent is the primary, higher-precision dataset. **Descent** data is noisier
(the pod has stirred the water it now falls through) and is therefore treated as **second-class**.

It is still useful: descent gives at least a *qualitative* sense of water-column **stability** and
the **rate of distortion** of structure between the ascent and the return. Because ascent and
descent of one profile are separated in time (minutes to tens of minutes — see the descent-duration
histogram in `profile_duration_histograms.py`), overlaying them shows two *different times*, and
the difference between them is exactly the stability/distortion signal of interest.

Primary consumer: a **"Descent" overlay button** in the MLD annotator (`MLD.py`) that plots the
descent trace behind the ascent trace for the current (site, sensor, gpi) as visual context.

## Scope

- **Descent scalar sensors (8, the HSD set that currently operates on ascent):** temperature,
  salinity, density, dissolvedoxygen, chlora, cdom, backscatter, par.
- **Excluded — no descent shards:**
  - **nitrate (NUTNR):** ascent-only sensor.
  - **pCO2 (PCO2W), pH (PHSEN):** these already operate on **descent** as their primary mode, so a
    separate "descent" version would be redundant — their normal shards are already the descent.
- **Sites:** same per-site scheme as ascent (`sb`/`oo`/`ab`); begin with `sb`.

## Where descent fits in the data scheme

Direction was previously *implicit by sensor* (the 8 HSD scalars = ascent; pCO2/pH = descent), so
the shard filename grammar has **no direction field**. Recovering descent for the 8 HSD sensors
means the *same* sensor now exists in both directions, so direction must become explicit. The
agreed design carries it **two ways** (belt-and-suspenders), leaving the ascent dataset untouched:

1. **Parallel directory tree** — descent shards live in `~/ooi/<site>/redux_descent/<yyyy>/`,
   mirroring the ascent `redux/<yyyy>/` tree with identical year subdirs. The pp06 equivalent
   mirrors under a descent postproc tree (e.g. `postproc/pp06_descent/<yyyy>/`). The ascent
   `redux/` and `postproc/pp06/` sets are left **byte-for-byte pristine**. Direction carried by
   *location* keeps the filename grammar clean and makes descent's second-class status structural
   (easy to exclude, not-publish, delete, or regenerate independently).
2. **Version token in the filename** — descent shards use version **`V1D`** where ascent redux uses
   `V1`. The positional filename grammar is unchanged (still
   `RCA_<site>_sp_<sensor>_<yyyy>_<ddd>_<gpi>_<daily>_<version>.nc`; parsers still read `gpi` at the
   same position) — only the `<version>` field's value differs. So a descent shard **self-identifies**
   even if copied out of its tree.

Example: ascent `RCA_sb_sp_temperature_2022_043_13614_1_V1.nc` →
descent `RCA_sb_sp_temperature_2022_043_13614_1_V1D.nc` under `redux_descent/2022/`.

### ooipaths support

Path/token knowledge stays centralized in `ooipaths.py` (no hardcoding). Add a **`direction`**
concept (default `"ascent"`) to the relevant accessors — e.g. `redux_dir(year, site,
direction="descent")` returning `redux_descent/<yyyy>`, and the analogous postproc accessor — or
dedicated `redux_descent_dir` / descent postproc accessors. Ascent callers are unchanged.

## Processing

Descent extraction is **not new machinery**. `pipeline/shard.py` already models direction:
`SENSOR_MAP` maps each science variable to `(shard_name, direction)` and slices `start→peak`
(ascent) or `peak→end` (descent) using the profileIndices `start`/`peak`/`end` columns. Descent
recovery is running the existing pass with the direction flipped for the 8 HSD sensors, writing to
the `redux_descent` tree with the `V1D` token.

**Execution model — Build-Config-Execute-Destroy on a disposable EC2 box** (the existing CDK flow;
see `operational-recipes` §4 / §4b): `cdk deploy` → run the descent pass (`redux_descent` shards →
pp06_descent) → `aws s3 sync` up to `s3://s3ooi/<site>/...` → `cdk destroy`. One-time per site.
Local-then-sync, same as the ascent pipeline. Volume roughly adds the 8-sensor shard count again
for each processed site (bounded, known from ascent counts).

**redux_descent → pp06_descent:** carried through with the **same filter settings as ascent**
(Filter 0/1 in pp06, plus filter2/filter3) for an apples-to-apples baseline. Caveat: those filters
(Sav-Gol windows, salinity/density MRA) were tuned to ascent characteristics; applying them to
noisier descent data is accepted as a *baseline* choice, not a claim of optimality. Revisit if
descent pp06 proves poorly behaved.

### Deferred: pause-interval precision (post-pp06)

On daily indices **4 (midnight)** and **9 (post-noon)** — 2 of every 9 profiles — the descent has
**built-in pauses** that let the chemical sensors equilibrate. For the 8 HSD sensors those pauses
mean **repeated measurement at nearly the same depth**, an opportunity for *better* precision via
averaging. This is **deferred to a post-pp06 step**, deliberately parallel to how MLD filtering
sits downstream of pp06. For now, indices 4 & 9 descent shards contain the raw paused samples passed
through the same filters — so those two profiles may look "lumpy" (clustered depths, longer dwell)
compared with the smooth-descent profiles. That is expected, not an artifact.

## MLD.py "Descent" button

With descent pre-sharded, the button is a cheap **S3 GET of a small per-profile shard** — no
per-click compute, no whole-file read. Behavior:
- Look up the descent shard for the current (site, sensor, gpi) using the same filename logic as
  the ascent index, pointed at the `redux_descent` (or pp06_descent) tree / `V1D` version.
- If found, **overlay** it on the current chart behind the ascent trace (distinct linestyle, e.g.
  dashed, in the sensor color); if absent, a "no descent data" status message.
- The descent trace is **context only — not pickable.** MLD is labeled on ascent; descent informs
  the human's judgment about stability but is never itself annotated.

## Open / deferred items

- Processing level exposed to the button: pp06_descent (comparable to the ascent pp06 the tool
  reads) is the default intent; redux_descent remains available.
- Pause-interval averaging for indices 4 & 9 (post-pp06 precision step) — deferred.
- Whether to make descent data public on S3 (like pp06) — a separate deliberate decision per the
  "Public data sharing" steering rule; **not** exposed automatically.
- Filter appropriateness for descent (see caveat above) — revisit after inspecting descent pp06.
