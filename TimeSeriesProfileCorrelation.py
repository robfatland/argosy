# TimeSeriesProfileCorrelation.py
# Generates a time series of vertical offsets between consecutive profiles.
#
# Method: Cross-correlation between adjacent profiles on a regular depth grid.
# The lag at peak correlation gives the vertical shift (meters) that best aligns
# profile N+1 with profile N. This reveals tidal and current-driven platform
# displacement over time.
#
# Run this as: %run ~/argosy/TimeSeriesProfileCorrelation.py
#
# Output: A chart with:
#   - Red: temperature inter-profile vertical offset (relative to mean)
#   - Blue: salinity inter-profile vertical offset (relative to mean)
#   - Black: profile start depth (~180m) and end depth (~15m) relative to their means

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# == Configuration =============================================================
DATA_BASE = Path("~/ooi/postproc/pp06").expanduser()
DEPTH_GRID = np.linspace(27, 185, 3950)  # 0.04m (4cm) resolution for cross-correlation
DG_STEP = DEPTH_GRID[1] - DEPTH_GRID[0]  # meters per grid step

# Time range: first 10 days of 2024
TIME_START = datetime(2024, 1, 1)
TIME_END = datetime(2024, 1, 11)

SENSORS = ['temperature', 'salinity']
COLORS = {'temperature': 'red', 'salinity': 'blue'}

# Jump threshold: offsets exceeding this are treated as no-data
JUMP_THRESHOLD = .10  # meters

print("TimeSeriesProfileCorrelation")
print(f"  Source: {DATA_BASE}")
print(f"  Time range: {TIME_START.strftime('%Y-%m-%d')} to {TIME_END.strftime('%Y-%m-%d')}")
print(f"  Depth grid: {DEPTH_GRID[0]:.0f}-{DEPTH_GRID[-1]:.0f}m, step={DG_STEP:.2f}m")

# == Gather profiles in time range =============================================

def get_profiles_in_range(sensor, data_base, time_start, time_end):
    """Get sorted list of (global_idx, filepath, actual_mid_time) for profiles in time range."""
    profiles = []
    for year in range(time_start.year, time_end.year + 1):
        redux_dir = data_base / f"redux{year}"
        if not redux_dir.exists():
            continue
        files = sorted(redux_dir.glob(f"*_{sensor}_*.nc"))
        for f in files:
            parts = f.stem.split('_')
            file_year = int(parts[4])
            doy = int(parts[5])
            gidx = int(parts[6])
            # Quick date check from filename to avoid opening every file
            approx_date = datetime(file_year, 1, 1) + timedelta(days=doy - 1)
            if approx_date < time_start - timedelta(days=1) or approx_date > time_end + timedelta(days=1):
                continue
            # Get actual mid-time from the file
            try:
                ds = xr.open_dataset(f)
                t = ds.time.values
                ds.close()
                if len(t) == 0:
                    continue
                mid_time = t[len(t)//2].astype('datetime64[us]').astype(datetime)
                if time_start <= mid_time <= time_end:
                    profiles.append((gidx, f, mid_time))
            except:
                continue
    profiles.sort(key=lambda x: x[0])
    return profiles


def interpolate_to_grid(filepath, sensor, depth_grid):
    """Load a profile and interpolate to regular depth grid. Also return time at ~70m."""
    try:
        ds = xr.open_dataset(filepath)
        data = ds[sensor].values
        depth = ds['depth'].values
        times = ds['time'].values
        ds.close()

        valid = ~(np.isnan(data) | np.isnan(depth))
        if valid.sum() < 10:
            return None, None, None, None

        d = depth[valid]
        v = data[valid]
        t = times[valid]
        sort_idx = np.argsort(d)
        d = d[sort_idx]
        v = v[sort_idx]
        t = t[sort_idx]

        interp = np.interp(depth_grid, d, v, left=np.nan, right=np.nan)

        # Start and end depths (actual data extent)
        start_depth = d.max()   # deepest point (bottom of ascent)
        end_depth = d.min()     # shallowest point (top of ascent)

        # Time at ~70m (interpolate from depth-sorted times)
        if d.min() <= 70 <= d.max():
            time_at_70 = np.interp(70.0, d, t.astype(float))
            time_at_70 = np.datetime64(int(time_at_70), 'ns')
        else:
            # Fallback to mid-time
            time_at_70 = t[len(t)//2]

        return interp, start_depth, end_depth, time_at_70
    except:
        return None, None, None, None


def cross_correlate_offset(profile_a, profile_b, dg_step):
    """
    Compute vertical offset between two profiles via normalized cross-correlation.
    Uses the 25-100m depth range where gradient structure is strongest.
    Returns offset in meters: positive = profile_b is shifted deeper relative to A.
    """
    # Restrict to 25-100m range within the depth grid
    depth_mask = (DEPTH_GRID >= 25) & (DEPTH_GRID <= 100)
    a_region = profile_a[depth_mask]
    b_region = profile_b[depth_mask]

    # Mask NaN: only use overlapping valid region
    valid = ~(np.isnan(a_region) | np.isnan(b_region))
    if valid.sum() < 20:
        return np.nan

    a = a_region[valid]
    b = b_region[valid]

    # Normalize
    a_norm = (a - np.mean(a)) / (np.std(a) + 1e-10)
    b_norm = (b - np.mean(b)) / (np.std(b) + 1e-10)

    # Cross-correlation
    corr = np.correlate(a_norm, b_norm, mode='full')
    corr = corr / len(a)

    # Lag axis
    lags = np.arange(-len(a) + 1, len(a))

    # Restrict to reasonable offsets (±10m)
    max_lag = int(10.0 / dg_step)
    center = len(a) - 1
    lo = max(0, center - max_lag)
    hi = min(len(corr), center + max_lag + 1)

    corr_window = corr[lo:hi]
    lags_window = lags[lo:hi]

    if len(corr_window) == 0:
        return np.nan

    # Sub-sample peak finding via quadratic interpolation
    peak_idx = np.argmax(corr_window)

    # Quadratic interpolation for sub-grid precision
    if 0 < peak_idx < len(corr_window) - 1:
        y0 = corr_window[peak_idx - 1]
        y1 = corr_window[peak_idx]
        y2 = corr_window[peak_idx + 1]
        denom = 2.0 * (2.0 * y1 - y0 - y2)
        if abs(denom) > 1e-10:
            shift = (y0 - y2) / denom
        else:
            shift = 0.0
        offset_steps = lags_window[peak_idx] + shift
    else:
        offset_steps = lags_window[peak_idx]

    offset_meters = offset_steps * dg_step

    # Reject unreasonable offsets
    if abs(offset_meters) > JUMP_THRESHOLD:
        return np.nan

    return offset_meters


# == Process each sensor =======================================================
results = {}

for sensor in SENSORS:
    print(f"\n  Processing {sensor}...")
    profiles = get_profiles_in_range(sensor, DATA_BASE, TIME_START, TIME_END)
    print(f"    {len(profiles)} profiles in range")

    times = []
    offsets = []
    start_depths = []
    end_depths = []

    prev_interp = None
    prev_time_70 = None
    prev_date = None

    for i, (gidx, filepath, profile_date) in enumerate(profiles):
        interp, start_d, end_d, time_70 = interpolate_to_grid(filepath, sensor, DEPTH_GRID)
        if interp is None:
            prev_interp = None
            prev_time_70 = None
            continue

        if prev_interp is not None and prev_time_70 is not None and time_70 is not None:
            offset = cross_correlate_offset(prev_interp, interp, DG_STEP)
            # Time marker: mean of the two profiles' times at 70m depth
            t70_prev = prev_time_70.astype('datetime64[us]').astype('int64')
            t70_curr = time_70.astype('datetime64[us]').astype('int64')
            mean_us = (t70_prev + t70_curr) // 2
            mean_time_70 = datetime.utcfromtimestamp(mean_us / 1e6)
            times.append(mean_time_70)
            offsets.append(offset)

        start_depths.append((profile_date, start_d))
        end_depths.append((profile_date, end_d))

        prev_interp = interp
        prev_time_70 = time_70
        prev_date = profile_date

    # Compute cumulative offsets, then bias to zero mean
    offsets_arr = np.array(offsets)
    cumulative = np.nancumsum(np.where(np.isnan(offsets_arr), 0, offsets_arr))
    # Where original was NaN, keep NaN in cumulative
    cumulative = np.where(np.isnan(offsets_arr), np.nan, cumulative)
    # Bias to zero mean
    cum_mean = np.nanmean(cumulative)
    cumulative = cumulative - cum_mean

    results[sensor] = {
        'times': times,
        'cumulative_offsets': cumulative,
        'start_depths': start_depths,
        'end_depths': end_depths,
    }
    print(f"    {len(offsets)} offset values computed")

# == Plot ======================================================================
fig, axes = plt.subplots(5, 1, figsize=(14, 16), sharex=True)

# Panel 1: cumulative vertical offsets (temp + salinity)
ax = axes[0]
for sensor in SENSORS:
    r = results[sensor]
    if len(r['cumulative_offsets']) == 0:
        continue
    ax.plot(r['times'], r['cumulative_offsets'], '-', color=COLORS[sensor], linewidth=0.8,
            alpha=0.8, label=f"{sensor.capitalize()}")

ax.axhline(0, color='gray', linewidth=0.5, linestyle='--')
ax.set_ylabel('Cumulative offset (m)')
ax.set_ylim(-0.05, 0.05)
ax.set_title(f'Cumulative inter-profile vertical shift, '
             f'{TIME_START.strftime("%Y-%m-%d")} to {TIME_END.strftime("%Y-%m-%d")}')
ax.legend()
ax.grid(True, alpha=0.3)

# Panel 2: End depth (shallowest point) absolute
ax = axes[1]
r = results['temperature']
if r['end_depths']:
    ed_times = [pd.Timestamp(x[0]) for x in r['end_depths']]
    ed_values = np.array([x[1] for x in r['end_depths']])
    ax.plot(ed_times, ed_values, '-', color='black', linewidth=0.8, alpha=0.8)
    ax.set_title('End depth / shallowest (absolute, 0 = ocean surface)')

ax.axhline(0, color='lightblue', linewidth=1)
ax.set_ylabel('Depth (m)')
ax.invert_yaxis()
ax.grid(True, alpha=0.3)

# Panel 3: Start depth (deepest point) relative to mean
ax = axes[2]

if r['start_depths']:
    sd_times = [pd.Timestamp(x[0]) for x in r['start_depths']]
    sd_values = np.array([x[1] for x in r['start_depths']])
    sd_mean = np.nanmean(sd_values)
    ax.plot(sd_times, sd_values - sd_mean, '-', color='black', linewidth=0.8,
            alpha=0.8, label=f'Start depth (~{sd_mean:.0f}m, rel. mean)')

ax.axhline(0, color='gray', linewidth=0.5, linestyle='--')
ax.set_ylabel('Depth rel. mean (m)')
ax.set_ylim(-2, 2)
ax.set_title('Start depth / deepest (relative to mean)')
ax.legend()
ax.grid(True, alpha=0.3)

# Panel 4: Tidal height
ax = axes[3]

import json
from datetime import timezone

json_path = Path("~/argosy/tidal_constituents.json").expanduser()
with open(json_path) as f:
    tidal_data = json.load(f)

def predict_tide(constituents_dict, times):
    """Predict tidal height from extracted constituents."""
    t0 = datetime(2000, 1, 1, tzinfo=timezone.utc)
    hours = np.array([(t.replace(tzinfo=timezone.utc) - t0).total_seconds() / 3600.0
                      for t in times])
    heights = np.zeros(len(hours))
    for const_name, params in constituents_dict.items():
        amp = params["amplitude_m"]
        phase = np.radians(params["phase_deg"])
        omega = np.radians(params["omega_deg_per_hr"])
        heights += amp * np.cos(omega * hours - phase)
    return heights

n_hours = int((TIME_END - TIME_START).total_seconds() / 3600)
tide_times = [TIME_START + timedelta(hours=h) for h in range(n_hours + 1)]
tide_heights = predict_tide(tidal_data["Oregon Slope Base"]["constituents"], tide_times)

ax.plot(tide_times, tide_heights, color='darkblue', linewidth=0.8, alpha=0.8)
ax.axhline(0, color='gray', linewidth=0.5, linestyle='--')
ax.set_ylabel('Tidal height (m)')
ax.set_ylim(-2, 2)
ax.set_xlabel('Date')
ax.set_title('Predicted tidal height — Oregon Slope Base')
ax.grid(True, alpha=0.3)

# Panel 5: Shifted tidal signal minus start depth (placeholder — filled after correlation)
ax5 = axes[4]
ax5.set_ylabel('Residual (m)')
ax5.set_xlabel('Date')
ax5.axhline(0, color='gray', linewidth=0.5, linestyle='--')
ax5.grid(True, alpha=0.3)

# Compute correlation here so we can plot panel 5 immediately
if r['start_depths']:
    # Interpolate both signals to a common regular time grid (every 10 minutes)
    dt_minutes = 10
    n_steps_corr = int((TIME_END - TIME_START).total_seconds() / (dt_minutes * 60))
    reg_seconds = np.array([i * dt_minutes * 60 for i in range(n_steps_corr)])

    # Start depth on regular grid
    sd_times_dt = [x[0] for x in r['start_depths']]
    sd_seconds = np.array([(t - TIME_START).total_seconds() for t in sd_times_dt])
    sd_vals = sd_values - sd_mean
    sd_regular = np.interp(reg_seconds, sd_seconds, sd_vals)

    # Tidal height on regular grid
    tide_seconds_arr = np.array([(t - TIME_START).total_seconds() for t in tide_times])
    tide_regular = np.interp(reg_seconds, tide_seconds_arr, tide_heights)

    # Normalize both
    sd_norm = (sd_regular - np.mean(sd_regular)) / (np.std(sd_regular) + 1e-10)
    tide_norm = (tide_regular - np.mean(tide_regular)) / (np.std(tide_regular) + 1e-10)

    # Cross-correlation
    corr_full = np.correlate(sd_norm, tide_norm, mode='full')
    corr_full = corr_full / len(sd_norm)
    lags_all = np.arange(-len(sd_norm) + 1, len(sd_norm))
    lag_hours_all = lags_all * dt_minutes / 60.0

    # Restrict to ±9 hours
    window_mask = (lag_hours_all >= -9) & (lag_hours_all <= 9)
    corr_window = corr_full[window_mask]
    lag_hours_window = lag_hours_all[window_mask]

    # Forward shift peak (lag > 0)
    fwd_mask = lag_hours_window > 0
    fwd_corr = corr_window[fwd_mask]
    fwd_lags = lag_hours_window[fwd_mask]
    fwd_peak_idx = np.argmax(fwd_corr)
    fwd_peak_lag = fwd_lags[fwd_peak_idx]
    fwd_peak_val = fwd_corr[fwd_peak_idx]

    # Backward shift peak (lag < 0)
    bwd_mask = lag_hours_window < 0
    bwd_corr = corr_window[bwd_mask]
    bwd_lags = lag_hours_window[bwd_mask]
    bwd_peak_idx = np.argmax(bwd_corr)
    bwd_peak_lag = bwd_lags[bwd_peak_idx]
    bwd_peak_val = bwd_corr[bwd_peak_idx]

    # Determine best lag
    if fwd_peak_val > bwd_peak_val:
        best_lag_hours = fwd_peak_lag
        best_corr_val = fwd_peak_val
    else:
        best_lag_hours = bwd_peak_lag
        best_corr_val = bwd_peak_val

    # Plot shifted tide minus start depth
    best_shift = timedelta(hours=best_lag_hours)
    tide_times_best = [t - best_shift for t in tide_times]
    tide_seconds_best = np.array([(t - TIME_START).total_seconds() for t in tide_times_best])
    tide_shifted_at_sd = np.interp(sd_seconds, tide_seconds_best, tide_heights)
    residual = tide_shifted_at_sd - sd_vals

    ax5.plot([pd.Timestamp(t) for t in sd_times_dt], residual, '-', color='purple',
             linewidth=0.8, alpha=0.8)
    ax5.set_title(f'Shifted tidal height minus start depth (shift={best_lag_hours:+.2f} hr, r={best_corr_val:.3f})')

plt.tight_layout()

# Save
out_path = Path("~/ooi/visualizations/TidalSignal.png").expanduser()
out_path.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out_path, dpi=150, bbox_inches='tight')
plt.show()
print(f"\nSaved: {out_path}")

# Print correlation results
if r['start_depths']:
    print("\n=== Start depth vs Tidal height cross-correlation ===")
    print(f"  Forward shift peak:  lag = {fwd_peak_lag:+.2f} hours, correlation = {fwd_peak_val:.4f}")
    print(f"  Backward shift peak: lag = {bwd_peak_lag:+.2f} hours, correlation = {bwd_peak_val:.4f}")
    print()
    if fwd_peak_val > bwd_peak_val:
        print(f"  Best match: shift tidal signal FORWARD by {fwd_peak_lag:.2f} hours (r={fwd_peak_val:.4f})")
    else:
        print(f"  Best match: shift tidal signal BACKWARD by {abs(bwd_peak_lag):.2f} hours (r={bwd_peak_val:.4f})")
    print(f"  (Positive lag = tide leads start depth; negative lag = tide lags start depth)")

