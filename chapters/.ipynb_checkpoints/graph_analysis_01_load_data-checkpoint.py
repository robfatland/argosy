# Module 1: Load and prepare profile data for graph analysis
# This module loads shard files and creates a structured dataset

import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def get_input_with_default(prompt, default):
    """Get user input with default value."""
    response = input(f"{prompt} ").strip()
    return response if response else str(default)

# Configuration
SENSORS = ['temperature', 'salinity', 'density', 'dissolvedoxygen', 'cdom', 'chlora', 'backscatter']
STANDARD_DEPTHS = np.linspace(0, 180, 91)  # 2m resolution

# Get year range
start_year = int(get_input_with_default("Start year (default 2018):", "2018"))
end_year = int(get_input_with_default("End year (default 2018):", "2018"))

print(f"\nLoading profile data from {start_year} to {end_year}...")

# Collect all profile files
all_profiles = {}
for sensor in SENSORS:
    profile_files = []
    for year in range(start_year, end_year + 1):
        redux_dir = Path(f"~/redux{year}").expanduser()
        if redux_dir.exists():
            year_files = sorted(list(redux_dir.glob(f"*_{sensor}_*.nc")))
            profile_files.extend(year_files)
    all_profiles[sensor] = profile_files
    print(f"  {sensor}: {len(profile_files)} files")

# Use temperature as reference (most complete)
reference_files = all_profiles['temperature']
n_profiles = len(reference_files)

print(f"\nTotal profiles to process: {n_profiles}")

# Extract profile metadata
def extract_profile_metadata(filename):
    """Extract metadata from filename."""
    parts = filename.stem.split('_')
    year = int(parts[4])
    doy = int(parts[5])
    profile_idx = int(parts[6])
    profile_num = int(parts[7])
    
    # Convert to datetime
    date = datetime(year, 1, 1) + pd.Timedelta(days=doy - 1)
    
    return {
        'filename': filename.name,
        'year': year,
        'doy': doy,
        'profile_idx': profile_idx,
        'profile_num': profile_num,
        'date': date
    }

# Build profile index
print("\nBuilding profile index...")
profile_metadata = []
for i, ref_file in enumerate(reference_files):
    if (i + 1) % 500 == 0:
        print(f"  Processed {i + 1}/{n_profiles}")
    metadata = extract_profile_metadata(ref_file)
    metadata['index'] = i
    profile_metadata.append(metadata)

profile_index = pd.DataFrame(profile_metadata)
print(f"\nProfile index created: {len(profile_index)} profiles")
print(f"Date range: {profile_index['date'].min()} to {profile_index['date'].max()}")

# Save for later use
profile_index.to_csv('profile_index.csv', index=False)
print("\nProfile index saved to profile_index.csv")
