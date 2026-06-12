# _bundle_chart.py
# Bundle chart visualization — standalone development file.
# Once validated, this becomes the bundle plot cell in Visualizations.ipynb.
# Temporary file (per convention: _ prefix). Delete after injection into notebook.
#
# Design:
#   - Navigation is by GLOBAL PROFILE INDEX (from profileIndices metadata).
#   - index0 slider spans the full global index range for the selected year range.
#   - Both sensors look up files by global index. If no file exists for a given
#     index, nothing is drawn for that sensor at that index.
#   - Sensors are always co-temporal: same global index = same time.
#   - Data source is selectable via dropdown (redux, pp01, pp02, pp05, pp06).
#     pp05 uses a manifest filter; all others read files directly.

import matplotlib.pyplot as plt
import xarray as xr
from pathlib import Path
import ipywidgets as widgets
from IPython.display import display, clear_output
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
from zoneinfo import ZoneInfo


# == Utility ===================================================================

def get_input_with_default(prompt, default):
    """Get user input with default value."""
    response = input(f"{prompt} ").strip()
    return response if response else str(default)


# == Sensor exclusions =========================================================

_EXCLUSIONS_CSV = Path("~/argosy/sensor_exclusions.csv").expanduser()
_sensor_exclusions = {}
if _EXCLUSIONS_CSV.exists():
    _exc_df = pd.read_csv(_EXCLUSIONS_CSV)
    for _, _row in _exc_df.iterrows():
        _sensor_exclusions.setdefault(_row['sensor'], []).append(
            (np.datetime64(_row['start']), np.datetime64(_row['end'])))
exclusion_filter_enabled = False


def _is_excluded(sensor_var, mid_time):
    """Check if a sensor measurement at mid_time falls in an exclusion window."""
    if not exclusion_filter_enabled:
        return False
    if sensor_var not in _sensor_exclusions:
        return False
    for exc_start, exc_end in _sensor_exclusions[sensor_var]:
        if exc_start <= mid_time <= exc_end:
            return True
    return False


# == Constants =================================================================

OREGON_TZ = ZoneInfo('America/Los_Angeles')

# display_name: used for axis labels (preserves intended capitalization)
SENSORS = {
    'temperature':     {'low': 7.0,    'high': 20.0,   'units': '°C',                   'color': 'red',       'display_name': 'Temperature'},
    'salinity':        {'low': 32.0,   'high': 34.0,   'units': 'PSU',                  'color': 'blue',      'display_name': 'Salinity'},
    'density':         {'low': 1024.0, 'high': 1028.0, 'units': 'kg/m³',                'color': 'black',     'display_name': 'Density'},
    'dissolvedoxygen': {'low': 50.0,   'high': 300.0,  'units': 'µmol/kg',              'color': 'darkblue',  'display_name': 'Dissolved Oxygen'},
    'cdom':            {'low': 0.0,    'high': 20.0,   'units': 'ppb',                  'color': 'darkcyan',  'display_name': 'CDOM'},
    'chlora':          {'low': 0.0,    'high': 20.0,   'units': 'µg/L',                 'color': 'green',     'display_name': 'ChlorA'},
    'backscatter':     {'low': 0.0,    'high': 0.01,   'units': 'm⁻¹sr⁻¹',             'color': 'gray',      'display_name': 'Backscatter'},
    'ph':              {'low': 7.6,    'high': 8.2,    'units': '',                     'color': 'purple',    'display_name': 'pH'},
    'pco2':            {'low': 200.0,  'high': 1200.0, 'units': 'µatm',                 'color': 'orange',    'display_name': 'pCO2'},
    'nitrate':         {'low': 0.0,    'high': 35.0,   'units': 'µmol/L',               'color': 'darkgreen', 'display_name': 'Nitrate'},
    'par':             {'low': 0.0,    'high': 300.0,  'units': 'µmol photons m⁻²s⁻¹',  'color': 'gold',     'display_name': 'PAR'},
}

# Data source paths
SOURCE_PATHS = {
    'redux': Path("~/ooi/redux").expanduser(),
    'pp01':  Path("~/ooi/postproc/pp01/redux").expanduser(),
    'pp02':  Path("~/ooi/postproc/pp02/redux").expanduser(),
    'pp05':  Path("~/ooi/redux").expanduser(),          # virtual — uses manifest
    'pp06':  Path("~/ooi/postproc/pp06").expanduser(),  # physical copy
}

# pp05 manifest (loaded once, indexed as a set for O(1) lookup)
_pp05_manifest = None
_pp05_manifest_set = set()
_pp05_manifest_path = Path("~/ooi/metadata/pp05_manifest.csv").expanduser()
if _pp05_manifest_path.exists():
    _pp05_manifest = pd.read_csv(_pp05_manifest_path)
    _pp05_manifest_set = set(zip(_pp05_manifest['sensor'], _pp05_manifest['global_idx']))


# == Data scanning =============================================================

# Global state: the index map and range
sensor_index_map = {sensor: {} for sensor in SENSORS}
min_global_idx = 1
max_global_idx = 1


def build_index_map(source, start_year, end_year):
    """Scan shard files and build global-index-keyed lookup."""
    global sensor_index_map, min_global_idx, max_global_idx

    data_base = SOURCE_PATHS[source]
    use_manifest = (source == 'pp05')

    sensor_index_map = {sensor: {} for sensor in SENSORS}

    for year in range(start_year, end_year + 1):
        redux_dir = data_base / f"redux{year}"
        if not redux_dir.exists():
            continue
        for sensor in SENSORS:
            year_files = list(redux_dir.glob(f"*_{sensor}_*.nc"))
            for f in year_files:
                parts = f.stem.split('_')
                global_idx = int(parts[6])
                if use_manifest and _pp05_manifest_set:
                    if (sensor, global_idx) not in _pp05_manifest_set:
                        continue
                sensor_index_map[sensor][global_idx] = f

    all_global_indices = set()
    for sensor in SENSORS:
        all_global_indices.update(sensor_index_map[sensor].keys())

    if all_global_indices:
        min_global_idx = min(all_global_indices)
        max_global_idx = max(all_global_indices)
    else:
        min_global_idx = 1
        max_global_idx = 1


# == Initial setup: get year range from user ===================================

start_year = int(get_input_with_default("Start year (default 2020):", "2020"))
end_year = int(get_input_with_default(f"End year (default {start_year}):", str(start_year)))

# Initial scan with default source (pp06)
print(f"\nScanning pp06 from {start_year} to {end_year}...")
build_index_map('pp06', start_year, end_year)

# Report
first_file = None
for sensor in SENSORS:
    if min_global_idx in sensor_index_map[sensor]:
        first_file = sensor_index_map[sensor][min_global_idx]
        break
if first_file:
    _parts = first_file.stem.split('_')
    print(f"First potential profile is year {int(_parts[4])} Julian day {int(_parts[5])}")
print(f"Global index range: {min_global_idx} to {max_global_idx}")
for sensor in SENSORS:
    count = len(sensor_index_map[sensor])
    if count > 0:
        print(f"  {sensor}: {count} profiles")


# == Plotting ==================================================================

def check_noon_midnight(ds):
    """Check if profile spans local noon or midnight."""
    try:
        times = ds.time.values
        start_time = pd.to_datetime(times[0])
        end_time = pd.to_datetime(times[-1])
        peak_time = pd.to_datetime(times[len(times) // 2])

        start_local = start_time.tz_localize('UTC').astimezone(OREGON_TZ)
        end_local = end_time.tz_localize('UTC').astimezone(OREGON_TZ)
        peak_local = peak_time.tz_localize('UTC').astimezone(OREGON_TZ)

        window_start = start_local - timedelta(minutes=30)
        window_end = end_local + timedelta(minutes=30)

        local_midnight = start_local.replace(hour=0, minute=0, second=0, microsecond=0)
        local_noon = start_local.replace(hour=12, minute=0, second=0, microsecond=0)

        if window_start <= local_midnight <= window_end:
            return 'MIDNIGHT', peak_local
        if window_start <= local_noon <= window_end:
            return 'NOON', peak_local
    except Exception as e:
        print(f"Error in check_noon_midnight: {e}")
    return None, None


def plot_bundle(sensor1, sensor2, low1, high1, mode1, low2, high2, mode2,
                nProfiles, index0):
    """Plot a bundle of consecutive profiles keyed by global index."""

    if nProfiles == 0:
        fig, ax = plt.subplots(figsize=(10.2, 6.8))
        ax.set_title('nProfiles = 0', fontsize=14)
        ax.text(0.5, 0.5, 'Select nProfiles > 0',
                ha='center', va='center', transform=ax.transAxes)
        plt.show()
        return

    # The range of global indices to plot
    gidx_start = index0
    gidx_end = index0 + nProfiles

    # Create figure: sensor 1 on bottom x-axis, sensor 2 on top x-axis
    fig, ax1 = plt.subplots(figsize=(10.2, 6.8))
    ax2 = ax1.twiny()

    sensor_configs = [
        {'name': sensor1, 'low': low1, 'high': high1,
         'units': SENSORS[sensor1]['units'],
         'color': SENSORS[sensor1]['color'], 'mode': mode1, 'ax': ax1},
        {'name': sensor2, 'low': low2, 'high': high2,
         'units': SENSORS[sensor2]['units'],
         'color': 'black' if sensor1 == sensor2 else SENSORS[sensor2]['color'],
         'mode': mode2, 'ax': ax2},
    ]

    # Track whether we found any data and check for time gaps
    has_time_gap = False
    noon_midnight_label = None
    peak_time_local = None
    prev_date = None
    first_title_info = None
    last_title_info = None

    # For mean/std mode: collect interpolated data per sensor position
    meanstd_data_list = [[], []]  # index 0 = sensor1, index 1 = sensor2
    depth_grid = np.linspace(0, 200, 200)

    for gidx in range(gidx_start, gidx_end):
        for cfg_idx, config in enumerate(sensor_configs):
            sensor = config['name']
            ax = config['ax']
            filepath = sensor_index_map[sensor].get(gidx)

            if filepath is None:
                continue

            try:
                ds = xr.open_dataset(filepath)

                # Exclusion filter check
                if exclusion_filter_enabled:
                    t = ds.time.values
                    if len(t) > 0:
                        mid_t = t[len(t) // 2]
                        if _is_excluded(sensor, mid_t):
                            ds.close()
                            continue

                sensor_data = ds[sensor].values
                depth = ds['depth'].values

                valid_mask = ~(np.isnan(sensor_data) | np.isnan(depth))
                if not np.any(valid_mask):
                    ds.close()
                    continue

                data_clean = sensor_data[valid_mask]
                depth_clean = depth[valid_mask]

                if config['mode'] == 'bundle':
                    ax.plot(data_clean, depth_clean, '-',
                            color=config['color'], alpha=0.6, linewidth=1)
                else:
                    # mean/std mode: interpolate to common grid
                    if len(depth_clean) > 1:
                        sort_idx = np.argsort(depth_clean)
                        interp_data = np.interp(
                            depth_grid, depth_clean[sort_idx],
                            data_clean[sort_idx], left=np.nan, right=np.nan)
                        if np.any(~np.isnan(interp_data)):
                            meanstd_data_list[cfg_idx].append(interp_data)

                # Title info and time gap detection (sensor1 only)
                if sensor == sensor1:
                    parts = filepath.stem.split('_')
                    yr = int(parts[4])
                    doy = int(parts[5])
                    daily_idx = int(parts[7])

                    if first_title_info is None:
                        first_title_info = (yr, doy, daily_idx, gidx)
                    last_title_info = (yr, doy, daily_idx, gidx)

                    date_cur = datetime(yr, 1, 1) + timedelta(days=doy - 1)
                    if prev_date is not None:
                        if (date_cur - prev_date).days > 2:
                            has_time_gap = True
                    prev_date = date_cur

                # Noon/midnight check for single-profile view
                if nProfiles == 1 and sensor == sensor1:
                    noon_midnight_label, peak_time_local = check_noon_midnight(ds)

                ds.close()
            except Exception:
                continue

    # Draw mean/std envelopes
    for idx, config in enumerate(sensor_configs):
        sensor = config['name']
        ax = config['ax']
        mcolor = 'black' if idx == 0 else 'darkred'
        if config['mode'] == 'meanstd' and len(meanstd_data_list[idx]) >= 1:
            data_array = np.array(meanstd_data_list[idx])
            if len(data_array) >= 2:
                valid_counts = np.sum(~np.isnan(data_array), axis=0)
                mask = valid_counts >= 2
                mean = np.full(len(depth_grid), np.nan)
                std = np.full(len(depth_grid), np.nan)
                mean[mask] = np.nanmean(data_array[:, mask], axis=0)
                std[mask] = np.nanstd(data_array[:, mask], axis=0)
                valid = ~np.isnan(mean)
                if np.any(valid):
                    ax.plot(mean[valid], depth_grid[valid], '-',
                            color=mcolor, linewidth=3)
                    ax.plot((mean + std)[valid], depth_grid[valid], '-',
                            color=mcolor, linewidth=1, alpha=0.7)
                    ax.plot((mean - std)[valid], depth_grid[valid], '-',
                            color=mcolor, linewidth=1, alpha=0.7)
            elif len(data_array) == 1:
                mean = data_array[0]
                valid = ~np.isnan(mean)
                if np.any(valid):
                    ax.plot(mean[valid], depth_grid[valid], '-',
                            color=mcolor, linewidth=3)

    # Configure axes
    disp1 = SENSORS[sensor1]['display_name']
    disp2 = SENSORS[sensor2]['display_name']

    if sensor_configs[0]['mode'] == 'meanstd':
        color1 = 'black'
    else:
        color1 = SENSORS[sensor1]['color']

    if sensor_configs[1]['mode'] == 'meanstd':
        color2 = 'darkred'
    elif sensor1 == sensor2:
        color2 = 'black'
    else:
        color2 = SENSORS[sensor2]['color']

    ax1.set_xlabel(f'{disp1} ({SENSORS[sensor1]["units"]})',
                   fontsize=12, color=color1)
    ax1.set_xlim(low1, high1)
    ax1.tick_params(axis='x', labelcolor=color1)

    ax2.set_xlabel(f'{disp2} ({SENSORS[sensor2]["units"]})',
                   fontsize=12, color=color2)
    ax2.set_xlim(low2, high2)
    ax2.tick_params(axis='x', labelcolor=color2)
    ax2.xaxis.set_label_position('top')

    ax1.set_ylabel('Depth (m)', fontsize=12)
    ax1.set_ylim(200, 0)
    ax1.grid(True, alpha=0.3)

    # Time Gap warning
    if has_time_gap:
        ax1.text(0.95, -0.08, '(time gap)', transform=ax1.transAxes,
                 fontsize=10, ha='right', va='top')

    # NOON/MIDNIGHT label
    if noon_midnight_label:
        label_text = f"{noon_midnight_label}\n{peak_time_local.strftime('%H:%M:%S')}"
        ax1.text(0.95, 0.15, label_text, transform=ax1.transAxes,
                 fontsize=20, fontweight='bold', ha='right', va='bottom')

    # Title
    if first_title_info and last_title_info:
        yr1, doy1, di1, gi1 = first_title_info
        yr2, doy2, di2, gi2 = last_title_info
        if nProfiles == 1:
            fig.suptitle(
                f'{yr1}-{doy1:03d}-{di1} (Global index {gi1})',
                fontsize=14)
        else:
            fig.suptitle(
                f'{yr1}-{doy1:03d}-{di1} through {yr2}-{doy2:03d}-{di2} '
                f'(Global indices {gidx_start} - {gidx_end - 1})',
                fontsize=14)
    else:
        fig.suptitle(
            f'No data: global indices {gidx_start} - {gidx_end - 1}',
            fontsize=14)

    plt.tight_layout()
    plt.show()


# == Widget setup ==============================================================

sensor_options = [(SENSORS[k]['display_name'], k) for k in SENSORS]

sensor1_dropdown = widgets.Dropdown(
    options=sensor_options, value='temperature', description='Sensor 1:')
sensor2_dropdown = widgets.Dropdown(
    options=sensor_options, value='salinity', description='Sensor 2:')

# --- Data source dropdown and reload button -----------------------------------

source_dropdown = widgets.Dropdown(
    options=['redux', 'pp01', 'pp02', 'pp05', 'pp06'],
    value='pp06',
    description='Source:')

source_status = widgets.Label(value=f'pp06 loaded ({max_global_idx - min_global_idx + 1} positions)')

def on_source_change(change):
    """Rebuild the index map when source changes."""
    global min_global_idx, max_global_idx
    new_source = change['new']
    source_status.value = f'Loading {new_source}...'

    build_index_map(new_source, start_year, end_year)

    # Update index0 slider range
    index0_slider.min = min_global_idx
    index0_slider.max = max_global_idx
    index0_slider.value = min_global_idx

    # Report
    total_profiles = sum(len(v) for v in sensor_index_map.values())
    positions = max_global_idx - min_global_idx + 1
    source_status.value = f'{new_source} loaded ({positions} positions, {total_profiles} files)'

source_dropdown.observe(on_source_change, names='value')

# --- Slider creation ----------------------------------------------------------

def _safe_slider(value, lo, hi, rng, label):
    """Create a FloatSlider with range safely encompassing the value."""
    return widgets.FloatSlider(
        value=value,
        min=lo,
        max=hi,
        step=rng / 100 if rng > 0 else 0.01,
        description=label,
        continuous_update=False,
        readout_format='.3f',
        style={'description_width': 'initial'})

s1 = SENSORS['temperature']
rng1 = abs(s1['high'] - s1['low'])
low1_slider = _safe_slider(s1['low'], s1['low'] - rng1, s1['high'], rng1, 'Sensor 1 low:')
high1_slider = _safe_slider(s1['high'], s1['low'], s1['high'] + rng1, rng1, 'Sensor 1 high:')

s2 = SENSORS['salinity']
rng2 = abs(s2['high'] - s2['low'])
low2_slider = _safe_slider(s2['low'], s2['low'] - rng2, s2['high'], rng2, 'Sensor 2 low:')
high2_slider = _safe_slider(s2['high'], s2['low'], s2['high'] + rng2, rng2, 'Sensor 2 high:')

mode1_toggle = widgets.ToggleButtons(
    options=['bundle', 'meanstd'], value='bundle',
    description='Sensor 1 mode:')
mode2_toggle = widgets.ToggleButtons(
    options=['bundle', 'meanstd'], value='bundle',
    description='Sensor 2 mode:')

# Profile navigation
nProfiles_slider = widgets.IntSlider(
    value=1, min=0, max=180, step=1,
    description='nProfiles:', continuous_update=False)
index0_slider = widgets.IntSlider(
    value=min_global_idx, min=min_global_idx, max=max_global_idx, step=1,
    description='index0:', continuous_update=False,
    style={'description_width': 'initial'})

# --- Sensor change callbacks --------------------------------------------------

def update_sensor1_sliders(change):
    sensor = change['new']
    s = SENSORS[sensor]
    rng = abs(s['high'] - s['low'])
    low1_slider.min = -1e6
    low1_slider.max = 1e6
    high1_slider.min = -1e6
    high1_slider.max = 1e6
    low1_slider.value = s['low']
    high1_slider.value = s['high']
    low1_slider.min = s['low'] - rng
    low1_slider.max = s['high']
    low1_slider.step = rng / 100 if rng > 0 else 0.01
    high1_slider.min = s['low']
    high1_slider.max = s['high'] + rng
    high1_slider.step = rng / 100 if rng > 0 else 0.01

def update_sensor2_sliders(change):
    sensor = change['new']
    s = SENSORS[sensor]
    rng = abs(s['high'] - s['low'])
    low2_slider.min = -1e6
    low2_slider.max = 1e6
    high2_slider.min = -1e6
    high2_slider.max = 1e6
    low2_slider.value = s['low']
    high2_slider.value = s['high']
    low2_slider.min = s['low'] - rng
    low2_slider.max = s['high']
    low2_slider.step = rng / 100 if rng > 0 else 0.01
    high2_slider.min = s['low']
    high2_slider.max = s['high'] + rng
    high2_slider.step = rng / 100 if rng > 0 else 0.01

sensor1_dropdown.observe(update_sensor1_sliders, names='value')
sensor2_dropdown.observe(update_sensor2_sliders, names='value')

# --- Navigation buttons -------------------------------------------------------

def make_nav_button(label, step):
    btn = widgets.Button(description=label, layout=widgets.Layout(width='40px'))
    def on_click(b):
        if label in ('--', '++'):
            delta = step * nProfiles_slider.value
        else:
            delta = step
        new_val = index0_slider.value + delta
        new_val = max(min_global_idx, min(max_global_idx, new_val))
        index0_slider.value = new_val
    btn.on_click(on_click)
    return btn

btn_prev_big = make_nav_button('--', -1)
btn_prev = make_nav_button('-', -1)
btn_next = make_nav_button('+', 1)
btn_next_big = make_nav_button('++', 1)

# --- Exclusion toggle ---------------------------------------------------------

exclusion_btn = widgets.Button(description='Exclusions: INACTIVE')

def toggle_exclusions(b):
    global exclusion_filter_enabled
    exclusion_filter_enabled = not exclusion_filter_enabled
    exclusion_btn.description = (
        'Exclusions: ACTIVE' if exclusion_filter_enabled else 'Exclusions: INACTIVE')

exclusion_btn.on_click(toggle_exclusions)

# --- Interactive output -------------------------------------------------------

out = widgets.interactive_output(plot_bundle, {
    'sensor1': sensor1_dropdown,
    'sensor2': sensor2_dropdown,
    'low1': low1_slider,
    'high1': high1_slider,
    'mode1': mode1_toggle,
    'low2': low2_slider,
    'high2': high2_slider,
    'mode2': mode2_toggle,
    'nProfiles': nProfiles_slider,
    'index0': index0_slider,
})

# Layout
controls = widgets.VBox([
    widgets.HBox([source_dropdown, source_status]),
    widgets.HBox([sensor1_dropdown, sensor2_dropdown]),
    widgets.HBox([low1_slider, high1_slider, mode1_toggle]),
    widgets.HBox([low2_slider, high2_slider, mode2_toggle]),
    widgets.HBox([nProfiles_slider, index0_slider,
                  btn_prev_big, btn_prev, btn_next, btn_next_big,
                  exclusion_btn]),
])

display(controls, out)
