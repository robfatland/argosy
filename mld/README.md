This folder `~/argosy/mld` contains files for the **MLD neural network** (a 1-D CNN that learns to
pick the mixed layer depth from pp06 profiles and human labels), and is the entry point to the
whole MLD project, most of whose pieces live in the repo root.

- **Status:** paused (reviewed Nov 2026)
- **Purpose:** 1-D CNN that learns to pick the mixed layer depth from human labels; hub for the MLD project
- **Next:** finish re-annotation (oo, sb, ab); retrain (`python ~/argosy/mld/train.py --epochs 60`); rerun the synthetic acceptance test (`python ~/argosy/mld/score_synthetic.py`) and compare with the Oct 2026 baseline in `../SessionState.md`

## Files in this folder (the model)

This is a Python package (`from mld.mld_config import ...` is used by nine files): do not rename it.

- `mld_config.py` -- shared constants (sensors T/S/DO, depth grid, paths).
- `dataset.py` -- build training examples from pp06 shards and the label CSVs.
- `model.py` -- shared 1-D CNN backbone with one heatmap head per sensor.
- `train.py` -- train on human labels (split by time block, not at random).
- `infer.py` -- run a trained model over pp06 and write MLD metadata.
- `inspector.py` -- step through profiles comparing model prediction with the human label.
- `synthetic.py` -- generate a shadow dataset of artificial pp06 profiles with KNOWN MLD in `~/ooi/synthetic/`.
- `eval_synthetic.py`, `score_synthetic.py`, `diagnose.py` -- test the model against that known truth.

## The rest of the MLD project (repo root unless noted)

- **Human labeling:** `MLD.py` (interactive annotator), `PreSelectProfiles.py` (candidate sampling into
  `mld_candidates/`), `MLDTimeSeries.py` (time-series viewer of the labels), `sync_labels.py` with
  `shared_labels/` (share label CSVs through git), `vis/mld_coverage.py` (where labels exist).
- **Synthetic data helpers:** `SyntheticViewer.py`, `ArchetypeValuePuller.py`.
- **Algorithm vs human:** `HAT_vs_science_compare.py` and `HAT_vs_science_plot.py` (Holte and Talley
  algorithm compared with hand labels, Slope Base).
- **Docs:** `MLDAnnotationPlan.md` (spec), `MLDObservations.md` (field notes), `MLDDataRelease.md`
  (Zenodo training set), `MLDModelReflection.md` (critique of the model), `SyntheticMLDPlan.md`.
- **Neighbors:** `som/` (oxygen maximum below the MLD), `seastate/` (MLD against weather forcing),
  `iw/` (computes its own algorithmic MLD; no code is shared with this folder).
