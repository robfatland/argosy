# Module 3: Normalize features and handle missing data
# Prepares data for similarity computation

import numpy as np
import pandas as pd
import pickle
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

# Load data
print("Loading feature matrix...")
feature_matrix = np.load('feature_matrix.npy')
profile_index = pd.read_csv('profile_index.csv')
profile_index['date'] = pd.to_datetime(profile_index['date'])

with open('feature_names.pkl', 'rb') as f:
    feature_names = pickle.load(f)

print(f"Feature matrix shape: {feature_matrix.shape}")
print(f"Profiles: {len(profile_index)}")

# Strategy for missing data
print("\n=== Missing Data Strategy ===")
print("Options:")
print("  1. Remove profiles with >50% missing data")
print("  2. Impute missing values (mean imputation)")
print("  3. Use only complete profiles")

strategy = input("Select strategy (1/2/3, default 1): ").strip() or "1"

if strategy == "1":
    # Remove profiles with too much missing data
    profile_completeness = np.sum(~np.isnan(feature_matrix), axis=1) / feature_matrix.shape[1]
    good_mask = profile_completeness >= 0.5
    
    feature_matrix_clean = feature_matrix[good_mask]
    profile_index_clean = profile_index[good_mask].reset_index(drop=True)
    
    print(f"\nRemoved {np.sum(~good_mask)} profiles with >50% missing data")
    print(f"Remaining profiles: {len(profile_index_clean)}")
    
    # Impute remaining missing values with column mean
    imputer = SimpleImputer(strategy='mean')
    feature_matrix_imputed = imputer.fit_transform(feature_matrix_clean)
    
elif strategy == "2":
    # Impute all missing values
    imputer = SimpleImputer(strategy='mean')
    feature_matrix_imputed = imputer.fit_transform(feature_matrix)
    profile_index_clean = profile_index.copy()
    
    print(f"\nImputed all missing values")
    print(f"Profiles: {len(profile_index_clean)}")
    
elif strategy == "3":
    # Use only complete profiles
    complete_mask = ~np.any(np.isnan(feature_matrix), axis=1)
    
    feature_matrix_imputed = feature_matrix[complete_mask]
    profile_index_clean = profile_index[complete_mask].reset_index(drop=True)
    
    print(f"\nRemoved {np.sum(~complete_mask)} incomplete profiles")
    print(f"Remaining profiles: {len(profile_index_clean)}")

# Normalize features (z-score normalization)
print("\n=== Feature Normalization ===")
print("Applying z-score normalization (mean=0, std=1)...")

scaler = StandardScaler()
feature_matrix_normalized = scaler.fit_transform(feature_matrix_imputed)

print(f"Normalized feature matrix shape: {feature_matrix_normalized.shape}")

# Verify normalization
print("\nVerification:")
print(f"  Mean: {np.mean(feature_matrix_normalized):.6f} (should be ~0)")
print(f"  Std: {np.std(feature_matrix_normalized):.6f} (should be ~1)")

# Save processed data
print("\nSaving processed data...")
np.save('feature_matrix_normalized.npy', feature_matrix_normalized)
profile_index_clean.to_csv('profile_index_clean.csv', index=False)

with open('scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

print("\nSaved:")
print("  - feature_matrix_normalized.npy")
print("  - profile_index_clean.csv")
print("  - scaler.pkl")

# Summary statistics
print("\n=== Summary ===")
print(f"Final dataset: {feature_matrix_normalized.shape[0]} profiles × {feature_matrix_normalized.shape[1]} features")
print(f"Date range: {profile_index_clean['date'].min()} to {profile_index_clean['date'].max()}")
print(f"Time span: {(profile_index_clean['date'].max() - profile_index_clean['date'].min()).days} days")
