# Module 7: Characterize Water Column Regimes
# Analyzes physical properties of each cluster

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import xarray as xr
from pathlib import Path
import pickle

# Load clustering results
print("Loading clustering results...")
profile_index = pd.read_csv('profile_index_clustered.csv')
profile_index['date'] = pd.to_datetime(profile_index['date'])
cluster_labels = np.load('cluster_labels.npy')

with open('clustering_results.pkl', 'rb') as f:
    clustering_results = pickle.load(f)

n_clusters = clustering_results['n_clusters']
print(f"Clusters: {n_clusters}")
print(f"Profiles: {len(profile_index)}")

# Configuration
SENSORS = ['temperature', 'salinity', 'density', 'dissolvedoxygen', 'cdom', 'chlora', 'backscatter']
STANDARD_DEPTHS = np.linspace(0, 180, 91)

# Load profile files
print("\nLoading profile files...")
all_profiles = {}
for sensor in SENSORS:
    profile_files = []
    for year in profile_index['year'].unique():
        redux_dir = Path(f"~/redux{year}").expanduser()
        if redux_dir.exists():
            year_files = sorted(list(redux_dir.glob(f"*_{sensor}_*.nc")))
            profile_files.extend(year_files)
    all_profiles[sensor] = profile_files

def load_and_interpolate_profile(filepath, sensor_name, standard_depths):
    """Load and interpolate a profile."""
    try:
        ds = xr.open_dataset(filepath)
        sensor_data = ds[sensor_name].values
        depth = ds['depth'].values
        
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

# Compute mean profiles for each cluster
print("\n=== Computing Cluster Mean Profiles ===")

cluster_profiles = {sensor: {i: [] for i in range(n_clusters)} for sensor in SENSORS}

for sensor in SENSORS:
    print(f"Processing {sensor}...")
    sensor_files = all_profiles[sensor]
    
    for idx, cluster in enumerate(cluster_labels):
        if idx < len(sensor_files):
            profile_data = load_and_interpolate_profile(sensor_files[idx], sensor, STANDARD_DEPTHS)
            if not np.all(np.isnan(profile_data)):
                cluster_profiles[sensor][cluster].append(profile_data)

# Calculate statistics
cluster_means = {sensor: {} for sensor in SENSORS}
cluster_stds = {sensor: {} for sensor in SENSORS}

for sensor in SENSORS:
    for cluster in range(n_clusters):
        profiles = cluster_profiles[sensor][cluster]
        if len(profiles) > 0:
            profiles_array = np.array(profiles)
            cluster_means[sensor][cluster] = np.nanmean(profiles_array, axis=0)
            cluster_stds[sensor][cluster] = np.nanstd(profiles_array, axis=0)
        else:
            cluster_means[sensor][cluster] = np.full(len(STANDARD_DEPTHS), np.nan)
            cluster_stds[sensor][cluster] = np.full(len(STANDARD_DEPTHS), np.nan)

# Plot mean profiles for each sensor
print("\n=== Plotting Cluster Characteristics ===")

for sensor in SENSORS:
    fig, ax = plt.subplots(figsize=(8, 10))
    
    for cluster in range(n_clusters):
        mean_profile = cluster_means[sensor][cluster]
        std_profile = cluster_stds[sensor][cluster]
        
        valid = ~np.isnan(mean_profile)
        if np.any(valid):
            ax.plot(mean_profile[valid], STANDARD_DEPTHS[valid], 
                   linewidth=2, label=f'Cluster {cluster}')
            
            # Add shaded std region
            ax.fill_betweenx(STANDARD_DEPTHS[valid],
                            (mean_profile - std_profile)[valid],
                            (mean_profile + std_profile)[valid],
                            alpha=0.2)
    
    ax.set_ylabel('Depth (m)', fontsize=12)
    ax.set_xlabel(f'{sensor.capitalize()}', fontsize=12)
    ax.set_title(f'Mean {sensor.capitalize()} Profiles by Cluster', fontsize=14)
    ax.set_ylim(180, 0)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'cluster_profiles_{sensor}.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print(f"Saved cluster_profiles_{sensor}.png")

# Create summary comparison plot (temperature and salinity)
fig, axes = plt.subplots(1, 2, figsize=(14, 8))

for cluster in range(n_clusters):
    # Temperature
    temp_mean = cluster_means['temperature'][cluster]
    valid = ~np.isnan(temp_mean)
    if np.any(valid):
        axes[0].plot(temp_mean[valid], STANDARD_DEPTHS[valid], 
                    linewidth=2, label=f'Cluster {cluster}')

    # Salinity
    sal_mean = cluster_means['salinity'][cluster]
    valid = ~np.isnan(sal_mean)
    if np.any(valid):
        axes[1].plot(sal_mean[valid], STANDARD_DEPTHS[valid], 
                    linewidth=2, label=f'Cluster {cluster}')

axes[0].set_ylabel('Depth (m)', fontsize=12)
axes[0].set_xlabel('Temperature (°C)', fontsize=12)
axes[0].set_title('Mean Temperature Profiles', fontsize=14)
axes[0].set_ylim(180, 0)
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].set_ylabel('Depth (m)', fontsize=12)
axes[1].set_xlabel('Salinity (PSU)', fontsize=12)
axes[1].set_title('Mean Salinity Profiles', fontsize=14)
axes[1].set_ylim(180, 0)
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('cluster_summary.png', dpi=150, bbox_inches='tight')
plt.show()

print("\nSaved cluster_summary.png")

# Cluster characterization summary
print("\n=== Cluster Characterization Summary ===")

for cluster in range(n_clusters):
    cluster_profiles_idx = profile_index[profile_index['cluster'] == cluster]
    
    print(f"\nCluster {cluster}:")
    print(f"  Size: {len(cluster_profiles_idx)} profiles ({len(cluster_profiles_idx)/len(profile_index)*100:.1f}%)")
    print(f"  Date range: {cluster_profiles_idx['date'].min()} to {cluster_profiles_idx['date'].max()}")
    
    # Seasonal distribution
    months = cluster_profiles_idx['date'].dt.month
    dominant_months = months.value_counts().head(3)
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    print(f"  Dominant months: {', '.join([month_names[m-1] for m in dominant_months.index])}")
    
    # Physical characteristics (surface values)
    temp_surface = cluster_means['temperature'][cluster][0]
    sal_surface = cluster_means['salinity'][cluster][0]
    
    if not np.isnan(temp_surface):
        print(f"  Surface temperature: {temp_surface:.2f}°C")
    if not np.isnan(sal_surface):
        print(f"  Surface salinity: {sal_surface:.2f} PSU")

# Save cluster characterization
print("\nSaving cluster characterization...")

characterization = {
    'cluster_means': cluster_means,
    'cluster_stds': cluster_stds,
    'n_clusters': n_clusters,
    'sensors': SENSORS,
    'depths': STANDARD_DEPTHS
}

with open('cluster_characterization.pkl', 'wb') as f:
    pickle.dump(characterization, f)

print("\nSaved:")
print("  - cluster_characterization.pkl")
print("  - cluster_profiles_*.png (one per sensor)")
print("  - cluster_summary.png")

print("\n=== Characterization Complete ===")
print("Water column regimes have been identified and characterized.")
print("Each cluster represents a distinct oceanographic state.")
