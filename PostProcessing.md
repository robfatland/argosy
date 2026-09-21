# PostProcessing

> New to argosy? Start at `ArgosyOverview.md`. This is a Phase 1 (pipeline) document.


The *redux* dataset maps profiles from raw OOINET data to shard files in the redux directory. From there the next step is "post-processing" to create multiple versions of the data, moving towards actual analysis.
Thematically the post-processing results feature...


- cleaner data: bad data removed, noise reduced via filters
- data subsets: noon/midnight profiles


## Recap of the data filesystem logic 


The data filesystem contains multiple types of data isolated from the project/repository directory `~/argosy`. 


### Sites

The project covers three shallow-profiler sites. All three share the identical
sensor layout (15 sensors: 4 vector + 11 scalar), so the sensor breakdown stated
elsewhere in this doc applies to every site. Each site maintains its own Global
Profile Index (GPI) sequence starting at 1.

| Code | Site | OOI designator | SP node | Array |
|------|------|----------------|---------|-------|
| `sb` | Oregon Slope Base | `RS01SBPS` | `SF01A` | RCA (Cabled Continental Margin) |
| `oo` | Oregon Offshore | `CE04OSPS` | `SF01B` | Coastal Endurance (cabled) |
| `ab` | Axial Base | `RS03AXPS` | `SF03A` | RCA |

These two-letter codes are the project-standard site identifiers used in the
planned per-site directory layout (`~/ooi/<site>/...`) and in shard filenames.
`~/ooi` is implicitly the RCA/Endurance *shallow-profiler* corpus; deep profilers
and seafloor nodes, if added later, get their own root and their own structure.

> **Note:** The layout described below reflects the *current* single-site state.
> A restructure to the per-site tree (`~/ooi/<site>/{ooinet,redux/<yyyy>,postproc/<pp>/<yyyy>,profileIndices,metadata}`)
> is planned and centralized through the `ooipaths.py` path module. See the
> "Filesystem restructure" plan in `DevelopmentLog.md`.

### Current layout

All path knowledge is centralized in the `ooipaths.py` module (repo root); code should
obtain paths from it rather than hardcoding. The layout is per-site: `<site>` is the
2-letter code (`sb`/`oo`/`ab`, see Sites table above).

- Data filesystem root on localhost is `~/ooi`
- Per-site subtree: `~/ooi/<site>/{ooinet, redux, postproc, profileIndices, metadata, analysis, visualizations}`
- Source raw data $\to$ `~/ooi/<site>/ooinet[/scalar|vector]`
    - Backed up to `s3://s3ooi/ooinet/` (see note); local copy deletable to free space
- Shards (redux) $\to$ `~/ooi/<site>/redux/<yyyy>` (e.g. `~/ooi/sb/redux/2016`)
    - One NetCDF file per sensor per profile as available
    - profiles numbered sequentially per external metadata
        - Per site: Global Profile Index (GPI) starting 1, 2, 3, ...
    - Nine possible profiles per day
    - A skipped profile does not result in a GPI skip
    - `redux` contains considerable problematic data
        - This data is modified in stages to produce more usable subsets
        - This is 'postprocessing'
        - Results get a designator like `pp06`
        - The various `pp` results form a directed graph
- Postprocessing results $\to$ `~/ooi/<site>/postproc/<pp>/<yyyy>` (e.g. `~/ooi/sb/postproc/pp06/2022`)
    - Uniform nesting across all pp results (pp01/pp02 no longer carry an extra `redux/` level)
    - Within each year the files break out by sensor
    - shallow profiler has 15 sensors
        - 4 vector
        - 11 scalar
            - Three Low Sample Density (LSD: 10 to 150 per profile)
                - Profiles 4 and 9 only (midnight and noon)
            - Eight High Sample Density (HSD: thousands per profile)
    - Days are delimited using Greenwich Mean Time
        - 8 hour offset relative to local
        - profile 4 runs at midnight local time
        - profile 9 runs at noon local time
        - Noon-only is `pp01` and Midnight-only is `pp02`
    - Data file example (filenames are unchanged by the per-site restructure — the site
      lives in the directory path AND the `RCA_<site>_sp` filename token):
        - `~/ooi/sb/postproc/pp06/2022/RCA_sb_sp_dissolvedoxygen_2022_043_13614_1_V1.nc`
              - Regional Cabled Array
              - `sb` = Slope Base (site token)
              - Shallow Profiler
              - Sensor = Dissolved Oxygen (HSD)
              - Year 2022, Julian day 43
              - Global Profile Index 13614
              - Day relative profile is number 1
              - This is version 1 (V1) of this data
              - File is NetCDF format
- `~/ooi/<site>/profileIndices` stores start/peak/end timestamps for profiles
- Metadata is stored in `~/ooi/<site>/metadata`
    - This does not include profile start/peak/end timestamps
    - A breakdown of metadata types, folders and names is pending
        - See "Metadata folder inventory" in `DevelopmentLog.md` → Pending To Do


## Post-Processing 01 02 noon midnight profile subset


pp01 (noon) and pp02 (midnight) are subsets of the redux dataset containing only profiles
that ran at local noon or local midnight respectively. These profiles correspond to
daily_index 4 (midnight) and daily_index 9 (post-noon, ~13:40 local). They are
distinguished by longer descent durations that allow equilibration time for the slower
chemical sensors. From 2017 onward, three sensors operate exclusively on these two
profiles: nitrate (ascent, ~150 pts/profile), pCO2 (descent, ~10 pts), and pH (descent,
~10 pts). pH has shard files for all 9 daily indices but only indices 4 and 9 contain
usable data.


### Implementation


Single script: `~/argosy/postprocess_special_profiles.py`

```
python postprocess_special_profiles.py noon      # writes to pp01
python postprocess_special_profiles.py midnight  # writes to pp02
```

The script:
- Reads the corresponding metadata CSV
- For each profile global index, locates all matching shard files in `~/ooi/<site>/redux/<yyyy>/`
- Applies depth filter on the temperature shard
- Copies passing shards to `~/ooi/<site>/postproc/pp01/<yyyy>/` (or pp02), renaming V1 to V2
- Handles missing shards gracefully: logs and skips
- Prints summary: total profiles in CSV, excluded by depth filter, copied per sensor, missing shards


### Results (May 2026)


| | pp01 (noon) | pp02 (midnight) |
|---|---|---|
| Profiles in CSV | 2480 | 2443 |
| No shards in redux | 1 | 2 |
| Excluded (depth > 50m) | 200 | 186 |
| Included | 2279 | 2255 |
| Total shards copied | 17,148 | 17,029 |


Depth histograms, computed from included profiles only, 2-meter bins, x-axis brackets
non-zero data ±6m:
- `~/ooi/sb/visualizations/pp01_depth_histogram_deep.png`
- `~/ooi/sb/visualizations/pp01_depth_histogram_shallow.png`
- `~/ooi/sb/visualizations/pp02_depth_histogram_deep.png`
- `~/ooi/sb/visualizations/pp02_depth_histogram_shallow.png`


## Postprocessing 05+: basic data cleaning


### Overview


To date we are only considering scalar sensors; vector sensors will be incorporated later.


The goal of the `pp05` sequence is to arrive at a dataset usable for spectral graph analysis,
cluster analysis, and an AutoDiscovery trial.


The scalar sensors fall into two groups as described above.


**HSD sensors** (temperature, salinity, density, DO, cdom, chlora, backscatter, par)
**LSD sensors** (nitrate, pH, pCO2)


`redux` > `pp05` (virtual) > `pp06` (actual) is the starting postprocessing sequence.


### `redux` to `pp05`


`pp05` is a virtual dataset. It consists of a CSV manifest, a list of files that are "good to keep"
from the redux dataset.


- Source: `~/ooi/<site>/redux/<yyyy>` where `<yyyy>` is a year: 2015, 2016 etcetera
- pp05 rules
    - Exclude profiles falling within manual exclusion windows (`sensor_exclusions.csv`)
    - Exclude profiles where >20% of values fall outside site-specific suspect ranges
    - For HSD sensors: include all 9 daily profiles (PAR excludes nighttime indices 3/4/5)
    - For LSD sensors: include only daily_index 4 and 9; require minimum valid points (nitrate >= 50, pH >= 5, pCO2 >= 5)
    - Per-sensor logic: excluding one sensor's shard does not affect other sensors at the same global index
- Output: `~/ooi/<site>/metadata/pp05_manifest.csv`
- Note: the manifest's `filepath` column stores absolute source paths; if the data tree
  moves, regenerate the manifest or path-patch it (see the restructure gotcha in `DevelopmentLog.md`).
- Script: `~/argosy/postprocess_pp05.py`
- Manifest columns: `filepath, sensor, year, doy, global_idx, daily_idx, n_valid, n_suspect`
- Resumable: appends per-year, skips completed years. Delete the manifest to regenerate from scratch.
- Full methodology: `~/argosy/PP05_QCAnalysis.md`


### `pp05` to `pp06`


`pp06` is an actual (physical) dataset. It is a QC-filtered copy of the shards referenced
by the pp05 manifest, restricted to the 8 HSD sensors. pp06 also applies sample-level
filtering to remove erratic data points within individual profiles.


- Source: pp05 manifest → corresponding redux shard files
- Sensors: temperature, salinity, density, dissolvedoxygen, cdom, chlora, backscatter, par
- Output: `~/ooi/<site>/postproc/pp06/<yyyy>/<shard_files>.nc`
- Script: `~/argosy/postprocess_pp06.py` (Filter 0 + Filter 1)
- Script: `~/argosy/postprocess_pp06_filter2.py` (Filter 2)
- Script: `~/argosy/postprocess_pp06_filter3.py` (Filter 3)


#### pp06 Filters


**Filter 0** (baseline): Copy pp05-qualifying HSD shards to pp06 as physical files.
Non-salinity/density sensors are straight-copied. No data modification.


**Filter 1** (salinity/density MRA despiking): Walk through the ascending salinity
profile sequentially. Each sample must pass two gates: physically possible (28–36 PSU)
and within 0.3 PSU of the Most Recent Acceptable value. Failed samples are removed
from both the salinity and density shards. Discards logged to `pp06_filter1.csv`.

Reference: Custom implementation. See `PP06_Filters.md` for the full Filter 0–3 reference.


**Filter 2** (CDOM/ChlorA smoothing): Savitzky-Golay filter (window=11, polyorder=2)
applied in-place to reduce quantization noise from the FLORT sensor's coarse ADC.

Reference: Savitzky, A. and Golay, M.J.E. (1964). "Smoothing and Differentiation of
Data by Simplified Least Squares Procedures." Analytical Chemistry, 36(8), 1627–1639.


**Filter 3** (backscatter despiking): Rolling-minimum baseline extraction (window=11)
applied in-place. Removes positive particle-encounter spikes, retaining the smooth
background particulate backscatter field.

Reference: Briggs, N. et al. (2011). "High-resolution observations of aggregate flux
during a sub-polar North Atlantic spring bloom." Deep-Sea Research Part I, 58(12), 1169–1186.


### Sensor exclusions

Manual data quality exclusions are defined in `~/argosy/sensor_exclusions.csv`.
This file is version-controlled in the argosy repo.

Format: `sensor,start,end,reason`

The postprocess scripts and visualization cells load this CSV and skip profiles
whose mid-time falls within an exclusion window for the given sensor.

Workflow for adding new exclusions:
1. Observe anomaly in curtain plot or bundle plot
2. Confirm boundaries by scanning daily values in redux
3. Add entry to `sensor_exclusions.csv` with precise date range and reason
4. Re-run pp05 then pp06 to propagate the exclusion


## Tides and current correction


Correcting profile data to align successive profiles in view of current pressure
on the shallow profiler platform and tidal variation.

See `TidalAnalysis.md` for the TPXO10 tidal prediction methodology and start-depth
correlation results. Not yet implemented as a postprocessing correction.


## QC Filter


### Motivation: Data quality flags in OOI source files


OOI source NetCDF files include per-observation quality flags alongside the science
data. Two flag systems are present:

1. **QARTOD flags** (`<variable>_qartod_results`): Quality Assurance of Real-Time
   Oceanographic Data. Uses integer codes: 1=Pass, 2=Not Evaluated, 3=Suspect,
   4=Fail, 9=Missing Data.

2. **OOI internal QC flags** (`<variable>_qc_results`): A bitmask-style system with
   values like 13 and 29. Interpretation TBD — these appear to encode which specific
   tests were applied and passed/failed.

The QARTOD system is the more interpretable and actionable of the two.


### Data study: CTD file from January 2018

Source file examined:
```
~/ooi/sb/ooinet/scalar/2018_ctd/
  deployment0004_RS01SBPS-SF01A-2A-CTDPFA102-streamed-ctdpf_sbe43_sample_
  20180119T191420.236756-20180206T235959.424256.nc
```

This file contains 1,572,316 observations spanning 18 days.

**QARTOD results by variable:**

| Variable | Pass | Not Evaluated | Suspect | Fail |
|----------|------|---------------|---------|------|
| Temperature | 98.40% | 1.50% | **0.11%** (1,707 obs) | 0% |
| Salinity | 98.50% | 1.50% | 0% | 0% |
| Dissolved Oxygen | 98.50% | 1.50% | 0% | 0% |
| Pressure | 100% | 0% | 0% | 0% |
| Conductivity | 90.62% | 0% | **9.38%** (147,535 obs) | 0% |

**Observations:**

- **Temperature suspect (0.11%)**: 1,707 observations flagged. These may be spikes or
  values outside the expected climatological range. Small enough to be isolated events
  rather than systematic sensor failure.

- **Conductivity suspect (9.38%)**: 147,535 observations flagged. This is significant
  and likely corresponds to the known salinity dropout issue (clogged conductivity cell)
  documented by the RCA data team. Notably, the derived salinity variable itself passes
  its own qartod gross-range test — meaning the salinity values are within plausible
  bounds even though the underlying conductivity measurement is flagged as suspect.

- **Not Evaluated (1.5%)**: 23,521 observations across temperature, salinity, and DO.
  These occur when ancillary data needed for the climatology test is unavailable.

- **No Fail (4) or Missing (9) flags** in this file.

- **Density has no qartod flags** — only the internal `_qc_results` field (89% at value 13,
  11% at value 29). Density is a derived quantity (from T, S, P) so its quality depends
  on the inputs.


### Implications for post-processing

A future QC-based filter (potentially pp03 or pp04) could:

1. Exclude observations where `<variable>_qartod_results == 3` (Suspect) or `== 4` (Fail)
   before sharding or during post-processing.

2. For conductivity-flagged periods: Investigate whether the derived salinity and density
   are actually compromised, or whether the flag is overly conservative.

3. Track which profiles contain flagged data and produce a "profile quality score"
   (fraction of observations passing qartod) to enable filtering at the profile level
   rather than the observation level.

4. The 1.5% "Not Evaluated" observations should be treated as Pass (no evidence of
   problems; the test simply couldn't run).


### Next steps

- Examine flagged observations in the context of profiles: Are the suspect temperature
  values concentrated in specific profiles, or scattered? Do they occur during ascent
  (science data) or at rest (engineering data)?
- Survey qartod flags across multiple years to determine if the conductivity issue is
  deployment-specific or persistent.
- Design and implement the filter as a post-processing step.


## Data operations (S3 sync, disk management)

Cloud backup to S3 and localhost disk-space management have moved to `DataOps.md`.
See `DataOps.md` for S3 sync/verify/restore commands and WSL vhdx compaction.
