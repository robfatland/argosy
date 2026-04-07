"""
Curtain plots: Salinity and Temperature for Oregon Slope Base shallow profiler.
Two stacked panels, Aug 10 2024 through Dec 31 2025.
Color encodes data over the central 90% of each sensor's dynamic range.
Contour line overlays: 4 lines per panel, low-pass filtered.
Contour lines are broken at gaps >= 3 days.
White background where no profile data exists.

Runs in a Jupyter cell (Visualizations.ipynb).
"""

import glob
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from scipy.ndimage import uniform_filter1d

# == Config ====================================================================
REDUX_DIRS    = ["/home/rob/ooi/redux/redux2024", "/home/rob/ooi/redux/redux2025"]
DEPTH_MIN     = 0
DEPTH_MAX     = 200
DEPTH_BINS    = 200
TIME_START    = datetime(2024, 8, 10)
TIME_END      = datetime(2025, 12, 31, 23, 59, 59)
OUTPUT_PNG    = "/home/rob/argosy/chapters/curtain_salinity_2024_2025.png"
GAP_HOURS     = 12
N_CONTOURS    = 4
LP_WINDOW     = 27
CONTOUR_GAP_DAYS = 3        # break contour lines at gaps >= this many days

SENSORS = [
    {"glob": "RCA_sb_sp_salinity_*.nc",    "var": "salinity",    "label": "Salinity (PSU)",
     "cmap": "viridis", "contour_colors": ["white", "salmon", "cyan", "orange"], "title_var": "Salinity"},
    {"glob": "RCA_sb_sp_temperature_*.nc", "var": "temperature", "label": "Temperature (deg C)",
     "cmap": "inferno",  "contour_colors": ["cyan", "lime", "white", "yellow"],  "title_var": "Temperature"},
]

depth_edges   = np.linspace(DEPTH_MIN, DEPTH_MAX, DEPTH_BINS + 1)
depth_centers = 0.5 * (depth_edges[:-1] + depth_edges[1:])
gap_threshold = np.timedelta64(GAP_HOURS, 'h')
contour_gap_threshold = np.timedelta64(CONTOUR_GAP_DAYS, 'D')
bins_range    = np.arange(DEPTH_BINS)


# == Helper: build curtain data for one sensor =================================
def build_curtain(shard_glob, var_name):
    files = []
    for d in REDUX_DIRS:
        files.extend(sorted(glob.glob(f"{d}/{shard_glob}")))
    n_files = len(files)
    print(f"\n  Found {n_files} {var_name} shard files")
    report_interval = max(1, n_files // 10)

    # Pass 1: data range
    print(f"  Pass 1: scanning {var_name} range...")
    all_vals = []
    for i, f in enumerate(files):
        if (i + 1) % report_interval == 0:
            print(f"    {100 * (i + 1) // n_files}% ({i + 1}/{n_files})")
        ds = xr.open_dataset(f)
        v = ds[var_name].values
        d = ds["depth"].values
        mask = (d >= DEPTH_MIN) & (d <= DEPTH_MAX) & np.isfinite(v)
        all_vals.append(v[mask])
        ds.close()
    all_vals = np.concatenate(all_vals)
    vmin = np.nanpercentile(all_vals, 5)
    vmax = np.nanpercentile(all_vals, 95)
    print(f"  {var_name} central 90% range: {vmin:.3f} to {vmax:.3f}")
    del all_vals

    # Pass 2: build columns
    print(f"  Pass 2: building curtain data...")
    profile_columns = []
    for i, f in enumerate(files):
        if (i + 1) % report_interval == 0:
            print(f"    {100 * (i + 1) // n_files}% ({i + 1}/{n_files})")
        ds = xr.open_dataset(f)
        t = ds["time"].values
        d = ds["depth"].values
        v = ds[var_name].values
        ds.close()
        mask = (d >= DEPTH_MIN) & (d <= DEPTH_MAX) & np.isfinite(v)
        if mask.sum() == 0:
            continue
        d_m, v_m, t_m = d[mask], v[mask], t[mask]
        mean_time = t_m[0] + (t_m[-1] - t_m[0]) / 2
        col = np.full(DEPTH_BINS, np.nan)
        bin_idx = np.digitize(d_m, depth_edges) - 1
        for bi in bins_range:
            vals = v_m[bin_idx == bi]
            if len(vals) > 0:
                col[bi] = np.nanmean(vals)
        profile_columns.append((mean_time, col))

    print(f"  Profiles with data: {len(profile_columns)}")
    profile_columns.sort(key=lambda x: x[0])
    return profile_columns, vmin, vmax


# == Helper: compute and filter contour lines ==================================
def compute_contours(profile_columns, vmin, vmax):
    contour_values = np.linspace(vmin, vmax, N_CONTOURS + 2)[1:-1]
    raw_times = np.array([pc[0] for pc in profile_columns])
    raw_curtain = np.column_stack([pc[1] for pc in profile_columns])

    gap_mask = np.ones(len(raw_times), dtype=bool)
    for j in range(1, len(raw_times)):
        if (raw_times[j] - raw_times[j - 1]) > gap_threshold:
            gap_mask[j] = False

    contour_filtered = {}
    for sv in contour_values:
        depths_at_sv = np.full(len(profile_columns), np.nan)
        for j in range(len(profile_columns)):
            col = raw_curtain[:, j]
            valid_mask = np.isfinite(col)
            if valid_mask.sum() < 2:
                continue
            dc = depth_centers[valid_mask]
            sc = col[valid_mask]
            crossings = np.where(np.diff(np.sign(sc - sv)))[0]
            if len(crossings) > 0:
                k = crossings[0]
                s0, s1 = sc[k], sc[k + 1]
                d0, d1 = dc[k], dc[k + 1]
                if s1 != s0:
                    depths_at_sv[j] = d0 + (sv - s0) * (d1 - d0) / (s1 - s0)

        filtered = depths_at_sv.copy()
        seg_start = 0
        for j in range(1, len(filtered) + 1):
            if j == len(filtered) or not gap_mask[j]:
                seg = filtered[seg_start:j]
                valid = np.isfinite(seg)
                if valid.sum() >= LP_WINDOW:
                    indices = np.arange(len(seg))
                    seg_interp = np.interp(indices, indices[valid], seg[valid])
                    seg_smooth = uniform_filter1d(seg_interp, size=LP_WINDOW)
                    seg_smooth[~valid] = np.nan
                    filtered[seg_start:j] = seg_smooth
                seg_start = j
        contour_filtered[sv] = filtered

    return contour_values, raw_times, contour_filtered


# == Helper: insert NaN gap columns ============================================
def insert_gaps(profile_columns):
    expanded = [profile_columns[0]]
    gaps_found = 0
    for j in range(1, len(profile_columns)):
        t_prev = profile_columns[j - 1][0]
        t_curr = profile_columns[j][0]
        if (t_curr - t_prev) > gap_threshold:
            nan_col = np.full(DEPTH_BINS, np.nan)
            expanded.append((t_prev + np.timedelta64(1, 'h'), nan_col))
            expanded.append((t_curr - np.timedelta64(1, 'h'), nan_col))
            gaps_found += 1
        expanded.append(profile_columns[j])
    print(f"  Time gaps > {GAP_HOURS}h: {gaps_found}, total columns: {len(expanded)}")
    times = np.array([pc[0] for pc in expanded])
    curtain = np.column_stack([pc[1] for pc in expanded])
    return times, curtain


# == Helper: plot contour line with gap breaks =================================
def plot_contour_segments(ax, raw_times, depths, color, label):
    """Plot a contour line, breaking it at gaps >= CONTOUR_GAP_DAYS."""
    valid = np.isfinite(depths)
    indices = np.where(valid)[0]
    if len(indices) == 0:
        return

    # Split into segments at time gaps
    segments = []
    seg_start = 0
    for k in range(1, len(indices)):
        i_prev = indices[k - 1]
        i_curr = indices[k]
        if (raw_times[i_curr] - raw_times[i_prev]) >= contour_gap_threshold:
            segments.append(indices[seg_start:k])
            seg_start = k
    segments.append(indices[seg_start:])

    # Plot each segment; only label the first one for the legend
    for s_idx, seg in enumerate(segments):
        if len(seg) < 2:
            continue
        t_mpl = mdates.date2num(raw_times[seg].astype("datetime64[us]").astype(datetime))
        lbl = label if s_idx == 0 else None
        ax.plot(t_mpl, depths[seg], color=color, linewidth=1.5, alpha=0.85, label=lbl)


# == Build data for both sensors ===============================================
sensor_data = []
for sensor in SENSORS:
    print(f"\n{'='*60}\nProcessing {sensor['title_var']}...")
    pcols, vmin, vmax = build_curtain(sensor["glob"], sensor["var"])
    contour_values, raw_times, contour_filtered = compute_contours(pcols, vmin, vmax)
    times, curtain = insert_gaps(pcols)
    sensor_data.append({
        "times": times, "curtain": curtain,
        "vmin": vmin, "vmax": vmax,
        "contour_values": contour_values, "raw_times": raw_times,
        "contour_filtered": contour_filtered, "sensor": sensor,
    })


# == Plot: two stacked panels ==================================================
fig, axes = plt.subplots(2, 1, figsize=(30, 12.8), sharex=True)

for ax, sd in zip(axes, sensor_data):
    sensor = sd["sensor"]
    times_mpl = mdates.date2num(sd["times"].astype("datetime64[us]").astype(datetime))

    dt_half = np.diff(times_mpl) / 2
    time_edges = np.empty(len(times_mpl) + 1)
    time_edges[0]    = times_mpl[0] - (dt_half[0] if len(dt_half) > 0 else 0.01)
    time_edges[-1]   = times_mpl[-1] + (dt_half[-1] if len(dt_half) > 0 else 0.01)
    time_edges[1:-1] = times_mpl[:-1] + dt_half

    pcm = ax.pcolormesh(time_edges, depth_edges, sd["curtain"],
                         cmap=sensor["cmap"], vmin=sd["vmin"], vmax=sd["vmax"],
                         shading="flat")

    # Overlay contour lines with gap breaks
    for idx, sv in enumerate(sd["contour_values"]):
        fd = sd["contour_filtered"][sv]
        color = sensor["contour_colors"][idx % len(sensor["contour_colors"])]
        label = f"{sensor['title_var'][:3]} = {sv:.2f}"
        plot_contour_segments(ax, sd["raw_times"], fd, color, label)

    ax.legend(loc="lower right", fontsize=9, framealpha=0.8)
    ax.set_ylim(DEPTH_MAX, DEPTH_MIN)
    ax.set_xlim(mdates.date2num(TIME_START), mdates.date2num(TIME_END))
    ax.set_ylabel("Depth (m)")
    ax.set_title(f"Oregon Slope Base -- {sensor['title_var']} Curtain Plot (2024-2025)", fontsize=13)

    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO))

    cbar = fig.colorbar(pcm, ax=ax, pad=0.01)
    cbar.set_label(sensor["label"])

axes[-1].set_xlabel("Date")
fig.set_facecolor("white")
for ax in axes:
    ax.set_facecolor("white")

plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=150, facecolor="white")
print(f"\nCurtain plot saved to {OUTPUT_PNG}")
