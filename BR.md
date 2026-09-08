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
side). Genuinely ad-hoc → Option 1/2 (Lambda + S3 byte-range). PARKED for decision.


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
7. [OPEN] Descent-data recovery: on-demand (Lambda + S3 byte-range) vs bulk (shard.py descent pass
   on the ephemeral box). Plus the shard-name direction-token decision. See "Descent-data recovery".
8. [OPEN] **Which data products should be free to download from S3, and how bundled?** Currently
   ONLY pp06 is public (all 3 sites, `<site>/postproc/pp06/*`, ~46 GB total). Candidates for future
   public release: pp07 (once defined), the per-profile cline/N²/MLD metadata, noon/midnight subsets
   (pp01/pp02), tidal_constituents.json, etc. Open: what belongs in the public set, and should
   related products be BUNDLED (e.g. a single downloadable release / Zenodo archive) rather than
   loose prefixes? Egress is owner-billed, so scope deliberately. Steering rule now requires ASKING
   the human before making any new dataset public.

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
