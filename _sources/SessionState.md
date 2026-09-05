# Session State

## Last updated
2026-09-05 — Metadata folder sorted into 7 self-documenting subfolders (qc/profiles/features/annotations/external/cache/scans). Earlier: per-site filesystem restructure COMPLETE.

## Completed this session
- **Metadata subfolder sort**: `~/ooi/sb/metadata/` reorganized into `qc/ profiles/ features/
  annotations/ external/ cache/ scans/`, each with a README (per new steering guideline).
  Files moved without renaming. `ooipaths.metadata_dir(site, sub)` + `METADATA_SUBDIRS` added;
  producer/consumer scripts updated (incl. converting plume/*.py + iw/*.py to ooipaths). All
  accessors verified against relocated files. VisQC completion logged as Pending To Do.
  New steering rule added: create a README when making a subfolder for existing files.
- **PostProcessing.md restructure**: merged duplicate "QC Filter" sections; rehomed orphaned
  pp01/pp02 depth-histogram block; reordered into pipeline-logical flow. Now 363 lines
  (under 400-line convention).
- **HSD acronym typo fixed** ("HDS" → "HSD", and wrong expansion "High Data-density Sampling"
  → "High Sample Density"): `postprocess_pp06.py` (docstring + `HSD_SENSORS`/`hsd_manifest`
  identifiers, recompiles clean), `DevelopmentLog.md`, `SpectralGraphAnalysis.md`, `CodeManifest.md`.
- **Confirmed no HSD fix needed in notebooks**: scanned all `chapters/*.ipynb` cell sources;
  the "HDS" grep hits were base64 image-output blobs, not editable text. Nothing pending.
- **Script-name/cross-reference audit**: no drift. All pp05/pp06 scripts + `PP05_QCAnalysis.md`
  exist and match the doc.
- **DataOps.md created**: split S3 sync/backup + localhost WSL vhdx disk management out of
  PostProcessing.md. Cross-refs wired in ArgosyOverview.md (pointers, companion index, pandoc
  list) and CodeManifest.md. Fixed a pre-existing duplicate/corrupted S3-backup pointer in
  ArgosyOverview.md.
- **Filesystem restructure Step 1 DONE**: canonicalized site codes (verified vs OOI):
  `sb`=Oregon Slope Base (RS01SBPS/SF01A, RCA), `oo`=Oregon Offshore (CE04OSPS/SF01B, Endurance),
  `ab`=Axial Base (RS03AXPS/SF03A, RCA). All three share identical 15-sensor layout. Recorded
  a Sites table in PostProcessing.md recap + the full ordered restructure plan in
  DevelopmentLog.md "Next". Resolved PostProcessing.md open-topic item 1.

## In progress / partially done
- **Filesystem restructure: COMPLETE.** All data under `~/ooi/<site>/` (currently just `sb`),
  S3 mirrors it (`s3://s3ooi/sb/...`; `ooinet/` kept legacy keys), bucket policy public-read on
  `sb/redux/*`+`sb/postproc/*` (verified). All code uses `ooipaths.py`; all docs updated. Full
  record in DevelopmentLog.md "Next" -> "Filesystem restructure" (RESTRUCTURE COMPLETE).
  Key gotcha for future: generated files with absolute paths (e.g. pp05 manifest) need
  path-patching after any data move. `ooipaths.py` created + verified; 23 scripts
  converted to use it (compile clean; pp06 dry-run + SGA module1 ran on real data). Notebook
  edits for DataDownload + DataSharding handed to user as cell-by-cell instructions — **user
  still needs to apply these** (see the assistant message with the edit list, or re-derive:
  swap `~/ooi/...` paths for `op.*` accessors, add the sys.path.insert preamble).
  **NEXT = Step 4** (the reversibility checkpoint): flip `ooipaths.py` to the per-site layout,
  then move local data (`mv`) + re-key S3 + update bucket policy — hand user copy-paste commands.
  Then Step 5 docs. Full plan + STEP-4 FLIP CONCERNS list in DevelopmentLog.md "Next" →
  "Filesystem restructure".
  Discoveries logged: pp01/02 have an extra `redux/` nesting level vs pp06 (Step 4 unifies);
  profileIndices already multi-site by OOI designator.
- SGA synthetic validation dataset not yet created (see Testing.md).
- InternalWaves.ipynb: scaffolding only, detection module not yet written.
- WSL vhdx compaction: fstrim done (prior session), diskpart step still pending.

## Reverted / needs redo
- Nothing currently reverted.
- Old `vis/bundle_animation.py` can be deleted (superseded by `vis/bundle_animate.py`).

## Blocked / waiting on user
- **S3 re-key + bucket policy** (Step 4 Phase C, local side done): user will run when internet is
  stable. Agent to reiterate the `_s3rekey.sh` script + policy update commands on request.
- **Cloud batch sharding = PLAN OF RECORD** (see DevelopmentLog "Next"): raw→S3 directly, ephemeral
  batch compute shards/postprocs in-cloud, download only ~20GB results. HARD REQ: incremental/
  restartable ingest (shard only new source; stochastic top-ups for missing sensors/years/vector).
  Not built yet; prerequisite is finishing the restructure.
- Three-sites table + metadata inventory (items above) need user input / a folder listing.
- Compact WSL vhdx (requires closing Kiro, running diskpart as admin).
- Isabella: provide download instructions for pp06 from S3.
- Decision-tree / random-forest work: user is in learning mode, no implementation requested yet.
  Candidate first project when ready: regression predicting one scalar sensor (e.g. dissolved
  oxygen) from others (T/S/depth), honest train/test split by profile or time.

## Next action
- Restructure + metadata sort done. Open threads to pick from: (a) complete the VisQC workflow
  (Pending To Do — output writer + Corrector + thickness reconciliation); (b) cloud batch
  sharding scaffold (plan of record, prerequisite now satisfied); (c) StubWork.ipynb path
  cleanup (Open Topics). No blocking items.
