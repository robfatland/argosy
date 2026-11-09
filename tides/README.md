# Tides

This folder `tides/` contains files for the tidal-signal analysis: predicting the tide at the three RCA sites and correlating it with the shallow profiler's start depth.

- **Status:** active (reviewed Nov 2026)
- **Purpose:** tide prediction (TPXO10 constituents) and its correlation with profiler start-depth variation
- **Next:** repeat the Slope Base analysis at Oregon Offshore and Axial Base (constituents for both are already in the JSON)

- `TidalAnalysis.md` -- method, results and open questions (part of the Jupyter Book).
- `TimeSeriesProfileCorrelation.py` -- 5-panel chart and cross-correlation; run by `../chapters/TidalSignal.ipynb` with `%run ~/argosy/tides/TimeSeriesProfileCorrelation.py`. Reads the JSON beside it.
- `tidal_constituents.json` -- 14 TPXO10 tidal constituents for the 3 sites (the extraction script is retired).
