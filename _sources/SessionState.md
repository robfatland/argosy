# Session State

## Last updated
2026-09-06 (session 2) — Resumed the live oo EC2 run. Diagnosed why the first full pipeline pass
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

## LIVE EC2 STATE (read this first next session)
- Instance `i-0a018916cfb9a8e46` (us-west-2, acct 879605964811). Connect:
  `aws ssm start-session --target i-0a018916cfb9a8e46` (keyless SSM; plugin installed on localhost).
- **BILLING METER IS RUNNING.** c6i.xlarge on-demand. Must `cdk destroy` when the run + S3 verify
  are done (from `~/argosy/cloud`, `argosy-cdk` conda env). Confirm no orphaned EBS after destroy.
- Box layout: 8 GB AMI root (nvme0n1, was the trap) + 1 TB `/dev/nvme1n1` xfs mounted at `/data`;
  `~/ooi -> /data/ooi` symlink so all pipeline output lands on the 1 TB. Minimal conda env `argosy`
  (python 3.11 xarray netcdf4 pandas numpy scipy requests beautifulsoup4 boto3 awscli) — NOT the
  full environment.yml (won't fit / not needed). conda ToS accepted for pkgs/main + pkgs/r.
- **Download stage: DONE** (raw OOINET NetCDF landed under `~/ooi/oo/ooinet/scalar/<yyyy>_<inst>/`
  on the 1 TB volume — the expensive-to-reproduce asset; do NOT destroy the box until shard+pp+sync
  succeed). **Shard stage: RUNNING** as of session end (launched
  `nohup bash pipeline/run_pipeline.sh oo shard > ~/ooi/oo_shard_<ts>.log 2>&1 &`), writing shards
  correctly after the profileIndices fix.
- **Reconnect procedure (now also in steering recipe 4b):** `aws ssm start-session --target
  i-0a018916cfb9a8e46` lands you as `ssm-user`; you MUST `sudo su - ec2-user` (repo/logs/~/ooi are
  ec2-user's). Non-invasive status = read the redux tree, NOT the log (log is block-buffered through
  tee → looks frozen). Use the shard-status snippet in recipe 4b, or:
  `find ~/ooi/oo/redux -name '*.nc' | wc -l` (should climb). For live logs on the NEXT stages set
  `export PYTHONUNBUFFERED=1` before launching.
- **Resume check next session:** re-attach, `sudo su - ec2-user`, confirm shard finished (proc gone +
  final `attempted=/written=/skipped=` block has NONZERO written). Then run `pp` then `sync`:
  `export PYTHONUNBUFFERED=1 ARGOSY_SITE=oo; cd ~/argosy;`
  `nohup bash pipeline/run_pipeline.sh oo pp   > ~/ooi/oo_pp_$(date +%Y%m%dT%H%M%S).log 2>&1 &`
  then `... oo sync ...`. Watch the DOFST-vs-CTDPF question (expectation: DO rides inside CTDPF as
  `corrected_dissolved_oxygen`, no separate DOFST download). Verify `s3://s3ooi/oo/`, THEN `cdk destroy`.
- The 5 oo async URLs (in download_link_list.txt, now on GitHub) are OOINET async-result links
  dated 20260905 tied to kilroy1618@gmail.com — they EXPIRE in ~2 weeks. Re-order if the run
  needs a rerun after that.

## Answered this session (design note)
- run_pipeline.sh emits **no PNG** and does not merge overlapping-time files into one series.
  Sharding SPLITS source files into per-profile shards; time-overlap redundancy is absorbed via
  idempotent per-profile shard naming (shows up as the `skipped=` count). Any consolidated
  coverage/curtain PNG is a separate future viz step (proposed `pipeline/coverage_plot.py`, Agg
  backend -> ~/ooi/oo/visualizations/); NOT yet built. User expressed interest.

## Completed this session (session 2)
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
- **#1 (time/cost sensitive): finish the live EC2 oo run.** Re-attach SSM to
  `i-0a018916cfb9a8e46`, `sudo su - ec2-user`, confirm the SHARD stage finished (proc gone + final
  `written>0`), then run `pp` then `sync` (commands in LIVE EC2 STATE above), verify `s3://s3ooi/oo/`,
  then **`cdk destroy`** (billing meter running) and confirm no orphaned EBS. Download is already
  DONE; do not re-run it.
- **#2: commit/push the WSL-side edits from session 2** (so `ab` + the book benefit): `run_pipeline.sh`
  (profileIndices pull/guard), `.kiro/steering/operational-recipes.md` (recipe 4b), `references.bib`,
  `_toc.yml` (bibliography page), `ColumbiaPlumePlan.md`, `ArgosyOverview.md`. Commit from WSL side.
  Then publish the book (`jupyter-book build .` ; `ghp-import -n -p -f _build/html`) to surface the
  new Bibliography page.
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
