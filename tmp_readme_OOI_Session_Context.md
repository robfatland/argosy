# OOI/RCA Session Context (from surface_project0 Kiro session, May 2026)

## Project Overview

This is the `argosy` project: Analysis of oceanographic data from the OOI Regional
Cabled Array (RCA) shallow profilers. The primary documentation is `AIPrompt.md`.
The project runs on two machines (Dell primary, Surface secondary) in WSL at `~/argosy`
with data at `~/ooi`.

## What Was Accomplished This Session

### 1. Tidal Sea Level Correction

**Goal:** Compute hourly tidal height at the three shallow profiler sites to support
depth correction of profile data.

**Files created (in surface_project0, need to move to ~/argosy):**

- `SeaLevelDelta.md` — Documentation of the tidal model approach, TPXO10-atlas-v2,
  Python code for hourly prediction at 3 sites, explanation of what the 30 GB TPXO
  data are, and the extraction strategy (extract ~90 numbers, delete 30 GB).

- `tidal_extract.py` — Script to extract harmonic constituents from TPXO10 at the
  3 sites, save to JSON, and include a self-contained prediction function. After
  running this, the 30 GB TPXO data can be deleted.

- `tidal_amplitude_map.py` — Generates a regional NE Pacific figure: log-scaled
  colormap of total tidal amplitude (RSS of all constituents) with the 3 profiler
  sites marked. Covers 42–49.5°N, 131.5–122°W (OR/CA border to Salish Sea, past
  Axial Seamount). Uses matplotlib Agg backend for WSL compatibility.
  
  **Status:** Data reading works. Amplitudes are in mm (TPXO convention), converted
  to meters. The grid is (nx=lon, ny=lat) — `hRe` shape is `(10800, 5401)` with
  dims `('nx', 'ny')`. `lon_z` is 0–360. Script has been debugged through 3 iterations.
  Last run succeeded through data reading but crashed on Qt display (fixed with Agg backend).
  **Needs one more test run.**

**TPXO10 data location:** `~/D/TPXO10_atlas_v2_nc/TPXO10_atlas_v2_nc/`
(Windows Downloads, symlinked from WSL as ~/D)

**TPXO10 file structure:**
- 15 constituent files: `h_<constituent>_tpxo10_atlas_30_v2.nc`
- Each file: dims `nx=10800, ny=5401`; data_vars: `con, lon_z, lat_z, hRe, hIm`
- `hRe` shape: `(10800, 5401)` = `(lon, lat)` — **first axis is longitude**
- `lon_z`: 0.03–360.0 (0–360 convention); `lat_z`: -90 to +90
- Amplitudes stored in **millimeters**

### 2. Coincidence Detection (Anomaly Flagging)

**Goal:** Define and implement two types of coincidence for detecting oceanographic
features in profile data.

**File created:** `Coincidence.md`

**Type 1 — Auto-coincidence (temporal persistence):**
A feature in a single sensor at a particular depth persists into subsequent profiles.
Distinguishes real structure from transient noise.

**Type 2 — Hetero-coincidence (cross-sensor corroboration):**
A feature at a particular depth in a particular profile appears simultaneously in
multiple sensors. Distinguishes real events from single-sensor artifacts.

**Feature definition:** "A signal at a point in time (profile) that is recognizably
distinct from what preceded it."

**Detection algorithms (sequential pipeline):**
1. Z-score deviation from running baseline (N~20 profiles)
2. Vertical gradient anomaly (dS/dz compared to baseline gradient)
3. Profile-to-profile difference (direct subtraction, normalized)
4. Residual after smooth fit (Savitzky-Golay, isolates narrow features)
5. Wavelet decomposition (multi-scale, advanced)

**Scoring pipeline:**
- Feature detection → auto-coincidence check → hetero-coincidence check → confidence score
- High confidence = passes both auto AND hetero

**Practical notes:**
- Interpolate all profiles to common depth grid (0.5–1m bins, 0–200m)
- Account for diurnal cycling in baseline
- Sensor-specific thresholds using xlow/xhigh from Sensor Table
- Meaningful sensor groupings: T+S+ρ, T+DO, Chl+backscatter+PAR, NO3+DO

### 3. S3 Mirror for ~/ooi

**File created:** `s3_sync_ooi.sh`

**Design:**
- Mirrors `~/ooi` to S3 bucket with identical folder structure
- Uses `aws s3 sync --delete` for clean overwrite semantics
- Selective sync by subfolder: `bash s3_sync_ooi.sh redux`, `postproc`, etc.
- Selective download: `aws s3 sync s3://BUCKET/redux/redux2018/ ~/ooi/redux/redux2018/`
- To wipe and replace (e.g., pp01): delete local, regenerate, re-sync — `--delete`
  ensures S3 matches new local state

### 4. Consolidation Instructions

**File created:** `CONSOLIDATION_INSTRUCTIONS.md`

Lists exactly which files move to `~/argosy`, which stay in surface_project0,
and provides text patches for AIPrompt.md, PostProcessing.md, and CodeManifest.md.

Key additions needed in AIPrompt.md:
- S3 Mirror section (under file system or workflow)
- Tidal Data section (pointing to SeaLevelDelta.md)

Key addition needed in PostProcessing.md:
- Under "Tides and Current" heading: pointer to SeaLevelDelta.md

## Site Coordinates (confirmed from AIPrompt.md)

```
Site name           Latitude  Longitude   Depth (m)  D-offshore (km)
-----------------   --------  ---------   ---------  ---------------
Oregon Offshore     44.37     -124.96      577        67
Oregon Slope Base   44.53     -125.39     2910       101
Axial Base          45.83     -129.75     2620       453
```

## Pending Actions

1. Run `tidal_amplitude_map.py` one more time (should work now with Agg backend)
2. Run `tidal_extract.py` to extract constituents and save JSON
3. Move files from surface_project0 to ~/argosy per CONSOLIDATION_INSTRUCTIONS.md
4. Update AIPrompt.md, PostProcessing.md, CodeManifest.md with patches
5. Set up S3 bucket and configure `s3_sync_ooi.sh` with bucket name (Dell)
6. Process data download orders (Dell, from recovered spam emails)
7. After tidal extraction succeeds: delete 30 GB TPXO data from ~/D
8. Prototype coincidence Algorithm 1 (z-score baseline) on temperature at Slope Base
