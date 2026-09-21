# MLD Observations

Experience and thoughts from hand-marking mixed-layer depth (MLD) on hundreds of shallow-profiler
profiles using the `MLD.py` annotation tool: Talk about patterns, edge cases, ambiguity, heuristics.


> This file is **not** part of the Jupyter Book; it is a working doc in the repo.


## MLD suite


The MLD effort is a small suite of files.


| Piece | File | Role |
|---|---|---|
| Design / spec | `MLDAnnotationPlan.md` | Two-program workflow, interaction model, label schema, decisions. **Read first.** |
| Candidate profiles | `PreSelectProfiles.py` | Reproducible seeded sampling: one profile per N-day block per site from pp06. `--bless` promotes chosen set to the repo. |
| Blessed candidate lists | `mld_candidates/` | The committed, shared candidate CSVs (`mld_candidates_<site>_block<NN>.csv`) that all annotators label against. See `mld_candidates/README.md`. |
| Annotator | `MLD.py` | Standalone TkAgg GUI to hand-label MLD on blessed candidates. |
| Collaborator env | `environment-mld.yml` | Portable minimal conda spec for running `MLD.py` on another machine. |
| Human labels (output) | `~/ooi/<site>/metadata/annotations/mld_labels_<site>_block<NN>_<who>.csv` | Label tables living in the data folder: One row per (gpi, sensor, who). |
| Observations (this file) | `MLDObservations.md` | Qualitative experience notes from doing the labeling. |
| ML / downstream | `Analysis.md` → "Mixed Layer Depth" / 1-D CNN section | Where the labels become training data (1-D CNN, heatmap head, sampling-density note). |


See also the "annotation problem" framing in the `argosy-conventions` steering file, and the
`ArgosyOverview.md` → "Pointers to Key Actions" entry for building the training dataset.


## On the *click* label records


- **Key = (gpi, sensor, who).** A profile can carry independent MLD calls for temperature,
  salinity, density, and DO, by each labeler.
- **`no_mld_recorded = True`** is a deliberate label: "there is no discernible MLD here," distinct
  from "not yet visited." Teaching the model to make this call is a central goal (see
  `Analysis.md`). We need to agree on what constitutes `no-MLD`.
- Both `value_raw` and `value_filtered` are stored, plus the filter key + slider settings, so a
  label stays interpretable regardless of which filter was active when it was made.


## Observations


Entries should include who, date, context and any amount of speculation. Can also include a a `[tag]`.

> **Descent overlay note (when the Descent button lands):** daily indices 4 (midnight) and 9
> (post-noon) have built-in descent pauses, so their descent traces may look "lumpy" (clustered
> depths, longer dwell) versus smooth-descent profiles — expected, not an artifact. Descent is
> second-class/noisier by design (see `DescentData.md`): use it as a qualitative read on
> water-column stability, not for placing MLD.


- Rob, 19-Sep-2026. The implicit *view* of MLD annotation is from the surface down. After completing 2024-25 x 4 sensors: A surprising number of MLs terminate with excursions to warmer water, commonly 20 or 30 meters thick. Even double excursions: Colder to warmer (than ML) to colder resuming the archetypical profile. This is above the thermocline proper. Current examples: sb T 929, 1077, 1365. However the white whale is corroboration in Salinity or DO: None in these examples; so keep looking.
    - Rob, 19-Sep-2026. Another really clean one: sb T 13271. Not corroborated... suggests looking at the descent
    - Rob, 19-Sep-2026. Another really clean one: sb T 13994. Corroborated by DO!


- Rob, 20-Sep-2026. Flagging sb salinity anomaly starting Jan 2017: A deep lens or double lens down below 50 meters of higher salinity but **warning** this could be primarily a chart autoscale artifact. Worth a look though. First appears in GPI 5042. Variants in 5088, 5125, 5173, 5213, 5237, 5262, etc... 5469 has an interesting complement-corroboration from DO. Last of the sequence might be 5611 (10-MAR-2018). Suggest check each DESCENT corroboration. 


- Rob, 19-Sep-2026. We can flag ranges of bad profiles for embargo. See sb 1711 (2016-05-07): erratic in T and DO. Look at adjacent profiles: Is this an embargo range?


- Rob, 20-Sep-2026. sb GPI 2457 and subsequent have an oxygen-rich lens below the MLD. Through perhaps 2915; so the date range is 19-AUG-2016 through 12-OCT-2016 and even beyond then.




## Open questions


These can be resolved and relocated to the "plan" document `MLDAnnotationPlan.md`


- Area between successive curves: Illusion but still suggests scanning for big jumps, another type of anomaly
- Re-do the candidate selection process using more stringent criterion on how shallow the data goes?
- Criteria for no-MLD...
- Handling double (or more) mixed layers with some delineator
- Reconcile four sensors? 
- Suppose working on DO MLDs: Make an option to ghost-present other sensor MLDs as reference?
    - The plus is this would help resolve ambiguous choices by harmonizing across sensors
    - The minus is this will bias the decision on the MLD
