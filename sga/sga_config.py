# SGA Configuration — Module 0
# Edit these values, then run all subsequent modules non-interactively.
# Run this as: %run /home/rob/argosy/sga/sga_config.py
#
# All modules read from ~/ooi/analysis/sga/sga_config.pkl
# For meta-runs (parameter sweeps), modify this config and re-run the pipeline.

import pickle
from pathlib import Path
import numpy as np

# Output directory
SGA_DIR = Path('~/ooi/analysis/sga').expanduser()
SGA_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# CONFIGURATION — edit below, then run this cell
# =============================================================================

config = {
    # --- Data source ---
    'data_base': str(Path("~/ooi/postproc/pp06").expanduser()),

    # --- Time range ---
    'start_year': 2023,
    'end_year': 2024,

    # --- Sensors ---
    # Toggle sensors on/off. Order: temperature, salinity, density,
    # dissolvedoxygen, cdom, chlora, backscatter
    'all_sensors': ['temperature', 'salinity', 'density', 'dissolvedoxygen',
                    'cdom', 'chlora', 'backscatter'],
    'sensors_active': [True, True, True, True, False, True, True],

    # --- Depth grid ---
    'depth_min': 27,       # shallowest bin (meters)
    'depth_max': 185,      # deepest bin (meters)
    'depth_bins': 80,      # number of bins (2m spacing for 27-185m)

    # --- Module 3: Missing data ---
    # Options: '1' = remove >50% missing + impute rest
    #          '2' = impute all
    #          '3' = only complete profiles
    'missing_data_strategy': '1',

    # --- Module 4: Similarity graph ---
    # Sigma options: 'median', '0.25x', '4x', or a float for custom sigma
    'sigma_choice': 'median',
    # Graph type: 'knn', 'epsilon', 'full'
    'graph_type': 'knn',
    'knn_k': 10,
    'epsilon_threshold': 0.1,

    # --- Module 5: Laplacian ---
    # Options: '1' = unnormalized, '2' = symmetric normalized, '3' = random walk
    'laplacian_type': '2',
    'n_eigenvalues': 50,

    # --- Module 6: Clustering ---
    'n_eigenvectors': 10,       # number of eigenvectors for spectral embedding
    'k_range_min': 2,           # min k to evaluate
    'k_range_max': 10,          # max k to evaluate
    'final_k': None,            # set to an int to override silhouette-best; None = auto
}

# =============================================================================
# DERIVED VALUES (computed from config, don't edit)
# =============================================================================

config['sensors'] = [s for s, active in zip(config['all_sensors'], config['sensors_active']) if active]
config['standard_depths'] = np.linspace(config['depth_min'], config['depth_max'], config['depth_bins']).tolist()

# =============================================================================
# SAVE CONFIG
# =============================================================================

with open(SGA_DIR / 'sga_config.pkl', 'wb') as f:
    pickle.dump(config, f)

# Print summary
print("=== SGA Configuration ===")
print(f"  Data source: {config['data_base']}")
print(f"  Years: {config['start_year']} - {config['end_year']}")
print(f"  Active sensors ({len(config['sensors'])}): {config['sensors']}")
print(f"  Depth grid: {config['depth_min']}m - {config['depth_max']}m, {config['depth_bins']} bins")
print(f"  Missing data strategy: {config['missing_data_strategy']}")
print(f"  Sigma: {config['sigma_choice']}")
print(f"  Graph: {config['graph_type']} (k={config['knn_k']})")
print(f"  Laplacian: type {config['laplacian_type']}")
print(f"  Clustering: {config['n_eigenvectors']} eigvecs, k={config['k_range_min']}-{config['k_range_max']}")
if config['final_k']:
    print(f"  Final k override: {config['final_k']}")
else:
    print(f"  Final k: auto (best silhouette)")
print(f"\n  Config saved to: {SGA_DIR / 'sga_config.pkl'}")
