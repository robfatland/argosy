This folder `~/argosy/pipeline/` contains files for the **Phase 1 pipeline**: getting data
from OOINET, sharding it into `redux`, and reducing it to `pp06` (a post-processing-cleaned,
analysis-ready version). The goal is one authoritative copy of this logic that runs identically
locally (from the notebooks) and headless on cloud/EC2 — see `cloud/` for the EC2 create/destroy
machinery that invokes it.

- `download.py` — OOINET acquisition. Extracted from `chapters/DataDownload.ipynb` so the
  notebook and the EC2 job call the same code (no duplication). Functions: `estimate_download_volume()`,
  `bulk_download(instrument, ooi_instrument, site)`, `download_all(site)`. Reads the async staging
  URLs from `~/argosy/download_link_list.txt`; writes to `ooipaths.ooinet_dir(site, "scalar")`.
  Restart-tolerant. CLI: `python download.py --site oo` (or `--estimate`).
- `shard.py` — shard OOINET source files into per-sensor, per-profile `redux` files. Extracted
  from `chapters/DataSharding.ipynb` (same no-duplication pattern as download.py). Walks the
  profile index, slices ascent/descent windows per sensor, writes
  `RCA_<site>_sp_<sensor>_<yyyy>_<ddd>_<gpi>_<daily>_V1.nc`. Restart-tolerant (skips existing).
  CLI: `python shard.py --site oo [--instruments ctd flor ...]`.
- `run_pipeline.sh` — EC2 entrypoint: download → shard → pp06 for one site, then sync results
  to S3 (local-then-sync). Incremental / restart-aware. Invoked by the cloud user-data.
  Optional 3rd arg or `pipeline/<site>_url_list.txt` supplies the OOINET URL list.

## Related code still at the repo root (not yet moved here)

Post-processing is `ooipaths`-based and site-parameterized; `run_pipeline.sh` calls it in place:
- `postprocess_pp05.py`, `postprocess_pp06.py`, `postprocess_pp06_filter2.py`,
  `postprocess_pp06_filter3.py`, `postprocess_special_profiles.py`.
Consolidating these under `pipeline/` is a possible future tidy-up (not done to avoid churn).

`run_pipeline.sh` calls these in place. Consolidating them under `pipeline/` is a possible
future tidy-up; not done now to avoid churn.

## Design notes

- All destinations come from `ooipaths.py` (per-site layout), so AWS is an accelerator, not a
  dependency: the same code runs from the notebook on localhost.
- The notebook's audit/dedup/plot cells (sensor audit, CTD overlap/minimum-cover, availability
  plot) remain in `DataDownload.ipynb` — they are human-in-the-loop (generate review-then-run
  deletion scripts) and viz, so they stay notebook-side rather than in the headless module.
