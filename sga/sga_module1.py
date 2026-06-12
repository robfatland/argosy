# Module 1: Load and prepare profile data for graph analysis
# Scans pp06 shard files and creates a profile index keyed by global index.
# Run this as: %run /home/rob/argosy/sga/sga_module1.py

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import pickle
import warnings
warnings.filterwarnings('ignore')

# Output directory
SGA_DIR = Path('~/ooi/analysis/sga').expanduser()
SGA_DIR.mkdir(parents=True, exist_ok=True)

# Load config
with open(SGA_DIR / 'sga_config.pkl', 'rb') as f:
    config = pickle.load(f)

DATA_BASE = Path(config['data_base'])
SENSORS = config['sensors']
start_year = config['start_year']
end_year = config['end_year']

print(f"Module 1: Load and Index")
print(f"  Data source: {DATA_BASE}")
print(f"  Years: {start_year} - {end_year}")
print(f"  Active sensors ({len(SENSORS)}): {SENSORS}")

# Build global-index-keyed file lookup per sensor
sensor_files = {sensor: {} for sensor in SENSORS}

for year in range(start_year, end_year + 1):
    redux_dir = DATA_BASE / f"redux{year}"
    if not redux_dir.exists():
        continue
    for sensor in SENSORS:
        year_files = list(redux_dir.glob(f"*_{sensor}_*.nc"))
        for f in year_files:
            parts = f.stem.split('_')
            global_idx = int(parts[6])
            sensor_files[sensor][global_idx] = f

# Determine the master set of global indices (union across all sensors)
all_global_indices = set()
for sensor in SENSORS:
    all_global_indices.update(sensor_files[sensor].keys())

all_global_indices = sorted(all_global_indices)
n_profiles = len(all_global_indices)

print(f"\n  Total unique global indices: {n_profiles}")
if n_profiles > 0:
    print(f"  Range: {all_global_indices[0]} to {all_global_indices[-1]}")
print(f"\n  Per-sensor file counts:")
for sensor in SENSORS:
    print(f"    {sensor}: {len(sensor_files[sensor])}")

# Build profile index metadata from filenames
print("\n  Building profile index...")
profile_metadata = []
for gidx in all_global_indices:
    meta_file = None
    for sensor in SENSORS:
        if gidx in sensor_files[sensor]:
            meta_file = sensor_files[sensor][gidx]
            break

    if meta_file is None:
        continue

    parts = meta_file.stem.split('_')
    year = int(parts[4])
    doy = int(parts[5])
    daily_idx = int(parts[7])
    date = datetime(year, 1, 1) + pd.Timedelta(days=doy - 1)

    profile_metadata.append({
        'global_idx': gidx,
        'year': year,
        'doy': doy,
        'daily_idx': daily_idx,
        'date': date,
    })

profile_index = pd.DataFrame(profile_metadata)
print(f"\n  Profile index: {len(profile_index)} profiles")
print(f"  Date range: {profile_index['date'].min()} to {profile_index['date'].max()}")

# Save
profile_index.to_csv(SGA_DIR / 'profile_index.csv', index=False)
with open(SGA_DIR / 'sensor_files.pkl', 'wb') as f:
    pickle.dump(sensor_files, f)

print(f"\n=== Module 1 Complete ===")
