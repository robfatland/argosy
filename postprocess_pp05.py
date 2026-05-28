#!/usr/bin/env python3
"""
Post-process redux shard files into pp05: Quality-controlled analysis dataset.

Usage:
    python postprocess_pp05.py

Selection:
  - HSD sensors: all 9 daily profiles (PAR excludes daily_index 3, 4, 5)
  - LSD sensors: daily_index 4 and 9 only, minimum data point filter

QC filters:
  - Tier 1: Time-window exclusions from sensor_exclusions.csv
  - Tier 2: Per-profile gross range filter (site-specific suspect thresholds)

Output: ~/ooi/postproc/pp05/redux/redux<yyyy>/
"""

import sys
import shutil
from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import numpy as np
import pandas as pd
import xarray as xr


# ── Configuration ─────────────────────────────────────────────────────────────

REDUX_BASE = Path.home() / "ooi" / "redux"
POSTPROC_BASE = Path.home() / "ooi" / "postproc" / "pp05"
METADATA_DIR = Path.home() / "ooi" / "metadata"
EXCLUSIONS_CSV = Path.home() / "argosy" / "sensor_exclusions.csv"

# Site-specific suspect ranges (Oregon Slope Base, 0-200m)
SUSPECT_RANGES = {
    "temperature":     (2.0, 22.0),
    "salinity":        (30.0, 35.5),
    "density":         (1022.0, 1028.5),
    "dissolvedoxygen": (10.0, 350.0),
    "cdom":            (-0.5, 10.0),
    "chlora":          (-0.1, 10.0),
    "backscatter":     (-0.0001, 0.005),
    "par":             (-1.0, 1500.0),
    "nitrate":         (-2.0, 45.0),
    "pco2":            (100.0, 2000.0),
    "ph":              (7.0, 8.5),
}

# Fraction of suspect values that triggers full-profile exclusion
SUSPECT_FRACTION_THRESHOLD = 0.20

HSD_SENSORS = [
    "temperature", "salinity", "density", "dissolvedoxygen",
    "cdom", "chlora", "backscatter", "par"
]

LSD_SENSORS = {
    "nitrate": 50,   # min valid points
    "ph": 5,
    "pco2": 5,
}

ALL_SENSORS = HSD_SENSORS + list(LSD_SENSORS.keys())

# PAR: exclude daily_index 3, 4, 5 (midnight ± 1)
PAR_EXCLUDED_INDICES = {3, 4, 5}

# LSD: only daily_index 4 and 9
LSD_DAILY_INDICES = {4, 9}


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_exclusions():
    exclusions = {}
    if EXCLUSIONS_CSV.exists():
        df = pd.read_csv(EXCLUSIONS_CSV)
        for _, row in df.iterrows():
            exclusions.setdefault(row['sensor'], []).append(
                (np.datetime64(row['start']), np.datetime64(row['end'])))
    return exclusions


def is_excluded(exclusions, sensor_var, mid_time):
    if sensor_var not in exclusions:
        return False
    for exc_start, exc_end in exclusions[sensor_var]:
        if exc_start <= mid_time <= exc_end:
            return True
    return False


def get_file_parts(filepath):
    """Parse shard filename into components."""
    parts = Path(filepath).stem.split('_')
    return {
        'sensor': parts[3],
        'year': int(parts[4]),
        'doy': int(parts[5]),
        'global_idx': int(parts[6]),
        'daily_idx': int(parts[7]),
    }


def check_gross_range(filepath, sensor_var):
    """
    Check if profile passes gross range filter.
    Returns: (pass, n_valid, n_suspect, n_total)
    - pass: True if file should be included
    - If pass=True but n_suspect > 0, suspect values should be NaN'd
    """
    smin, smax = SUSPECT_RANGES[sensor_var]

    try:
        ds = xr.open_dataset(filepath)
        vals = ds[sensor_var].values
        ds.close()
    except:
        return False, 0, 0, 0

    n_total = len(vals)
    valid_mask = ~np.isnan(vals)
    n_valid = int(valid_mask.sum())

    if n_valid == 0:
        return False, 0, 0, n_total

    valid_vals = vals[valid_mask]
    suspect_mask = (valid_vals < smin) | (valid_vals > smax)
    n_suspect = int(suspect_mask.sum())

    if n_suspect > SUSPECT_FRACTION_THRESHOLD * n_valid:
        return False, n_valid, n_suspect, n_total

    return True, n_valid, n_suspect, n_total


def copy_shard_with_qc(src_path, output_dir, sensor_var):
    """
    Copy shard file to output, NaN-ing out suspect values.
    Renames V1 to V2.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    new_name = src_path.name.replace("_V1.nc", "_V2.nc")
    dst_path = output_dir / new_name

    smin, smax = SUSPECT_RANGES[sensor_var]

    try:
        ds = xr.open_dataset(src_path)
        vals = ds[sensor_var].values
        suspect = (vals < smin) | (vals > smax)
        n_nannd = int(suspect.sum())

        if n_nannd > 0:
            # Need to modify data before saving
            vals_clean = vals.copy()
            vals_clean[suspect] = np.nan
            ds[sensor_var].values = vals_clean
            ds.to_netcdf(dst_path)
        else:
            # Byte-identical copy
            shutil.copy2(src_path, dst_path)

        ds.close()
        return n_nannd
    except:
        # Fall back to simple copy
        shutil.copy2(src_path, dst_path)
        return 0


def get_mid_time(filepath):
    try:
        ds = xr.open_dataset(filepath)
        t = ds.time.values
        ds.close()
        if len(t) > 0:
            return t[len(t) // 2]
    except:
        pass
    return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== Post-processing: pp05 (QC analysis dataset) ===\n")

    exclusions = load_exclusions()
    if exclusions:
        print(f"Loaded {sum(len(v) for v in exclusions.values())} exclusion window(s)")

    # Find all redux year directories
    year_dirs = sorted(REDUX_BASE.glob("redux*"))
    years = [int(d.name.replace("redux", "")) for d in year_dirs if d.is_dir()]
    print(f"Redux years: {years[0]}–{years[-1]}")

    # Stats tracking
    stats = {s: {'included': 0, 'excl_embargo': 0, 'excl_range': 0,
                 'excl_points': 0, 'excl_par_night': 0, 'values_nannd': 0}
             for s in ALL_SENSORS}

    # Process each year
    for year in years:
        redux_dir = REDUX_BASE / f"redux{year}"
        if not redux_dir.exists():
            continue
        output_dir = POSTPROC_BASE / "redux" / f"redux{year}"

        try:
            # Process HSD sensors
            for sensor_var in HSD_SENSORS:
                try:
                    files = sorted(redux_dir.glob(f"RCA_sb_sp_{sensor_var}_*_V1.nc"))
                except OSError:
                    continue

                for f in files:
                    try:
                        parts = get_file_parts(f)
                    except:
                        continue

                    # PAR: skip midnight ± 1
                    if sensor_var == 'par' and parts['daily_idx'] in PAR_EXCLUDED_INDICES:
                        stats[sensor_var]['excl_par_night'] += 1
                        continue

                    # Tier 1: time-window exclusion
                    mid_time = get_mid_time(f)
                    if mid_time is None:
                        continue
                    if is_excluded(exclusions, sensor_var, mid_time):
                        stats[sensor_var]['excl_embargo'] += 1
                        continue

                    # Tier 2: gross range
                    passes, n_valid, n_suspect, n_total = check_gross_range(f, sensor_var)
                    if not passes:
                        stats[sensor_var]['excl_range'] += 1
                        continue

                    # Copy (with QC NaN-ing if needed)
                    n_nannd = copy_shard_with_qc(f, output_dir, sensor_var)
                    stats[sensor_var]['included'] += 1
                    stats[sensor_var]['values_nannd'] += n_nannd

            # Process LSD sensors
            for sensor_var, min_pts in LSD_SENSORS.items():
                try:
                    files = sorted(redux_dir.glob(f"RCA_sb_sp_{sensor_var}_*_V1.nc"))
                except OSError:
                    continue

                for f in files:
                    try:
                        parts = get_file_parts(f)
                    except:
                        continue

                    # Only daily_index 4 and 9
                    if parts['daily_idx'] not in LSD_DAILY_INDICES:
                        continue

                    # Minimum points check
                    try:
                        ds = xr.open_dataset(f)
                        vals = ds[sensor_var].values
                        ds.close()
                        n_valid = int(np.sum(~np.isnan(vals)))
                    except:
                        continue

                    if n_valid < min_pts:
                        stats[sensor_var]['excl_points'] += 1
                        continue

                    # Tier 1: time-window exclusion
                    mid_time = get_mid_time(f)
                    if mid_time is None:
                        continue
                    if is_excluded(exclusions, sensor_var, mid_time):
                        stats[sensor_var]['excl_embargo'] += 1
                        continue

                    # Tier 2: gross range
                    passes, n_valid2, n_suspect, n_total = check_gross_range(f, sensor_var)
                    if not passes:
                        stats[sensor_var]['excl_range'] += 1
                        continue

                    # Copy
                    n_nannd = copy_shard_with_qc(f, output_dir, sensor_var)
                    stats[sensor_var]['included'] += 1
                    stats[sensor_var]['values_nannd'] += n_nannd

            print(f"  {year} done")
            sys.stdout.flush()
        except Exception as e:
            print(f"  {year} ERROR: {e} — skipping remainder of year")
            sys.stdout.flush()

    # Write summary
    print(f"\n{'='*70}")
    nannd_label = "NaN'd"
    print(f"{'Sensor':<18} {'Included':>9} {'Embargo':>8} {'Range':>7} {'Points':>7} {'PARnite':>8} {nannd_label:>7}")
    print(f"{'-'*70}")
    total_included = 0
    for s in ALL_SENSORS:
        st = stats[s]
        total_included += st['included']
        print(f"{s:<18} {st['included']:>9} {st['excl_embargo']:>8} "
              f"{st['excl_range']:>7} {st['excl_points']:>7} "
              f"{st['excl_par_night']:>8} {st['values_nannd']:>7}")
    print(f"{'-'*70}")
    print(f"{'TOTAL':<18} {total_included:>9}")

    # Write exclusion summary CSV
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = METADATA_DIR / "pp05_exclusion_summary.csv"
    with open(csv_path, 'w') as f:
        f.write("sensor,included,excl_embargo,excl_range,excl_points,excl_par_night,values_nannd\n")
        for s in ALL_SENSORS:
            st = stats[s]
            f.write(f"{s},{st['included']},{st['excl_embargo']},"
                    f"{st['excl_range']},{st['excl_points']},"
                    f"{st['excl_par_night']},{st['values_nannd']}\n")
    print(f"\nSummary: {csv_path}")

    # Write README
    POSTPROC_BASE.mkdir(parents=True, exist_ok=True)
    readme = POSTPROC_BASE / "README.md"
    readme.write_text(
        "# pp05 — Quality-Controlled Analysis Dataset\n\n"
        "Generated by: ~/argosy/postprocess_pp05.py\n\n"
        "## Selection\n\n"
        "- HSD sensors: all daily profiles (PAR excludes index 3,4,5)\n"
        "- LSD sensors: daily_index 4 and 9 only, min points filter\n\n"
        "## QC Filters\n\n"
        "- Tier 1: sensor_exclusions.csv time-window embargo\n"
        "- Tier 2: site-specific gross range (>20% suspect → exclude; else NaN suspect values)\n\n"
        "## Details\n\n"
        "See ~/argosy/PP05_QCAnalysis.md for full methodology.\n"
    )
    print(f"README: {readme}")
    print(f"\nTotal files in pp05: {total_included}")


if __name__ == "__main__":
    main()
