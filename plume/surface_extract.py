# surface_extract.py — Extract near-surface summary statistics from pp06 profiles.
# Run this as: %run ~/argosy/plume/surface_extract.py
#
# For each profile (by GPI), extracts the shallowest 10 valid measurements of
# salinity, temperature, dissolved oxygen, and CDOM. Computes mean, std, and
# vertical gradient for each sensor. Saves results to CSV.
#
# Output: ~/ooi/metadata/surface_extract_<site>.csv
#
# This supports the Columbia River plume detection analysis (see ColumbiaPlumePlan.md).

import numpy as np
import xarray as xr
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# == Configuration =============================================================

PP06_BASE = Path("~/ooi/postproc/pp06").expanduser()
OUTPUT_DIR = Path("~/ooi/metadata").expanduser()
EXCLUSIONS_CSV = Path("~/argosy/sensor_exclusions.csv").expanduser()

# Sensors to extract
SENSORS = ['salinity', 'temperature', 'dissolvedoxygen', 'cdom']

# Number of shallowest points to use
N_POINTS = 10

# Site: For now this script processes Slope Base (RS01SBPS).
# Change SITE_NAME and year folders as needed for Oregon Offshore.
SITE_NAME = "slopebase"

# Year range
START_YEAR = 2015
END_YEAR = 2025


# == Sensor exclusions =========================================================

_sensor_exclusions = {}
if EXCLUSIONS_CSV.exists():
    _exc_df = pd.read_csv(EXCLUSIONS_CSV)
    for _, row in _exc_df.iterrows():
        _sensor_exclusions.setdefault(row['sensor'], []).append(
            (np.datetime64(row['start']), np.datetime64(row['end'])))


def is_excluded(sensor, timestamp):
    """Check if a sensor measurement at timestamp falls in an exclusion window."""
    if sensor not in _sensor_exclusions:
        return False
    for exc_start, exc_end in _sensor_exclusions[sensor]:
        if exc_start <= timestamp <= exc_end:
            return True
    return False


# == Build GPI index ===========================================================

print(f"Scanning pp06 for {SITE_NAME} ({START_YEAR}–{END_YEAR})...")

# Index: {gpi: {sensor: filepath}}
gpi_index = {}

for year in range(START_YEAR, END_YEAR + 1):
    redux_dir = PP06_BASE / f"redux{year}"
    if not redux_dir.exists():
        continue
    for sensor in SENSORS:
        for f in redux_dir.glob(f"*_{sensor}_*.nc"):
            parts = f.stem.split('_')
            gpi = int(parts[6])
            if gpi not in gpi_index:
                gpi_index[gpi] = {}
            gpi_index[gpi][sensor] = f

all_gpis = sorted(gpi_index.keys())
print(f"  Found {len(all_gpis)} unique GPIs with at least one sensor file.")


# == Extract surface statistics ================================================

records = []
n_processed = 0
n_skipped = 0

for gpi in all_gpis:
    sensor_files = gpi_index[gpi]

    # We need at least salinity to proceed (primary plume indicator)
    if 'salinity' not in sensor_files:
        n_skipped += 1
        continue

    # Get timestamp and observation depth from salinity file (reference sensor)
    sal_path = sensor_files['salinity']
    try:
        ds = xr.open_dataset(sal_path)
    except Exception:
        n_skipped += 1
        continue

    sal_data = ds['salinity'].values
    depth = ds['depth'].values
    time_vals = ds['time'].values

    # Normalize depth to positive-down (some shards use negative convention)
    depth = np.abs(depth)

    # Valid mask
    valid = ~(np.isnan(sal_data) | np.isnan(depth))
    if np.sum(valid) < N_POINTS:
        ds.close()
        n_skipped += 1
        continue

    sal_clean = sal_data[valid]
    depth_clean = depth[valid]
    time_clean = time_vals[valid]

    # Sort by depth (shallowest first)
    sort_idx = np.argsort(depth_clean)
    sal_sorted = sal_clean[sort_idx]
    depth_sorted = depth_clean[sort_idx]
    time_sorted = time_clean[sort_idx]

    # Take shallowest N_POINTS
    sal_top = sal_sorted[:N_POINTS]
    depth_top = depth_sorted[:N_POINTS]

    # Observation depth: shallowest measurement
    obs_depth = depth_top[0]

    # Timestamp: time at shallowest point
    timestamp = pd.Timestamp(time_sorted[0])

    # Check exclusion for salinity
    mid_time = np.datetime64(timestamp)
    if is_excluded('salinity', mid_time):
        ds.close()
        n_skipped += 1
        continue

    # Salinity stats
    sal_mean = np.mean(sal_top)
    sal_std = np.std(sal_top, ddof=1) if N_POINTS > 1 else 0.0

    # Gradient: dS/dz over the N-point window (positive = freshening toward surface)
    if depth_top[-1] - depth_top[0] > 0:
        dsal_dz = (sal_top[-1] - sal_top[0]) / (depth_top[-1] - depth_top[0])
    else:
        dsal_dz = 0.0

    ds.close()

    # Extract other sensors at the same depth range
    record = {
        'site': SITE_NAME,
        'gpi': gpi,
        'timestamp': timestamp.isoformat(),
        'obs_depth_m': round(obs_depth, 2),
        'n_points': N_POINTS,
        'sal_mean': round(sal_mean, 4),
        'sal_std': round(sal_std, 4),
        'dsal_dz': round(dsal_dz, 5),
    }

    for sensor in ['temperature', 'dissolvedoxygen', 'cdom']:
        prefix = sensor[:4] if sensor != 'dissolvedoxygen' else 'do'
        if sensor not in sensor_files:
            record[f'{prefix}_mean'] = np.nan
            record[f'{prefix}_std'] = np.nan
            continue

        if is_excluded(sensor, mid_time):
            record[f'{prefix}_mean'] = np.nan
            record[f'{prefix}_std'] = np.nan
            continue

        try:
            ds2 = xr.open_dataset(sensor_files[sensor])
            s_data = ds2[sensor].values
            s_depth = np.abs(ds2['depth'].values)

            s_valid = ~(np.isnan(s_data) | np.isnan(s_depth))
            if np.sum(s_valid) < N_POINTS:
                record[f'{prefix}_mean'] = np.nan
                record[f'{prefix}_std'] = np.nan
                ds2.close()
                continue

            s_clean = s_data[s_valid]
            s_depth_clean = s_depth[s_valid]

            # Sort by depth, take shallowest N
            s_sort = np.argsort(s_depth_clean)
            s_top = s_clean[s_sort][:N_POINTS]

            record[f'{prefix}_mean'] = round(np.mean(s_top), 4)
            record[f'{prefix}_std'] = round(np.std(s_top, ddof=1), 4) if N_POINTS > 1 else 0.0
            ds2.close()

        except Exception:
            record[f'{prefix}_mean'] = np.nan
            record[f'{prefix}_std'] = np.nan

    records.append(record)
    n_processed += 1

    if n_processed % 500 == 0:
        print(f"  Processed {n_processed} profiles...")


# == Write CSV =================================================================

df = pd.DataFrame(records)
output_path = OUTPUT_DIR / f"surface_extract_{SITE_NAME}.csv"
output_path.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(output_path, index=False)

print(f"\nDone. {n_processed} profiles extracted, {n_skipped} skipped.")
print(f"Output: {output_path}")
print(f"Columns: {list(df.columns)}")
