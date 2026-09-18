# Session State

## Last updated
2026-09-18 — **Collaborator (Chuck) MLD setup + env-sprawl topic filed.** Added a portable minimal
conda spec so Chuck can run `MLD.py`, committed the (previously untracked) `MLD.py`, reconciled the
MLD docs to "implemented", and filed the env-sprawl refactor as an Open Topic. `MLD.py` and
`PreSelectProfiles.py` are both built. Details below; earlier 2026-09-15 vis/slide narrative retained
further down.

## Completed this session (2026-09-18)
- **`environment-mld.yml`** created — portable minimal conda spec (`numpy, pandas, scipy, xarray,
  netcdf4, matplotlib, tk` on `python=3.11`, `conda-forge`) for running the MLD workflow on a
  collaborator's machine. Deliberately NOT the full `environment.yml` snapshot (exact build hashes,
  `prefix:`, hundreds of unrelated packages — torch/CUDA, qiskit, pymatgen, etc.). YAML validated.
- **Committed `MLD.py`** — it was untracked; the whole point is Chuck running it. Committed with
  `environment-mld.yml` as `5e388d5` ("MLD: add MLD.py annotator + portable environment-mld.yml ...").
- **Docs reconciled to reality**: `MLDAnnotationPlan.md` status flipped spec→implemented, who-code
  table fixed (`I`→`C`), added "Implementation status" + "Collaborator setup" (env + `python3-tk` +
  TkAgg-needs-display caveat). `mld_candidates/README.md` "MLD.py (planned)"→built. `CodeManifest.md`
  root table gained `PreSelectProfiles.py`, `MLD.py`, `environment.yml`, `environment-mld.yml`,
  `mld_candidates/`.
- **Open Topic filed** in `DevelopmentLog.md`: **miniconda environment sprawl** — one `argosy` env
  carrying hundreds of unrelated packages; refactor directions (purpose-scoped envs; curated
  portable yml + separate lock snapshot; import audit). Deliberate design first, no destructive
  `conda remove` yet.
- **Chuck setup instructions relayed** to the user (git pull → `conda env create -f
  environment-mld.yml` → `sudo apt install python3-tk` → `python MLD.py --site sb --who C`).

## Next action (2026-09-18)
- **Standing by for Chuck's result** running `MLD.py` (user is relaying instructions). Likely
  follow-ups: X-display/TkAgg issues on his WSL, or env-solve issues → tune `environment-mld.yml`.
- Then (deferred, user-driven): the env-sprawl refactor (see the new Open Topic) when there's appetite.

---

## (Earlier) Last updated
2026-09-15 — **Vis-notebook site switching + slide/deck fixups.** Made the three `vis/` tools
site-switchable via a shared `op.select_site()` prompt; fixed the Marp deck image + math directive;
documented the pp06 public-download path and the ARGOSY_SITE-at-launch gotcha. Details below;
the older AB/oo Phase 1 EC2 narrative is retained further down.

## Completed this session (2026-09-15)
- **`ooipaths.select_site(default=None, announce=None)`** added (after `shard_glob`): starts from
  `DEFAULT_SITE` (reads `ARGOSY_SITE`, else `sb`), prompts Enter=keep / 2-letter code to switch
  (case-insensitive), silent fallback to default on no-stdin (cloud JupyterHub) or bad entry,
  prints a confirmation line when `announce` is given.
- **All three `vis/` scripts now call it**: `bundle_chart.py` (`announce="Bundle chart"`),
  `curtain_plot.py` (`"Curtain plot"`), `bundle_animate.py` (`"Bundle animation"`), each replacing
  the old `SITE = op.DEFAULT_SITE`. Lets Chuck switch sites by re-running a cell — no kernel restart
  or `ARGOSY_SITE` export. Verified: py_compile + monkeypatched-input tests for sb and oo.
- **`Visualizations.ipynb`** intro cell: added a "Switching sites (sb/oo/ab)" note. JSON validated.
- **`ArgosyOverview.md`** Pointers: added a select_site pointer; fixed the stale curtain-plot pointer
  (`Vis.ipynb` → `chapters/Visualizations.ipynb`).
- **Marp deck (`slides.md`)**: added `math: katex` directive; fixed the broken title image
  (`tidal_height_may2026.png` did not exist) → copied `~/ooi/sb/visualizations/TidalSignal.png` to
  `images/TidalSignal.png` and pointed the slide at `images/TidalSignal.png`. Rendered clean via
  `marp slides.md -o slides.html` (marp only on PATH under an interactive login shell — nvm).
- **Steering**: filed the MLD "annotation problem" concept (high-priority Phase 1 thinking) and a
  Marp `math`-directive recommendation in `argosy-conventions.md`.

## Next action (2026-09-15)
- **MLD annotation workflow spec is COMPLETE in `MLDAnnotationPlan.md`** (two programs:
  `PreSelectProfiles.py` candidate sampling → `MLD.py` interactive TkAgg annotator). Key decisions:
  5-day blocks from each site's first GPI, all4→T-only fallback, seeded pick, empty blocks kept
  (N=0); label key = (gpi, sensor, who), per-who output files `mld_labels_<site>_<who>.csv`,
  `--site/--year/--who` switches (who default `C`=Chuck, no UI chooser), four filters (None, savgol,
  adaptive_savgol_std, adaptive_savgol_mad), continuous click depth + both raw/filtered values.
- **Now building `PreSelectProfiles.py`** (candidate lists feed the tool). Then `MLD.py`.

---

## (Earlier) Last updated
2026-09-07 (session 3, continued) — **AB Phase 1 pipeline LAUNCHED on a fresh EC2 box; DOWNLOAD
stage running.** Also: started the **Bicameral Redesign (BR)** deliberation phase (see `BR.md`),
did a full git commit-sweep (working tree now clean + pushed), reconciled orphan cleanup, and
enhanced the VisQC Inspector. Details in "LIVE EC2 STATE" and "Completed this session" below.

### AB run — COMPLETE + verified in S3; box being destroyed (2026-09-07)
- **AB Phase 1 DONE end-to-end with ZERO mid-run intervention** (contrast oo's 4 fixes) — validates
  the whole disposable-box automation on a fresh clone. Shard `written>0` for ALL 11 sensors
  INCLUDING **pco2 (5842)** — the oo gap is closed for AB. pp05 saw Redux years 2014-2026, pp06/
  filters clean, sync to `s3://s3ooi/ab/`. Verified S3==local: **pp06 152738**, **redux 186043**.
- Box destroyed via `cdk destroy` (argosy-cdk env). Residual-EBS check (WSL, no console needed):
  `aws ec2 describe-volumes --region us-west-2 --filters Name=status,Values=available --query
  "Volumes[].[VolumeId,Size,CreateTime]" --output table` (anything listed = unattached/orphan →
  `aws ec2 delete-volume --region us-west-2 --volume-id <id>`). Instance-gone check:
  `aws ec2 describe-instances --region us-west-2 --filters Name=instance-state-name,Values=running,stopped ...`.
- **All three sites (sb, oo, ab) are now through Phase 1 and mirrored to S3.**
- NOTE: SessionState previously carried the STALE oo instance id `i-0a018916cfb9a8e46` as a "connect"
  example — that box is destroyed; do NOT reuse it. Find a live box via describe-instances.

### AB run — (historical, now complete) launch notes
- Fresh box deployed via `cdk deploy` (new instance, us-west-2). git commit-sweep done FIRST this
  time (untracked `_build/`+`__pycache__`+`.ipynb_checkpoints`; committed all BR work) so the clone
  is complete. profileIndices verified in `s3://s3ooi/ab/profileIndices/` (13 RS03AXPS files) AND
  locally before launch.
- **Fresh-box gotcha hit + FIXED:** `~/ooi` did not exist on the new box, so the caller's log
  redirect failed and the first launch exited immediately. Confirmed the CDK root-volume fix HELD
  (single 1 TB `/dev/nvme0n1p1` root, 989 GB free — NOT the second-disk trap). Fix: `mkdir -p ~/ooi`
  then relaunched. PERMANENT FIX applied (uncommitted, laptop): added `mkdir -p /home/ec2-user/ooi`
  to `cloud/app.py` user-data AND `mkdir -p "$HOME/ooi" "$HOME/ooi/$SITE"` early in
  `pipeline/run_pipeline.sh`. Commit these before the NEXT box.
- Launched: `export PYTHONUNBUFFERED=1 ARGOSY_SITE=ab; cd ~/argosy; nohup bash
  pipeline/run_pipeline.sh ab all > ~/ooi/ab_pipeline_<ts>.log 2>&1 &`. Confirmed DOWNLOAD running
  (RS03AXPS-SF03A files routing to `<year>_par/` etc., ~file 44/166 on PAR at last check).
- **Resume:** reconnect SSM → `sudo su - ec2-user` → snapshot with
  `tail -30 "$(ls -t ~/ooi/ab_pipeline_*.log | head -1)"` (NOT tail -f). Watch: shard `written>0`
  for ALL sensors INCLUDING **pco2** this time (pco2 was zero for oo — AB order included PCO2W);
  pp05 "Redux years: 2014-2026"; run ONE job only (double-run caused the oo permission error).
  Then verify `s3://s3ooi/ab/`, then **`cdk destroy`** (meter running) + confirm no orphaned EBS.

## Session 3 earlier — oo Phase 1 COMPLETE and verified in S3; that EC2 box DESTROYED.
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

## EC2 REFERENCE (the oo box was destroyed; a NEW ab box is now LIVE — see "AB run" above)
- The oo box `i-0a018916cfb9a8e46` + its 1 TB volume were destroyed earlier. (Confirm no orphaned
  EBS in the console.) The CURRENT live box is the ab one from the later `cdk deploy`.
- The facts below (deploy/connect/env, EBS note) apply to any box, including the live ab one.
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

## Completed this session (session 3, continued — visqc tools built)
- **`visqc/SignoffQC.py`** — standalone scalar-data sign-off GUI (Phase 1, TkAgg). 4 charts (T/S/den;
  DO/CDOM/ChlorA; backscatter/nitrate/PAR; pH/pCO2), multi-axis auto-scaled. 11 tri-state sensor
  buttons Ok/Discard (None does nothing); LSD absence shown None(expected) off noon/midnight vs
  None(missing) on. Display toggles per trace. Advance/Back + Julian-day GoTo. GMT->local title with
  noon/midnight tag. Reads **pp06**. Output = ONE ROW PER GPI at
  `metadata/annotations/scalar_signoff_<site>_<year>.csv` (cols: gpi, visits, 11 sensor states);
  resume/merge (preserves prior Discards, increments visits). Feeds future pp07. Compiles clean.
  Run: `python ~/argosy/visqc/SignoffQC.py --site <sb|oo|ab> --year <yyyy>`.
- **`visqc/shard_source.py`** — Local/S3 `ShardSource` abstraction for the notebook bundle explorer
  (discovery: glob local vs s3fs list; open: local path vs s3fs). anon s3fs for public pp06; other
  sources over S3 need creds. Index cached per year. Compiles clean. NOT yet wired into
  bundle_chart / Visualizations.ipynb.
- Both recorded as design topics in `BR.md`. Decisions there: visqc/ folder, pp06 source, per-GPI
  row CSV, None(expected/missing), SignoffQC output is a pp07 input.

## Completed this session (session 3, continued — S3 access safety + budget)
- **S3 public policy reconciled + tightened**: live bucket policy was sb-only with redux + ALL pp
  levels public (and the repo JSON was stale `pp06/*`). Now: public read (GetObject+ListBucket) on
  **pp06 ONLY, all 3 sites** (`{sb,oo,ab}/postproc/pp06/*`). Applied + verified via put/get-bucket-
  policy. redux (more flawed than pp06), pp01/02/05, metadata, ooinet all PRIVATE now.
  `s3_public_read_policy.json` rewritten; `DataOps.md` fixed; steering rule "Public data sharing
  (S3)" added (ASK before exposing new datasets). Safety assessment recorded in BR open-Q 8:
  security surface demonstrably safe (read-only, scoped, non-sensitive); cost surface NOT bounded
  (public egress unbounded in principle; ~$4.14/full 3-site pull of ~46 GB).
- **Budget + kill switch** (cost guardrail): `cloud/budget.json` ($100/mo ACCOUNT cost budget) +
  `cloud/budget_notifications.json` (email at ACTUAL 50%/100% + FORECASTED 100%). $100 chosen to not
  false-trip on routine EC2 runs. **USER TODO to activate**: put email in budget_notifications.json,
  get acct id (`aws sts get-caller-identity --query Account --output text`), run `aws budgets
  create-budget --account-id <id> --budget file://cloud/budget.json --notifications-with-subscribers
  file://cloud/budget_notifications.json`, then CONFIRM the SNS email subscription. Subject line is
  AWS-generated (not customizable without a Lambda relay). Not real-time (updates a few times/day).
  Kill switch built + syntax-checked: `cloud/s3_public_off.sh` (delete bucket policy → all public
  access OFF) and `cloud/s3_public_on.sh` (re-apply pp06 policy). Documented in steering recipe 6.
  Expected flow: alarm email → user asks kiro → run `bash ~/argosy/cloud/s3_public_off.sh`.

## Completed this session (session 3, continued — AB + BR)
- **AB Phase 1 launched** on a fresh box (download running); see "AB run — LIVE" up top.
- **git commit-sweep DONE**: working tree clean + pushed. Untracked `_build/`, `__pycache__`,
  `chapters/.ipynb_checkpoints` via `git rm --cached` (they were tracked pre-.gitignore); committed
  all BR-session work (pp06 fix, visqc changes, cline fixes, doc reconciliation, cloud/poster/BR/
  OOIUsability, orphan deletions). .gitignore also gained `cloud/cdk.out/`.
- **~/ooi fresh-box fix** (uncommitted, laptop — commit before next box): `cloud/app.py` user-data
  + `pipeline/run_pipeline.sh` both now `mkdir -p ~/ooi`.
- **Bicameral Redesign (BR) started** — `BR.md` created (deliberation doc, no premature file moves).
  Decisions: (1) Phase-1 cline/QC code → dedicated `~/argosy/visqc/` (NOT pipeline/); (4) Book
  notebooks: MidnightNoon OUT, Visualizations STAYS, DataDownload+DataSharding OUT; (5) visqc/ holds
  cline_extract+cline_plot too (no separate qc/). PARKED: (2) define pp07 (needs Vis-notebook data
  review), (3) Phase-2 internal-wave file home. `iw/` inventory recorded (3 Phase-1 QC files vs 3
  Phase-2 IW files). Orphan scan → deleted ctd_coverage/ctd_minimum_cover.png + 4 vector v*.csv +
  3 stray `_check_*.py`; reconciled the v*.csv references in SensorTable.md/CodeManifest.md/steering.
- **VisQC Inspector enhanced**: added the right-hand potential-density (σ₀, TEOS-10/gsw) panel;
  Accept/Correct/Discard buttons writing `metadata/annotations/visqc_visitation_<site>.csv`
  (schema: timestamp,gpi,sensor,decision,upper_depth,lower_depth,cline_depth,cline_thickness,
  reviewed_at); fixed SITE_NAME 'slopebase'→2-letter code (renamed the existing sb CSV too),
  START_DATE now env-configurable; widened window (22in) + deepened + lowered charts + bigger title
  so controls/labels/title don't collide. `cline_plot.py` adapted: dual-mode (notebook sliders /
  standalone Agg+PNG), site-code filename, full-data-span default (dropped hardcoded 2024).
  `cline_extract.py` now keys on 2-letter site + per-site lat/lon. Added `OOIUsability.md` (OOINET
  parameter/provenance/annotation friction as DSC feedback) + wired into ArgosyOverview/CodeManifest.

## Completed earlier this session (session 3)
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
- **AB Phase 1 DONE** (verified in S3, box destroyed). Post-destroy: confirm no orphaned EBS with the
  describe-volumes CLI in the "AB run — COMPLETE" section above (avoids the console).
- **#1: commit the two ~/ooi fresh-box fixes** (`cloud/app.py`, `pipeline/run_pipeline.sh`) from the
  laptop — still uncommitted; needed before any future box. Then optionally publish the book
  (`jupyter-book build .` ; `ghp-import -n -p -f _build/html`) for the new Bibliography page.
- **#2: BR (Bicameral Redesign) — now the main focus.** Resolve parked decisions in `BR.md`:
  (2) define pp07 (needs Vis-notebook data review); (3) Phase-2 internal-wave file home. Then plan
  + execute the `visqc/` move (cline_extract/cline_plot/VisQCInspector) and moving MidnightNoon/
  DataDownload/DataSharding OUT of the Book (decided). BR also holds: the "where do components go?"
  tenet, the descent-data-recovery topic (on-demand Lambda vs bulk shard.py pass), and the orphan
  cleanup (done). Guideline: deliberate design first, then implement.
- **TEST the two new visqc tools** (built, compile-clean, NOT yet run against real data):
  - **SignoffQC.py**: needs a display (TkAgg + python3-tk). Run
    `python ~/argosy/visqc/SignoffQC.py --site sb --year 2022` (sb pp06 is local after the earlier
    sync; or pick a year present locally). Check: 4 charts render with multi-axis traces; noon/
    midnight tag correct; tri-state buttons flip Ok<->Discard and None does nothing; LSD shows
    None(expected) off-index vs None(missing) on noon/midnight; Advance/Back + Julian GoTo navigate;
    the CSV `metadata/annotations/scalar_signoff_sb_2022.csv` is written one-row-per-GPI and RESUMES
    (visits increment, Discards persist) on relaunch. Watch layout collisions (title vs stacked top
    x-axis labels) like VisQCInspector needed.
  - **shard_source.py**: needs `s3fs` (`pip install s3fs` in argosy env if absent). Quick test:
    `ShardSource(site='sb', source='pp06', location='s3').build_index(2022)` returns non-empty per
    sensor, and `.open(ref)` yields a Dataset — proving public-pp06 anon S3 read works. Then wire the
    Local/S3 switch into bundle_chart / Visualizations.ipynb (separate task).
- **Commit the new visqc/ files + BR + SessionState** (laptop) when ready.
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
