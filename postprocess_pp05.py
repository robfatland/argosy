#!/usr/bin/env python3
"""
Generate pp05 manifest: Quality-controlled analysis dataset (manifest-based).

Instead of copying files, this script produces a manifest CSV listing which
redux shard files pass QC. Analysis code reads the manifest and accesses
files directly from redux.

Usage:
    python postprocess_pp05.py

Output:
    ~/ooi/metadata/pp05_manifest.csv
    ~/ooi/metadata/pp05_exclusion_summary.csv

The manifest CSV has columns:
    filepath, sensor, year, doy, global_idx, daily_idx, n_valid, n_suspect
"""

import sys
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
import xarray as xr


# ── Configuration ─────────────────────────────────────────────────────────────

REDUX_BASE = Path.home() / "ooi" / "redux"
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
    "backscatter":     (-0.0001, 0.015),
    "par":             (-1.0, 1500.0),
    "nitrate":         (-2.0, 45.0),
    "pco2":            (100.0, 2000.0),
    "ph":              (7.0, 8.5),
}

SUSPECT_FRACTION_THRESHOLD = 0.20

HSD_SENSORS = [
    "temperature", "salinity", "density", "dissolvedoxygen",
    "cdom", "chlora", "backscatter", "par"
]

LSD_SENSORS = {
    "nitrate": 50,
    "ph": 5,
    "pco2": 5,
}

ALL_SENSORS = HSD_SENSORS + list(LSD_SENSORS.keys())

PAR_EXCLUDED_INDICES = {3, 4, 5}
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
    Returns: (pass, n_valid, n_suspect)
    """
    smin, smax = SUSPECT_RANGES[sensor_var]
    try:
        ds = xr.open_dataset(filepath)
        vals = ds[sensor_var].values
        ds.close()
    except:
        return False, 0, 0

    valid_mask = ~np.isnan(vals)
    n_valid = int(valid_mask.sum())
    if n_valid == 0:
        return False, 0, 0

    valid_vals = vals[valid_mask]
    suspect_mask = (valid_vals < smin) | (valid_vals > smax)
    n_suspect = int(suspect_mask.sum())

    if n_suspect > SUSPECT_FRACTION_THRESHOLD * n_valid:
        return False, n_valid, n_suspect

    return True, n_valid, n_suspect


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
    print("=== Generating pp05 manifest (QC analysis dataset) ===\n")

    exclusions = load_exclusions()
    if exclusions:
        print(f"Loaded {sum(len(v) for v in exclusions.values())} exclusion window(s)")

    year_dirs = sorted(REDUX_BASE.glob("redux*"))
    years = [int(d.name.replace("redux", "")) for d in year_dirs if d.is_dir()]
    print(f"Redux years: {years[0]}-{years[-1]}")

    stats = {s: {'included': 0, 'excl_embargo': 0, 'excl_range': 0,
                 'excl_points': 0, 'excl_par_night': 0, 'n_suspect_total': 0}
             for s in ALL_SENSORS}

    # Resume logic: check which years are already in the manifest
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = METADATA_DIR / "pp05_manifest.csv"
    completed_years = set()
    if manifest_path.exists():
        existing = pd.read_csv(manifest_path)
        completed_years = set(existing['year'].unique())
        # Rebuild stats from existing data
        for s in ALL_SENSORS:
            sensor_rows = existing[existing['sensor'] == s]
            stats[s]['included'] = len(sensor_rows)
            stats[s]['n_suspect_total'] = int(sensor_rows['n_suspect'].sum())
        if completed_years:
            print(f"Resuming: years already done: {sorted(completed_years)}")
    else:
        # Write header for new manifest
        with open(manifest_path, 'w') as f:
            f.write("filepath,sensor,year,doy,global_idx,daily_idx,n_valid,n_suspect\n")

    for year in years:
        if year in completed_years:
            continue

        redux_dir = REDUX_BASE / f"redux{year}"
        if not redux_dir.exists():
            continue

        year_rows = []

        try:
            # HSD sensors
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

                    if sensor_var == 'par' and parts['daily_idx'] in PAR_EXCLUDED_INDICES:
                        stats[sensor_var]['excl_par_night'] += 1
                        continue

                    mid_time = get_mid_time(f)
                    if mid_time is None:
                        continue
                    if is_excluded(exclusions, sensor_var, mid_time):
                        stats[sensor_var]['excl_embargo'] += 1
                        continue

                    passes, n_valid, n_suspect = check_gross_range(f, sensor_var)
                    if not passes:
                        stats[sensor_var]['excl_range'] += 1
                        continue

                    stats[sensor_var]['included'] += 1
                    stats[sensor_var]['n_suspect_total'] += n_suspect
                    year_rows.append(
                        f"{f},{sensor_var},{parts['year']},{parts['doy']},"
                        f"{parts['global_idx']},{parts['daily_idx']},{n_valid},{n_suspect}\n")

            # LSD sensors
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

                    if parts['daily_idx'] not in LSD_DAILY_INDICES:
                        continue

                    try:
                        ds = xr.open_dataset(f)
                        vals = ds[sensor_var].values
                        ds.close()
                        n_valid_pts = int(np.sum(~np.isnan(vals)))
                    except:
                        continue

                    if n_valid_pts < min_pts:
                        stats[sensor_var]['excl_points'] += 1
                        continue

                    mid_time = get_mid_time(f)
                    if mid_time is None:
                        continue
                    if is_excluded(exclusions, sensor_var, mid_time):
                        stats[sensor_var]['excl_embargo'] += 1
                        continue

                    passes, n_valid, n_suspect = check_gross_range(f, sensor_var)
                    if not passes:
                        stats[sensor_var]['excl_range'] += 1
                        continue

                    stats[sensor_var]['included'] += 1
                    stats[sensor_var]['n_suspect_total'] += n_suspect
                    year_rows.append(
                        f"{f},{sensor_var},{parts['year']},{parts['doy']},"
                        f"{parts['global_idx']},{parts['daily_idx']},{n_valid},{n_suspect}\n")

            # Append this year's rows to manifest
            with open(manifest_path, 'a') as f:
                f.writelines(year_rows)

            print(f"  {year} done ({len(year_rows)} files)")
            sys.stdout.flush()
        except Exception as e:
            print(f"  {year} ERROR: {e}")
            sys.stdout.flush()

    # Write exclusion summary (stats may be incomplete if resumed — re-read manifest for accuracy)
    manifest_df = pd.read_csv(manifest_path)
    summary_path = METADATA_DIR / "pp05_exclusion_summary.csv"
    with open(summary_path, 'w') as f:
        f.write("sensor,included,excl_embargo,excl_range,excl_points,excl_par_night,n_suspect_values\n")
        for s in ALL_SENSORS:
            st = stats[s]
            f.write(f"{s},{st['included']},{st['excl_embargo']},"
                    f"{st['excl_range']},{st['excl_points']},"
                    f"{st['excl_par_night']},{st['n_suspect_total']}\n")

    # Print summary
    print(f"\n{'='*70}")
    print(f"{'Sensor':<18} {'Included':>9} {'Embargo':>8} {'Range':>7} {'Points':>7} {'PARnite':>8} {'Suspect':>8}")
    print(f"{'-'*70}")
    total_included = 0
    for s in ALL_SENSORS:
        st = stats[s]
        total_included += st['included']
        print(f"{s:<18} {st['included']:>9} {st['excl_embargo']:>8} "
              f"{st['excl_range']:>7} {st['excl_points']:>7} "
              f"{st['excl_par_night']:>8} {st['n_suspect_total']:>8}")
    print(f"{'-'*70}")
    print(f"{'TOTAL':<18} {total_included:>9}")
    print(f"\nManifest: {manifest_path} ({len(manifest_df)} entries)")
    print(f"Summary:  {summary_path}")


if __name__ == "__main__":
    main()
