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
- CodeManifest.md fully refreshed (removed 3 deleted files, added ~15 current files, added sga/ section)
- VisNotebookRebuild.md deleted: animation cell updated with pp06 source selector, all items resolved
- CoincidencePlans.md cross-referenced from Analysis.md and DevelopmentLog.md Open Topics
- pp06 LSD sensors: re-ran postprocess_pp06.py, 9086 files copied (nitrate, pCO2, pH shards)

## In progress / partially done
- SGA synthetic validation dataset not yet created (see Testing.md)
- Redux sync to S3: `aws s3 sync ~/ooi/redux/ s3://s3ooi/redux/` — then compact vhdx

## Reverted / needs redo
- Nothing currently reverted.

## Blocked / waiting on user
- Sync redux to S3, then compact WSL vhdx to reclaim C: drive space

## Next action
- CoincidencePlans.md: flesh out detection implementation
- SGA synthetic validation dataset (see Testing.md)
