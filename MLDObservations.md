# MLD Observations

Experience and thoughts from hand-marking mixed-layer depth (MLD) on hundreds of shallow-profiler
profiles using the `MLD.py` annotation tool: Talk about patterns, edge cases, ambiguity, heuristics.


> This file is **not** part of the Jupyter Book; it is a working doc in the repo.


## MLD suite


The MLD effort is a small suite of files.

| Piece | File | Role |
|---|---|---|
| Design / spec | `MLDAnnotationPlan.md` | The two-program workflow, interaction model, label schema, decisions. **Read this first.** |
| Candidate selection | `PreSelectProfiles.py` | Reproducible seeded sampling of one profile per N-day block per site (from pp06). `--bless` promotes the chosen set to the repo. |
| Blessed candidate lists | `mld_candidates/` | The committed, shared candidate CSVs (`mld_candidates_<site>_block<NN>.csv`) that all annotators label against. See `mld_candidates/README.md`. |
| Annotator | `MLD.py` | Standalone TkAgg GUI to hand-label MLD on the blessed candidates. |
| Collaborator env | `environment-mld.yml` | Portable minimal conda spec for running `MLD.py` on another machine. |
| Human labels (output) | `~/ooi/<site>/metadata/annotations/mld_labels_<site>_block<NN>_<who>.csv` | Per-labeler label tables in the data tree (NOT in git). One row per (gpi, sensor, who). |
| Observations (this file) | `MLDObservations.md` | Qualitative experience notes from doing the labeling. |
| ML / downstream | `Analysis.md` → "Mixed Layer Depth" / 1-D CNN section | Where the labels become training data (1-D CNN, heatmap head, sampling-density note). |


See also the "annotation problem" framing in the `argosy-conventions` steering file, and the
`ArgosyOverview.md` → "Pointers to Key Actions" entry for building the training dataset.


## How to read/interpret the label records

- **Key = (gpi, sensor, who).** A profile can carry independent MLD calls for temperature,
  salinity, density, and DO, by each labeler.
- **`no_mld_recorded = True`** is a deliberate call: "there is no discernible MLD here," distinct
  from "not yet visited." Teaching the model to make this call is a central goal (see
  `Analysis.md`), so be consistent about *when* you declare no-MLD.
- Both `value_raw` and `value_filtered` are stored, plus the filter key + slider settings, so a
  label stays interpretable regardless of which filter was active when it was made.


## Observations

*(Chronological or by-theme — add dated entries as labeling proceeds. Suggested tags:
`[no-MLD]`, `[double-ML]`, `[filter]`, `[sensor-disagreement]`, `[seasonal]`, `[artifact]`.)*

- _(placeholder — first observations to be added by the labeler(s). Example prompts to answer:_
  - _How often is there genuinely no MLD, and does it cluster by season?_
  - _When temperature and density disagree on the MLD, which do you trust, and why?_
  - _Which filter/adaptivity settings make the pick clean vs. which mislead?_
  - _Recurring artifacts (spikes, near-surface excursions, sensor fouling) that complicate the call.)_


## Open questions raised by the labeling

- _(collect the "we should decide this" items that surface while labeling — criteria for no-MLD,
  handling double mixed layers, whether to label all four sensors or lead with temperature, etc.
  Promote resolved decisions into `MLDAnnotationPlan.md`.)_
