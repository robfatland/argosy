# SGA Depth Analysis: Determine optimal depth bin range
# Analyzes temperature profiles from pp06 (2020-2025) to find the
# actual min/max depth range of shard data.
#
# Run this as: %run /home/rob/argosy/sga/sga_depth_analysis.py
#
# Output: Histograms of shallowest and deepest depth values per profile.
# These inform the choice of depth grid for Module 2.

import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Configuration
DATA_BASE = Path("~/ooi/postproc/pp06").expanduser()
SENSOR = 'temperature'
START_YEAR = 2020
END_YEAR = 2025
BIN_WIDTH = 0.05  # 5 cm bins for histograms

print(f"Scanning {SENSOR} profiles in pp06, {START_YEAR}-{END_YEAR}...")
print(f"Data source: {DATA_BASE}")

# Collect min/max depths from each profile
min_depths = []
max_depths = []
file_count = 0

for year in range(START_YEAR, END_YEAR + 1):
    redux_dir = DATA_BASE / f"redux{year}"
    if not redux_dir.exists():
        print(f"  redux{year}: not found, skipping")
        continue

    year_files = sorted(redux_dir.glob(f"*_{SENSOR}_*.nc"))
    year_count = 0

    for f in year_files:
        try:
            ds = xr.open_dataset(f)
            depth = ds['depth'].values
            ds.close()

            # Remove NaN depths
            valid_depth = depth[~np.isnan(depth)]
            if len(valid_depth) < 2:
                continue

            min_depths.append(valid_depth.min())
            max_depths.append(valid_depth.max())
            year_count += 1
        except Exception as e:
            print(f"  ERROR: {f.name}: {e}")
            continue

    print(f"  redux{year}: {year_count} profiles analyzed")
    file_count += year_count

print(f"\nTotal profiles analyzed: {file_count}")

min_depths = np.array(min_depths)
max_depths = np.array(max_depths)

# Statistics
print(f"\n=== Shallowest Depth (profile minimum) ===")
print(f"  Mean: {min_depths.mean():.2f} m")
print(f"  Median: {np.median(min_depths):.2f} m")
print(f"  Std: {min_depths.std():.2f} m")
print(f"  Min: {min_depths.min():.2f} m")
print(f"  Max: {min_depths.max():.2f} m")
print(f"  5th percentile: {np.percentile(min_depths, 5):.2f} m")
print(f"  95th percentile: {np.percentile(min_depths, 95):.2f} m")

print(f"\n=== Deepest Depth (profile maximum) ===")
print(f"  Mean: {max_depths.mean():.2f} m")
print(f"  Median: {np.median(max_depths):.2f} m")
print(f"  Std: {max_depths.std():.2f} m")
print(f"  Min: {max_depths.min():.2f} m")
print(f"  Max: {max_depths.max():.2f} m")
print(f"  5th percentile: {np.percentile(max_depths, 5):.2f} m")
print(f"  95th percentile: {np.percentile(max_depths, 95):.2f} m")

# Plot histograms
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# Shallowest depth histogram (5 cm bins)
bins_shallow = np.arange(min_depths.min(), min_depths.max() + BIN_WIDTH, BIN_WIDTH)
axes[0].hist(min_depths, bins=bins_shallow, edgecolor='black', alpha=0.7, color='steelblue')
axes[0].axvline(x=np.median(min_depths), color='r', linestyle='--', linewidth=2,
                label=f'Median: {np.median(min_depths):.2f} m')
axes[0].axvline(x=np.percentile(min_depths, 95), color='orange', linestyle='--', linewidth=2,
                label=f'95th pct: {np.percentile(min_depths, 95):.2f} m')
axes[0].set_xlabel('Depth (m)')
axes[0].set_ylabel('Count')
axes[0].set_title(f'Shallowest Depth per Profile ({SENSOR}, {START_YEAR}-{END_YEAR}, n={file_count})')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Deepest depth histogram (5 cm bins)
bins_deep = np.arange(max_depths.min(), max_depths.max() + BIN_WIDTH, BIN_WIDTH)
axes[1].hist(max_depths, bins=bins_deep, edgecolor='black', alpha=0.7, color='darkgreen')
axes[1].axvline(x=np.median(max_depths), color='r', linestyle='--', linewidth=2,
                label=f'Median: {np.median(max_depths):.2f} m')
axes[1].axvline(x=np.percentile(max_depths, 5), color='orange', linestyle='--', linewidth=2,
                label=f'5th pct: {np.percentile(max_depths, 5):.2f} m')
axes[1].set_xlabel('Depth (m)')
axes[1].set_ylabel('Count')
axes[1].set_title(f'Deepest Depth per Profile ({SENSOR}, {START_YEAR}-{END_YEAR}, n={file_count})')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()

# Save
SGA_DIR = Path('~/ooi/analysis/sga').expanduser()
SGA_DIR.mkdir(parents=True, exist_ok=True)
plt.savefig(SGA_DIR / 'depth_range_histograms.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"\nHistogram saved to {SGA_DIR / 'depth_range_histograms.png'}")
print(f"\n=== Recommendation ===")
print(f"  Based on 95th percentile shallow ({np.percentile(min_depths, 95):.1f} m)")
print(f"  and 5th percentile deep ({np.percentile(max_depths, 5):.1f} m):")
print(f"  Suggested depth grid: ~{np.ceil(np.percentile(min_depths, 95)):.0f} m to "
      f"~{np.floor(np.percentile(max_depths, 5)):.0f} m")
