# PP05: Quality-Controlled Analysis Dataset

## Purpose

pp05 is a quality-controlled subset of the full redux dataset intended for
analysis. Unlike pp01/pp02 (which select noon/midnight profiles only), pp05
includes all profiles that pass quality filters. The goal is a "ready for
analysis" dataset where every included shard file contains physically realistic
sensor data.


## Sensor categories

**High Sample Density (HSD):** temperature, salinity, density, DO, CDOM,
chlorophyll-A, backscatter, PAR. All 9 daily profiles are candidates (except
PAR excludes daily_index 3, 4, 5 — the midnight ± 1 profiles where PAR is
near-zero by design).

**Low Sample Density (LSD):** nitrate, pH, pCO2. Only daily_index 4 and 9 are
candidates. Minimum data point filter: nitrate >= 50, pH >= 5, pCO2 >= 5.


## Three-tier exclusion strategy


### Tier 1: Time-window exclusions (manual)

Source: `~/argosy/sensor_exclusions.csv`

Known fouling events and gross instrument failures spanning multiple days.
Identified visually from curtain plots, confirmed by data scan, added manually.

Current entries (as of May 2026):
- salinity + density: 2016-07-27 to 2016-08-01 (min values 11–16 PSU)
- salinity + density: 2018-12-13 to 2018-12-24 (~3 PSU drop)
- salinity + density: 2021-11-20 to 2021-12-03 (conductivity cell fouling)


### Tier 2: Per-profile gross range filter (automated)

For each shard file, check whether sensor values fall within physically
realistic bounds. Two threshold levels:

**Fail range** (instrument garbage — values outside sensor capability):

| Sensor | Fail min | Fail max | Source |
|--------|----------|----------|--------|
| Temperature | -2 | 40 | OOI global range |
| Salinity | 0 | 42 | OOI global range |
| Density | 1000 | 1100 | OOI global range |
| DO | 0 | 400 | OOI global range (RS01SBPD) |
| CDOM | 0 | 375 | OOI global range (RS01SBPD) |
| Chlorophyll-A | 0 | 50 | OOI global range |
| Backscatter | 0 | 0.0079 | OOI global range |
| PAR | 0 | 2500 | OOI global range |
| Nitrate | -5 | 50 | Site knowledge + literature |
| pCO2 | 50 | 3000 | Site knowledge |
| pH | 6.5 | 9.0 | Literature |

**Suspect range** (site-specific — values outside expected Oregon Slope Base
conditions in the 0–200m water column):

| Sensor | Suspect min | Suspect max | Basis |
|--------|-------------|-------------|-------|
| Temperature | 2.0 | 22.0 | 11-year observed range + margin |
| Salinity | 30.0 | 35.5 | 11-year observed range + margin |
| Density | 1022.0 | 1028.5 | Derived from T/S bounds |
| DO | 10.0 | 350.0 | Hypoxia floor + surface saturation |
| CDOM | -0.5 | 10.0 | Observed range + margin |
| Chlorophyll-A | -0.1 | 10.0 | Bloom max + margin |
| Backscatter | -0.0001 | 0.005 | Observed range + margin |
| PAR | -1.0 | 1500.0 | Surface max + margin |
| Nitrate | -2.0 | 45.0 | Deep max + margin |
| pCO2 | 100.0 | 2000.0 | Observed range + margin |
| pH | 7.0 | 8.5 | Site observed range + margin |

**Decision logic per shard file:**
1. If ANY value falls outside the fail range → exclude entire file
2. Count values outside the suspect range
3. If > 20% of valid points are suspect → exclude entire file
4. If ≤ 20% → keep file, NaN-out individual suspect values

Reference: [OOI qc-lookup repository](https://github.com/oceanobservatories/qc-lookup)
(contains `data_qc_global_range_values.csv` with per-instrument ranges)


### Tier 3: Statistical anomaly detection (Phase 2, deferred)

Build monthly depth-binned climatology from the pp05 dataset. Score each
profile by RMS deviation from climatology. Flag profiles exceeding 4 standard
deviations. Write flagged profiles to `~/ooi/metadata/pp05_flagged_profiles.csv`
for human review. Confirmed bad profiles get added to `sensor_exclusions.csv`.


## PAR midnight exclusion

PAR values near zero at night are physically correct but not useful for
analysis. Exclude daily_index 3, 4, and 5 for PAR only. These correspond to
midnight (4) and the profiles immediately before and after midnight (3, 5).
This is simpler than tracking seasonal sunrise/sunset times.


## Implementation

Script: `~/argosy/postprocess_pp05.py`

Usage: `python postprocess_pp05.py`

Output:
```
~/ooi/postproc/pp05/
    redux/
        redux2015/
        ...
        redux2025/
    README.md
~/ooi/metadata/
    pp05_exclusion_summary.csv    (per-sensor counts: included, excluded by tier)
```


## Relationship to other postproc datasets

| Dataset | Selection | QC level |
|---------|-----------|----------|
| redux | All profiles, all sensors | None (raw shards) |
| pp01 | Noon profiles (HSD) + daily_index 4/9 (LSD) | Depth filter + exclusions |
| pp02 | Midnight profiles (HSD) + daily_index 4/9 (LSD) | Depth filter + exclusions |
| pp05 | All profiles (HSD) + daily_index 4/9 (LSD) | Tier 1 + Tier 2 gross range |
| pp05+ | (future) | Tier 1 + Tier 2 + Tier 3 statistical |


## References

- OOI QARTOD implementation: https://oceanobservatories.org/2022/11/ooi-launches-qartod/
- OOI QC lookup tables: https://github.com/oceanobservatories/qc-lookup
- OOI gross range test methodology: fail thresholds from vendor calibration
  range; suspect thresholds from mean ± 3σ of historical site data
