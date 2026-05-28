#!/usr/bin/env python3
"""
Post-process redux shard files into pp01 (noon) or pp02 (midnight) subsets.

Usage:
    python postprocess_special_profiles.py noon
    python postprocess_special_profiles.py midnight

Selection logic:
  - HSD sensors (temperature, salinity, density, DO, cdom, chlora, backscatter, par):
    Selected from noon/midnight metadata CSV profiles. Depth filter applied (shallowest <= 50m).
  - LSD sensors (nitrate, ph, pco2):
    Selected from daily_index 4 and 9 profiles only. Minimum data point filter applied.
    Nitrate: >= 50 valid points. pH and pCO2: >= 5 valid points.

Both HSD and LSD selections respect the sensor_exclusions.csv embargo list.

Output: ~/ooi/postproc/pp01/redux/redux<yyyy>/ (noon) or pp02 (midnight)
Files are byte-identical copies with V1 -> V2 rename.
"""

import sys
import shutil
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr


# ── Configuration ─────────────────────────────────────────────────────────────

REDUX_BASE = Path.home() / "ooi" / "redux"
POSTPROC_BASE = Path.home() / "ooi" / "postproc"
METADATA_DIR = Path.home() / "ooi" / "metadata"
VIZ_DIR = Path.home() / "ooi" / "visualizations"
EXCLUSIONS_CSV = Path.home() / "argosy" / "sensor_exclusions.csv"

PROFILE_LISTS = {
    "noon": METADATA_DIR / "ooi_rca_sb_noon_global_profile_indices.csv",
    "midnight": METADATA_DIR / "ooi_rca_sb_midnight_global_profile_indices.csv",
}

PP_FOLDERS = {
    "noon": "pp01",
    "midnight": "pp02",
}

# Daily indices where LSD sensors operate (from 2017 onward; all indices for 2015-2016)
LSD_DAILY_INDICES = {4, 9}

MAX_SHALLOW_DEPTH = 50.0  # exclude profiles that never got above this depth

HSD_SENSORS = [
    "temperature", "salinity", "density", "dissolvedoxygen",
    "cdom", "chlora", "backscatter", "par"
]

LSD_SENSORS = {
    "nitrate": {"min_points": 50, "phase": "ascent"},
    "ph": {"min_points": 5, "phase": "descent"},
    "pco2": {"min_points": 5, "phase": "descent"},
}

ALL_SENSORS = HSD_SENSORS + list(LSD_SENSORS.keys())


# ── Load sensor exclusions ────────────────────────────────────────────────────

def load_exclusions():
    """Load sensor exclusion windows from CSV."""
    exclusions = {}
    if EXCLUSIONS_CSV.exists():
        df = pd.read_csv(EXCLUSIONS_CSV)
        for _, row in df.iterrows():
            exclusions.setdefault(row['sensor'], []).append(
                (np.datetime64(row['start']), np.datetime64(row['end'])))
    return exclusions


def is_excluded(exclusions, sensor_var, mid_time):
    """Check if a profile mid-time falls within an exclusion window."""
    if sensor_var not in exclusions:
        return False
    for exc_start, exc_end in exclusions[sensor_var]:
        if exc_start <= mid_time <= exc_end:
            return True
    return False


# ── Functions ─────────────────────────────────────────────────────────────────

def find_shards_for_profile(global_index, year):
    """Find all shard files in redux for a given global profile index and year."""
    redux_dir = REDUX_BASE / f"redux{year}"
    if not redux_dir.exists():
        return []
    pattern = f"*_{global_index}_*_V1.nc"
    matches = list(redux_dir.glob(pattern))
    verified = []
    for f in matches:
        parts = f.stem.split("_")
        if len(parts) >= 8 and parts[6] == str(global_index):
            verified.append(f)
    return verified


def get_daily_index(shard_file):
    """Extract daily_index from shard filename."""
    return int(shard_file.stem.split("_")[7])


def get_sensor_name(shard_file):
    """Extract sensor name from shard filename."""
    return shard_file.stem.split("_")[3]


def get_mid_time(shard_file):
    """Get the mid-time of a shard file."""
    try:
        ds = xr.open_dataset(shard_file)
        t = ds.time.values
        ds.close()
        if len(t) > 0:
            return t[len(t) // 2]
    except:
        pass
    return None


def check_depth_filter(shard_files):
    """Check depth filter using the temperature shard. Returns True if passes."""
    temp_files = [f for f in shard_files if "_temperature_" in f.name]
    if not temp_files:
        return False
    try:
        ds = xr.open_dataset(temp_files[0])
        if "depth" in ds.data_vars:
            min_depth = float(ds["depth"].min().values)
        elif "depth" in ds.coords:
            min_depth = float(ds["depth"].min().values)
        else:
            ds.close()
            return False
        ds.close()
        return min_depth <= MAX_SHALLOW_DEPTH
    except:
        return False


def count_valid_points(shard_file, sensor_var):
    """Count valid (non-NaN) data points in a shard file."""
    try:
        ds = xr.open_dataset(shard_file)
        vals = ds[sensor_var].values
        ds.close()
        return int(np.sum(~np.isnan(vals)))
    except:
        return 0


def copy_shard(src_path, output_dir):
    """Copy a shard file, renaming V1 to V2."""
    output_dir.mkdir(parents=True, exist_ok=True)
    new_name = src_path.name.replace("_V1.nc", "_V2.nc")
    dst_path = output_dir / new_name
    shutil.copy2(src_path, dst_path)
    return dst_path


def find_lsd_shards(year, sensor_var):
    """Find all LSD sensor shards with daily_index 4 or 9 for a given year."""
    redux_dir = REDUX_BASE / f"redux{year}"
    if not redux_dir.exists():
        return []
    files = sorted(redux_dir.glob(f"RCA_sb_sp_{sensor_var}_*.nc"))
    return [f for f in files if get_daily_index(f) in LSD_DAILY_INDICES]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("noon", "midnight"):
        print("Usage: python postprocess_special_profiles.py <noon|midnight>")
        sys.exit(1)

    label = sys.argv[1]
    pp_folder = PP_FOLDERS[label]
    csv_path = PROFILE_LISTS[label]

    print(f"=== Post-processing: {label} -> {pp_folder} ===\n")

    # Load exclusions
    exclusions = load_exclusions()
    if exclusions:
        print(f"Loaded sensor exclusions:")
        for sensor, windows in exclusions.items():
            for s, e in windows:
                print(f"  {sensor}: {s} to {e}")
        print()

    # Read profile list for HSD sensors
    if not csv_path.exists():
        print(f"ERROR: Metadata CSV not found: {csv_path}")
        sys.exit(1)

    df = pd.read_csv(csv_path, parse_dates=["start", "peak", "end"])
    total_profiles = len(df)
    print(f"HSD: Profiles in {label} metadata CSV: {total_profiles}")

    # ── Process HSD sensors ───────────────────────────────────────────────────
    excluded_depth = 0
    excluded_embargo = 0
    missing_shards_hsd = 0
    copied_hsd = {s: 0 for s in HSD_SENSORS}
    included_hsd = 0

    for _, row in df.iterrows():
        global_index = int(row["profile"])
        year = row["start"].year

        shard_files = find_shards_for_profile(global_index, year)
        if not shard_files:
            missing_shards_hsd += 1
            continue

        if not check_depth_filter(shard_files):
            excluded_depth += 1
            continue

        # Get mid-time for exclusion check
        temp_files = [f for f in shard_files if "_temperature_" in f.name]
        if not temp_files:
            missing_shards_hsd += 1
            continue
        mid_time = get_mid_time(temp_files[0])
        if mid_time is None:
            missing_shards_hsd += 1
            continue

        included_hsd += 1
        output_dir = POSTPROC_BASE / pp_folder / "redux" / f"redux{year}"

        for shard_file in shard_files:
            sensor = get_sensor_name(shard_file)
            if sensor not in HSD_SENSORS:
                continue
            if is_excluded(exclusions, sensor, mid_time):
                excluded_embargo += 1
                continue
            copy_shard(shard_file, output_dir)
            copied_hsd[sensor] += 1

    print(f"HSD: Included {included_hsd} profiles, excluded {excluded_depth} (depth), "
          f"{excluded_embargo} files (embargo), {missing_shards_hsd} missing")
    print(f"HSD files copied per sensor:")
    for s in HSD_SENSORS:
        if copied_hsd[s] > 0:
            print(f"    {s:20s} {copied_hsd[s]}")

    # ── Process LSD sensors ───────────────────────────────────────────────────
    print(f"\nLSD: Processing daily_index 4 and 9 profiles...")
    copied_lsd = {s: 0 for s in LSD_SENSORS}
    excluded_lsd_points = {s: 0 for s in LSD_SENSORS}
    excluded_lsd_embargo = {s: 0 for s in LSD_SENSORS}

    years = sorted(set(int(d.name.replace("redux", ""))
                       for d in REDUX_BASE.glob("redux*") if d.is_dir()))

    for sensor_var, config in LSD_SENSORS.items():
        min_pts = config["min_points"]

        for year in years:
            shards = find_lsd_shards(year, sensor_var)
            output_dir = POSTPROC_BASE / pp_folder / "redux" / f"redux{year}"

            for shard_file in shards:
                # Check data point count
                n_valid = count_valid_points(shard_file, sensor_var)
                if n_valid < min_pts:
                    excluded_lsd_points[sensor_var] += 1
                    continue

                # Check exclusion
                mid_time = get_mid_time(shard_file)
                if mid_time is not None and is_excluded(exclusions, sensor_var, mid_time):
                    excluded_lsd_embargo[sensor_var] += 1
                    continue

                copy_shard(shard_file, output_dir)
                copied_lsd[sensor_var] += 1

    print(f"LSD files copied per sensor:")
    for s in LSD_SENSORS:
        print(f"    {s:20s} {copied_lsd[s]:>5} copied, "
              f"{excluded_lsd_points[s]} excluded (too few points), "
              f"{excluded_lsd_embargo[s]} excluded (embargo)")

    # ── Summary ───────────────────────────────────────────────────────────────
    total_copied = sum(copied_hsd.values()) + sum(copied_lsd.values())
    print(f"\n=== Total files written to ~/ooi/postproc/{pp_folder}/redux/: {total_copied} ===")

    # Write README
    readme_dir = POSTPROC_BASE / pp_folder
    readme_dir.mkdir(parents=True, exist_ok=True)
    readme_path = readme_dir / "README.md"
    readme_path.write_text(
        f"# {pp_folder} - {label} profiles\n\n"
        f"Generated by: ~/argosy/postprocess_special_profiles.py {label}\n\n"
        f"## HSD sensors (all 9 profiles, ascent)\n\n"
        f"Source: {label} profiles from ~/ooi/metadata/ metadata CSV\n"
        f"Filter: shallowest depth <= 50m, sensor exclusions applied\n"
        f"Sensors: {', '.join(HSD_SENSORS)}\n\n"
        f"## LSD sensors (daily_index 4 and 9 only)\n\n"
        f"Source: all redux shards with daily_index in {{4, 9}}\n"
        f"Filter: minimum valid data points (nitrate >= {LSD_SENSORS['nitrate']['min_points']}, "
        f"pH >= {LSD_SENSORS['ph']['min_points']}, "
        f"pCO2 >= {LSD_SENSORS['pco2']['min_points']}), sensor exclusions applied\n"
        f"Sensors: {', '.join(LSD_SENSORS.keys())}\n\n"
        f"## Sensor exclusions\n\n"
        f"Exclusion windows loaded from ~/argosy/sensor_exclusions.csv\n"
        f"Files within exclusion windows are not copied.\n"
    )
    print(f"README: {readme_path}")


if __name__ == "__main__":
    main()
