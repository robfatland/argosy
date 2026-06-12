# Module 3: Normalize features and handle missing data
# Run this as: %run /home/rob/argosy/sga/sga_module3.py

import numpy as np
import pandas as pd
import pickle
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from pathlib import Path

# Output directory
SGA_DIR = Path('~/ooi/analysis/sga').expanduser()

# Load config
with open(SGA_DIR / 'sga_config.pkl', 'rb') as f:
    config = pickle.load(f)

strategy = config['missing_data_strategy']

# Load data
print("Module 3: Normalize")
feature_matrix = np.load(SGA_DIR / 'feature_matrix.npy')
profile_index = pd.read_csv(SGA_DIR / 'profile_index.csv')
profile_index['date'] = pd.to_datetime(profile_index['date'])

with open(SGA_DIR / 'feature_names.pkl', 'rb') as f:
    feature_names = pickle.load(f)

print(f"  Feature matrix: {feature_matrix.shape}")
print(f"  Missing data strategy: {strategy}")

if strategy == "1":
    profile_completeness = np.sum(~np.isnan(feature_matrix), axis=1) / feature_matrix.shape[1]
    good_mask = profile_completeness >= 0.5

    feature_matrix_clean = feature_matrix[good_mask]
    profile_index_clean = profile_index[good_mask].reset_index(drop=True)

    print(f"  Removed {np.sum(~good_mask)} profiles with >50% missing")
    print(f"  Remaining: {len(profile_index_clean)}")

    imputer = SimpleImputer(strategy='mean')
    feature_matrix_imputed = imputer.fit_transform(feature_matrix_clean)

elif strategy == "2":
    imputer = SimpleImputer(strategy='mean')
    feature_matrix_imputed = imputer.fit_transform(feature_matrix)
    profile_index_clean = profile_index.copy()
    print(f"  Imputed all missing values, profiles: {len(profile_index_clean)}")

elif strategy == "3":
    complete_mask = ~np.any(np.isnan(feature_matrix), axis=1)
    feature_matrix_imputed = feature_matrix[complete_mask]
    profile_index_clean = profile_index[complete_mask].reset_index(drop=True)
    print(f"  Removed {np.sum(~complete_mask)} incomplete, remaining: {len(profile_index_clean)}")

# Verify column count preserved
expected_cols = feature_matrix.shape[1]
actual_cols = feature_matrix_imputed.shape[1]
if actual_cols != expected_cols:
    print(f"  WARNING: Imputer dropped {expected_cols - actual_cols} all-NaN columns!")
    print(f"  Expected {expected_cols}, got {actual_cols}. Check depth grid or sensor coverage.")

# Z-score normalization
scaler = StandardScaler()
feature_matrix_normalized = scaler.fit_transform(feature_matrix_imputed)

print(f"  Normalized: {feature_matrix_normalized.shape}")
print(f"  Mean: {np.mean(feature_matrix_normalized):.6f}, Std: {np.std(feature_matrix_normalized):.6f}")

# Save
np.save(SGA_DIR / 'feature_matrix_normalized.npy', feature_matrix_normalized)
profile_index_clean.to_csv(SGA_DIR / 'profile_index_clean.csv', index=False)
with open(SGA_DIR / 'scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

print(f"\n=== Module 3 Complete ===")
print(f"  Final: {feature_matrix_normalized.shape[0]} profiles x {feature_matrix_normalized.shape[1]} features")
