This folder `~/argosy/visqc` contains files for **Phase 1 human quality control**: reviewing
scalar sensor data profile by profile and signing off or discarding it.

- **Status:** paused (reviewed Nov 2026; last edited Sep 2026)
- **Purpose:** Phase 1 human QC tools: sign off or discard scalar sensor data profile by profile
- **Next:** decide whether VisQCInspector and the cline code join this folder (BR.md decisions 1 and 5); wire `shard_source.py` into the notebook bundle explorer; define pp07 (BR.md)

## Files

- `SignoffQC.py` -- GUI to sign off the 11 scalar sensors profile by profile (Ok or Discard). Writes one row
  per GPI to `~/ooi/<site>/metadata/annotations/scalar_signoff_<site>_<year>.csv` (a file for Slope Base
  2024 exists). Feeds the planned pp07. Run:
  `python ~/argosy/visqc/SignoffQC.py --site <sb|oo|ab> --year <yyyy>`
- `shard_source.py` -- read shard files from the local tree or directly from S3, so a notebook need
  not download the whole shard set. Built but not yet wired into any notebook.

## Related

- Docs: `../VisQC.md`, `../BR.md` (design topics for both tools).
- `../iw/VisQCInspector.py` is the older QC inspector that still lives in `iw/`.
