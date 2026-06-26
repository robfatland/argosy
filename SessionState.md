# Session State

## Last updated
2026-06-26 — Major session: bundle chart, pp06, SGA, tidal analysis, internal wave viz, collaboration setup, full documentation audit.

## Completed this session
- Bundle chart: global-index nav, dynamic source, persistent range memory, display names, nav buttons
- pp06 built: Filters 0-3 (salinity MRA, Sav-Gol CDOM/ChlorA, backscatter despiking)
- SGA: refactored to 7 standalone modules + config, depth grid 27-185m, CDOM excluded
- Tidal analysis: 5-panel chart, cross-correlation, TidalAnalysis.md writeup
- Internal wave animation: divergence-free physics, incompressibility test
- Collaboration: SETUP.md, environment.yml, S3 public policy, pp06 on S3
- Documentation audit: fixed dead references, deleted obsolete files, fixed _toc.yml,
  removed duplicates in PostProcessing.md, fixed env name everywhere, deleted
  redux_s3_synch.py/requirements.txt/stray PNG/shell script
- Derived oceanographic parameters written up in Analysis.md
- N² (Brunt-Väisälä) writeup in Analysis.md
- Testing.md created (SGA synthetic + internal wave incompressibility)

## In progress / partially done
- **CodeManifest.md needs full refresh** — missing ~10 current files, lists deleted files.
  Major rewrite needed to reflect current repo state.
- Vis notebook rebuild: bundle chart done (as standalone `bundle_chart.py`), curtain plot done
  (as standalone `curtain_plot.py`). Animation cell still pending. `VisNotebookRebuild.md` can
  be deleted once animation is addressed.
- SGA synthetic validation dataset not yet created (see Testing.md)
- pp06 LSD sensors: added to build script but not yet copied (re-run postprocess_pp06.py)
- Redux sync to S3: `aws s3 sync ~/ooi/redux/ s3://s3ooi/redux/` — then compact vhdx

## Reverted / needs redo
- Nothing currently reverted.

## Blocked / waiting on user
- Sync redux to S3, then compact WSL vhdx to reclaim C: drive space
- Run postprocess_pp06.py to add LSD sensors to pp06

## Next action
- Refresh CodeManifest.md to reflect current repo state
- CoincidencePlans.md: add reference from Analysis.md or Open Topics
