# Testing

This document concerns setting up tests to show that project software works as
intended. Failed tests should be flagged to the Open Issues list.


## Spectral Graph Analysis

Plan: Generate a synthetic dataset that mimics the structure of pp06 shard data
but with clearly defined, known properties. Run SGA modules 1–7 on this synthetic
data and verify that the clustering output matches expectations.

Synthetic dataset design:
- Location: `~/ooi/<site>/postproc/pp06synthetic/<yyyy>/` (e.g. `~/ooi/sb/postproc/pp06synthetic/2022/`)
- Format: identical shard filenames and NetCDF structure to pp06
- Content: two distinct water column "states" (e.g. summer-stratified vs winter-mixed)
  constructed analytically with known temperature/salinity/density profiles
- Each state should be clearly separable in feature space
- Include ~100 profiles per state, assigned to consecutive global indices
- Optionally: add a third "transition" state with intermediate properties

Expected SGA result:
- Module 6 should identify the correct number of clusters (2 or 3)
- Cluster assignments should match the known state labels exactly (or nearly so)
- The Fiedler vector should show a clean sign change between the two primary states
- Silhouette score should be high (>0.7) for the correct k

Implementation steps:
1. Write a script to generate synthetic shard files with prescribed sensor profiles
2. Point `sga_config.py` at `pp06synthetic` (change `data_base`)
3. Run modules 1–7
4. Compare cluster labels against known ground truth
5. Report pass/fail


## Internal Waves

Incompressibility test for the internal wave displacement field.

- **Script**: `iw/TestInternalWaveIncompressibility.py`
- **What it tests**: Area conservation of 3 rectangular cells tracked over one full
  wave period through the divergence-free displacement field.
- **How to run**: `cd ~/argosy && python iw/TestInternalWaveIncompressibility.py`
- **Pass criterion**: Area variation < 3% of initial area.
- **Current result**: PASSES (<1% deep, ~2% near interface).

Physics derivation and development history: see `InternalWaves.md` → "Stream function physics".
