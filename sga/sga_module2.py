# Module 2: Interpolate profiles to standard depth grid
# Creates the feature matrix using global-index-based file lookup.
# Run this as: %run /home/rob/argosy/sga/sga_module2.py

import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path
import pickle

# Output directory
SGA_DIR = Path('~/ooi/analysis/sga').expanduser()

# Load config
with open(SGA_DIR / 'sga_config.pkl', 'rb') as f:
    config = pickle.load(f)

SENSORS = config['sensors']
STANDARD_DEPTHS = np.array(config['standard_depths'])

# Load profile index and sensor file lookup from Module 1
profile_index = pd.read_csv(SGA_DIR / 'profile_index.csv')
profile_index['date'] = pd.to_datetime(profile_index['date'])

with open(SGA_DIR / 'sensor_files.pkl', 'rb') as f:
    sensor_files = pickle.load(f)

n_profiles = len(profile_index)
n_depths = len(STANDARD_DEPTHS)
n_features = len(SENSORS) * n_depths

print(f"Module 2: Feature Matrix")
print(f"  Profiles: {n_profiles}")
print(f"  Sensors ({len(SENSORS)}): {SENSORS}")
print(f"  Depth grid: {STANDARD_DEPTHS[0]:.0f}-{STANDARD_DEPTHS[-1]:.0f}m, {n_depths} bins")
print(f"  Feature matrix: ({n_profiles}, {n_features})")


def interpolate_profile(filepath, sensor_name, standard_depths):
    """Interpolate a single profile to standard depth grid."""
    try:
        ds = xr.open_dataset(filepath)
        sensor_data = ds[sensor_name].values
        depth = ds['depth'].values
        ds.close()

        valid_mask = ~(np.isnan(sensor_data) | np.isnan(depth))
        if not np.any(valid_mask) or len(depth[valid_mask]) < 2:
            return np.full(len(standard_depths), np.nan)

        depth_clean = depth[valid_mask]
        data_clean = sensor_data[valid_mask]

        sort_idx = np.argsort(depth_clean)
        depth_sorted = depth_clean[sort_idx]
        data_sorted = data_clean[sort_idx]

        interp_data = np.interp(standard_depths, depth_sorted, data_sorted,
                                left=np.nan, right=np.nan)
        return interp_data

    except Exception:
        return np.full(len(standard_depths), np.nan)


# Create feature matrix
feature_matrix = np.full((n_profiles, n_features), np.nan)

feature_names = []
for sensor in SENSORS:
    for depth in STANDARD_DEPTHS:
        feature_names.append(f"{sensor}_{depth:.0f}m")

# Interpolate all profiles
print("\n  Interpolating profiles...")
for sensor_idx, sensor in enumerate(SENSORS):
    print(f"    {sensor}...", end=' ')
    start_col = sensor_idx * n_depths
    end_col = start_col + n_depths

    processed = 0
    for row_idx, row in profile_index.iterrows():
        gidx = row['global_idx']
        filepath = sensor_files[sensor].get(gidx)
        if filepath is None:
            continue

        filepath = Path(filepath)
        if not filepath.exists():
            continue

        interp_data = interpolate_profile(filepath, sensor, STANDARD_DEPTHS)
        feature_matrix[row_idx, start_col:end_col] = interp_data
        processed += 1

    print(f"{processed}/{n_profiles}")

# Completeness statistics
print("\n=== Data Completeness ===")
for sensor_idx, sensor in enumerate(SENSORS):
    start_col = sensor_idx * n_depths
    end_col = start_col + n_depths
    sensor_data = feature_matrix[:, start_col:end_col]
    completeness = np.sum(~np.isnan(sensor_data)) / sensor_data.size * 100
    print(f"  {sensor}: {completeness:.1f}%")

overall = np.sum(~np.isnan(feature_matrix)) / feature_matrix.size * 100
print(f"  Overall: {overall:.1f}%")

profile_completeness = np.sum(~np.isnan(feature_matrix), axis=1) / n_features
good = np.sum(profile_completeness >= 0.5)
print(f"  Profiles >=50% data: {good}/{n_profiles} ({good/n_profiles*100:.1f}%)")

# Save
np.save(SGA_DIR / 'feature_matrix.npy', feature_matrix)
with open(SGA_DIR / 'feature_names.pkl', 'wb') as f:
    pickle.dump(feature_names, f)

print(f"\n=== Module 2 Complete ===")
