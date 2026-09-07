# curtain_core.py — Shared rendering logic for curtain plots.
#
# Used by:
#   - curtain_plot.py (interactive, multi-sensor)
#   - curtain_batch.py (command-line, single-sensor, yearly batch)

import sys
import glob
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from pathlib import Path

# Make the repo root importable so `import ooipaths` works.
sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op
import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path
from scipy.ndimage import uniform_filter1d
import pandas as pd


# == Sensor configuration ======================================================

SENSOR_CONFIGS = {
    'temperature':     {"glob": "RCA_sb_sp_temperature_*.nc",     "var": "temperature",     "label": "Temperature (°C)",       "cmap": "inferno", "n_contours": 4, "contour_pcts": [20, 40, 60, 80], "contour_colors": ["white", "white", "black", "black"]},
    'salinity':        {"glob": "RCA_sb_sp_salinity_*.nc",        "var": "salinity",        "label": "Salinity (PSU)",         "cmap": "viridis", "n_contours": 4, "contour_pcts": [20, 40, 60, 80], "contour_colors": ["black", "black", "black", "black"]},
    'dissolvedoxygen': {"glob": "RCA_sb_sp_dissolvedoxygen_*.nc", "var": "dissolvedoxygen", "label": "Dissolved Oxygen (µmol/kg)", "cmap": "cividis", "n_contours": 4, "contour_pcts": [20, 40, 60, 80], "contour_colors": ["black", "black", "black", "black"]},
    'density':         {"glob": "RCA_sb_sp_density_*.nc",         "var": "density",         "label": "Density (kg/m3)",        "cmap": "plasma", "n_contours": 4, "contour_pcts": [20, 40, 60, 80], "contour_colors": ["black", "black", "black", "black"]},
    'cdom':            {"glob": "RCA_sb_sp_cdom_*.nc",            "var": "cdom",            "label": "CDOM (ppb)",             "cmap": "YlOrBr", "n_contours": 4, "contour_pcts": [20, 40, 60, 80], "contour_colors": ["black", "black", "black", "black"]},
    'chlora':          {"glob": "RCA_sb_sp_chlora_*.nc",          "var": "chlora",          "label": "Chlorophyll-A (ug/L)",   "cmap": "GnBu", "n_contours": 4, "contour_pcts": [20, 40, 60, 80], "contour_colors": ["black", "black", "black", "black"]},
    'backscatter':     {"glob": "RCA_sb_sp_backscatter_*.nc",     "var": "backscatter",     "label": "Backscatter (m-1 sr-1)", "cmap": "Greys", "n_contours": 4, "contour_pcts": [20, 40, 60, 80], "contour_colors": ["black", "black", "black", "black"]},
    'par':             {"glob": "RCA_sb_sp_par_*.nc",             "var": "par",             "label": "PAR (umol m-2 s-1)",     "cmap": "YlOrRd", "n_contours": 4, "contour_pcts": [20, 40, 60, 80], "contour_colors": ["black", "black", "black", "black"]},
}

# Friendly aliases
SENSOR_ALIASES = {'oxygen': 'dissolvedoxygen', 'do': 'dissolvedoxygen'}

VALID_SENSOR_NAMES = list(SENSOR_CONFIGS.keys())


# == Grid parameters ===========================================================

DEPTH_MIN, DEPTH_MAX, DEPTH_BINS = 0, 200, 200
GAP_HOURS = 12
LP_WINDOW = 27
CONTOUR_GAP_DAYS = 3

depth_edges = np.linspace(DEPTH_MIN, DEPTH_MAX, DEPTH_BINS + 1)
depth_centers = 0.5 * (depth_edges[:-1] + depth_edges[1:])
gap_threshold = np.timedelta64(GAP_HOURS, 'h')
contour_gap_threshold = np.timedelta64(CONTOUR_GAP_DAYS, 'D')


# == Sensor exclusions =========================================================

EXCLUSIONS_CSV = Path("~/argosy/sensor_exclusions.csv").expanduser()
_sensor_exclusions = {}
if EXCLUSIONS_CSV.exists():
    _exc_df = pd.read_csv(EXCLUSIONS_CSV)
    for _, row in _exc_df.iterrows():
        _sensor_exclusions.setdefault(row['sensor'], []).append(
            (np.datetime64(row['start']), np.datetime64(row['end'])))


def is_excluded(sensor_var, mid_time):
    if sensor_var not in _sensor_exclusions:
        return False
    for exc_start, exc_end in _sensor_exclusions[sensor_var]:
        if exc_start <= mid_time <= exc_end:
            return True
    return False


# == Core functions ============================================================

def load_profiles(sensor_config, data_base, time_start, time_end):
    """Load and bin profiles for a sensor within a time range.

    Returns list of (mid_time, depth_column) tuples, or empty list.
    """
    # Discover year directories — handles both new (<yyyy>) and old (redux<yyyy>) naming.
    redux_dirs = []
    for y in range(time_start.year, time_end.year + 1):
        candidate = data_base / str(y)             # new layout: <yyyy>
        if not candidate.is_dir():
            candidate = data_base / f"redux{y}"    # old layout: redux<yyyy>
        if candidate.is_dir():
            redux_dirs.append(str(candidate))

    files = []
    for d in redux_dirs:
        files.extend(sorted(glob.glob(f"{d}/{sensor_config['glob']}")))

    filtered = []
    for f in files:
        try:
            ds = xr.open_dataset(f)
            t = ds.time.values
            if len(t) == 0:
                ds.close()
                continue
            mid_time = t[len(t) // 2]
            if np.datetime64(time_start) <= mid_time <= np.datetime64(time_end):
                if not is_excluded(sensor_config['var'], mid_time):
                    filtered.append(f)
            ds.close()
        except Exception:
            continue

    profile_columns = []
    for f in filtered:
        try:
            ds = xr.open_dataset(f)
            vals = ds[sensor_config['var']].values
            depths = ds['depth'].values if 'depth' in ds.data_vars else ds.coords['depth'].values
            times = ds.time.values
            ds.close()

            valid = ~(np.isnan(vals) | np.isnan(depths))
            if valid.sum() < 2:
                continue

            mid_time = times[len(times) // 2]
            col = np.full(DEPTH_BINS, np.nan)
            d_valid = depths[valid]
            v_valid = vals[valid]

            for j in range(DEPTH_BINS):
                mask = (d_valid >= depth_edges[j]) & (d_valid < depth_edges[j + 1])
                if mask.sum() > 0:
                    col[j] = np.nanmean(v_valid[mask])

            profile_columns.append((mid_time, col))
        except Exception:
            continue

    return profile_columns


def render_curtain(ax, fig, sensor_config, profile_columns, time_start, time_end):
    """Render a single curtain panel on the given axes.

    Returns the pcolormesh object (for colorbar) or None if no data.
    """
    if not profile_columns:
        ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
        return None

    all_vals = np.concatenate([pc[1] for pc in profile_columns])
    all_vals = all_vals[~np.isnan(all_vals)]
    vmin = np.percentile(all_vals, 5)
    vmax = np.percentile(all_vals, 95)

    # Insert NaN columns at gaps
    typical_dt = np.timedelta64(3, 'h')
    expanded = []
    for i, pc in enumerate(profile_columns):
        expanded.append(pc)
        if i < len(profile_columns) - 1:
            dt = profile_columns[i + 1][0] - pc[0]
            if dt > gap_threshold:
                expanded.append((pc[0] + typical_dt, np.full(DEPTH_BINS, np.nan)))
                expanded.append((profile_columns[i + 1][0] - typical_dt, np.full(DEPTH_BINS, np.nan)))

    times_arr = np.array([pc[0] for pc in expanded])
    curtain = np.column_stack([pc[1] for pc in expanded])

    times_mpl = mdates.date2num(times_arr.astype('datetime64[ms]').astype(datetime))
    dt_half = np.diff(times_mpl).mean() / 2 if len(times_mpl) > 1 else 0.01

    time_edges = np.zeros(len(times_mpl) + 1)
    time_edges[0] = times_mpl[0] - dt_half
    time_edges[-1] = times_mpl[-1] + dt_half
    time_edges[1:-1] = times_mpl[:-1] + dt_half

    pcm = ax.pcolormesh(time_edges, depth_edges, curtain,
                        cmap=sensor_config['cmap'], vmin=vmin, vmax=vmax, shading='flat')

    # Contour rendering
    contour_pcts = sensor_config['contour_pcts']
    contour_values = np.array([np.percentile(all_vals, p) for p in contour_pcts])
    raw_times = np.array([pc[0] for pc in profile_columns])
    raw_curtain = np.column_stack([pc[1] for pc in profile_columns])
    contrast_colors = sensor_config.get('contour_colors', ['black'] * len(contour_values))

    for sv, color in zip(contour_values, contrast_colors):
        depths_at_sv = np.full(len(profile_columns), np.nan)
        for j in range(len(profile_columns)):
            col = raw_curtain[:, j]
            valid_mask = np.isfinite(col)
            if valid_mask.sum() < 2:
                continue
            d_v = depth_centers[valid_mask]
            c_v = col[valid_mask]
            crossings = np.where(np.diff(np.sign(c_v - sv)))[0]
            if len(crossings) > 0:
                idx = crossings[0]
                if c_v[idx + 1] != c_v[idx]:
                    frac = (sv - c_v[idx]) / (c_v[idx + 1] - c_v[idx])
                    depths_at_sv[j] = d_v[idx] + frac * (d_v[idx + 1] - d_v[idx])

        smoothed = np.full_like(depths_at_sv, np.nan)
        if len(raw_times) > 1:
            gap_indices = np.where(np.diff(raw_times) > contour_gap_threshold)[0] + 1
            segments = np.split(np.arange(len(raw_times)), gap_indices)
            for seg in segments:
                if len(seg) >= LP_WINDOW:
                    seg_data = depths_at_sv[seg]
                    valid_seg = np.isfinite(seg_data)
                    if valid_seg.sum() >= LP_WINDOW:
                        valid_idx = np.where(valid_seg)[0]
                        sub_breaks = np.where(np.diff(valid_idx) > 2)[0] + 1
                        sub_segs = np.split(valid_idx, sub_breaks)
                        for sub in sub_segs:
                            if len(sub) >= LP_WINDOW:
                                local_range = np.arange(sub[0], sub[-1] + 1)
                                local_data = seg_data[local_range]
                                local_valid = np.isfinite(local_data)
                                if local_valid.sum() >= LP_WINDOW:
                                    filled = np.interp(np.arange(len(local_data)),
                                                       np.where(local_valid)[0],
                                                       local_data[local_valid])
                                    smoothed[seg[local_range]] = uniform_filter1d(filled, LP_WINDOW)

        valid = np.isfinite(smoothed)
        if valid.sum() > 0:
            valid_indices = np.where(valid)[0]
            rt_valid = raw_times[valid_indices]
            sm_valid = smoothed[valid_indices]
            rt_mpl = mdates.date2num(rt_valid.astype('datetime64[ms]').astype(datetime))

            time_gaps = np.diff(rt_valid)
            breaks = np.where(time_gaps > np.timedelta64(3, 'D'))[0] + 1
            seg_starts = np.concatenate([[0], breaks])
            seg_ends = np.concatenate([breaks, [len(rt_mpl)]])

            for s_start, s_end in zip(seg_starts, seg_ends):
                if s_end - s_start >= 2:
                    ax.plot(rt_mpl[s_start:s_end], sm_valid[s_start:s_end],
                            color=color, linewidth=0.9, alpha=0.9)

    contour_text = "Contours: " + ", ".join([f"{v:.2f}" for v in contour_values])
    ax.text(0.005, 0.99, contour_text, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', horizontalalignment='left',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='gray'))

    ax.set_xlim(mdates.date2num(time_start), mdates.date2num(time_end))
    ax.set_ylim(DEPTH_MAX, DEPTH_MIN)
    ax.set_ylabel('Depth (m)')
    ax.set_title(f"{sensor_config['label']}  {time_start.strftime('%b-%Y')} — {time_end.strftime('%b-%Y')}", fontsize=14)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%y'))
    ax.tick_params(axis='x', which='major', length=8, width=1.5)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    cbar = fig.colorbar(pcm, ax=ax, pad=0.01)
    cbar.set_label(sensor_config['label'])

    return pcm
