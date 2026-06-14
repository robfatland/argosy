# Curtain plot: HSD sensors for Oregon Slope Base shallow profiler
# Run this as: %run ~/argosy/curtain_plot.py
#
# Inputs (interactive):
#   - Data source (redux/pp01/pp02/pp05/pp06)
#   - Start and end dates
#   - Sensor selection (All or subset)
#
# Outputs:
#   - Stacked curtain plot PNG: ~/ooi/visualizations/CurtainPlots_<loc>_<start>_<end>.png
#   - Contour values CSV: ~/ooi/metadata/curtain_contour_values_<loc>_<start>_<end>.csv

import glob, csv
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path
from scipy.ndimage import uniform_filter1d
import pandas as pd

# == Data source selection ======================================================
source_choice = input("Data source (redux/pp01/pp02/pp05/pp06, default pp06): ").strip().lower()
if source_choice in ('pp01', 'pp02'):
    DATA_BASE = Path(f"~/ooi/postproc/{source_choice}/redux").expanduser()
elif source_choice == 'pp06':
    DATA_BASE = Path("~/ooi/postproc/pp06").expanduser()
elif source_choice == 'pp05':
    DATA_BASE = Path("~/ooi/redux").expanduser()
else:
    source_choice = "pp06"
    DATA_BASE = Path("~/ooi/postproc/pp06").expanduser()

print(f"Source: {source_choice} ({DATA_BASE})")

# == All 8 HSD sensors =========================================================
ALL_SENSORS = [
    {"glob": "RCA_sb_sp_temperature_*.nc", "var": "temperature", "label": "Temperature (°C)",
     "cmap": "inferno", "instrum": "CTD", "n_contours": 4, "contour_pcts": [20, 40, 60, 80], "contour_colors": ["white", "white", "black", "black"]},
    {"glob": "RCA_sb_sp_salinity_*.nc", "var": "salinity", "label": "Salinity (PSU)",
     "cmap": "viridis", "instrum": "CTD", "n_contours": 4, "contour_pcts": [20, 40, 60, 80]},
    {"glob": "RCA_sb_sp_dissolvedoxygen_*.nc", "var": "dissolvedoxygen", "label": "Dissolved Oxygen (µmol/kg)",
     "cmap": "cividis", "instrum": "CTD", "n_contours": 4, "contour_pcts": [20, 40, 60, 80]},
    {"glob": "RCA_sb_sp_density_*.nc", "var": "density", "label": "Density (kg/m³)",
     "cmap": "plasma", "instrum": "CTD", "n_contours": 4, "contour_pcts": [20, 40, 60, 80]},
    {"glob": "RCA_sb_sp_cdom_*.nc", "var": "cdom", "label": "CDOM (ppb)",
     "cmap": "YlOrBr", "instrum": "FLORT", "n_contours": 4, "contour_pcts": [20, 40, 60, 80]},
    {"glob": "RCA_sb_sp_chlora_*.nc", "var": "chlora", "label": "Chlorophyll-A (µg/L)",
     "cmap": "GnBu", "instrum": "FLORT", "n_contours": 4, "contour_pcts": [20, 40, 60, 80]},
    {"glob": "RCA_sb_sp_backscatter_*.nc", "var": "backscatter", "label": "Backscatter (m⁻¹sr⁻¹)",
     "cmap": "Greys", "instrum": "FLORT", "n_contours": 4, "contour_pcts": [20, 40, 60, 80]},
    {"glob": "RCA_sb_sp_par_*.nc", "var": "par", "label": "PAR (µmol m⁻²s⁻¹)",
     "cmap": "YlOrRd", "instrum": "PARAD", "n_contours": 4, "contour_pcts": [20, 40, 60, 80]},
]

# == User input: time range ====================================================
start_str = input("Start date (YYYY-MM-DD, default 2023-01-01): ").strip()
end_str = input("End date (YYYY-MM-DD, default 2024-01-01): ").strip()
TIME_START = datetime.strptime(start_str, "%Y-%m-%d") if start_str else datetime(2023, 1, 1)
TIME_END = datetime.strptime(end_str, "%Y-%m-%d") if end_str else datetime(2024, 1, 1)

# == User input: sensor selection ==============================================
choice = input("Sensors - All or Select? (default All): ").strip().lower()
if choice.startswith('s'):
    numbered = "  ".join([f"{i+1}:{s['var']}" for i, s in enumerate(ALL_SENSORS)])
    picks = input(f"Enter numbers ({numbered}): ").strip()
    indices = [int(x) - 1 for x in picks.replace(',', ' ').split() if x.isdigit()]
    SENSORS = [ALL_SENSORS[i] for i in indices if 0 <= i < len(ALL_SENSORS)]
else:
    SENSORS = ALL_SENSORS

# == Configuration =============================================================
LOCATION = "SlopeBase"
REDUX_DIRS = [str(DATA_BASE / f"redux{y}") for y in range(TIME_START.year, TIME_END.year + 1)]

DEPTH_MIN, DEPTH_MAX, DEPTH_BINS = 0, 200, 200
GAP_HOURS, LP_WINDOW, CONTOUR_GAP_DAYS = 12, 27, 3

depth_edges = np.linspace(DEPTH_MIN, DEPTH_MAX, DEPTH_BINS + 1)
depth_centers = 0.5 * (depth_edges[:-1] + depth_edges[1:])
gap_threshold = np.timedelta64(GAP_HOURS, 'h')
contour_gap_threshold = np.timedelta64(CONTOUR_GAP_DAYS, 'D')

# == Load sensor exclusions ====================================================
EXCLUSIONS_CSV = Path("~/argosy/sensor_exclusions.csv").expanduser()
sensor_exclusions = {}
if EXCLUSIONS_CSV.exists():
    exc_df = pd.read_csv(EXCLUSIONS_CSV)
    for _, row in exc_df.iterrows():
        sensor_exclusions.setdefault(row['sensor'], []).append(
            (np.datetime64(row['start']), np.datetime64(row['end'])))

def is_excluded(sensor_var, mid_time):
    if sensor_var not in sensor_exclusions:
        return False
    for exc_start, exc_end in sensor_exclusions[sensor_var]:
        if exc_start <= mid_time <= exc_end:
            return True
    return False

# == Process all sensors =======================================================
sensor_results = []

for sensor in SENSORS:
    print(f"  Processing {sensor['var']}...", end=' ')
    files = []
    for d in REDUX_DIRS:
        files.extend(sorted(glob.glob(f"{d}/{sensor['glob']}")))

    filtered = []
    for f in files:
        try:
            ds = xr.open_dataset(f)
            t = ds.time.values
            if len(t) == 0:
                ds.close()
                continue
            mid_time = t[len(t)//2]
            if np.datetime64(TIME_START) <= mid_time <= np.datetime64(TIME_END):
                if not is_excluded(sensor['var'], mid_time):
                    filtered.append(f)
            ds.close()
        except:
            continue

    profile_columns = []
    for f in filtered:
        try:
            ds = xr.open_dataset(f)
            vals = ds[sensor['var']].values
            depths = ds['depth'].values if 'depth' in ds.data_vars else ds.coords['depth'].values
            times = ds.time.values
            ds.close()

            valid = ~(np.isnan(vals) | np.isnan(depths))
            if valid.sum() < 2:
                continue

            mid_time = times[len(times)//2]
            col = np.full(DEPTH_BINS, np.nan)
            d_valid = depths[valid]
            v_valid = vals[valid]

            for j in range(DEPTH_BINS):
                mask = (d_valid >= depth_edges[j]) & (d_valid < depth_edges[j+1])
                if mask.sum() > 0:
                    col[j] = np.nanmean(v_valid[mask])

            profile_columns.append((mid_time, col))
        except:
            continue

    if not profile_columns:
        print("no data")
        continue

    all_vals = np.concatenate([pc[1] for pc in profile_columns])
    all_vals = all_vals[~np.isnan(all_vals)]
    vmin = np.percentile(all_vals, 5)
    vmax = np.percentile(all_vals, 95)

    typical_dt = np.timedelta64(3, 'h')
    expanded = []
    for i, pc in enumerate(profile_columns):
        expanded.append(pc)
        if i < len(profile_columns) - 1:
            dt = profile_columns[i+1][0] - pc[0]
            if dt > gap_threshold:
                expanded.append((pc[0] + typical_dt, np.full(DEPTH_BINS, np.nan)))
                expanded.append((profile_columns[i+1][0] - typical_dt, np.full(DEPTH_BINS, np.nan)))

    times_arr = np.array([pc[0] for pc in expanded])
    curtain = np.column_stack([pc[1] for pc in expanded])

    sensor_results.append({
        'sensor': sensor, 'times': times_arr, 'curtain': curtain,
        'vmin': vmin, 'vmax': vmax, 'profile_columns': profile_columns,
    })
    print(f"{len(profile_columns)} profiles")

# == Plot: stacked panels ======================================================
n_panels = len(sensor_results)
fig, axes = plt.subplots(n_panels, 1, figsize=(20, 6 * n_panels))
if n_panels == 1:
    axes = [axes]

for ax, sr in zip(axes, sensor_results):
    sensor = sr['sensor']
    times_arr = sr['times']
    curtain = sr['curtain']
    vmin, vmax = sr['vmin'], sr['vmax']
    profile_columns = sr['profile_columns']

    times_mpl = mdates.date2num(times_arr.astype('datetime64[ms]').astype(datetime))
    dt_half = np.diff(times_mpl).mean() / 2 if len(times_mpl) > 1 else 0.01

    time_edges = np.zeros(len(times_mpl) + 1)
    time_edges[0] = times_mpl[0] - dt_half
    time_edges[-1] = times_mpl[-1] + dt_half
    time_edges[1:-1] = times_mpl[:-1] + dt_half

    pcm = ax.pcolormesh(time_edges, depth_edges, curtain,
                         cmap=sensor['cmap'], vmin=vmin, vmax=vmax, shading='flat')

    # Contour rendering
    contour_pcts = sensor['contour_pcts']
    all_vals_plot = np.concatenate([pc[1] for pc in profile_columns])
    all_vals_plot = all_vals_plot[~np.isnan(all_vals_plot)]
    contour_values = np.array([np.percentile(all_vals_plot, p) for p in contour_pcts])
    raw_times = np.array([pc[0] for pc in profile_columns])
    raw_curtain = np.column_stack([pc[1] for pc in profile_columns])

    contrast_colors = sensor.get('contour_colors', ['black'] * len(contour_values))

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
                if c_v[idx+1] != c_v[idx]:
                    frac = (sv - c_v[idx]) / (c_v[idx+1] - c_v[idx])
                    depths_at_sv[j] = d_v[idx] + frac * (d_v[idx+1] - d_v[idx])

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
                                                       np.where(local_valid)[0], local_data[local_valid])
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

    ax.set_xlim(mdates.date2num(TIME_START), mdates.date2num(TIME_END))
    ax.set_ylim(DEPTH_MAX, DEPTH_MIN)
    ax.set_ylabel('Depth (m)')
    ax.set_title(f"{sensor['label']}  {TIME_START.strftime('%b-%Y')} — {TIME_END.strftime('%b-%Y')}", fontsize=14)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%y'))
    ax.tick_params(axis='x', which='major', length=8, width=1.5)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    cbar = fig.colorbar(pcm, ax=ax, pad=0.01)
    cbar.set_label(sensor['label'])

plt.tight_layout()

# == Save outputs ==============================================================
s_tag = TIME_START.strftime("%Y%m%d")
e_tag = TIME_END.strftime("%Y%m%d")

png_path = Path(f"~/ooi/visualizations/CurtainPlots_{LOCATION}_{s_tag}_{e_tag}.png").expanduser()
fig.savefig(png_path, dpi=150, facecolor="white")

csv_path = Path(f"~/ooi/metadata/curtain_contour_values_{LOCATION}_{s_tag}_{e_tag}.csv").expanduser()
with open(csv_path, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['sensor', 'n_contours', 'contour_values', 'vmin_5pct', 'vmax_95pct'])
    for sr in sensor_results:
        nc = sr['sensor']['n_contours']
        cp = sr['sensor']['contour_pcts']
        av = np.concatenate([pc[1] for pc in sr['profile_columns']])
        av = av[~np.isnan(av)]
        cv = np.array([np.percentile(av, p) for p in cp])
        cv_str = ";".join([f"{v:.4f}" for v in cv])
        writer.writerow([sr['sensor']['var'], nc, cv_str, f"{sr['vmin']:.4f}", f"{sr['vmax']:.4f}"])

plt.show()
print(png_path)
print(csv_path)
