#!/usr/bin/env python3
"""
Post-process redux shard files into pp01 (noon) or pp02 (midnight) subsets.

Usage:
    python postprocess_special_profiles.py noon
    python postprocess_special_profiles.py midnight

Reads the corresponding metadata CSV from ~/ooi/metadata/, applies a depth filter,
and copies qualifying shard files to ~/ooi/postproc/pp01/ or pp02/ with V1 -> V2 rename.
Also generates depth histograms in ~/ooi/visualizations/.
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

PROFILE_LISTS = {
    "noon": METADATA_DIR / "ooi_rca_sb_noon_global_profile_indices.csv",
    "midnight": METADATA_DIR / "ooi_rca_sb_midnight_global_profile_indices.csv",
}

PP_FOLDERS = {
    "noon": "pp01",
    "midnight": "pp02",
}

MAX_SHALLOW_DEPTH = 50.0  # exclude profiles that never got above this depth

SENSORS = [
    "temperature", "salinity", "density", "dissolvedoxygen",
    "cdom", "chlora", "backscatter", "ph"
]


# ── Functions ─────────────────────────────────────────────────────────────────

def find_shards_for_profile(global_index, year):
    """Find all shard files in redux for a given global profile index and year."""
    redux_dir = REDUX_BASE / f"redux{year}"
    if not redux_dir.exists():
        return []
    # Shard filename pattern: RCA_sb_sp_<sensor>_<year>_<ddd>_<global_index>_<daily>_V1.nc
    pattern = f"*_{global_index}_*_V1.nc"
    matches = list(redux_dir.glob(pattern))
    # Filter to ensure the global index field (field 6, 0-indexed) matches exactly
    verified = []
    for f in matches:
        parts = f.stem.split("_")
        if len(parts) >= 8 and parts[6] == str(global_index):
            verified.append(f)
    return verified


def check_depth_filter(shard_files):
    """
    Check depth filter using the temperature shard.
    Returns True if profile passes (shallowest depth <= 50m), False if excluded.
    """
    temp_files = [f for f in shard_files if "_temperature_" in f.name]
    if not temp_files:
        return False  # no temperature shard means we can't verify; exclude
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
    except Exception:
        return False


def copy_shard(src_path, output_dir):
    """Copy a shard file, renaming V1 to V2."""
    output_dir.mkdir(parents=True, exist_ok=True)
    new_name = src_path.name.replace("_V1.nc", "_V2.nc")
    dst_path = output_dir / new_name
    shutil.copy2(src_path, dst_path)
    return dst_path


def generate_histograms(depth_data, pp_label):
    """Generate deep and shallow depth histograms."""
    deepest = np.array(depth_data["deepest"])
    shallowest = np.array(depth_data["shallowest"])

    bins = np.arange(0, 210, 2)  # 2-meter bins from 0 to 208

    # Deepest depth histogram - x-axis brackets non-zero data by 6m on each side
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(deepest, bins=bins, color="steelblue", edgecolor="black", linewidth=0.3)
    ax.set_xlabel("Deepest recorded depth (m)", fontsize=12)
    ax.set_ylabel("Number of profiles", fontsize=12)
    ax.set_title(f"{pp_label.upper()} - Deepest recorded depth per profile (2m bins)", fontsize=13)
    ax.set_xlim(float(np.min(deepest)) - 6, float(np.max(deepest)) + 6)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out_path = VIZ_DIR / f"{PP_FOLDERS[pp_label]}_depth_histogram_deep.png"
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"  Histogram saved: {out_path}")

    # Shallowest depth histogram - x-axis brackets non-zero data by 6m on each side
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(shallowest, bins=bins, color="coral", edgecolor="black", linewidth=0.3)
    ax.set_xlabel("Shallowest recorded depth (m)", fontsize=12)
    ax.set_ylabel("Number of profiles", fontsize=12)
    ax.set_title(f"{pp_label.upper()} - Shallowest recorded depth per profile (2m bins)", fontsize=13)
    ax.set_xlim(float(np.min(shallowest)) - 6, float(np.max(shallowest)) + 6)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out_path = VIZ_DIR / f"{PP_FOLDERS[pp_label]}_depth_histogram_shallow.png"
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"  Histogram saved: {out_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("noon", "midnight"):
        print("Usage: python postprocess_special_profiles.py <noon|midnight>")
        sys.exit(1)

    label = sys.argv[1]
    pp_folder = PP_FOLDERS[label]
    csv_path = PROFILE_LISTS[label]

    print(f"=== Post-processing: {label} -> {pp_folder} ===\n")

    # Read profile list
    if not csv_path.exists():
        print(f"ERROR: Metadata CSV not found: {csv_path}")
        sys.exit(1)

    df = pd.read_csv(csv_path, parse_dates=["start", "peak", "end"])
    total_profiles = len(df)
    print(f"Profiles in metadata CSV: {total_profiles}")

    # Ensure output directories exist
    VIZ_DIR.mkdir(parents=True, exist_ok=True)

    # Process each profile
    excluded_depth = 0
    missing_temp = 0
    copied_per_sensor = {s: 0 for s in SENSORS}
    missing_shards = 0
    included_profiles = 0
    depth_data = {"deepest": [], "shallowest": []}

    for _, row in df.iterrows():
        global_index = int(row["profile"])
        year = row["start"].year

        # Find all shards for this profile
        shard_files = find_shards_for_profile(global_index, year)

        if not shard_files:
            missing_temp += 1
            continue

        # Apply depth filter on temperature shard
        if not check_depth_filter(shard_files):
            excluded_depth += 1
            continue

        # Profile passes - collect depth stats from temperature shard
        temp_files = [f for f in shard_files if "_temperature_" in f.name]
        if temp_files:
            try:
                ds = xr.open_dataset(temp_files[0])
                if "depth" in ds.data_vars:
                    depth_vals = ds["depth"].values
                elif "depth" in ds.coords:
                    depth_vals = ds["depth"].values
                else:
                    depth_vals = np.array([])
                ds.close()
                if len(depth_vals) > 0:
                    depth_data["deepest"].append(float(np.nanmax(depth_vals)))
                    depth_data["shallowest"].append(float(np.nanmin(depth_vals)))
            except Exception:
                pass

        # Copy all sensor shards for this profile
        included_profiles += 1
        output_dir = POSTPROC_BASE / pp_folder / "redux" / f"redux{year}"

        for shard_file in shard_files:
            # Determine sensor from filename
            parts = shard_file.stem.split("_")
            if len(parts) >= 4:
                sensor = parts[3]
                if sensor in SENSORS:
                    copy_shard(shard_file, output_dir)
                    copied_per_sensor[sensor] += 1
                # else: skip sensors not in our list

    # Write README
    readme_dir = POSTPROC_BASE / pp_folder
    readme_dir.mkdir(parents=True, exist_ok=True)
    readme_path = readme_dir / "README.md"
    readme_path.write_text(
        f"# {pp_folder} - {label} profiles\n\n"
        f"Source: ~/ooi/redux/redux<yyyy>\n\n"
        f"Filter 1: Only {label} profiles per ~/ooi/metadata/ooi_rca_sb_{label}_global_profile_indices.csv\n\n"
        f"Filter 2: Excluded profiles where shallowest recorded depth > 50m "
        f"(min(depth) > 50 means exclude)\n\n"
        f"Data: Byte-identical copies of redux shard files; "
        f"V2 version tag indicates subset selection only\n\n"
        f"Generated by: ~/argosy/postprocess_special_profiles.py {label}\n"
    )

    # Generate histograms
    print(f"\nGenerating depth histograms...")
    if depth_data["deepest"]:
        generate_histograms(depth_data, label)
    else:
        print("  No depth data available for histograms")

    # Print summary
    print(f"\n=== Summary ===")
    print(f"  Profiles in CSV:          {total_profiles}")
    print(f"  No shards found in redux: {missing_temp}")
    print(f"  Excluded (depth > 50m):   {excluded_depth}")
    print(f"  Included:                 {included_profiles}")
    print(f"\n  Shards copied per sensor:")
    for sensor in SENSORS:
        count = copied_per_sensor[sensor]
        if count > 0:
            print(f"    {sensor:20s} {count}")
    total_copied = sum(copied_per_sensor.values())
    print(f"    {'TOTAL':20s} {total_copied}")
    print(f"\n  Output: ~/ooi/postproc/{pp_folder}/redux/")
    print(f"  README: {readme_path}")


if __name__ == "__main__":
    main()
