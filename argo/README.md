This folder `~/argosy/argo` contains files for comparing the OOI Regional Cabled Array shallow
profiler (SP) with the GO-BGC Argo float array, as one small three-panel graphic.

- **Status:** active (reviewed Nov 2026)
- **Purpose:** comparison of the shallow profilers with GO-BGC Argo floats: a three-panel graphic, the nearby-float table, and pointers to float data
- **Next:** source the three guessed Argo numbers; run a Slope Base SP-vs-float comparison (float 5906296, 2021-22)

- `compare_sp_argo.py` -- draws `~/argosy/images/sp_vs_argo.png`: samples/meter vs profiles/day,
  sensors vs mission years, and area vs depth. Each axis is ticked at the SP value and the Argo
  value. Edit the `V` dictionary at the top to change a number; mark `"guess"` until sourced.

## The numbers behind the graphic

| Quantity | SP | GO-BGC Argo | Status |
|---|---|---|---|
| Samples per meter | 22 (measured Nov 2026: one Slope Base ascent, 4,020 samples at 1 Hz over 182 m) | 0.5 (about 2 m spacing) | Argo is a GUESS |
| Profiles per day | 9 | 0.1 (one profile every 10 days) | sourced |
| Number of sensors | 17 (ADCP counted twice) | 6 (CTD + oxygen, nitrate, pH, chlorophyll, backscatter; the floats near our sites carry no irradiance sensor) | sourced |
| Mission duration | 11 years and continuing | 5 years | Argo is a GUESS |
| Area covered | 7.9e-5 km^2 (a disc 10 m across) | one float's life: 3e5 km^2; whole array: 3.6e8 km^2 (global ocean) | Argo "one float" is a GUESS; "whole array" assumes a global array |
| Depth | 0 to 200 m | 0 to 2000 m | sourced |
| Floats | 1 per site | 500 funded (GO-BGC); the wider BGC-Argo vision is 1000 | sourced |

Float data (CSV, one row per depth sample, with QC flags) are NOT kept here: they live in
`~/ooi/<site>/metadata/external/argo/argo_bgc_<WMO>.csv`, like the satellite and ERA5 data.

## Nearby biogeochemical Argo floats (Ifremer ERDDAP dataset ArgoFloats-synthetic-BGC, Nov 2026)

Profiles within about 130 km of each site since Dec 2014. "Closest" = smallest profile-to-site
distance. All five BGC sensors = oxygen, nitrate, pH, chlorophyll, backscatter (plus CTD). Oregon
Offshore (500 m deep) has no sensible match; the floats there are the same slope-edge visitors.

| Site | Float (WMO) | Type | PI (from the archive) | Profiles / dates in the box | Closest | Sensors with data |
|---|---|---|---|---|---|---|
| SB | 5906296 | APEX | Fassbender, G. Johnson, Riser, K. Johnson | 33, Jun 2021 - Apr 2022 | 8 km | all five |
| SB | 4903499 | NAVIS_A | Fassbender | 12, Dec 2022 - Apr 2023 | 16 km | all five |
| SB | 5906885 | NAVIS_EBR | Fassbender | 75, Aug 2025 - Nov 2026 (active) | 51 km | all five |
| AB | 2903938 | SOLO_BGC_MRV | Fassbender | 75, Feb - Nov 2025 | 17 km | all five |
| AB | 4902551 | ARVOR | Greenan (Canada) | 29, Nov 2023 - Sep 2026 | 29 km | oxygen only |
| AB | 4901784 | NOVA | Greenan (Canada) | 21, Jul 2015 - Jan 2016 | 40 km | oxygen only |

The dataset has no program field, so GO-BGC membership is not confirmed. The PI list of 5906296
matches the GO-BGC leads. None of these floats carries a downwelling-irradiance sensor, so a
typical "GO-BGC float" here has the CTD plus five biogeochemical sensors (6), not 7.

Sources for Argo: the GO-BGC and BGC-Argo program descriptions (go-bgc.org; Frontiers in Marine
Science 2019 "A BGC-Argo Guide"; Argo float cycle of 10 days to 2000 m, parking at 1000 m). Not yet
found: a sourced typical lifetime, vertical resolution, and one-float lifetime footprint.
