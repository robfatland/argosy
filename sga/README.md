This folder `~/argosy/sga` contains files for the **spectral graph analysis (SGA)** of pp06
profiles: numbered modules that load profiles, interpolate them to a depth grid, build a
similarity graph, cluster it spectrally, and characterize the resulting water-column regimes.

- **Status:** paused (reviewed Nov 2026)
- **Purpose:** spectral graph analysis of pp06 profiles: find seasonal water-column regimes by clustering a depth-time similarity graph
- **Next:** resolve the two-cluster problem (multi-year runs collapse to k=2, seasonal dominance); see `../SpectralGraphAnalysis.md` "Known Issues"

## Files

Run in order (non-interactively, via `%run` from `../chapters/SpectralGraphAnalysis.ipynb`):

- `sga_config.py` -- Module 0: the run settings (site, years, depth range); edit, then run the rest.
- `sga_module1.py` -- load and prepare profile data (scan pp06 shards, index by global profile index).
- `sga_module2.py` -- interpolate profiles to a standard depth grid; build the feature matrix.
- `sga_module3.py` -- normalize features and handle missing data.
- `sga_module4.py` -- build the depth-time similarity graph.
- `sga_module5.py` -- spectral analysis of the similarity graph.
- `sga_module6.py` -- spectral clustering.
- `sga_module7.py` -- characterize the water-column regime of each cluster.
- `sga_depth_analysis.py` -- find the actual min/max depth range of pp06 data (informs the depth grid).
- `sga_sensor_presence.py` -- chart of when each sensor has data in pp06 over a time range.

## Related

- Docs: `../SpectralGraphAnalysis.md` (module guide), `../Analysis.md`, `../Testing.md` (synthetic validation).
- Data: intermediates and results go to `~/ooi/<site>/analysis/sga/`.
- Portability: the notebook runs these modules with `%run ~/argosy/sga/...` (no machine-specific paths).
