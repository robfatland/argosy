# cline_extract.py — Extract cline (pycnocline, thermocline, halocline, oxycline)
# depths and strengths from pp06 profiles.
#
# Run: python ~/argosy/iw/cline_extract.py
#   or: %run ~/argosy/iw/cline_extract.py
#
# Output: ~/ooi/metadata/cline_extract_slopebase.csv
#
# See InternalWaves.md → "Cline Extraction" for full documentation.

import numpy as np
import xarray as xr
import pandas as pd
import gsw
from pathlib import Path
from scipy.signal import savgol_filter, find_peaks

# == Configuration =============================================================

PP06_BASE = Path("~/ooi/postproc/pp06").expanduser()
OUTPUT_DIR = Path("~/ooi/metadata").expanduser()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
EXCLUSIONS_CSV = Path("~/argosy/sensor_exclusions.csv").expanduser()

SITE_NAME = "slopebase"
SITE_LAT = 44.53
SITE_LON = -125.39

START_YEAR = 2015
END_YEAR = 2025

# Smoothing parameters
SAVGOL_WINDOW = 11   # ~3 m at 0.3 m/sample
SAVGOL_ORDER = 2

# MLD criterion
MLD_DELTA_SIGMA = 0.03  # kg/m3 from 5m reference
MLD_REF_DEPTH = 5.0     # meters

# Minimum points required for a valid profile
MIN_POINTS = 50

# Minimum gradient peak prominence (relative to profile range)
MIN_PROMINENCE_FRAC = 0.05


# == Sensor exclusions =========================================================

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


# == Build GPI index ===========================================================

print(f"Scanning pp06 for {SITE_NAME} ({START_YEAR}–{END_YEAR})...")

# Index: {gpi: {sensor: filepath}}
gpi_index = {}
SENSORS_NEEDED = ['temperature', 'salinity', 'dissolvedoxygen']

for year in range(START_YEAR, END_YEAR + 1):
    redux_dir = PP06_BASE / f"redux{year}"
    if not redux_dir.exists():
        continue
    for sensor in SENSORS_NEEDED:
        for f in redux_dir.glob(f"*_{sensor}_*.nc"):
            parts = f.stem.split('_')
            gpi = int(parts[6])
            if gpi not in gpi_index:
                gpi_index[gpi] = {}
            gpi_index[gpi][sensor] = f

all_gpis = sorted(gpi_index.keys())
print(f"  Found {len(all_gpis)} unique GPIs")


# == Helper functions ==========================================================

def load_profile(filepath, var_name):
    """Load a single profile, return (depth, values, mid_time) sorted by depth."""
    ds = xr.open_dataset(filepath)
    vals = ds[var_name].values
    depth = np.abs(ds['depth'].values)
    times = ds['time'].values
    ds.close()

    valid = ~(np.isnan(vals) | np.isnan(depth))
    if valid.sum() < MIN_POINTS:
        return None, None, None

    d = depth[valid]
    v = vals[valid]
    t = times[valid]

    sort_idx = np.argsort(d)
    mid_time = t[len(t) // 2]
    return d[sort_idx], v[sort_idx], mid_time


def compute_gradient(depth, values):
    """Compute dv/dz on smoothed data. Returns (depth_centers, gradient)."""
    if len(values) < SAVGOL_WINDOW:
        return None, None

    smoothed = savgol_filter(values, SAVGOL_WINDOW, SAVGOL_ORDER)
    dv = np.diff(smoothed)
    dz = np.diff(depth)

    # Avoid division by zero
    dz[dz == 0] = 0.001
    gradient = dv / dz
    centers = 0.5 * (depth[:-1] + depth[1:])

    return centers, gradient


def find_primary_cline(depth_centers, gradient, min_prominence=None):
    """Find depth and strength of the strongest gradient peak.
    Returns (depth, strength) or (NaN, NaN).
    """
    if depth_centers is None or len(gradient) < 5:
        return np.nan, np.nan

    abs_grad = np.abs(gradient)

    # Determine prominence threshold
    if min_prominence is None:
        grad_range = np.nanmax(abs_grad) - np.nanmin(abs_grad)
        min_prominence = grad_range * MIN_PROMINENCE_FRAC

    peaks, properties = find_peaks(abs_grad, prominence=min_prominence)

    if len(peaks) == 0:
        # Fallback: just use the maximum
        idx = np.nanargmax(abs_grad)
        return depth_centers[idx], abs_grad[idx]

    # Strongest peak
    strongest = peaks[np.argmax(properties['prominences'])]
    return depth_centers[strongest], abs_grad[strongest]


def find_secondary_cline(depth_centers, gradient, primary_depth, min_prominence=None):
    """Find the second-strongest gradient peak, excluding the primary.
    Returns (depth, strength) or (NaN, NaN).
    """
    if depth_centers is None or len(gradient) < 5:
        return np.nan, np.nan

    abs_grad = np.abs(gradient)

    if min_prominence is None:
        grad_range = np.nanmax(abs_grad) - np.nanmin(abs_grad)
        min_prominence = grad_range * MIN_PROMINENCE_FRAC

    peaks, properties = find_peaks(abs_grad, prominence=min_prominence)

    if len(peaks) < 2:
        return np.nan, np.nan

    # Sort by prominence, take second-strongest
    order = np.argsort(properties['prominences'])[::-1]
    for i in order[1:]:
        candidate_depth = depth_centers[peaks[i]]
        # Must be at least 15m from primary
        if abs(candidate_depth - primary_depth) > 15:
            return candidate_depth, abs_grad[peaks[i]]

    return np.nan, np.nan


def compute_mld(depth, sigma0):
    """Compute mixed layer depth using density threshold criterion.
    Reference: mean sigma0 within the shallowest 3 meters of available data.
    MLD = first depth below reference band where sigma0 exceeds reference + 0.03 kg/m3.
    """
    # Reference band: all points within 3m of the shallowest measurement
    MLD_REF_BAND = 3.0  # meters
    shallowest = depth[0]
    ref_mask = depth <= shallowest + MLD_REF_BAND

    if ref_mask.sum() == 0:
        return np.nan

    ref_sigma = np.nanmean(sigma0[ref_mask])
    ref_bottom = shallowest + MLD_REF_BAND
    threshold = ref_sigma + MLD_DELTA_SIGMA

    # Find first depth below the reference band where sigma0 exceeds threshold
    below_ref = depth > ref_bottom
    if below_ref.sum() == 0:
        return np.nan

    exceeds = (sigma0 > threshold) & below_ref
    if exceeds.sum() == 0:
        return np.nan

    return depth[exceeds][0]


def compute_cline_thickness(depth_centers, gradient, cline_depth, cline_strength):
    """Compute cline thickness using the 50% gradient threshold method with
    interpolated threshold crossings for sub-grid resolution.
    Returns the depth range (meters) over which |gradient| exceeds 50% of peak.
    Returns NaN if cline_depth is NaN or data is insufficient.
    """
    if np.isnan(cline_depth) or np.isnan(cline_strength) or depth_centers is None:
        return np.nan

    abs_grad = np.abs(gradient)
    threshold = 0.5 * cline_strength

    # Find the peak index
    peak_idx = np.argmin(np.abs(depth_centers - cline_depth))

    # Walk upward from peak to find where gradient crosses below threshold
    top_depth = depth_centers[peak_idx]
    for i in range(peak_idx, 0, -1):
        if abs_grad[i - 1] < threshold:
            # Interpolate crossing between i-1 and i
            frac = (threshold - abs_grad[i - 1]) / (abs_grad[i] - abs_grad[i - 1])
            top_depth = depth_centers[i - 1] + frac * (depth_centers[i] - depth_centers[i - 1])
            break
    else:
        top_depth = depth_centers[0]

    # Walk downward from peak to find where gradient crosses below threshold
    bot_depth = depth_centers[peak_idx]
    for i in range(peak_idx, len(abs_grad) - 1):
        if abs_grad[i + 1] < threshold:
            # Interpolate crossing between i and i+1
            frac = (threshold - abs_grad[i + 1]) / (abs_grad[i] - abs_grad[i + 1])
            bot_depth = depth_centers[i + 1] - frac * (depth_centers[i + 1] - depth_centers[i])
            break
    else:
        bot_depth = depth_centers[-1]

    thickness = bot_depth - top_depth
    return thickness if thickness > 0 else np.nan


# == Main extraction loop ======================================================

records = []
n_processed = 0
n_skipped = 0

for gpi in all_gpis:
    sensor_files = gpi_index[gpi]

    # Need at least T and S for potential density
    if 'temperature' not in sensor_files or 'salinity' not in sensor_files:
        n_skipped += 1
        continue

    # Load temperature
    d_t, t_vals, mid_time_t = load_profile(sensor_files['temperature'], 'temperature')
    if d_t is None:
        n_skipped += 1
        continue

    # Check exclusion
    if is_excluded('temperature', mid_time_t):
        n_skipped += 1
        continue

    # Load salinity
    d_s, s_vals, mid_time_s = load_profile(sensor_files['salinity'], 'salinity')
    if d_s is None:
        n_skipped += 1
        continue

    if is_excluded('salinity', mid_time_s):
        n_skipped += 1
        continue

    # Interpolate T and S to common depth grid
    d_min = max(d_t[0], d_s[0])
    d_max = min(d_t[-1], d_s[-1])
    if d_max - d_min < 50:
        n_skipped += 1
        continue

    # Regular grid at ~0.5m resolution
    n_grid = int((d_max - d_min) / 0.5)
    d_grid = np.linspace(d_min, d_max, n_grid)
    t_interp = np.interp(d_grid, d_t, t_vals)
    s_interp = np.interp(d_grid, d_s, s_vals)

    # Compute potential density (sigma-0)
    pressure = gsw.p_from_z(-d_grid, SITE_LAT)
    SA = gsw.SA_from_SP(s_interp, pressure, SITE_LON, SITE_LAT)
    CT = gsw.CT_from_t(SA, t_interp, pressure)
    sigma0 = gsw.sigma0(SA, CT)

    # Compute gradients
    d_centers_rho, grad_rho = compute_gradient(d_grid, sigma0)
    d_centers_t, grad_t = compute_gradient(d_grid, t_interp)
    d_centers_s, grad_s = compute_gradient(d_grid, s_interp)

    # Pycnocline
    pyc_depth, pyc_strength = find_primary_cline(d_centers_rho, grad_rho)

    # Secondary pycnocline
    sec_pyc_depth, sec_pyc_strength = find_secondary_cline(
        d_centers_rho, grad_rho, pyc_depth)

    # Thermocline
    therm_depth, therm_strength = find_primary_cline(d_centers_t, grad_t)

    # Halocline
    halo_depth, halo_strength = find_primary_cline(d_centers_s, grad_s)

    # N2 at pycnocline
    g = 9.81
    if not np.isnan(pyc_depth) and d_centers_rho is not None:
        idx = np.argmin(np.abs(d_centers_rho - pyc_depth))
        rho_at_pyc = 1025.0  # approximate
        n2_max = (g / rho_at_pyc) * np.abs(grad_rho[idx])
        n2_depth = d_centers_rho[idx]
    else:
        n2_max = np.nan
        n2_depth = np.nan

    # Oxycline
    oxy_depth, oxy_strength = np.nan, np.nan
    d_centers_o, grad_o = None, None
    if 'dissolvedoxygen' in sensor_files:
        d_o, o_vals, mid_time_o = load_profile(
            sensor_files['dissolvedoxygen'], 'dissolvedoxygen')
        if d_o is not None and not is_excluded('dissolvedoxygen', mid_time_o):
            o_interp = np.interp(d_grid, d_o, o_vals)
            d_centers_o, grad_o = compute_gradient(d_grid, o_interp)
            oxy_depth, oxy_strength = find_primary_cline(d_centers_o, grad_o)

    # Cline thicknesses (50% gradient threshold method)
    pyc_thickness = compute_cline_thickness(d_centers_rho, grad_rho, pyc_depth, pyc_strength)
    therm_thickness = compute_cline_thickness(d_centers_t, grad_t, therm_depth, therm_strength)
    halo_thickness = compute_cline_thickness(d_centers_s, grad_s, halo_depth, halo_strength)
    oxy_thickness = compute_cline_thickness(d_centers_o, grad_o, oxy_depth, oxy_strength)

    # MLD
    mld = compute_mld(d_grid, sigma0)

    # Timestamp
    timestamp = pd.Timestamp(mid_time_t)

    records.append({
        'site': SITE_NAME,
        'gpi': gpi,
        'timestamp': timestamp.isoformat(),
        'pycnocline_depth': round(pyc_depth, 2) if not np.isnan(pyc_depth) else np.nan,
        'pycnocline_strength': round(pyc_strength, 5) if not np.isnan(pyc_strength) else np.nan,
        'pycnocline_thickness': round(pyc_thickness, 2) if not np.isnan(pyc_thickness) else np.nan,
        'thermocline_depth': round(therm_depth, 2) if not np.isnan(therm_depth) else np.nan,
        'thermocline_strength': round(therm_strength, 4) if not np.isnan(therm_strength) else np.nan,
        'thermocline_thickness': round(therm_thickness, 2) if not np.isnan(therm_thickness) else np.nan,
        'halocline_depth': round(halo_depth, 2) if not np.isnan(halo_depth) else np.nan,
        'halocline_strength': round(halo_strength, 5) if not np.isnan(halo_strength) else np.nan,
        'halocline_thickness': round(halo_thickness, 2) if not np.isnan(halo_thickness) else np.nan,
        'oxycline_depth': round(oxy_depth, 2) if not np.isnan(oxy_depth) else np.nan,
        'oxycline_strength': round(oxy_strength, 4) if not np.isnan(oxy_strength) else np.nan,
        'oxycline_thickness': round(oxy_thickness, 2) if not np.isnan(oxy_thickness) else np.nan,
        'N2_max': round(n2_max, 7) if not np.isnan(n2_max) else np.nan,
        'N2_max_depth': round(n2_depth, 2) if not np.isnan(n2_depth) else np.nan,
        'secondary_pycnocline_depth': round(sec_pyc_depth, 2) if not np.isnan(sec_pyc_depth) else np.nan,
        'secondary_pycnocline_strength': round(sec_pyc_strength, 5) if not np.isnan(sec_pyc_strength) else np.nan,
        'mld': round(mld, 2) if not np.isnan(mld) else np.nan,
    })

    n_processed += 1
    if n_processed % 500 == 0:
        print(f"  Processed {n_processed} profiles...")


# == Save ======================================================================

df = pd.DataFrame(records)
output_path = OUTPUT_DIR / f"cline_extract_{SITE_NAME}.csv"
df.to_csv(output_path, index=False)

print(f"\nDone. {n_processed} profiles extracted, {n_skipped} skipped.")
print(f"Output: {output_path}")
print(f"Columns: {list(df.columns)}")
