# surface_plot.py — Plot near-surface summary statistics from surface_extract CSV.
# Run this as: %run ~/argosy/plume/surface_plot.py
#
# Produces a stacked time series plot:
#   Panel 1: Salinity mean + std
#   Panel 2: Temperature mean + std
#   Panel 3: DO mean + std
#   Panel 4: CDOM mean + std
#   Panel 5: Observation depth + dsal_dz
#
# Gaps > 1 day are broken (no connecting diagonals).
# Output: inline display + PNG to ~/ooi/visualizations/

import sys
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Make the repo root importable so `import ooipaths` works under %run.
sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op
SITE = op.DEFAULT_SITE

# == Configuration =============================================================

CSV_PATH = op.metadata_dir(SITE, "features") / "surface_extract_slopebase.csv"
OUTPUT_DIR = op.visualizations_dir(SITE)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SITE_NAME = "slopebase"
GAP_THRESHOLD_HOURS = 24  # break lines at gaps larger than this


# == Load data =================================================================

df = pd.read_csv(CSV_PATH, parse_dates=['timestamp'])
df = df.sort_values('timestamp').reset_index(drop=True)

print(f"Loaded {len(df)} records from {CSV_PATH.name}")
print(f"  Time range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")

# Load SMAP satellite data if available
SMAP_SSS_PATH = op.metadata_dir(SITE, "external") / "satellite_sss_slopebase.csv"
SMAP_SST_PATH = op.metadata_dir(SITE, "external") / "satellite_sst_slopebase.csv"
# Fallback to old combined file
SMAP_OLD_PATH = op.metadata_dir(SITE, "external") / "smap_sss_slopebase.csv"

smap_sss_df = None
smap_sst_df = None

if SMAP_SSS_PATH.exists():
    smap_sss_df = pd.read_csv(SMAP_SSS_PATH, parse_dates=['timestamp'])
    smap_sss_df['timestamp'] = smap_sss_df['timestamp'].dt.tz_localize(None)
    print(f"Loaded {len(smap_sss_df)} satellite SSS records")
elif SMAP_OLD_PATH.exists():
    smap_sss_df = pd.read_csv(SMAP_OLD_PATH, parse_dates=['timestamp'])
    smap_sss_df['timestamp'] = smap_sss_df['timestamp'].dt.tz_localize(None)
    print(f"Loaded {len(smap_sss_df)} satellite SSS records (legacy file)")

if SMAP_SST_PATH.exists():
    smap_sst_df = pd.read_csv(SMAP_SST_PATH, parse_dates=['timestamp'])
    smap_sst_df['timestamp'] = smap_sst_df['timestamp'].dt.tz_localize(None)
    print(f"Loaded {len(smap_sst_df)} satellite SST records")
elif SMAP_OLD_PATH.exists() and smap_sss_df is not None and 'sst_degC' in smap_sss_df.columns:
    smap_sst_df = smap_sss_df[['timestamp', 'sst_degC']].dropna(subset=['sst_degC']).copy()
    print(f"Loaded {len(smap_sst_df)} satellite SST records (from legacy file)")

# Keep backward compat: smap_df for code that references it
smap_df = smap_sss_df


# == Time range selection ======================================================

default_start = df['timestamp'].iloc[0].strftime("%Y-%m-%d")
default_end = df['timestamp'].iloc[-1].strftime("%Y-%m-%d")

try:
    start_input = input(f"Start date (default {default_start}): ").strip()
    end_input = input(f"End date (default {default_end}): ").strip()
except (EOFError, OSError):
    start_input = ""
    end_input = ""

start_date = pd.Timestamp(start_input) if start_input else pd.Timestamp(default_start)
end_date = pd.Timestamp(end_input) if end_input else pd.Timestamp(default_end)

mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
df = df[mask].reset_index(drop=True)
print(f"  Plotting {len(df)} records from {start_date.date()} to {end_date.date()}")


# == Gap-aware plotting utility ================================================

def plot_gapped(ax, timestamps, values, color, label, linewidth=0.8):
    """Plot a time series with breaks at gaps > GAP_THRESHOLD_HOURS."""
    if len(timestamps) == 0:
        return

    t = timestamps.values
    v = values.values

    # Find gap indices
    dt_hours = np.diff(t).astype('timedelta64[h]').astype(float)
    gap_indices = np.where(dt_hours > GAP_THRESHOLD_HOURS)[0]

    # Split into segments
    segments = np.split(np.arange(len(t)), gap_indices + 1)

    for seg in segments:
        if len(seg) < 2:
            continue
        ax.plot(t[seg], v[seg], color=color, linewidth=linewidth, label=label)
        label = None  # only label once for legend


# == Create figure =============================================================

fig, axes = plt.subplots(9, 1, figsize=(16, 22), sharex=True)
fig.suptitle(f"Near-Surface Extract: {SITE_NAME} ({start_date.date()} to {end_date.date()})",
             fontsize=13)

# == Mean panels ===============================================================

# Panel 1: Salinity mean (profiler + SMAP overlay)
ax = axes[0]
plot_gapped(ax, df['timestamp'], df['sal_mean'].clip(30.5, 34.0), 'blue', 'Profiler sal')
if smap_df is not None:
    sm = smap_df[(smap_df['timestamp'] >= start_date) & (smap_df['timestamp'] <= end_date)].copy()
    sss_col = 'sss_8day' if 'sss_8day' in sm.columns else 'sss_psu'
    plot_gapped(ax, sm['timestamp'], sm[sss_col].clip(30.5, 34.0), 'orange', 'SMAP SSS (8d)', linewidth=1.2)
ax.set_ylabel('Salinity (PSU)')
ax.set_ylim(30.5, 34.0)
ax.grid(True, alpha=0.3)
ax.legend(loc='upper right', fontsize=8)

# Panel 2: SMAP SSS alone (autoscaled, 8-day smoothed)
ax = axes[1]
if smap_df is not None:
    sm = smap_df[(smap_df['timestamp'] >= start_date) & (smap_df['timestamp'] <= end_date)].copy()
    sss_col = 'sss_8day' if 'sss_8day' in sm.columns else 'sss_psu'
    sm_valid = sm.dropna(subset=[sss_col])
    plot_gapped(ax, sm_valid['timestamp'], sm_valid[sss_col], 'orange', 'SMAP SSS (8d)')
ax.set_ylabel('SMAP SSS (PSU)')
# Autoscale — do not set ylim
ax.grid(True, alpha=0.3)
ax.legend(loc='upper right', fontsize=8)

# Panel 3: Temperature mean (profiler + SST with markers)
ax = axes[2]
plot_gapped(ax, df['timestamp'], df['temp_mean'].clip(8.0, 20.0), 'red', 'Profiler temp')
if smap_sst_df is not None:
    sm = smap_sst_df[(smap_sst_df['timestamp'] >= start_date) & (smap_sst_df['timestamp'] <= end_date)].copy()
    sm_valid = sm.dropna(subset=['sst_degC'])
    if len(sm_valid) > 0:
        plot_gapped(ax, sm_valid['timestamp'], sm_valid['sst_degC'].clip(8.0, 20.0), 'orange', 'Satellite SST', linewidth=1.2)
        ax.scatter(sm_valid['timestamp'].values, sm_valid['sst_degC'].clip(8.0, 20.0).values,
                   color='orange', s=8, zorder=5, alpha=0.6)
ax.set_ylabel('Temp (°C)')
ax.set_ylim(8.0, 20.0)
ax.grid(True, alpha=0.3)
ax.legend(loc='upper right', fontsize=8)

# Panel 4: DO mean
ax = axes[3]
plot_gapped(ax, df['timestamp'], df['do_mean'].clip(200.0, 300.0), 'darkblue', 'DO mean')
ax.set_ylabel('DO (µmol/kg)')
ax.set_ylim(200.0, 300.0)
ax.grid(True, alpha=0.3)
ax.legend(loc='upper right', fontsize=8)

# Panel 5: CDOM mean
ax = axes[4]
plot_gapped(ax, df['timestamp'], df['cdom_mean'].clip(0.0, 5.0), 'darkcyan', 'CDOM mean')
ax.set_ylabel('CDOM (ppb)')
ax.set_ylim(0.0, 5.0)
ax.grid(True, alpha=0.3)
ax.legend(loc='upper right', fontsize=8)

# Panel 6: Observation depth
ax = axes[5]
plot_gapped(ax, df['timestamp'], df['obs_depth_m'].clip(0.0, 50.0), 'black', 'Obs depth')
ax.set_ylabel('Depth (m)')
ax.set_ylim(50.0, 0.0)  # inverted
ax.grid(True, alpha=0.3)
ax.legend(loc='upper right', fontsize=8)

# == Std panels ================================================================

# Panel 7: Salinity std
ax = axes[6]
plot_gapped(ax, df['timestamp'], df['sal_std'].clip(0.0, 0.1), 'blue', 'Salinity std')
ax.set_ylabel('Sal std (PSU)')
ax.set_ylim(0.0, 0.1)
ax.grid(True, alpha=0.3)
ax.legend(loc='upper right', fontsize=8)

# Panel 8: Temperature std
ax = axes[7]
plot_gapped(ax, df['timestamp'], df['temp_std'].clip(0.0, 0.10), 'red', 'Temperature std')
ax.set_ylabel('Temp std (°C)')
ax.set_ylim(0.0, 0.10)
ax.grid(True, alpha=0.3)
ax.legend(loc='upper right', fontsize=8)

# Panel 9: DO std (code retained but chart suppressed)
# ax = axes[8]
# plot_gapped(ax, df['timestamp'], df['do_std'].clip(0.0, 2.0), 'darkblue', 'DO std')
# ax.set_ylabel('DO std (µmol/kg)')
# ax.set_ylim(0.0, 2.0)
# ax.grid(True, alpha=0.3)
# ax.legend(loc='upper right', fontsize=8)

# Panel 10: CDOM std (code retained but chart suppressed)
# ax = axes[9]
# plot_gapped(ax, df['timestamp'], df['cdom_std'].clip(0.0, 0.5), 'darkcyan', 'CDOM std')
# ax.set_ylabel('CDOM std (ppb)')
# ax.set_ylim(0.0, 0.5)
# ax.grid(True, alpha=0.3)
# ax.legend(loc='upper right', fontsize=8)

# Panel 11: dS/dz
ax = axes[8]
plot_gapped(ax, df['timestamp'], df['dsal_dz'].clip(-0.04, 0.04), 'green', 'dS/dz')
ax.set_ylabel('dS/dz (PSU/m)')
ax.set_ylim(-0.04, 0.04)
ax.grid(True, alpha=0.3)
ax.legend(loc='upper right', fontsize=8)

axes[-1].set_xlabel('Date')
plt.tight_layout()

# Save
output_path = OUTPUT_DIR / f"surface_extract_{SITE_NAME}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.png"
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"\nSaved: {output_path}")

plt.show()
