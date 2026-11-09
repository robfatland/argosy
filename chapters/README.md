This folder `~/argosy/chapters` contains files for the **Jupyter Book's executable notebooks**
(the reader-facing Phase 2 chapters), listed in `../_toc.yml`.

- **Status:** active (reviewed Nov 2026)
- **Purpose:** the Jupyter Book's executable notebooks (Phase 2 analysis chapters)
- **Next:** act on BR.md decision 4 (move the Phase 1 notebooks out of the Book)

## Notebooks

Each mostly runs a script from another folder with `%run`:

- `Visualizations.ipynb` -- bundle chart, curtain plot, bundle animation (scripts in `../vis/`). The main Phase 2 notebook.
- `SpectralGraphAnalysis.ipynb` -- runs the modules in `../sga/`.
- `InternalWaves.ipynb` -- a small notebook that runs `../iw/cline_plot.py`.
- `TidalSignal.ipynb` -- tide against profiler start depth (`../tides/TimeSeriesProfileCorrelation.py`).
- `ColumbiaPlume.ipynb` -- runs the scripts in `../plume/`.
- `MidnightNoon.ipynb` -- classifying midnight and noon profiles (pp01/pp02): Phase 1.
- `DataSharding.ipynb` -- Phase 1, superseded by `../pipeline/shard.py`.
- (`DataDownload` and `StubWork` notebooks were retired Nov 2026; both remain in git history.)
- `MLD.md` -- a one-kilobyte Book page that `_toc.yml` lists under Phase 1.

Note: BR.md decision 4 put `MidnightNoon` and `DataSharding` OUT of the Book, but
`_toc.yml` still lists both under "Chapters (executable notebooks)".
