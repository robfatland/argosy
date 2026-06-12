# Module 7: Characterize Water Column Regimes
# Analyzes physical properties of each cluster.
# Run this as: %run /home/rob/argosy/sga/sga_module7.py

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle
from pathlib import Path

# Output directory for SGA intermediate and result files
SGA_DIR = Path('~/ooi/analysis/sga').expanduser()
SGA_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
ALL_SENSORS = ['temperature', 'salinity', 'density', 'dissolvedoxygen',
               'cdom', 'chlora', 'backscatter']
SENSORS_ACTIVE = [True, True, True, True, False, True, True]  # Toggle sensors on/off
SENSORS = [s for s, active in zip(ALL_SENSORS, SENSORS_ACTIVE) if active]
STANDARD_DEPTHS = np.linspace(27, 185, 80)  # 2m resolution, 27-185m (95th pct range)

# Load clustering results
print("Loading clustering results...")
profile_index = pd.read_csv(SGA_DIR / 'profile_index_clustered.csv')
profile_index['date'] = pd.to_datetime(profile_index['date'])
cluster_labels = np.load(SGA_DIR / 'cluster_labels.npy')

with open(SGA_DIR / 'cluster_metadata.pkl', 'rb') as f:
    clustering_results = pickle.load(f)

n_clusters = clustering_results['n_clusters']
print(f"Number of clusters: {n_clusters}")
print(f"Profiles: {len(profile_index)}")

# Load the full normalized feature matrix
feature_matrix = np.load(SGA_DIR / 'feature_matrix_normalized.npy')

# Derive n_depths from actual feature matrix shape
n_features = feature_matrix.shape[1]
n_sensors = len(SENSORS)
n_depths = n_features // n_sensors

# Reconstruct the actual depth grid used (in case it differs from STANDARD_DEPTHS)
actual_depths = STANDARD_DEPTHS[:n_depths] if n_depths <= len(STANDARD_DEPTHS) else STANDARD_DEPTHS

# Also load the scaler for inverse-transforming back to physical units
with open(SGA_DIR / 'scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

# Inverse transform to get physical units
feature_matrix_physical = scaler.inverse_transform(feature_matrix)

print("\n=== Cluster Characterization ===")

# For each cluster, compute mean profiles per sensor
fig, axes = plt.subplots(len(SENSORS), 1, figsize=(12, 4 * len(SENSORS)))

colors = plt.cm.tab10(np.linspace(0, 1, n_clusters))

for sensor_idx, sensor in enumerate(SENSORS):
    ax = axes[sensor_idx]
    start_col = sensor_idx * n_depths
    end_col = start_col + n_depths

    for c in range(n_clusters):
        mask = cluster_labels == c
        cluster_data = feature_matrix_physical[mask, start_col:end_col]

        # Compute mean profile for this cluster
        mean_profile = np.nanmean(cluster_data, axis=0)
        std_profile = np.nanstd(cluster_data, axis=0)

        n_in_cluster = np.sum(mask)
        ax.plot(mean_profile, actual_depths, '-', color=colors[c],
                linewidth=2, label=f'Cluster {c} (n={n_in_cluster})')
        ax.fill_betweenx(actual_depths,
                         mean_profile - std_profile,
                         mean_profile + std_profile,
                         alpha=0.1, color=colors[c])

    ax.set_ylabel('Depth (m)')
    ax.set_xlabel(sensor.capitalize())
    ax.set_title(f'{sensor.capitalize()} - Mean Profiles by Cluster')
    ax.set_ylim(actual_depths[-1], 0)
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(SGA_DIR / 'cluster_profiles.png', dpi=150, bbox_inches='tight')
plt.show()
print("Cluster profiles plot saved.")

# Temporal distribution of clusters
print("\n=== Temporal Distribution ===")
for c in range(n_clusters):
    mask = cluster_labels == c
    cluster_profiles = profile_index[mask]
    years = cluster_profiles['year'].value_counts().sort_index()
    print(f"\nCluster {c} ({np.sum(mask)} profiles):")
    print(f"  Date range: {cluster_profiles['date'].min()} to {cluster_profiles['date'].max()}")
    print(f"  Year distribution:")
    for year, count in years.items():
        print(f"    {year}: {count} profiles")

# Save characterization results
print("\n\nSaving characterization results...")
characterization = {
    'n_clusters': n_clusters,
    'sensors': SENSORS,
    'standard_depths': actual_depths,
}

# Store per-cluster statistics
for c in range(n_clusters):
    mask = cluster_labels == c
    cluster_stats = {}
    for sensor_idx, sensor in enumerate(SENSORS):
        start_col = sensor_idx * n_depths
        end_col = start_col + n_depths
        cluster_data = feature_matrix_physical[mask, start_col:end_col]
        cluster_stats[sensor] = {
            'mean': np.nanmean(cluster_data, axis=0),
            'std': np.nanstd(cluster_data, axis=0),
        }
    characterization[f'cluster_{c}'] = cluster_stats

with open(SGA_DIR / 'cluster_characterization.pkl', 'wb') as f:
    pickle.dump(characterization, f)

print(f"\nSaved to {SGA_DIR}:")
print("  - cluster_profiles.png")
print("  - cluster_characterization.pkl")
print("\n=== Module 7 Complete ===")
