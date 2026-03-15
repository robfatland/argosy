# Module 2: Interpolate profiles to standard depth grid
# Creates feature vectors for each profile

import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path
import pickle

# Load profile index
profile_index = pd.read_csv('profile_index.csv')
profile_index['date'] = pd.to_datetime(profile_index['date'])

# Configuration
SENSORS = ['temperature', 'salinity', 'density', 'dissolvedoxygen', 'cdom', 'chlora', 'backscatter']
STANDARD_DEPTHS = np.linspace(0, 180, 91)  # 2m resolution
start_year = profile_index['year'].min()
end_year = profile_index['year'].max()

print(f"Interpolating {len(profile_index)} profiles to standard depth grid...")
print(f"Standard depths: {len(STANDARD_DEPTHS)} levels (0-180m, 2m resolution)")

# Collect profile files by sensor
all_profiles = {}
for sensor in SENSORS:
    profile_files = []
    for year in range(start_year, end_year + 1):
        redux_dir = Path(f"~/redux{year}").expanduser()
        if redux_dir.exists():
            year_files = sorted(list(redux_dir.glob(f"*_{sensor}_*.nc")))
            profile_files.extend(year_files)
    all_profiles[sensor] = profile_files

def interpolate_profile(filepath, sensor_name, standard_depths):
    """Interpolate a single profile to standard depth grid."""
    try:
        ds = xr.open_dataset(filepath)
        sensor_data = ds[sensor_name].values
        depth = ds['depth'].values
        
        # Remove NaN values
        valid_mask = ~(np.isnan(sensor_data) | np.isnan(depth))
        if not np.any(valid_mask) or len(depth[valid_mask]) < 2:
            return np.full(len(standard_depths), np.nan)
        
        depth_clean = depth[valid_mask]
        data_clean = sensor_data[valid_mask]
        
        # Sort by depth
        sort_idx = np.argsort(depth_clean)
        depth_sorted = depth_clean[sort_idx]
        data_sorted = data_clean[sort_idx]
        
        # Interpolate to standard depths
        interp_data = np.interp(standard_depths, depth_sorted, data_sorted, 
                               left=np.nan, right=np.nan)
        
        return interp_data
        
    except Exception as e:
        return np.full(len(standard_depths), np.nan)

# Create feature matrix
# Shape: (n_profiles, n_sensors * n_depths)
n_profiles = len(profile_index)
n_features = len(SENSORS) * len(STANDARD_DEPTHS)

feature_matrix = np.zeros((n_profiles, n_features))
feature_names = []

# Build feature names
for sensor in SENSORS:
    for depth in STANDARD_DEPTHS:
        feature_names.append(f"{sensor}_{depth:.0f}m")

print(f"\nFeature matrix shape: {feature_matrix.shape}")
print(f"Features per profile: {n_features}")

# Interpolate all profiles
print("\nInterpolating profiles...")
for sensor_idx, sensor in enumerate(SENSORS):
    print(f"\n  Processing {sensor}...")
    sensor_files = all_profiles[sensor]
    
    for profile_idx in range(n_profiles):
        if (profile_idx + 1) % 500 == 0:
            print(f"    Profile {profile_idx + 1}/{n_profiles}")
        
        if profile_idx < len(sensor_files):
            interp_data = interpolate_profile(sensor_files[profile_idx], sensor, STANDARD_DEPTHS)
            
            # Store in feature matrix
            start_col = sensor_idx * len(STANDARD_DEPTHS)
            end_col = start_col + len(STANDARD_DEPTHS)
            feature_matrix[profile_idx, start_col:end_col] = interp_data

# Calculate completeness statistics
print("\n=== Data Completeness ===")
for sensor_idx, sensor in enumerate(SENSORS):
    start_col = sensor_idx * len(STANDARD_DEPTHS)
    end_col = start_col + len(STANDARD_DEPTHS)
    sensor_data = feature_matrix[:, start_col:end_col]
    
    completeness = np.sum(~np.isnan(sensor_data)) / sensor_data.size * 100
    print(f"{sensor}: {completeness:.1f}% complete")

# Overall completeness
overall_completeness = np.sum(~np.isnan(feature_matrix)) / feature_matrix.size * 100
print(f"\nOverall: {overall_completeness:.1f}% complete")

# Count profiles with at least 50% data
profile_completeness = np.sum(~np.isnan(feature_matrix), axis=1) / n_features
good_profiles = np.sum(profile_completeness >= 0.5)
print(f"\nProfiles with ≥50% data: {good_profiles}/{n_profiles} ({good_profiles/n_profiles*100:.1f}%)")

# Save feature matrix
print("\nSaving feature matrix...")
np.save('feature_matrix.npy', feature_matrix)
with open('feature_names.pkl', 'wb') as f:
    pickle.dump(feature_names, f)

print("Feature matrix saved to feature_matrix.npy")
print("Feature names saved to feature_names.pkl")
