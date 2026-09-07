# Session State

## Last updated
2026-09-07 (session 3) — **oo Phase 1 COMPLETE and verified in S3; EC2 box DESTROYED (meter off).**
Drove the oo run from shard through pp through sync on the disposable box, fixing FOUR more latent
bugs along the way (all pre-restructure leftovers, now committed + pushed so `ab` won't hit them):
(1) pp05 + special_profiles globbed `redux<yyyy>` year dirs but the per-site layout uses `<yyyy>` →
`years[0]` IndexError / zero years — fixed to glob `[0-9][0-9][0-9][0-9]`. (2) pp06_filter2/filter3
same stale `redux*` glob on postproc/pp06 → fixed. (3) pp06 had a HARDCODED pre-restructure manifest
path `~/ooi/metadata/pp05_manifest.csv` (committed HEAD was the OLD file; local ooipaths fix was
never committed) → now `op.pp05_manifest(SITE)`. (4) pp06 Filter 1 applied the salinity keep-mask via
`isel(obs=...)`, assuming obs len == salinity len → `Boolean index has wrong length` on many oo
shards; fixed to index the variable's OWN dim + guard salinity/density length mismatch. Also hit a
`[Errno 13] Permission denied` on pp06/2019 caused by running TWO pp jobs at once (one created dirs
the other couldn't write) — killed both, `sudo chown -R ec2-user:ec2-user ~/ooi/oo/postproc`, reran
single job. Final verified counts: pp06 132056 .nc (S3 == local), redux 157854 .nc (S3 == local).
**Flag: pco2 produced ZERO shards/manifest entries for oo** — source not downloaded/recognized;
revisit when ordering the next site's data. EC2 auth = IAM instance role (no keys); keyless SSM.

## Session 2 (2026-09-06)
Resumed the live oo EC2 run. Diagnosed why the first full pipeline pass
produced NOTHING despite a "pipeline done" banner: sharding reported `attempted=0` because
`~/ooi/oo/profileIndices/` was EMPTY on the box (the CE04OSPS_profiles_*.csv are hand-maintained,
live outside the download AND outside git's data tree, so the fresh clone lacked them → pp05 then
crashed on `years[0]` IndexError). FIX: user pushed the 13 oo profileIndices to
`s3://s3ooi/oo/profileIndices/`, pulled them onto the box, re-ran `shard` — now writing shards
correctly (990+ and climbing, correct RCA_oo_sp_* names). Hardened `run_pipeline.sh`: download
stage now pulls profileIndices from S3 + warns if absent; shard stage guards the same. Added
steering recipe 4b (reconnect/monitor). Also: cleared sb local redux (S3-verified complete) to
reclaim vhdx, left an empty dir + self-doc README as a Phase-1 marker. Added Nash & Moum 2005 to
references.bib + ColumbiaPlumePlan.md; fixed the bibliography (added `reference/bibliography` to
_toc.yml — it was missing, so ALL {cite} refs had nothing to resolve against); verified via build.

## Previous session (1)
Deployed disposable EC2 (CDK) and LAUNCHED the full oo Phase 1 pipeline. Fixed two classes of
blocker: (1) CDK attached the 1 TB EBS as a SECOND disk instead of root — worked around live
(formatted/mounted nvme1n1 at /data, symlinked ~/ooi -> /data/ooi) AND fixed the CDK stack
(device_name /dev/sda1 -> /dev/xvda); (2) ooipaths.py + pipeline/* + the 5 oo download URLs were
UNTRACKED in git so the EC2 clone lacked them — committed + pushed (added .gitattributes pinning LF).

## EC2 STATE: NO LIVE BOX (destroyed session 3, meter off)
- `ArgosyPipelineStack` destroyed via `cdk destroy` (from `~/argosy/cloud`, `argosy-cdk` env).
  Instance `i-0a018916cfb9a8e46` + its 1 TB volume gone. TODO: eyeball the EC2 console once to
  confirm no orphaned EBS (stack-managed volume should be deleted).
- Reusable box facts for the next deploy: c6i.xlarge, us-west-2, acct 879605964811, keyless SSM
  (`aws ssm start-session --target <id>` → lands as ssm-user → `sudo su - ec2-user`). EC2 auth is
  the IAM instance role (S3 access to s3ooi; no keys on disk). Minimal conda env `argosy` via
  user-data. Full create/run/destroy in steering recipe 4; reconnect/monitor in recipe 4b.
- CDK EBS gotcha from session 1 (verify it's actually fixed before trusting a fresh box): the stack
  was fixed to attach the big volume as ROOT (`device_name /dev/xvda`), replacing the session-1 live
  workaround (format nvme1n1 → /data, symlink ~/ooi). If a fresh box again shows ~/ooi tiny, re-apply
  the workaround and re-check the stack.

## NEXT SITE = ab (Axial Base) — FRONT-LOADED bring-up checklist (do IN ORDER, before `cdk deploy`)
ab designator = **RS03AXPS** (profile-index files are `RS03AXPS_profiles_<yyyy>.csv`). ab is NOT set
up locally yet (`~/ooi/ab/` does not exist). The profileIndices step MUST come first — it's the exact
thing that made oo silently produce `attempted=0`. Steps, all from WSL:

  1. [DONE] **profileIndices** — the 13 `RS03AXPS_profiles_2014..2026.csv` already existed in
     `~/ooi/sb/profileIndices/` (GitHub clone dropped all sites there); copied to
     `~/ooi/ab/profileIndices/` and pushed to `s3://s3ooi/ab/profileIndices/`. **AB start of
     operations = 03-DEC-2014** (first profile 2014-12-03 23:11:00; 2014 has 47 profiles, real
     volume from 2015). Use OOINET order start `2014-12-01 00:00:00.0`.
  2. [DONE] `~/ooi/ab/` skeleton created (mirrors oo: ooinet/{scalar,vector}, redux, postproc,
     analysis, visualizations, metadata/{qc,profiles,features,annotations,external,cache,scans},
     profileIndices). ooipaths verified resolving all ab paths (designator RS03AXPS).
  3. [IN PROGRESS — user ordering now] Order ab scalar data from OOINET: node **SF03A**, designator
     **RS03AXPS**, Stream type=Science, Include Provenance + Annotations, start `2014-12-01 00:00:00.0`.
     INCLUDE **PCO2W** (pco2 is listed for ab; it was MISSING for oo — verify it yields shards after
     the run). Put the async "order ready" URLs (one per line) into the ab URL list
     (`pipeline/ab_url_list.txt` OR `~/argosy/download_link_list.txt`); URLs expire ~2 weeks.
     **When URLs are in place, the NEXT action is step 4 (git commit-sweep) — user asked to be
     reminded.** Commit-sweep detail: `.gitignore` was updated (added `cloud/cdk.out/`); still need
     to `git rm -r --cached __pycache__ chapters/.ipynb_checkpoints`, then `git add -A`, verify no
     _build//cdk.out//.pyc staged, commit + push, confirm `working tree clean`. Judgment calls:
     stray root PNGs (ctd_coverage.png, ctd_minimum_cover.png) and cloud/cdk.context.json.
  4. **git commit-sweep FIRST** (see Blocked): the working tree has a big pile of uncommitted changes
     (ooipaths conversion across many scripts, cloud/, poster/, DeveloperGuide.md, steering, the 4 pp
     fixes were pushed individually but verify `git status` is clean) — a fresh box clones HEAD, so
     anything uncommitted is invisible to it. This is what bit us repeatedly with oo.
  5. `conda activate argosy-cdk; cd ~/argosy/cloud; cdk deploy` → connect → `sudo su - ec2-user` →
     `export PYTHONUNBUFFERED=1 ARGOSY_SITE=ab; nohup bash pipeline/run_pipeline.sh ab all > ...log 2>&1 &`
     Monitor per recipe 4b. shard success = `written>0` all sensors; verify S3; `cdk destroy`.

## Answered this session (design note)
- run_pipeline.sh emits **no PNG** and does not merge overlapping-time files into one series.
  Sharding SPLITS source files into per-profile shards; time-overlap redundancy is absorbed via
  idempotent per-profile shard naming (shows up as the `skipped=` count). Any consolidated
  coverage/curtain PNG is a separate future viz step (proposed `pipeline/coverage_plot.py`, Agg
  backend -> ~/ooi/oo/visualizations/); NOT yet built. User expressed interest.

## Completed this session (session 3)
- **oo Phase 1 COMPLETE**: shard (all sensors written>0 except pco2=0) → pp05 (243905-entry manifest)
  → pp06 (132056 shards, Errors:0) → filter2 (Sav-Gol cdom/chlora) → filter3 (backscatter despike,
  16942 files) → `aws s3 sync` to s3://s3ooi/oo/. Verified S3==local: pp06 132056, redux 157854.
- **Four pp bugs fixed + pushed** (all pre-restructure leftovers; see header for detail):
  pp05/special_profiles year glob, filter2/filter3 year glob, pp06 hardcoded manifest path, pp06
  Filter 1 wrong-dim boolean mask. Each committed individually and pulled onto the box.
- **EC2 destroyed** (meter off). oo async URLs now spent; re-order if oo ever needs a rerun.
- **AB bring-up staged** (see the FRONT-LOADED checklist above) with profileIndices as step 1.

## Completed session 2 (2026-09-06)
- **Diagnosed + fixed the oo `attempted=0` shard failure** (empty profileIndices on the box, see
  header). One-time-per-site fix: push profileIndices to `s3://s3ooi/<site>/profileIndices/`.
- **Hardened `run_pipeline.sh`**: download stage now `aws s3 sync`s profileIndices down from S3
  before sharding and warns (with the exact push command) if the count is 0; shard stage has the
  same guard for standalone `shard` runs. This makes the `ab` bring-up automatic (no manual copy to
  forget). NOTE: committed/pushed from WSL side by user; steering + this change are WSL-side edits.
- **Steering recipe 4b added** (`operational-recipes.md`): reconnect-to & monitor-a-running-pipeline
  — the `sudo su - ec2-user` step + why, filesystem-based status snippet, rate/ETA one-liner,
  `PYTHONUNBUFFERED=1` fix for frozen logs, stage list + `written>0` success check, profileIndices
  requirement, verify + `cdk destroy` reminder.
- **sb local redux cleared**: dry-run `aws s3 sync ... --dryrun` confirmed `s3://s3ooi/sb/redux/`
  complete → `rm -rf` local sb redux to reclaim vhdx, then recreated empty + added a self-doc
  `~/ooi/sb/redux/README.md` (S3 canonical + restore cmd + Phase-1 lineage). pp06 KEPT.
- **pp07 dependency answered**: pp07/annotation reads `postproc/pp06`, NOT redux (matches
  pp06_filter2/filter3 pattern; VisQC.md frames pp07 as deferred). So clearing local redux does not
  block pp07. Only pp05/pp06/special_profiles rebuilds need redux back (re-pull from S3 if ever).
- **Bibliography fixed + Nash 2005 added**: `references.bib` was EMPTY and `reference/bibliography`
  was missing from `_toc.yml`, so ALL `{cite}` refs silently failed. Added `nash2005` BibTeX entry,
  added `- file: reference/bibliography` to _toc.yml Reference section, added inline cite to
  ColumbiaPlumePlan.md References. Verified with a build: cite renders + bib page lists it. Left a
  working `{cite}`nash2005`` example near the top of ArgosyOverview.md (user's request). NOTE: VS
  Code Preview never renders `{cite}` — only a jupyter-book build does.

## Completed previous session (session 1)
- **Cloud Phase 1 pipeline scaffold** (EC2 create/destroy). `pipeline/download.py` extracts the
  OOINET download logic from DataDownload.ipynb (no duplication; notebook+EC2 share it).
  `pipeline/run_pipeline.sh` = download→shard→pp06→sync-to-S3, honors `ARGOSY_SITE`.
  `ooipaths.DEFAULT_SITE` now reads `$ARGOSY_SITE` (whole-pipeline site switch). `cloud/` CDK
  (Python) app: on-demand EC2 (c6i.xlarge ~<$0.40/hr, 500GB gp3 deleted-on-destroy, S3 IAM role,
  SSH SG, miniconda user-data); `cdk deploy`/`cdk destroy`. All compiles; cdk synth deferred
  (aws-cdk not installed on localhost — user does CDK one-time setup). pipeline/ + cloud/ READMEs
  + steering recipe added.
  PENDING for user: install CDK toolchain + `cdk bootstrap`; apply DataDownload notebook-thinning
  edits; extract sharding to pipeline/shard.py (run_pipeline currently skips shard stage).
- **Multi-site (`oo`) enablement prep**: `~/ooi/oo/` skeleton created; 13 CE04OSPS profileIndices
  placed; ooipaths verified site-generic for oo (no guard; RCA_oo_sp_ shard token). Notebook audit
  found 2 hardcoded-sb fixes needed (shard filename in DataSharding; doc string in DataDownload) —
  logged as Pending To Do for user to apply. User is ordering oo scalar data (all 11 types) from OOINET.
- **AGU poster** (`poster/AGUPoster.html`): embedded real title (3-tier format), authors stub,
  session OS025, abstract 2097211, condensed abstract; panels remapped to the submitted abstract's
  narrative (baseline envelopes / self+inter coincidence / pycnocline finding / corroborated+open-science).
- **Docs reorg for personae + Phase 1/2 + republish** (details in DevelopmentLog Completed):
  DeveloperGuide.md created (absorbs retired Workflow.md); README.md rewritten (persona-framed,
  book+Abernathey links, START HERE, publish cmd kept in steering); ArgosyOverview got START HERE
  + persona fork; _toc.yml restructured (Orientation/Phase1/Phase2/Reference/Chapters, working
  docs excluded); intro.md reciprocal repo pointer; scaffolding deleted; indexes reconciled.
  Book rebuilt + published (34 cosmetic warnings). Fixed dangling `building-the-pdf` xref.
- **Earlier this run**: per-site filesystem restructure COMPLETE; metadata sorted into 7
  self-documenting subfolders; AGU poster scaffold; operational-recipes steering; Publishing.md.
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
- **#1: AB bring-up** — follow the FRONT-LOADED checklist above, IN ORDER. profileIndices to S3
  FIRST (step 1), then skeleton, then order OOINET data (include pco2!), then the git commit-sweep,
  then `cdk deploy` + `run_pipeline.sh ab all`. Rebuild-from-scratch is deliberate: it's the tested
  path and exercises the fresh-provision automation the disposable-box design is for.
- **#2: git commit-sweep** (blocker for a clean AB box AND for the book): the WSL working tree still
  has many uncommitted changes (ooipaths conversion across scripts, docs, cloud/, poster/,
  DeveloperGuide.md, operational-recipes.md steering, references.bib, _toc.yml, ArgosyOverview.md,
  ColumbiaPlumePlan.md). A fresh box clones HEAD, so uncommitted = invisible to it (this bit us 3×
  during oo). Commit + push from WSL. Then publish the book (`jupyter-book build .` ;
  `ghp-import -n -p -f _build/html`) to surface the new Bibliography page.
- Then (lower priority) open threads:
  (a) **AGU poster** — fill the scaffold (four theme figures, final title/authors/abstract, QR).
  (b) complete the **VisQC** workflow (output writer + Corrector + thickness reconciliation).
  (c) proposed `pipeline/coverage_plot.py` (consolidated overlap/coverage PNG — user asked about it).
  (d) get **ab** site to sb/oo's stage (multi-site expansion).
  (e) thin DataDownload.ipynb + DataSharding.ipynb to call pipeline/ modules (still pending).
  (f) cleanup backlog: OOIFAQ Google-Docs artifacts; StubWork.ipynb paths; notebook-TOC decisions.

## Lesson logged this session (git hygiene)
- Several pipeline-critical files (`ooipaths.py`, `pipeline/*`, the oo URLs in
  `download_link_list.txt`) were UNTRACKED locally, so the EC2 clone silently lacked them. When
  provisioning any fresh clone (EC2/CI/collaborator), first confirm needed files are committed +
  pushed: `git status --short --untracked-files=all`. Windows-side git has core.autocrlf=true;
  `.gitattributes` now pins LF for .sh/.py/.yml so bash scripts don't break on Linux.
- Committing/pushing from the Windows/PowerShell side fails (no git author identity there); do
  git commits from the WSL side where identity is configured.
