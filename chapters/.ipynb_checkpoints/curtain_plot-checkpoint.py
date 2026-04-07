"""
Curtain plot: Salinity for Oregon Slope Base shallow profiler, 2024-2025.
Color encodes salinity over the central 80% of the dynamic range.
Vertical axis: depth 0 (top) to 200 m (bottom).
Horizontal axis: 01-JAN-2024 through 31-DEC-2025.
White background where no profile data exists.

Runs in a Jupyter cell (Visualizations.ipynb).
"""

import glob
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
REDUX_DIRS   = ["/home/rob/ooi/redux/redux2024", "/home/rob/ooi/redux/redux2025"]
SHARD_GLOB   = "RCA_sb_sp_salinity_*.nc"
DEPTH_MIN    = 0
DEPTH_MAX    = 200
DEPTH_BINS   = 200          # 1-meter vertical resolution
TIME_START   = datetime(2024, 1, 1)
TIME_END     = datetime(2025, 12, 31, 23, 59, 59)
OUTPUT_PNG   = "/home/rob/argosy/chapters/curtain_salinity_2024_2025.png"

# ── Collect all salinity shard files ──────────────────────────────────────────
files = []
for d in REDUX_DIRS:
    files.extend(sorted(glob.glob(f"{d}/{SHARD_GLOB}")))
n_files = len(files)
print(f"Found {n_files} salinity shard files across {len(REDUX_DIRS)} folders")

# ── First pass: determine the central 80% of salinity range ──────────────────
print("Pass 1: scanning salinity range...")
all_sal = []
report_interval = max(1, n_files // 10)
for i, f in enumerate(files):
    if (i + 1) % report_interval == 0:
        print(f"  {100 * (i + 1) // n_files}% ({i + 1}/{n_files})")
    ds = xr.open_dataset(f)
    s = ds["salinity"].values
    d = ds["depth"].values
    mask = (d >= DEPTH_MIN) & (d <= DEPTH_MAX) & np.isfinite(s)
    all_sal.append(s[mask])
    ds.close()

all_sal = np.concatenate(all_sal)
vmin = np.nanpercentile(all_sal, 10)
vmax = np.nanpercentile(all_sal, 90)
print(f"Salinity central 80% range: {vmin:.3f} to {vmax:.3f}")
del all_sal

# ── Second pass: build the curtain image ──────────────────────────────────────
# Each profile becomes a thin vertical stripe at its mean time position.
# We collect (time, depth, salinity) triplets and bin them onto a regular grid.

depth_edges = np.linspace(DEPTH_MIN, DEPTH_MAX, DEPTH_BINS + 1)
depth_centers = 0.5 * (depth_edges[:-1] + depth_edges[1:])

# Accumulate profile columns: list of (mean_time, binned_salinity)
profile_columns = []

print("Pass 2: building curtain data...")
for i, f in enumerate(files):
    if (i + 1) % report_interval == 0:
        print(f"  {100 * (i + 1) // n_files}% ({i + 1}/{n_files})")
    ds = xr.open_dataset(f)
    t = ds["time"].values
    d = ds["depth"].values
    s = ds["salinity"].values
    ds.close()

    # filter to depth range and valid data
    mask = (d >= DEPTH_MIN) & (d <= DEPTH_MAX) & np.isfinite(s)
    if mask.sum() == 0:
        continue

    d_m = d[mask]
    s_m = s[mask]
    t_m = t[mask]

    # mean time for this profile's horizontal position
    mean_time = t_m.mean()

    # bin salinity by depth
    col = np.full(DEPTH_BINS, np.nan)
    bin_idx = np.digitize(d_m, depth_edges) - 1
    for bi in range(DEPTH_BINS):
        vals = s_m[bin_idx == bi]
        if len(vals) > 0:
            col[bi] = np.nanmean(vals)

    profile_columns.append((mean_time, col))

print(f"Profiles with data in depth range: {len(profile_columns)}")

# Sort by time
profile_columns.sort(key=lambda x: x[0])
times = np.array([pc[0] for pc in profile_columns])
curtain = np.column_stack([pc[1] for pc in profile_columns])  # shape: (DEPTH_BINS, n_profiles)

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(24, 8))

# Convert numpy datetime64 to matplotlib dates
times_mpl = mdates.date2num(times.astype("datetime64[us]").astype(datetime))

# pcolormesh wants edges; synthesize time edges from midpoints
dt_half = np.diff(times_mpl) / 2
time_edges = np.empty(len(times_mpl) + 1)
time_edges[0]    = times_mpl[0] - (dt_half[0] if len(dt_half) > 0 else 0.01)
time_edges[-1]   = times_mpl[-1] + (dt_half[-1] if len(dt_half) > 0 else 0.01)
time_edges[1:-1] = times_mpl[:-1] + dt_half

pcm = ax.pcolormesh(time_edges, depth_edges, curtain,
                     cmap="viridis", vmin=vmin, vmax=vmax,
                     shading="flat")

ax.set_ylim(DEPTH_MAX, DEPTH_MIN)
ax.set_xlim(mdates.date2num(TIME_START), mdates.date2num(TIME_END))
ax.set_ylabel("Depth (m)")
ax.set_xlabel("Date")
ax.set_title("Oregon Slope Base Shallow Profiler — Salinity Curtain Plot (2024–2025)", fontsize=14)

ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO))

cbar = fig.colorbar(pcm, ax=ax, pad=0.01)
cbar.set_label("Salinity (PSU)")

fig.set_facecolor("white")
ax.set_facecolor("white")

plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=150, facecolor="white")
print(f"\nCurtain plot saved to {OUTPUT_PNG}")
