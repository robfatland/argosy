This folder `~/argosy/iw` contains files for **internal-wave analysis**: finding internal waves
from profile-to-profile shifts of the pycnocline and other clines, plus the cline-extraction and
visual-QC tools that grew up alongside it.

- **Status:** paused (reviewed Nov 2026; to be revived for the AGU26 poster)
- **Purpose:** internal-wave analysis from profile-to-profile cline shifts, with the cline-extraction and visual-QC tools it grew from
- **Next:** revive: add the descent profiles as a second time series (`../DescentData.md`); then settle whether the cline family and VisQCInspector move to `../visqc/` (BR.md decisions 1 and 5, never carried out)

## Files

- `cline_extract.py` -- per profile, the depth and strength of the pycnocline, thermocline, halocline
  and oxycline, plus its own algorithmic MLD (density 0.03 kg/m^3 above a 3 m reference band).
  Writes `~/ooi/<site>/metadata/features/cline_extract_<site>.csv`.
- `cline_plot.py` -- plots those results as time series (run by `../chapters/InternalWaves.ipynb`).
- `VisQCInspector.py` -- interactive profile inspector/annotator for visual QC (a Phase 1 tool).
- `internal_wave.py` -- animation of an internal wave (particle orbits in two layers).
- `internal_wave_physics.py` -- stream-function physics shared by the animation and the test.
- `TestInternalWaveIncompressibility.py` -- checks the displacement field conserves area (passes, under 3%).

## Related

- Docs: `../InternalWaves.md` (method), `../VisQC.md`, `../TidalAnalysis.md`, `../Testing.md`, `../BR.md`.
- MLD link: `mld/` (human labels and CNN) shares no code with this folder. The planned "cline curve"
  derived data type is where a human or CNN MLD would feed this analysis.
