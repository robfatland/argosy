This folder `~/argosy/vis` contains files for the **plotting scripts behind
`chapters/Visualizations.ipynb`**, plus the MLD coverage chart.

- **Status:** active (reviewed Nov 2026)
- **Purpose:** plotting scripts behind the Visualizations notebook: bundle chart, curtain plots, bundle animation, MLD coverage
- **Next:** fix stale "run this as" paths in the docstrings of `curtain_plot.py` and `bundle_chart.py`

## Files

- `bundle_chart.py` -- overlay consecutive profiles (modes `bundle` and `meanstd`); the meanstd mode
  draws the mean and mean plus/minus one standard deviation on a common depth grid.
- `bundle_animate.py` -- an mp4 of the bundle chart advancing through time.
- `curtain_core.py` -- shared rendering logic for curtain plots.
- `curtain_plot.py` -- curtain plot of the high-sample-density (HSD) sensors for a chosen site and time range.
- `curtain_batch.py` -- yearly single-sensor curtain plots in batch.
- `mld_coverage.py` -- the "MLD Coverage" chart: where in time MLD labels exist (oo/sb/ab by sensor).

## Related

- Figures are written to `~/ooi/<site>/visualizations/`; key charts are copied to `../images/`.
- Docs: `../Visualization.md`. Notebook: `../chapters/Visualizations.ipynb`.
