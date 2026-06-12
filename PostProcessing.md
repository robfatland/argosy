# PostProcessing


Modifying redux by stages for analysis


- Cleaning the data (removing bad data, noise reduction via filters)
- Selecting particular data subsets


The root data directory is referred to as `~/ooi`. The source data is downloaded to
`~/ooi/ooinet` for sharding; informally Level 1 > Level 2. The sharded or "redux" 
data consists of one NetCDF file per sensor per profile when available. Profiles
are numbered sequentially according to external metadata. This provides a global
profile index of consecutive integers starting 1, 2, 3, ... in 2015 for the
Oregon Slope Base shallow profiler. There are nine possible profiles per day so
from one day to the next the global profile index will increment by at most 9. 
If a profile fails to run for some reason we have a non-profile or a missing 
profile that is *not* assigned a global profile index. 


The redux dataset, consisting of sensor-shard profiles, contains a considerable amount 
of problematic data. We will operate on this data in stages to produce intermediate
versions of the data and ultimately a "polished" version of the data suitable for
analysis. Each postprocessing result gets its own designator in the format `ppNN`
where `NN` is a two digit number starting at 01. Hence `pp01` and `pp02` are the
first two postprocessing results and they happen to be unrelated to `pp05`. 


The shallow profiler has a total of 15 sensors; 4 vector and 11 scalar. Of the
11 scalar sensors three are considered Low Sample Density (LSD: 10 to 150 samples
per profile) while the remaining 8 are considered High Sample Density (HSD: thousands
of samples per profile). The LSD sensors only operate on profiles 4 and 9 each
day; they do not operate on the other 7 profiles. A "day" is delimited using
Greenwich Mean Time so there is about an 8 hour offset in time. For this reason
profile 4 runs at midnight local time and profile 9 runs at noon local time, 
approximately. To create a data subset that contains LSD data we isolate noon to
`pp01` and midnight to `pp02` as described below.



## Post-Processing 01 02 noon midnight profile subset


pp01 (noon) and pp02 (midnight) are subsets of the redux dataset containing only profiles
that ran at local noon or local midnight respectively. These profiles correspond to
daily_index 4 (midnight) and daily_index 9 (post-noon, ~13:40 local). They are
distinguished by longer descent durations that allow equilibration time for the slower
chemical sensors. From 2017 onward, three sensors operate exclusively on these two
profiles: nitrate (ascent, ~150 pts/profile), pCO2 (descent, ~10 pts), and pH (descent,
~10 pts). pH has shard files for all 9 daily indices but only indices 4 and 9 contain
usable data.


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


- Source: `~/ooi/redux/redux<yyyy>` where `yyyy` is a year: 2015, 2016 etcetera
- pp05 rules
    - Exclude profiles falling within manual exclusion windows (`sensor_exclusions.csv`)
    - Exclude profiles where >20% of values fall outside site-specific suspect ranges
    - For HSD sensors: include all 9 daily profiles (PAR excludes nighttime indices 3/4/5)
    - For LSD sensors: include only daily_index 4 and 9; require minimum valid points (nitrate >= 50, pH >= 5, pCO2 >= 5)
    - Per-sensor logic: excluding one sensor's shard does not affect other sensors at the same global index
- Output: `~/ooi/metadata/pp05_manifest.csv`
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
- Output: `~/ooi/postproc/pp06/redux<yyyy>/<shard_files>.nc`
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

Reference: Custom implementation. See `~/argosy/pp06ErraticFilterPrompt.md` for design.


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

See `SeaLevelDelta.md` for using the OSU tidal model to generate offset at
(lat, lon, time). Not yet implemented in the postprocessing pipeline.


## QC Filter (qartod flags)


### Motivation

OOI source NetCDF files include per-observation QARTOD quality flags
(`<variable>_qartod_results`): 1=Pass, 2=Not Evaluated, 3=Suspect, 4=Fail, 9=Missing.

A study of a January 2018 CTD file (1.57M observations, 18 days) found:
- Temperature: 0.11% suspect (1,707 obs)
- Conductivity: 9.38% suspect (147,535 obs) — likely clogged cell issue
- All other variables: 0% suspect

The conductivity issue is significant. Derived salinity passes its own gross-range
test even when conductivity is flagged, suggesting the flag may be overly conservative.

### Status

Not yet incorporated into the pipeline. A future filter (pp03 or pp04) could use
qartod flags to exclude suspect observations before or during sharding. Key question:
do the 0.11% suspect temperature values fall within profiles (actionable) or at rest
(ignorable)?


Computed from included profiles only, 2-meter bins, x-axis brackets non-zero data ±6m:
- `~/ooi/visualizations/pp01_depth_histogram_deep.png`
- `~/ooi/visualizations/pp01_depth_histogram_shallow.png`
- `~/ooi/visualizations/pp02_depth_histogram_deep.png`
- `~/ooi/visualizations/pp02_depth_histogram_shallow.png`


### Implementation


Single script: `~/argosy/postprocess_special_profiles.py`

```
python postprocess_special_profiles.py noon      # writes to pp01
python postprocess_special_profiles.py midnight  # writes to pp02
```

The script:
- Reads the corresponding metadata CSV
- For each profile global index, locates all matching shard files in `~/ooi/redux/redux<yyyy>/`
- Applies depth filter on the temperature shard
- Copies passing shards to `~/ooi/postproc/pp01/redux/redux<yyyy>/` (or pp02), renaming V1 to V2
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


## Tides and Current


This concerns correcting profile data to align successive profiles in view of 
current pressure on the shallow profiler platform and tidal variation.


See the documentation in `SeaLevelDelta.md`. This describes using the OSU model
to generate tidal offset at (lat, lon, time). 


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
~/ooi/ooinet/rca/SlopeBase/scalar/2018_ctd/
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


## S3 Backup: Syncing ooinet to AWS

The `~/ooi/ooinet/` directory (204 GB of source NetCDF files from OOINET) is
backed up to S3. This allows the local copy to be deleted to free disk space,
with the data retrievable from the cloud if re-sharding is ever needed.

### Sync command

```bash
aws s3 sync ~/ooi/ooinet/ s3://s3ooi/ooinet/ --storage-class STANDARD_IA
```

- Uploads only new/changed files (compares size and modification time)
- `STANDARD_IA`: ~$0.0125/GB/month (~$2.55/month for 204 GB)
- One-directional: local → S3. Does not delete from S3 if deleted locally.
- Safe to interrupt with Ctrl+C and restart — picks up where it left off.
- Bandwidth throttle (optional): `aws configure set default.s3.max_bandwidth 25MB/s`

### When to run

Run overnight or when stepping away. The main impact is network bandwidth.
Does not lock files or interfere with local reads. At 50 Mbps upload: ~9 hours
for a full 200 GB sync.

### Verification after sync

```bash
aws s3 ls s3://s3ooi/ooinet/ --recursive --summarize | tail -3
```

Compare object count and total size against:
```bash
du -sh ~/ooi/ooinet/
find ~/ooi/ooinet -type f | wc -l
```

### After verification: freeing local space

Once the sync is verified complete, `~/ooi/ooinet/` can be deleted locally to
reclaim ~204 GB. Redux (18 GB) and postproc remain local as working datasets.
To restore from S3 if needed:

```bash
aws s3 sync s3://s3ooi/ooinet/ ~/ooi/ooinet/
```


## Localhost Data Management

### WSL virtual disk (ext4.vhdx)

WSL stores its entire Linux filesystem in a single file on C: drive:
```
C:\Users\robfa\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\LocalState\ext4.vhdx
```

Key behaviors:
- The vhdx **grows** automatically as WSL writes data
- It does **not shrink** automatically when data is deleted inside WSL
- `df -h /` inside WSL reports virtual capacity, NOT actual C: drive free space
- The real constraint is C: drive free space (check with `Get-PSDrive C` in PowerShell)

### Checking actual free space

From inside WSL, `df` is misleading. Always check from Windows:
```powershell
Get-PSDrive C | ForEach-Object { "C: Free: $([math]::Round($_.Free/1GB,1)) GB" }
```

### Compacting the vhdx (reclaiming C: space after deleting data in WSL)

After deleting large amounts of data inside WSL, the vhdx retains its size on C:.
To reclaim that space:

1. Inside WSL, discard freed blocks: `sudo fstrim -v /`
2. **Close Kiro/VS Code** (it holds the vhdx open via `\\wsl.localhost\` paths)
3. Open Command Prompt **as Administrator**
4. Run:
```
wsl --shutdown
diskpart
select vdisk file="C:\Users\robfa\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\LocalState\ext4.vhdx"
compact vdisk
exit
```

Important: Kiro must be closed first — its file access keeps the vhdx locked.

### When compaction is NOT needed

If you delete data inside WSL and then write new data of similar size, the vhdx
reuses the freed internal space without growing. Compaction is only needed when
you want to reclaim C: space for other Windows programs. WSL itself is not
constrained by the vhdx being "too large" — it can use all internal free space
regardless of whether the vhdx has been compacted.

### Current state (May 2026)

- `~/ooi/ooinet/` deleted locally (204 GB), backed up to `s3://s3ooi/ooinet/`
- vhdx is 288 GB on disk with ~75 GB used internally (~213 GB internal headroom)
- C: drive has ~32 GB free (would be ~230 GB after successful compaction)
- WSL can write ~200 GB of new data without any C: space issues
