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


Entries should include who, date, context and any amount of speculation. 

> **Descent overlay note:** The idea is to add a button that overlays descent data on a particular 
> ascent profile. When this happens: Daily indices 4 (midnight) and 9
> (post-noon) have built-in descent pauses, so their descent traces should look "lumpy" (clustered
> depths, longer dwell) in comparison with smooth-descent profiles. This is expected, not 
> an artifact. Descent is second-class/noisier by design (see `DescentData.md`): use it as 
> a qualitative read on water-column stability, not for placing MLD.


- Rob, 19-Sep-2026. The implicit *view* of MLD annotation is from the surface down. After completing 2024-25 x 4 sensors: A surprising number of MLs terminate with excursions to warmer water, commonly 20 or 30 meters thick. Even double excursions: Colder to warmer (than ML) to colder resuming the archetypical profile. This is above the thermocline proper. Current examples: sb T GPIs 929, 1077, 1365. However the white whale is corroboration in Salinity or DO: None in these examples; so keep looking.
    - Rob, 19-Sep-2026. Another very clean: sb T 13271. Not corroborated... suggests looking at the descent
    - Rob, 19-Sep-2026. Another very clean: sb T 13994. Corroborated by DO!


- Rob, 20-Sep-2026. Flagging sb salinity anomaly starting Jan 2017: A deep lens or double lens down below 50 meters of higher salinity but **warning** this could be primarily a chart autoscale artifact. Worth a look though. First appears in GPI 5042. Variants in 5088, 5125, 5173, 5213, 5237, 5262, etc... 5469 has an interesting complement-corroboration from DO. Last of the sequence might be 5611 (10-MAR-2018). Suggest check each DESCENT corroboration. 


- Rob, 19-Sep-2026. We can flag ranges of bad profiles for embargo. See sb 1711 (2016-05-07): erratic in T and DO. Look at adjacent profiles: Is this an embargo range?


- Rob, 20-Sep-2026. sb GPI 2457 and subsequent have an oxygen-rich lens below the MLD. Through perhaps 2915; so the date range is 19-AUG-2016 through 12-OCT-2016 and even beyond then.

- Rob, 24-Sep-2026. ab GPI 16970 Salinity has a minor inversion/deviation at 60 meters; not a big deal by itself but this develops into a 1 psu lens in 17054, persisting to 17156 and then continuing to persist while dropping down to below 80 meters in 17196, 17197, back up to 60 m in 17203 and continuing through 17311. It seems like a coherent narrative, the full date range 01-11-2023 through 28-12-2023, almost two months. Over the same interval the temperature was textbook monotonic. Density followed salinity. DO was not in sync with salinity but rather followed its own peculiar excursions. 


- Rob, 25-SEP-2026. ab GPI 7130 through 8600: Oxygen inversion for like six months: June through December 2019.

> NOTE: Rob went back with an improved `MLD.py` to re-annotate all 3 sites x all 4 sensors in October. This 
produced a new set of anomalies (in addition to allowing `No Usable Data` added to options).


- Rob, 10-OCT-2026. oo GPI 1613 2016-05-04 Salinity **massive** inversion. Thorough exploration needed. Similar anomaly 2026-09-22 GPI 2224, again Salinity at OO. Are these peculiar to OO?

- Rob, 10-OCT-2026. oo GPI 4826 2019-02-24 Salinity lens 16m thick centered at 100m. COINCIDENT with DO and somewhat corroborated in temperature. This really seems to be a cline-interrupting entity.

- Rob, 11-OCT-2026. oo GPI 9828 2023-01-23 Temperature shows an anomalously deep mixed layer down to 106.5m.

- Rob, 11-OCT-2026. oo GPI 10899 2023-09-19 Temperature shows SP in a long-term *broken* state with no data shallower than 140m; engineering would have to confirm; maybe HITL? Ends around 2024-08-13 so that's about a year of down time. 


## Good archetype profiles


For the synthetic dataset these site + GPI + type identifiers are what "really easy" examples look like, either with a MLD in meters or a `No MLD` result. This table has left to right entries: site key, User (R = Rob), GPI nnnn (self-explanatory; for that site), sensor type from {Temp, Salinity, Density, DO}, MLD result. Assume for all cases that the filter is adaptive_savgol_mad with window 59 and adaptivity 2.


- oo R GPI 567 Temp result 55.0m
- oo R GPI 881 Temp result 52.6m
- oo R GPI 1027 Temp result 47.4m
- oo R GPI 2561 Temp result 61.1m
- oo R GPI 5075 Temp result No MLD
- oo R GPI 5437 Temp result No MLD
- oo R GPI 2547 Salinity result 61.8m
- oo R GPI 2561 Salinity result 61.8m 
- oo R GPI 2667 Salinity result 72.0m
- oo R GPI 3913 Salinity result 24.0m
- oo R GPI 4064 Salinity result No MLD
- oo R GPI 5075 Salinity result No MLD
- oo R GPI 2667 DO result 72.4m
- oo R GPI 2747 DO result 55.2m
- oo R GPI 4443 DO result 63.8
- oo R GPI 1812 DO result No MLD
- oo R GPI 1914 DO result No MLD
- oo R GPI 2078 DO result No MLD




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
