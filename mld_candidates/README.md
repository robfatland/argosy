This folder `~/argosy/mld_candidates/` contains the **blessed, canonical candidate-profile
lists** for the MLD annotation workflow — the shared source of truth that both annotators
(Chuck, Rob) label against so they sample the *same* profiles.

These are small, diff-friendly CSV manifests kept under version control (a deliberate exception
to the "no data in `~/argosy`" rule, like `sensor_exclusions.csv`). Full design in
`../MLDAnnotationPlan.md`.

Files:
- `mld_candidates_<site>_block<NN>.csv` — one candidate profile per `<NN>`-day time block for a
  site (`sb`/`oo`/`ab`), produced by `../PreSelectProfiles.py` and promoted here via its
  `--bless` step. Columns: block bounds, `N` (profiles in block), selection tier
  (`all4`/`T_only`), chosen `gpi`/`timestamp`/`daily_index`, per-sensor presence flags, seed,
  block width.

Producers / consumers:
- `../PreSelectProfiles.py` — generates the working copies in `~/ooi/<site>/metadata/annotations/`
  and, with `--bless`, copies the chosen set here.
- `MLD.py` (planned) — the interactive annotator; reads these blessed lists to drive labeling.

Regeneration is NOT guaranteed identical across machines (selection depends on the local pp06
set). Treat these blessed copies as authoritative; do not overwrite from an unverified re-run.
