# BR — Bicameral Redesign (September 2026)

> **Status: DESIGN / DELIBERATION. No file moves, renames, new folders, or rewrites yet.**
> This document thinks through options and tradeoffs first, then converges on a plan.
> Implementation happens only after the plan below is settled and explicitly approved.

## What BR is

BR is the **Bicameral Redesign**, a September 2026 fix-up of Argosy. "Bicameral" alludes to
Argosy's two-chamber nature: the **Jupyter Book** (the science narrative, reader-facing) and
the **working data-analysis environment** (code + data that produce results). The redesign
aims to make that dichotomy clean and legible instead of tangled by organic growth.

It serves two personae in particular:
- **Arthur** (science reader) — sees the Book. Should encounter Phase 2 analysis, not pipeline plumbing.
- **Chuck** (collaborator) — works the machinery. Needs the pipeline and analysis code cleanly separated and discoverable.

## Goals (the "done" criteria for BR)

1. **Phase separation is physical, not just conceptual.** Phase 1 (pipeline) code and Phase 2
   (analysis) code live in clearly distinct, self-describing locations.
2. **The Book contains Phase 2, and (almost) no Phase 1.** Phase-1 code that grew inside Book
   notebooks is identified and moved out (or demoted to repo-only working notebooks).
3. **Default time range is 2014–2026 (soon 2027) and runs without hanging.** No hardcoded
   narrow windows (e.g. the leftover 2024 defaults); year ranges derive from data or config.
4. **Everything conforms to the per-site data restructure** (`~/ooi/<site>/...`, all paths via
   `ooipaths.py`, 2-letter site codes, no `slopebase`-style legacy tokens).
5. Redesign supports Arthur (Book) and Chuck (machinery) reading paths without friction.

## Non-goals / constraints

- Not a science-methods change: the physics/QC logic stays; this is about **organization**.
- Must not break the AB run happening in parallel (see "Parallel track" below).
- Follow the project rule: don't move data into `~/argosy`; generated data → `~/ooi`.


## Bicameral model (the two chambers)

| | Chamber A: Jupyter Book | Chamber B: Working environment |
|---|---|---|
| Audience | Arthur (reader), Maggie (oversight) | Chuck (collaborator), the pipeline itself |
| Content | Phase 2 analysis, narrative, figures | Phase 1 pipeline, QC, data production |
| In `_toc.yml`? | Yes | No (repo-only) |
| Examples | internal-wave analysis, SGA, tidal, plume | download/shard/pp/VisQC, ooipaths |

**Phase 1** = the data pipeline that produces analysis-ready datasets **and metadata**
(download → shard → pp05 → pp06 → **pp07/VisQC**). Tends NOT to appear in the Book.
**Phase 2** = analysis on those datasets (internal wave amplitude/speed, SGA, tidal, plume).
SHOULD appear in the Book.


## Design tenet: where do the components go? (laptop vs cloud vs web)

Argosy is a reasonably complex project with many moving parts, so the recurring question is
"where does each component go?" The guiding placement map:

- **The Argosy repo** holds the Jupyter Book AND the computational code (sorted within it).
- **The data** lives in the `ooi/` directory, kept SEPARATE from `argosy/`.
- **The data is backed up on S3 object storage.** Once backed up:
  - high-volume, low-touch data is DELETED from localhost as superfluous (reclaim disk);
  - some S3 content is kept in a collaborative/shared state — no cost to download.
- **The localhost machine (laptop etc.) is for EDITING and ORCHESTRATION** — of both the Book
  and the computation. It is NOT where heavy data-touching computation should happen.
- **Actual computation should be relegated to the cloud when doing so makes sense.** For any new
  data task the question to ask FIRST is: *"Is this a cloud task?"* (Compute goes to the data,
  which lives in S3 — not the other way around. Getting AWAY from "pull the data to the laptop
  and work on it locally" is an explicit goal.)
- **Other components live elsewhere on the web:**
  - **GitHub** — the safe master copy of the repo (localhost + EC2 are clones).
  - **Zenodo / similar** — archival + open-science / DOI use.
  - **Published Jupyter Book** — the reader-facing site (GitHub Pages).
  - **Published AGU26 poster** — reached via QR code.

Consequence for design decisions (e.g. descent-data recovery, VisQC pp07 production): prefer
cloud-side compute against the S3-resident raw/redux/pp data over pulling large files to the
laptop. See "Descent-data recovery" below for a worked example of applying this tenet.


## Descent-data recovery (design topic — applies the cloud-vs-laptop tenet)

Motivation: temperature (and other ascent-only sensors) on DESCENT is useful as a comparison
with ascent. Mechanism (confirmed correct against `shard.py`): descent is just the OTHER
time-window slice of the SAME source file — `peak → end` instead of `start → peak`, using the
profileIndices `peak` and `end` timestamps for a GPI. The sharder ALREADY does this for pH/pCO2
(direction="descent" in SENSOR_MAP), so producing descent temperature is a naming/where-to-run
decision, not new physics.

Naming problem: current shard name `RCA_<site>_sp_<sensor>_<yyyy>_<ddd>_<gpi>_<daily>_V1.nc` has
no direction token, so ascent + descent temperature would collide. Options: sensor-name token
(`temperature_desc`), a direction field in the filename, or a separate redux subtree.

Where to run it (the "is this a cloud task?" question — YES, the raw is in S3):
1. **Lambda, per-request descent shard** — serverless, on-demand. CAVEAT: CTD source files are
   ~500 MB each; Lambda /tmp up to 10 GB fits one, but memory + 15-min limit make multi-file /
   many-GPI requests marginal. Best for occasional/interactive "give me descent for GPI X".
2. **Lambda + prebuilt index** (GPI → source file + byte range) so it does a cheap S3 byte-range
   read instead of scanning 500 MB. More setup, much faster/cheaper per call.
3. **Bulk pass on the ephemeral EC2 box** — add a `descent` direction to `shard.py`'s SENSOR_MAP,
   run as one more pipeline stage while the box is up, sync descent shards to S3. Best if descent
   is a STANDARD Phase-1 product rather than ad-hoc. No new service; reuses existing machinery.
4. **AWS Batch / Fargate** for the bulk case without a persistent box.

Underlying decision = **on-demand vs bulk**. Bulk-standard → Option 3 (simplest, cheapest, cloud-
side). Genuinely ad-hoc → Option 1/2 (Lambda + S3 byte-range).

**RESOLVED (2026-09-19): Option 3 (bulk pass on ephemeral EC2), NOT Lambda.** Rationale: descent
is a standard Phase-1 product; per-request Lambda would re-read whole ~500 MB source files per
click, whereas a one-time bulk pass reads each source once. Naming decided: parallel
`redux_descent/<yyyy>` tree + `V1D` version token (double delineation; ascent tree untouched);
`ooipaths` gains a `direction` concept. Scope: the 8 HSD sensors only (no nitrate; pCO2/pH already
descent). redux_descent → pp06_descent with the same filter settings (apples-to-apples baseline).
Pause-interval (indices 4 & 9) precision deferred to post-pp06. Full spec: **`DescentData.md`**.


## Central question raised this session: where does VisQC / cline work live?

The `iw/` folder currently MIXES both phases (inventory below). The user proposes:
- **VisQC is a good Phase-1 process name**, with two outputs:
  1. a **pp07** version of the shard data (by site and year) — human-QC-corrected shards;
  2. a **metadata file, one line per profile**, describing clines + N² + MLD.
- Open question: should this Phase-1 QC work get its **own dedicated directory**, or go into
  **`~/argosy/pipeline/`** (alongside download.py / shard.py / run_pipeline.sh)?

### Current `iw/` inventory (classified)

Phase 1 (pipeline/QC — operate on pp06 to produce metadata / planned pp07):
- `cline_extract.py` — batch: pp06 → per-profile cline depths/strengths/thickness, N²(max/depth),
  MLD, σ₀; writes `metadata/features/cline_extract_<site>.csv`. (This IS the "one line per
  profile" metadata the user describes for VisQC output #2.)
- `cline_plot.py` — time-series viewer of the cline_extract CSV (dual-mode after this session).
- `VisQCInspector.py` — interactive human QC over pp06 (two-panel GUI + Accept/Correct/Discard
  → `metadata/annotations/visqc_visitation_<site>.csv`).

Phase 2 (analysis/theory — Book-facing):
- `internal_wave.py` — idealized westward internal-wave animation (→ mp4).
- `internal_wave_physics.py` — stream-function physics (incompressible displacement field).
- `TestInternalWaveIncompressibility.py` — area-conservation test of that physics.

So `iw/` = "internal waves" but has accreted the Phase-1 cline/QC toolchain that merely
*feeds* internal-wave analysis. That is the mess to untangle.

### Option set for the Phase-1 QC code location (NOT YET DECIDED)

**Option 1 — Fold into `~/argosy/pipeline/`.**
- Pro: one home for all Phase-1 code; matches the mental model "pipeline = Phase 1"; run_pipeline
  could eventually call cline_extract as a pp-adjacent step.
- Con: `pipeline/` so far is batch/headless/cloud-run (download/shard/pp). VisQCInspector is an
  interactive local GUI — a different beast. Mixing batch and GUI in one folder may re-blur things.

**Option 2 — A dedicated Phase-1 QC folder (e.g. `~/argosy/visqc/` or `~/argosy/qc/`).**
- Pro: names the process the user likes ("VisQC"); keeps interactive QC distinct from the
  headless pipeline; clear home for Inspector + Corrector + cline_extract + cline_plot.
- Con: a third code folder to know about; need to decide what counts as "QC" vs "pipeline."

**Option 3 — Split by execution mode, not just phase:** batch pp-producers (cline_extract) into
`pipeline/`; interactive tools (VisQCInspector, cline_plot) into a `visqc/` or `tools/` folder.
- Pro: respects the batch-vs-interactive distinction that Option 1's con exposes.
- Con: cline_extract and its viewer/inspector get separated, though they're a tight family.

**DECIDED (2026-09-07): Option 2 — a dedicated `~/argosy/visqc/` directory** for the 0607 task.
Rationale from the user: do NOT muddy `~/argosy/pipeline/` (which is headless/batch/cloud) with
the interactive VisQC work. The `visqc/` folder holds the cline/QC family (cline_extract,
cline_plot, VisQCInspector, future VisQCCorrector). The three Phase-2 internal-wave files move to
a Phase-2 analysis home (see below). Keeps "VisQC = Phase-1 process producing pp07 + per-profile
metadata" intact and unmixed. (Still open: whether the folder should be named `visqc/` given
cline_extract isn't strictly "visual" — see open question 5; but `visqc/` is the working choice.)

### The pp07 question (needs a definition before building)

pp07 is referenced as the deferred "human-corrected shards" output (VisQC.md, Analysis.md's
`pp05 > pp06 > pp07`). BR should NAIL DOWN:
- Is pp07 a full re-shard, or a filtered/annotated copy of pp06 (like filter2/filter3)? (Prior
  finding: filters read pp06, not redux — pp07 likely follows.)
- Layout: `~/ooi/<site>/postproc/pp07/<yyyy>/` (consistent with pp06). Confirm.
- Who writes it: the planned `VisQCCorrector.py` (Stage 2), consuming the visitation CSV +
  cline_extract + pp06.


## Where do the Phase-2 internal-wave files go?

Candidates: a `~/argosy/analysis/` or `~/argosy/iw/` (kept, but Phase-2-only after the cline/QC
family moves out). The Book chapter `InternalWaves.ipynb` is the Phase-2 narrative that should
consume these. Decide alongside the SGA/tidal/plume folders (are those already organized by
phase? — audit pending).


## Phase-1 code that grew inside the Jupyter Book (audit pending)

Book notebooks (`chapters/`) currently include: DataDownload, DataSharding, MidnightNoon,
Visualizations, SpectralGraphAnalysis, StubWork. Of these, **DataDownload** and **DataSharding**
are Phase-1 pipeline steps living in Book space. BR should decide:
- Move them out of the Book (repo-only notebooks, or supersede by `pipeline/download.py` +
  `pipeline/shard.py` which already exist)?
- The SessionState already flags "thin DataDownload/DataSharding to call pipeline/ modules" —
  BR is the natural place to resolve that.
- MidnightNoon / Visualizations: Phase-1 or Phase-2? (Visualization feeds analysis; midnight/noon
  is profile classification metadata = arguably Phase 1.) Audit + classify each chapter.


## Default time-range hardening (cross-cutting)

Leftover narrow defaults to purge (found so far):
- `VisQCInspector.py`: default start 2024-01-01 (now env-overridable, but 2024 is the default).
- `cline_plot.py`: FIXED this session (now full data span).
- `cline_extract.py`: START_YEAR/END_YEAR = 2015/2025 — should be 2014–2026 (→2027).
BR guideline: year ranges come from the data present or explicit config, spanning 2014–2026+,
and long runs must not hang.


## Parallel track (does NOT wait on BR)

AB data is on order from OOINET (node SF03A, RS03AXPS, start 2014-12-01, **includes pCO2**).
When the staging URLs arrive: git commit-sweep → `cdk deploy` → `run_pipeline.sh ab all` →
verify S3 → `cdk destroy`. See SessionState "NEXT SITE = ab" checklist. BR design work proceeds
in parallel and should not block (or be blocked by) the AB run.


## Open questions to resolve (running list)

1. [DECIDED] VisQC/cline code location: **`~/argosy/visqc/`** (Option 2). Don't muddy `pipeline/`.
2. [PARKED — needs data review in the Vis notebook] Define pp07 precisely (re-shard vs filtered
   copy of pp06; who writes it; layout `postproc/pp07/<yyyy>/`?).
3. [PARKED — undecided; remind user] Phase-2 internal-wave file home; reconcile with SGA/tidal/
   plume folder organization.
4. [DECIDED] `chapters/` classification: **MidnightNoon OUT** of Book (Phase-1 profile class.);
   **Visualizations STAYS** in Book (Phase-2); **DataDownload OUT**, **DataSharding OUT** (Phase-1,
   superseded by pipeline/download.py + pipeline/shard.py). SpectralGraphAnalysis stays (Phase-2);
   StubWork = scratch (TBD).
5. [DECIDED] Folder is **`visqc/`** and it DOES house cline_extract + cline_plot ("part and
   parcel"), not only the visual inspector. There is NO separate `qc/`.
6. [OPEN] How much of this is reversible/low-risk vs. needs care (git-tracked moves, import updates).
7. [RESOLVED 2026-09-19] Descent-data recovery: **bulk shard.py descent pass on the ephemeral box**
   (not Lambda). Naming = parallel `redux_descent/<yyyy>` tree + `V1D` token. Full spec in
   **`DescentData.md`**. See "Descent-data recovery" above.
8. [OPEN] **Which data products should be free to download from S3, and how bundled?** Currently
   ONLY pp06 is public (all 3 sites, `<site>/postproc/pp06/*`, ~46 GB total). Candidates for future
   public release: pp07 (once defined), the per-profile cline/N²/MLD metadata, noon/midnight subsets
   (pp01/pp02), tidal_constituents.json, etc. Open: what belongs in the public set, and should
   related products be BUNDLED (e.g. a single downloadable release / Zenodo archive) rather than
   loose prefixes? Egress is owner-billed, so scope deliberately. Steering rule now requires ASKING
   the human before making any new dataset public. See `Publishing.md` → "Relationship to the S3
   public bucket" for the S3-live-vs-Zenodo-durable framing and the deposit plan (all 3 sites,
   ~46 GB, within Zenodo's ~50 GB limit).

   **Safety assessment of the public pp06 policy (2026-09-07):**
   - DEMONSTRABLY SAFE on the SECURITY surface: grants only GetObject + ListBucket on the pp06
     prefixes — no Put/Delete/config, so no tamper/ransom/upload-cost path. Scope is prefix-limited
     (redux, pp01/02/05, metadata, 204 GB ooinet all private — verified). Data is non-sensitive
     derived measurements (no PII/creds). "Use outside intent" = unintended VOLUME, not unintended
     access; open scientific reuse is fine.
   - NOT demonstrably safe on the COST surface: public GetObject egress is UNBOUNDED in principle.
     ~$4.14 per full 3-site pull (46 GB × $0.09/GB), but no rate limit, no cap, no requester auth —
     a bot/scraper/loop could run the bill arbitrarily high. ListBucket makes contents enumerable,
     easing both legit reuse and abuse. So: bounded surface + low expected cost, but unbounded
     worst-case bill. NOT "demonstrably safe" in the cost sense.
   - Mitigations (in increasing effort): AWS Budgets alarm (smoke detector — alerts, doesn't
     prevent; DOING NOW at $25 ≈ ~5 downloads) → CloudFront+WAF rate-limit → Requester Pays (needs
     downloader AWS acct, kills frictionless access) → publish the fixed pp06 set via ZENODO instead
     of live public S3 (offloads hosting+egress to an open-data service; likely the right long-term
     home per the "where do components go?" tenet). LEANING: keep S3 public-read for now WITH a
     budget alarm + a manual kill switch, migrate to Zenodo for the durable public release.


## Possible orphans (repo scan, 2026-09-07)

Scan scope: `~/argosy` code + docs only (not the `~/ooi` data tree). "Orphan" = no textual
reference in .py/.md/.ipynb/.yml/.sh.

**Deleted this session (user-approved):**
- `ctd_coverage.png`, `ctd_minimum_cover.png` — raw-OOINET-overlap visuals produced by
  DataDownload/DataSharding; stray at repo root (generated images belong in
  `~/ooi/<site>/visualizations/`). Notebook code that made them is not a concern.
- `vbeamatten.csv`, `vcurrent.csv`, `vopticalabsorb.csv`, `vspectralirr.csv` — vector-sensor
  channel CSVs anticipating a future vector-data download; not needed now. NOTE: three of these
  (vcurrent, vspectralirr, vopticalabsorb) are still referenced by `SensorTable.md` and
  `CodeManifest.md` → those docs need reconciliation (BR follow-up). `vbeamatten.csv` was
  already unreferenced. `SensorTable.md` also references a `vspectrophot.csv` that never existed.

**Also noticed (not deleted — clutter, gitignored `_*.py`):**
- `_check_ranges.py`, `_check_smap.py`, `_check_sst.py` — leftover temp scripts (convention says
  delete after use). Untracked; safe to remove anytime.

**BR follow-up: DONE (2026-09-07).** Reconciled the vector-CSV references after the vXXXX.csv
deletions: `SensorTable.md` (companion-files line reworded to "deferred until vector download";
phantom `vspectrophot.csv` mention dropped), `CodeManifest.md` (four v*.csv rows removed), and
the `argosy-conventions.md` steering (vector-channel line reworded). No dangling references remain.


## Change log (BR deliberation)

- 2026-09-07: BR.md created. Inventoried `iw/` (3 Phase-1 QC files + 3 Phase-2 IW files).
  Framed the bicameral model, the VisQC-location option set (leaning Option 2, not decided),
  the pp07-definition gap, the Book-notebook audit, and the time-range hardening. No files moved.
- 2026-09-07 (later): Decisions recorded. #1 visqc/ (Option 2). #4 notebook classification:
  MidnightNoon out, Visualizations stays, DataDownload+DataSharding out. #5 visqc/ houses the
  cline family too (no separate qc/). #2 (pp07) parked pending Vis-notebook data review. #3 (IW
  Phase-2 home) parked, remind user. Also clarified the environment model: GitHub is master;
  laptop = working master (edit+commit+push); EC2 only pulls (ephemeral, dies on cdk destroy) —
  so download_link_list.txt lives on the laptop and travels laptop→GitHub→EC2.
- 2026-09-07 (later still): Added the "where do the components go?" design tenet (localhost =
  edit/orchestrate; compute → cloud when it makes sense; data in ooi/ + S3, high-volume low-touch
  deleted from localhost after backup; web components = GitHub master, Zenodo archival, published
  Book, AGU26 poster via QR). Added the "Descent-data recovery" design topic (open-demand-vs-bulk;
  Lambda big-file caveat; shard.py already does descent for pH/pCO2). Open questions 7 added.
- 2026-09-07 (S3 public-access reconciliation): Found a THREE-WAY mismatch — repo
  `s3_public_read_policy.json` said `pp06/*` (flat, pre-restructure/stale), DataOps.md said
  `sb/redux/*`+`sb/postproc/*`, and the LIVE bucket policy said `sb/redux/*`+`sb/postproc/*`
  (sb-only, redux public, all pp levels public). DECISION: only pp06 public, all 3 sites.
  Rewrote `s3_public_read_policy.json` → GetObject+ListBucket on `{sb,oo,ab}/postproc/pp06/*`;
  APPLIED via put-bucket-policy and verified the live policy matches. redux + pp01/02/05 +
  metadata + ooinet now private. Reasons: redux is more flawed than pp06; narrower public surface;
  egress is owner-billed. Added steering rule "Public data sharing (S3)" (ASK before exposing new
  datasets). Fixed DataOps.md to describe reality. New BR open question 8 (what else to share / how
  to bundle). Cost/security note: public GET egress bills the bucket OWNER (~$0.09/GB out); risk is
  bulk/bot download of a discoverable public prefix — bounded but unbounded-in-principle; mitigations
  = Requester Pays (needs downloader AWS acct), CloudFront caching, or accept bounded open-science cost.


## Design topic: SignoffQC — standalone scalar sign-off tool (DECIDED, building)

A Phase-1 QC/annotation tool, sibling to VisQCInspector, in the decided `visqc/` folder. Purpose:
a human "first pass" to SIGN OFF on scalar data (mark suspect sensors), NOT cline estimation.

- **Launch:** `python visqc/SignoffQC.py --site <sb|oo|ab> --year <yyyy>` (TkAgg GUI; needs display).
- **Layout:** one window, four charts on a horizontal row, each with multiple auto-scaled x-axes
  (may later switch to SensorTable low/high ranges):
  - Chart 1: temperature, salinity, density
  - Chart 2: dissolvedoxygen, cdom, chlora
  - Chart 3: backscatter, nitrate, par
  - Chart 4: ph, pco2
- **Title:** GMT→local (America/Los_Angeles) time-of-day, with parenthetical "midnight"/"noon" for
  those extended profiles (reuse bundle_chart.check_noon_midnight logic).
- **Navigation:** Advance / Back (a profile qualifies if ≥1 of the 11 sensors is present); plus a
  Julian-day text field + Go To button for time navigation within the year.
- **Per-sensor state buttons (11):** tri-state Ok / None / Discard. If data present → Ok; clicking
  toggles Ok↔Discard. If absent → None and clicking does nothing.
- **LSD nuance:** ph/pco2/nitrate run only on daily-index 4 & 9. So mark absence as
  **None (expected)** for non-noon/midnight profiles, **None (missing)** for noon/midnight profiles.
- **Display toggles:** one per trace, initially on, to declutter.
- **Data source:** **pp06** (less data to page through than redux).
- **Output = state table, ONE ROW PER GPI** (transposed from the original 13-row sketch):
  `metadata/annotations/scalar_signoff_<site>_<year>.csv`. Columns: gpi, visits, then 11 sensor
  state columns (temperature…pco2) each Ok/None-expected/None-missing/Discard. `visits` starts 0,
  increments each time the tool lands on that GPI ("has the user seen this profile?").
- **Resume/merge:** relaunching a year LOADS the existing table and continues (increment visits,
  preserve prior Discards) — idempotent, no overwrite. Same pattern as pp scripts / VisQC.
- **Role in the pipeline:** pp07 will be built in a TBD way, and the SignoffQC output table will be
  PART of its input (the discard decisions feed pp07 construction). This resolves BR open-Q 6's
  "how does Discard connect" for the scalar sign-off case: it's a pp07 input, distinct from
  `sensor_exclusions.csv` (the time-window embargo list).

## Design topic: notebook bundle explorer — Local/S3 source switch (DESIGN)

Goal: let the Jupyter Book enable data exploration WITHOUT the reader downloading ~15 GB of shards
— a source switch (Local vs S3) so shards can be pulled per-profile from S3 on demand (slower, but
no bulk download). Fits the "compute-to-data / don't pull to laptop" tenet.
- Implemented via a shared **source-access module** (`visqc/shard_source.py` or similar) that
  abstracts (a) file DISCOVERY — glob local FS vs `list-objects` on S3 — and (b) file OPEN — local
  path vs `xr.open_dataset` over `s3fs`/`fsspec`. Notebook bundle_chart consumes it via a Local/S3
  dropdown.
- **Public-access constraint:** only **pp06** is public on S3 (redux/pp01/pp02/pp05 private). So the
  S3 source can serve ONLY pp06 to an unauthenticated Book reader; the UI must reflect that (other
  sources are Local-only). Per-profile shards are small (KB) so latency is modest; cache the S3
  index (listing) since it's the slow part.
- Shared plotting core: factor `plot_bundle` so the notebook (interactive ipywidgets) and any
  standalone variant share one implementation (parallels the cline_plot dual-mode / pipeline module
  pattern).
- 2026-09-20: Doc legibility — evaluated folding PP05_QCAnalysis.md + PP06_Filters.md into
  PostProcessing.md. DECIDED: do NOT merge (would push PostProcessing.md ~362→~590 lines, over the
  <400 steering guideline, and collapse a deliberate overview-vs-deep-dive split). Instead THINNED
  PostProcessing.md: replaced the duplicated redux→pp05→pp06 + pp06-Filters detail with a summary +
  pointers to PP05_QCAnalysis.md / PP06_Filters.md (362→313 lines). The old "Data operations"
  overlap with DataOps.md was already reduced to a pointer (no action needed). Also added the
  publish commands to the _toc.yml header comment.


## Roadmap: align argosy to the MOAR "AI-ready building block" objectives

Source: `MakingOOIAIReady.md` → "Is argosy a building block?" lists six gaps between argosy's
current state ("excellent private practice") and an AI-ready building block. This is the near-term
roadmap to close them, so argosy can serve as the credible Phase-0/1/2 prototype the MOAR proposal
leans on. Ordered by leverage + dependency. (BR guideline: deliberate design, then implement.)

### G1 — Cloud-optimized format: shard → Zarr  [HIGH PRIORITY]
**Gap:** per-profile NetCDF shards are analysis-ready but not ARCO; an agent can't slice across the
record without fetching many files. **Target:** a Zarr representation of the pp06 (and redux?) data
that supports lazy, chunked, cross-profile/cross-time access over S3 (`xarray.open_zarr`,
consolidated metadata), so "give me temperature at Slope Base 2018–2020, 0–50 m" is one lazy read,
not thousands of file opens.
- Design questions: one big Zarr store per (site, sensor) spanning all years+profiles, vs per-year?
  Chunking strategy (by profile? by depth-bin? by time?) — this is the key perf lever, like RAG
  chunking. How to represent the ragged per-profile depth axis in a regular Zarr array (interpolate
  to a common depth grid? store as a 2-D [profile × depth-bin] cube?). Keep the shards too, or
  supersede? Relationship to the existing `shard_source.py` Local/S3 layer.
- Likely the biggest single win for AI-readiness AND for the notebook explorer (kills the "pull
  15 GB" problem outright). Revisit sharding with Zarr as the primary output target.

**Shard vs Zarr — the mental model (for the transition):**
- A **shard** = one file per (profile × sensor): the FILE is the unit. ~150,000 files. Great for
  "give me one profile," bad for "sweep the record" (glob + thousands of file-opens + manual stitch).
- **Zarr** = one big N-D array (e.g. `temperature[profile, depth]`) physically diced into compressed
  CHUNKS, each chunk a separate object, plus small JSON metadata. The ARRAY is the unit; files are
  hidden. Query = slice the array; the library fetches only the chunks covering the slice.
  `xr.open_zarr(...)` is near-instant (reads only metadata); data loads **lazily** on compute. This
  is why the "pull 15 GB" problem vanishes — a reader slices and only those bytes travel.
- Two knobs that matter: **chunking** (chunk shape = the main perf lever, like RAG chunk size — chunk
  along the dimension most queries range over) and **lazy loading** (open ≠ load).
- xarray writes/reads Zarr natively (`ds.to_zarr(...)`), so tooling is a small change.

**The hard part = regularizing ragged profiles** (each profile has different depth samples, but a
Zarr array is a rectangle). Options: (A) interpolate every profile onto a COMMON DEPTH GRID (clean
regular cube, ML-friendly; COST = resamples, no longer raw values); (B) pad to longest profile
(preserves values, wastes space, depth axis becomes a meaningless index); (C) CF ragged-array
encoding (fidelity + standards, more complex). **DECISION (leaning, 2026-09): Option A** — a common
depth grid — since MLD/ML/cross-record work wants gridded profiles anyway; **keep the NetCDF shards
as the fidelity-preserving archive** and add the Zarr cube as the analysis-ready ARCO product (with
CF/ACDD attrs written at build time, per G3). Be explicit that Option A resamples (a QC decision).

**S3 object count:** Zarr yields FAR FEWER objects than shards (a knob, not fixed): count ≈ (chunks
per array × #arrays) + a little metadata. E.g. ~22k profiles chunked in ~1000-profile blocks ≈ ~22
chunks/array × ~11 sensors ≈ hundreds of objects vs ~150,000 shards — 2–3 orders of magnitude fewer.
Inversely proportional to chunk size (tiny chunks → many objects; large → few but over-fetch per
query). Consolidated metadata (xarray default on write) collapses per-array metadata into ONE object,
so open is a single small read. Fewer/larger objects also cuts S3 per-request costs on top of egress.

### G2 — Trust layer: uncertainty + queryable provenance + first-class QC
**Gap:** pp05 encodes inclusion but not uncertainty; provenance lives in filenames/docs, not a
queryable per-observation lineage; QARTOD flags aren't first-class in the products. **Target:**
carry per-observation/per-profile QC state, processing lineage, and quantified uncertainty *in the
data products* (Zarr attrs / companion tables), not just in prose. Fold QARTOD flags through the
pipeline. SignoffQC discard decisions become part of this trust record (→ pp07).

### G3 — Standardized, interoperable metadata  [SINGLE BIGGEST GAP per MOAR]
**Gap:** metadata is coherent within argosy but not in community conventions. **Target:** express
products with **CF conventions** (units, standard_names), **ACDD** (discovery attrs), and **STAC**
(catalog/collection items for the S3 assets) so other tools/agents consume argosy data without
bespoke glue. This is what turns "private practice" into "infrastructure." Pairs naturally with the
Zarr work (set the attrs correctly at write time).

### G4 — Knowledge corpus / retrieval layer (Block 4 seed)
**Gap:** no RAG corpus yet — but the docset is unusually good, so argosy is well-positioned to
BECOME one. **Target:** a retrieval-grounded (RAG) assistant that answers questions about the
project + OOI/RCA with CITATIONS, over a locally-built index. A natural Phase-3 pilot; low effort,
high leverage (also a proof-of-concept for MOAR Block 4). Weekend-scale PoC.

**How RAG works here (so the split below is clear):** to be searchable, each source's TEXT must be
fetched, split into chunks, embedded (chunk → vector), and stored in a vector index with the chunk
text + metadata (source, URL/citation, fetch date). Retrieval = embed the question, pull the
nearest chunks, hand them to the LLM to answer WITH citations. "By reference" (URL only) is NOT
enough — the text must be copied in to be embedded. So every source is *copied and ingested*, and
the index physically contains source text.

**The corpus = THREE constituent sources:**
1. **argosy's own docs** (`*.md` + `references.bib`) — authored here, in the repo. Freely
   shareable; a fresh clone already has them. This half regenerates for free.
2. **OOI/RCA online documentation** — web pages (oceanobservatories.org, interactiveoceans /
   UW APL, instrument-series pages, etc.), *scraped into local text snapshots*. Store the source
   URL + fetch date as metadata so answers cite the live page. Snapshots go STALE → re-scrape
   periodically. Mostly OOI/UW public content (likely shareable, but check each site's terms);
   regenerable by anyone from the public URLs in the build recipe.
3. **Scientific papers** (PDFs) — under copyright. Text is embedded into the index (so the index
   contains copyrighted text) and the PDFs themselves cannot be redistributed. Each reuser must
   supply their own copies. This is the ONE genuine speed bump for Angus/Chuck; copyright forces it.

**Storage (cross-site → top-level, NOT under `<site>/`; per "no generated data in the repo"):**
```
~/ooi/corpus/
    papers/     source PDFs (copyright — private, not redistributed)
    webdocs/    scraped OOI/RCA web-doc text snapshots (+ URL + fetch date)
    index/      the vector store (embeddings + chunk text + metadata)
```
The build RECIPE + the argosy-doc half live in the repo (public); the built `index/`, scraped
`webdocs/`, and `papers/` stay LOCAL/PRIVATE. Do NOT publish the index (it embeds copyrighted paper
text — same class of issue as the children's-lit RAG). If ever served, serve cite-grounded ANSWERS,
not the raw index.

**Index characteristics:** small — a few thousand chunks; each vector ~384–1536 float32 (~1.5–6 KB)
plus chunk text; **tens of MB total**, growing linearly (still tens-to-hundreds of MB even with
papers). Format depends on the store (Chroma/LanceDB = a local dir; FAISS = binary index + text
sidecar). Data = float vectors + text strings + small JSON metadata.

**Use scenarios:** Chuck — "how does pp06 Filter 1 work and what paper justifies it?" → cites
PostProcessing.md + Briggs 2011. Angus (Neversee) — "how were the MLD labels made / what's the
benchmark?" → cites VisQC.md + Holte & Talley 2009. Author — "what did I decide about Zarr
chunking?" → cites BR.md. (Arthur the casual reader is served by the Book, not the RAG.)

### G5 — Standardized human-label schema + benchmark protocol
**Gap:** SignoffQC and MLD labeling are the right idea but ad hoc — no standard label schema,
inter-annotator provenance, or benchmark protocol. **Target:** a documented label schema (who,
when, what, confidence), versioned label sets, and a train/test/benchmark protocol. The MLD
labeled-set + Holte&Talley benchmark is the first instance; generalize it (VisQC clines, SignoffQC
sensor discards). This makes the Phase-2 template reusable.

### G6 — Beyond single-team (governance/standards)  [PROPOSAL-SCOPE, not code]
**Gap:** AI-readiness is partly a standards/governance problem a one-team repo can't confer.
**Target:** this is the MOAR proposal's job — not an argosy code task, but noted so the roadmap is
honest about what argosy CAN'T fix alone. argosy's job is to be the demonstrated pattern (G1–G5);
the proposal turns the pattern into facility-scale standards.

### Sequencing (leverage × dependency)
1. **G1 (Zarr)** first — unblocks the explorer AND is the ARCO foundation; G2/G3 attrs ride on it.
2. **G3 (CF/ACDD/STAC)** with G1 — set standard metadata at Zarr write time (do together).
3. **G2 (trust layer)** next — uncertainty/provenance/QARTOD into the Zarr products + pp07.
4. **G5 (label schema/benchmark)** alongside the MLD Phase-2 work (already in motion).
5. **G4 (RAG corpus)** as a Phase-3 pilot once products stabilize.
6. **G6** is the proposal, ongoing.


## Plume: quantify PO.DAAC/satellite SST vs top-of-profile SP temperature

**Current state (verified Sep 2026):** the SST↔SP-surface comparison exists but is VISUAL ONLY —
`plume/surface_plot.py` Panel 3 overlays profiler `temp_mean` (shallowest-10-point mean from
`surface_extract.py`, on pp06) against satellite SST (from `fetch_sst.py`). No quantitative fit.
**Also:** the "SST" is actually **NOAA Coral Reef Watch** (`noaacrwsstDaily` via CoastWatch
ERDDAP), NOT literally PO.DAAC — reconcile the "NASA PO.DAAC SST" wording in DeveloperGuide/MOAR.
And the plume fetchers hardcode `slopebase` + sb lat/lon (same stale-naming pattern fixed elsewhere).

**To do:**
- Add a QUANTITATIVE SST-vs-SP-surface analysis: time-align satellite SST with per-profile surface
  temp, compute correlation / RMSE / bias (and seasonal breakdown), to substantiate the MOAR claim
  "SST tracks SP surface well" (currently flagged as an unverified project observation).
- Reconcile provider wording (NOAA CRW vs PO.DAAC) across code + docs.
- Generalize plume fetchers to the 2-letter site code + per-site lat/lon (retire `slopebase`).
- (Ties to G3: this cross-comparison is exactly what standardized metadata + a satellite "external"
  product should make routine rather than bespoke.)


## Design topic: potential density (σ₀) as a derived data value

Add **potential density** (σθ / σ₀) as a first-class derived product, analogous to how `density`
(in-situ) is already a derived variable. Physics note: in-situ `density` is derived from
temperature + salinity + **pressure/depth** (includes compression by overlying pressure);
**potential density removes the pressure effect** (density a parcel would have if moved adiabatically
to a reference pressure, usually the surface). σ₀ is the better variable for stratification, water
masses, and MLD because it compares parcels on equal footing — directly relevant to the MLD work,
the cline/VisQC work, and the water-mass-intrusion science hook.

Already PROVEN in-project: `VisQCInspector.py` → `compute_potential_density()` computes σ₀ via
TEOS-10 (`gsw.sigma0` from S + in-situ T + pressure, with nominal site lat/lon). So this is
PRODUCTIZING an existing calculation, not new science.

**Two implementation modes to evaluate (the decision):**
- **Static (precomputed):** compute σ₀ once during post-processing and store it as its own product
  (a `potentialdensity` shard, or — better under G1 — a variable in the Zarr cube). Pro: computed
  once, consistent, directly queryable/plottable, no per-read cost, feeds ML as a ready feature.
  Con: another product to build/version; must be recomputed if S/T QC changes.
- **On-the-fly:** compute σ₀ at read time from the S + T (+ depth→pressure) shards/arrays. Pro: no
  storage, always consistent with current S/T. Con: recomputed on every read; requires S and T to be
  co-located and depth-aligned at query time (the interpolation SignoffQC already does).

**Leaning:** since G1 moves toward a regular Zarr cube on a common depth grid (where S, T, depth are
already aligned), σ₀ becomes cheap to add as a **precomputed variable in the cube** — the static
option, essentially free once the cube exists, and the cleanest for ML + agents. On-the-fly remains
the right choice for the interactive tools (VisQCInspector already does it). So likely BOTH: static
in the ARCO product, on-the-fly in interactive GUIs. Requires `gsw` (already in the argosy env).
Ties to G1 (Zarr cube), G2 (record its provenance/derivation), G3 (CF standard_name
`sea_water_potential_density`).


## Analysis topic: harmonizing data to scale water-mass emplacement anomalies

Emerging motivation: the SP appears to be observing water-mass EMPLACEMENT (e.g. a high-salinity
signal persisting ~2 months at ab). Goal: harmonize available data to give these anomalies a
spatial/dynamical scale and a fuller narrative, not just a time signature. Two sub-topics.

### A. PO.DAAC/satellite SST 2D heatmap time-series movie (eddy structure)
Extend the current POINT SST fetch (`plume/fetch_sst.py`, single lat/lon) to a REGIONAL BOX fetch
(`SST[time, lat, lon]`) — the ERDDAP griddap box-query form already appears in `ColumbiaPlumePlan.md`
(`[(42):(49)][(-130):(-122)]`). Animate frames over time (reuse `vis/bundle_animate.py` machinery)
to SEE a mesoscale feature approach/pass a SP site, then check whether top-of-profile temperature
registers it at the matching time — turning "2-month anomaly" into "here is the feature responsible."
- Caveats: NOAA CRW ~5 km resolves mesoscale eddies (tens of km) but NOT submesoscale filaments;
  IR SST has cloud gaps (analysed products gap-fill/smooth); SST is surface-only (corroborates
  top-of-profile T, says nothing direct about the subsurface salinity lens).
- Upgrade path if eddies become central: sea-surface-height / geostrophic velocity (AVISO/Copernicus)
  detects eddies DIRECTLY (closed SSH contours + rotation) — a stronger eddy detector than SST.

### B. Synthesize current(depth) V from SP velocity + platform ADCP; anomaly scale S = V·T
Combine the SP science-pod point velocity (VELPT-class; current at the pod's instantaneous
depth/time as it profiles — NOT a clean instantaneous V(depth)) with the 200 m platform ADCP
(profiles current across depths at fixed time — the real V(depth) workhorse) into a fused
current(depth) field. VERIFY from the sensor inventory: one ADCP or two, their range/orientation
(upward-looking coverage of the upper column?) — determines depth coverage.
- Fusion approach: ADCP as primary V(depth); SP point velocity as co-located check / gap-filler where
  the profiler passes through ADCP range. Put both on a common depth grid + time base, reconcile
  disagreement, quantify uncertainty. This is a small research task, not a one-off script.
- **S = V·T** = advective length-scale of an anomaly (Taylor "frozen-field" hypothesis: feature
  advected past a fixed sensor ≈ unchanged, so duration-at-point × advection-speed ≈ spatial extent).
  Legitimate first-order estimate. Cautions: assumes advection not in-place evolution (2 months is
  long — treat S as ORDER-OF-MAGNITUDE, not precise); use the depth-appropriate current and the
  component ACROSS the site (advection), so V is V(depth) projected, not a scalar speed.
- **Turbulence-layer bonus (strong, novel thread):** ADCP-derived shear (∂V/∂z) or backscatter can
  flag depth layers of likely turbulent mixing; correlate those with profile SEGMENTS of high sensor
  noise (salinity/DO erratics). Would give a PHYSICAL explanation for QC anomalies instead of just
  flagging them → turbulence-flagged layers become a QC covariate. Connects directly to G2 (trust
  layer) and the SignoffQC / erratic-filter work.

These are Phase-2 analysis threads (Book-facing), feeding the water-mass-intrusion science hook in
`MakingOOIAIReady.md`. Both give the intrusion narrative a physical scale — the "harmonize all the
data" goal.
