# Bundle animation: Generate an mp4 of the bundle chart advancing through time.
# Run this as: %run ~/argosy/vis/bundle_animate.py
#
# Workflow:
#   1. Prompt for start date (M-YYYY) and end date (M-YYYY)
#   2. Display ipywidgets for configuration (sensors, ranges, modes, etc.)
#   3. Click "Animate" to generate ~/ooi/visualizations/bundle_animation.mp4
#
# The animation renders the chart only (no widget controls).

import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import xarray as xr
from pathlib import Path
import ipywidgets as widgets
from IPython.display import display, HTML
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
import calendar

# Make the repo root importable so `import ooipaths` works under %run.
sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op
# Choose the SP site interactively (Enter keeps the ARGOSY_SITE default).
SITE = op.select_site(announce="Bundle animation")
from zoneinfo import ZoneInfo

OREGON_TZ = ZoneInfo('America/Los_Angeles')

# == Sensor exclusions =========================================================

_EXCLUSIONS_CSV = Path("~/argosy/sensor_exclusions.csv").expanduser()
_sensor_exclusions = {}
if _EXCLUSIONS_CSV.exists():
    _exc_df = pd.read_csv(_EXCLUSIONS_CSV)
    for _, _row in _exc_df.iterrows():
        _sensor_exclusions.setdefault(_row['sensor'], []).append(
            (np.datetime64(_row['start']), np.datetime64(_row['end'])))


def _is_excluded(sensor_var, mid_time):
    """Check if a sensor measurement at mid_time falls in an exclusion window."""
    if sensor_var not in _sensor_exclusions:
        return False
    for exc_start, exc_end in _sensor_exclusions[sensor_var]:
        if exc_start <= mid_time <= exc_end:
            return True
    return False


# == Constants =================================================================

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

def source_year_dir(source, year):
    """Per-year data directory for a source choice, via ooipaths accessors.
    pp05 is virtual (reads redux + manifest filter); redux reads redux directly."""
    if source in ('redux', 'pp05'):
        return op.redux_dir(year, SITE)
    return op.postproc_dir(source, year, SITE)   # pp01, pp02, pp06

_pp05_manifest_set = set()
_pp05_manifest_path = op.pp05_manifest(SITE)
if _pp05_manifest_path.exists():
    _pp05_df = pd.read_csv(_pp05_manifest_path)
    _pp05_manifest_set = set(zip(_pp05_df['sensor'], _pp05_df['global_idx']))


# == Source and date input ======================================================

def parse_date_input(text, is_end=False):
    """Parse M-YYYY or MM-YYYY into a datetime. If is_end, returns last day of month."""
    parts = text.strip().split('-')
    if len(parts) != 2:
        return None
    try:
        month = int(parts[0])
        year = int(parts[1])
    except ValueError:
        return None
    if month < 1 or month > 12 or year < 2014 or year > 2027:
        return None
    if is_end:
        last_day = calendar.monthrange(year, month)[1]
        return datetime(year, month, last_day)
    else:
        return datetime(year, month, 1)


# 1. Source dataset
raw_source = input("Data source (redux/pp01/pp02/pp05/pp06, default pp06): ").strip().lower()
if raw_source in ('redux', 'pp01', 'pp02', 'pp05', 'pp06'):
    initial_source = raw_source
elif raw_source == '':
    initial_source = 'pp06'
else:
    print(f"ERROR: Unknown data source '{raw_source}'. "
          f"Expected one of: redux, pp01, pp02, pp05, pp06")
    raise SystemExit

# 2. Start date
raw_start = input("Start date (M-YYYY, default 1-2024): ").strip() or "1-2024"
start_date = parse_date_input(raw_start, is_end=False)
if start_date is None:
    print(f"ERROR: Cannot parse start date '{raw_start}'. Expected format: M-YYYY (e.g. 1-2024)")
    raise SystemExit

# 3. End date
raw_end = input("End date (M-YYYY, default 3-2024): ").strip() or "3-2024"
end_date = parse_date_input(raw_end, is_end=True)
if end_date is None:
    print(f"ERROR: Cannot parse end date '{raw_end}'. Expected format: M-YYYY (e.g. 3-2024)")
    raise SystemExit

if end_date <= start_date:
    print(f"ERROR: End date ({end_date.strftime('%d-%b-%Y')}) must be after "
          f"start date ({start_date.strftime('%d-%b-%Y')})")
    raise SystemExit

print(f"Source: {initial_source}")
print(f"Animation range: {start_date.strftime('%d-%b-%Y')} to {end_date.strftime('%d-%b-%Y')}")
print(f"NOTE: nProfiles means consecutive Global Index Positions (GIP). Fewer than")
print(f"  nProfiles traces may appear in a frame if positions have no data or if")
print(f"  EXCLUDE filters remove profiles.")

start_year = start_date.year
end_year = end_date.year


# == Index map =================================================================

sensor_index_map = {sensor: {} for sensor in SENSORS}
# Also store date info per global index for time filtering
_gidx_dates = {}  # gidx -> datetime


def build_index_map(source):
    """Scan shard files and build global-index-keyed lookup."""
    global sensor_index_map, _gidx_dates

    use_manifest = (source == 'pp05')
    sensor_index_map = {sensor: {} for sensor in SENSORS}
    _gidx_dates = {}

    for year in range(start_year, end_year + 1):
        redux_dir = source_year_dir(source, year)
        if not redux_dir.exists():
            continue
        for sensor in SENSORS:
            year_files = list(redux_dir.glob(f"*_{sensor}_*.nc"))
            for f in year_files:
                parts = f.stem.split('_')
                yr = int(parts[4])
                doy = int(parts[5])
                global_idx = int(parts[6])

                # Time filter
                file_date = datetime(yr, 1, 1) + timedelta(days=doy - 1)
                if file_date < start_date or file_date > end_date:
                    continue

                if use_manifest and _pp05_manifest_set:
                    if (sensor, global_idx) not in _pp05_manifest_set:
                        continue

                sensor_index_map[sensor][global_idx] = f
                _gidx_dates[global_idx] = file_date


# Initial build with pp06
print("Scanning pp06...")
build_index_map('pp06')

# Determine valid index range
all_indices = set()
for sensor in SENSORS:
    all_indices.update(sensor_index_map[sensor].keys())

if not all_indices:
    print("ERROR: No profile data found in the specified date range.")
    raise SystemExit

min_idx = min(all_indices)
max_idx = max(all_indices)
print(f"Global index range: {min_idx} to {max_idx} ({len(all_indices)} positions with data)")


# == Widget UI =================================================================

sensor_options = [(SENSORS[k]['display_name'], k) for k in SENSORS]

source_dropdown = widgets.Dropdown(
    options=['redux', 'pp01', 'pp02', 'pp05', 'pp06'],
    value='pp06', description='Source:')

sensor1_dropdown = widgets.Dropdown(
    options=sensor_options, value='temperature', description='Sensor 1:')
sensor2_dropdown = widgets.Dropdown(
    options=sensor_options, value='salinity', description='Sensor 2:')

s1 = SENSORS['temperature']
rng1 = abs(s1['high'] - s1['low'])
low1_slider = widgets.FloatSlider(
    value=s1['low'], min=s1['low'] - rng1, max=s1['high'],
    step=rng1 / 100, description='S1 low:', continuous_update=False,
    readout_format='.2f', style={'description_width': 'initial'})
high1_slider = widgets.FloatSlider(
    value=s1['high'], min=s1['low'], max=s1['high'] + rng1,
    step=rng1 / 100, description='S1 high:', continuous_update=False,
    readout_format='.2f', style={'description_width': 'initial'})

s2 = SENSORS['salinity']
rng2 = abs(s2['high'] - s2['low'])
low2_slider = widgets.FloatSlider(
    value=s2['low'], min=s2['low'] - rng2, max=s2['high'],
    step=rng2 / 100, description='S2 low:', continuous_update=False,
    readout_format='.2f', style={'description_width': 'initial'})
high2_slider = widgets.FloatSlider(
    value=s2['high'], min=s2['low'], max=s2['high'] + rng2,
    step=rng2 / 100, description='S2 high:', continuous_update=False,
    readout_format='.2f', style={'description_width': 'initial'})

mode1_toggle = widgets.ToggleButtons(
    options=['bundle', 'meanstd'], value='bundle', description='S1 mode:')
mode2_toggle = widgets.ToggleButtons(
    options=['bundle', 'meanstd'], value='bundle', description='S2 mode:')

nProfiles_slider = widgets.IntSlider(
    value=27, min=1, max=180, step=1,
    description='nProfiles:', continuous_update=False)

fps_slider = widgets.IntSlider(
    value=5, min=1, max=20, step=1,
    description='FPS:', continuous_update=False)

stride_slider = widgets.IntSlider(
    value=1, min=1, max=27, step=1,
    description='Stride:', continuous_update=False)

exclusion_toggle = widgets.ToggleButtons(
    options=['EXCLUDE', 'NO FILTER'], value='EXCLUDE',
    description='Exclusions:')

status_label = widgets.Label(value='Ready. Configure settings then click Animate.')
estimate_label = widgets.Label(value='')

# Load timing history for runtime estimation
_timing_path = op.metadata_dir(SITE, "cache") / "bundle_animation_timing.csv"
_rate_sec_per_frame = None
if _timing_path.exists():
    try:
        _timing_df = pd.read_csv(_timing_path)
        if len(_timing_df) > 0:
            _rate_sec_per_frame = _timing_df['sec_per_frame'].median()
    except Exception:
        pass


def _update_estimate(*args):
    """Update the estimated runtime display."""
    if _rate_sec_per_frame is None:
        estimate_label.value = '(Run once to calibrate time estimate)'
        return
    n_prof = nProfiles_slider.value
    stride_val = stride_slider.value
    n_frames_est = max(0, (max_idx - min_idx - n_prof + 1) // stride_val + 1)
    est_sec = n_frames_est * _rate_sec_per_frame
    if est_sec < 60:
        estimate_label.value = f'Est: {n_frames_est} frames × {_rate_sec_per_frame:.2f} s/frame ≈ {est_sec:.0f}s'
    else:
        estimate_label.value = f'Est: {n_frames_est} frames × {_rate_sec_per_frame:.2f} s/frame ≈ {est_sec/60:.1f} min'


nProfiles_slider.observe(lambda c: _update_estimate(), names='value')
stride_slider.observe(lambda c: _update_estimate(), names='value')
_update_estimate()

animate_btn = widgets.Button(
    description='Animate', button_style='success',
    layout=widgets.Layout(width='120px', height='36px'))


# -- Sensor change callbacks (widen-first pattern) -----------------------------

_sensor1_ranges = {}
_sensor2_ranges = {}


def update_sensor1_sliders(change):
    old_sensor = change['old']
    if old_sensor is not None:
        _sensor1_ranges[old_sensor] = (low1_slider.value, high1_slider.value)
    sensor = change['new']
    s = SENSORS[sensor]
    rng = abs(s['high'] - s['low'])
    if sensor in _sensor1_ranges:
        lo, hi = _sensor1_ranges[sensor]
    else:
        lo, hi = s['low'], s['high']
    low1_slider.min = -1e6
    low1_slider.max = 1e6
    high1_slider.min = -1e6
    high1_slider.max = 1e6
    low1_slider.value = lo
    high1_slider.value = hi
    low1_slider.min = s['low'] - rng
    low1_slider.max = s['high']
    low1_slider.step = rng / 100 if rng > 0 else 0.01
    high1_slider.min = s['low']
    high1_slider.max = s['high'] + rng
    high1_slider.step = rng / 100 if rng > 0 else 0.01


def update_sensor2_sliders(change):
    old_sensor = change['old']
    if old_sensor is not None:
        _sensor2_ranges[old_sensor] = (low2_slider.value, high2_slider.value)
    sensor = change['new']
    s = SENSORS[sensor]
    rng = abs(s['high'] - s['low'])
    if sensor in _sensor2_ranges:
        lo, hi = _sensor2_ranges[sensor]
    else:
        lo, hi = s['low'], s['high']
    low2_slider.min = -1e6
    low2_slider.max = 1e6
    high2_slider.min = -1e6
    high2_slider.max = 1e6
    low2_slider.value = lo
    high2_slider.value = hi
    low2_slider.min = s['low'] - rng
    low2_slider.max = s['high']
    low2_slider.step = rng / 100 if rng > 0 else 0.01
    high2_slider.min = s['low']
    high2_slider.max = s['high'] + rng
    high2_slider.step = rng / 100 if rng > 0 else 0.01


sensor1_dropdown.observe(update_sensor1_sliders, names='value')
sensor2_dropdown.observe(update_sensor2_sliders, names='value')


# -- Source change callback ----------------------------------------------------

def on_source_change(change):
    global min_idx, max_idx, all_indices
    new_source = change['new']
    status_label.value = f'Loading {new_source}...'
    build_index_map(new_source)
    all_indices = set()
    for sensor in SENSORS:
        all_indices.update(sensor_index_map[sensor].keys())
    if all_indices:
        min_idx = min(all_indices)
        max_idx = max(all_indices)
    status_label.value = f'{new_source} loaded ({len(all_indices)} positions)'


source_dropdown.observe(on_source_change, names='value')


# == Animation generation ======================================================

# Progress bar widget
progress_bar = widgets.IntProgress(
    value=0, min=0, max=100, description='Progress:',
    bar_style='info', layout=widgets.Layout(width='400px', visibility='hidden'))


def generate_animation(b):
    """Build the mp4 animation with profile caching for speed."""
    import time as _time
    global min_idx, max_idx

    # Disable button during render
    animate_btn.disabled = True
    animate_btn.button_style = ''
    progress_bar.layout.visibility = 'visible'
    progress_bar.value = 0

    sensor1 = sensor1_dropdown.value
    sensor2 = sensor2_dropdown.value
    low1 = low1_slider.value
    high1 = high1_slider.value
    low2 = low2_slider.value
    high2 = high2_slider.value
    mode1 = mode1_toggle.value
    mode2 = mode2_toggle.value
    n_profiles = nProfiles_slider.value
    fps = fps_slider.value
    stride = stride_slider.value
    apply_exclusions = (exclusion_toggle.value == 'EXCLUDE')

    # Build frame list: each frame starts at a different index0
    frame_starts = list(range(min_idx, max_idx - n_profiles + 2, stride))
    n_frames = len(frame_starts)

    if n_frames == 0:
        status_label.value = 'ERROR: No frames to generate (index range too small for nProfiles).'
        animate_btn.disabled = False
        animate_btn.button_style = 'success'
        progress_bar.layout.visibility = 'hidden'
        return

    output_path = op.visualizations_dir(SITE) / "bundle_animation.mp4"
    status_label.value = (
        f'Generating {n_frames} frames at {fps} fps → {output_path}')
    progress_bar.max = n_frames

    t_start = _time.time()
    depth_grid = np.linspace(0, 200, 200)

    # == Profile cache (avoids redundant disk reads between frames) ==
    # Stores: {(sensor, gidx): (data_clean, depth_clean, stem_parts) | None}
    _cache = {}
    sensors_to_load = list(set([sensor1, sensor2]))

    def _load(sensor, gidx):
        key = (sensor, gidx)
        if key in _cache:
            return _cache[key]
        filepath = sensor_index_map[sensor].get(gidx)
        if filepath is None:
            _cache[key] = None
            return None
        try:
            ds = xr.open_dataset(filepath)
            if apply_exclusions:
                t = ds.time.values
                if len(t) > 0:
                    mid_t = t[len(t) // 2]
                    if _is_excluded(sensor, mid_t):
                        ds.close()
                        _cache[key] = None
                        return None
            sensor_data = ds[sensor].values
            depth = ds['depth'].values
            valid_mask = ~(np.isnan(sensor_data) | np.isnan(depth))
            if not np.any(valid_mask):
                ds.close()
                _cache[key] = None
                return None
            result = (sensor_data[valid_mask], depth[valid_mask],
                      filepath.stem.split('_'))
            ds.close()
            _cache[key] = result
            return result
        except Exception:
            _cache[key] = None
            return None

    # Warm cache for first window
    for gidx in range(frame_starts[0], frame_starts[0] + n_profiles):
        for sensor in sensors_to_load:
            _load(sensor, gidx)

    # == Render frames ==
    fig, ax1 = plt.subplots(figsize=(10.2, 6.8))
    ax2 = ax1.twiny()

    def render_frame(frame_idx):
        ax1.clear()
        ax2.clear()

        index0 = frame_starts[frame_idx]
        gidx_end = index0 + n_profiles

        # Ensure new indices entering this window are cached
        for gidx in range(index0, gidx_end):
            for sensor in sensors_to_load:
                _load(sensor, gidx)

        sensor_configs = [
            {'name': sensor1, 'low': low1, 'high': high1,
             'units': SENSORS[sensor1]['units'],
             'color': SENSORS[sensor1]['color'], 'mode': mode1, 'ax': ax1},
            {'name': sensor2, 'low': low2, 'high': high2,
             'units': SENSORS[sensor2]['units'],
             'color': 'black' if sensor1 == sensor2 else SENSORS[sensor2]['color'],
             'mode': mode2, 'ax': ax2},
        ]

        has_time_gap = False
        prev_date = None
        first_title_info = None
        last_title_info = None
        meanstd_data_list = [[], []]

        for gidx in range(index0, gidx_end):
            for cfg_idx, config in enumerate(sensor_configs):
                sensor = config['name']
                ax = config['ax']
                result = _cache.get((sensor, gidx))
                if result is None:
                    continue

                data_clean, depth_clean, parts = result

                if config['mode'] == 'bundle':
                    ax.plot(data_clean, depth_clean, '-',
                            color=config['color'], alpha=0.6, linewidth=1)
                else:
                    if len(depth_clean) > 1:
                        sort_idx = np.argsort(depth_clean)
                        interp_data = np.interp(
                            depth_grid, depth_clean[sort_idx],
                            data_clean[sort_idx], left=np.nan, right=np.nan)
                        if np.any(~np.isnan(interp_data)):
                            meanstd_data_list[cfg_idx].append(interp_data)

                if sensor == sensor1:
                    yr = int(parts[4])
                    doy = int(parts[5])
                    daily_idx = int(parts[7])
                    if first_title_info is None:
                        first_title_info = (yr, doy, daily_idx, gidx)
                    last_title_info = (yr, doy, daily_idx, gidx)
                    date_cur = datetime(yr, 1, 1) + timedelta(days=doy - 1)
                    if prev_date is not None and (date_cur - prev_date).days > 2:
                        has_time_gap = True
                    prev_date = date_cur

        # Draw mean/std envelopes
        for idx, config in enumerate(sensor_configs):
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

        color1 = 'black' if mode1 == 'meanstd' else SENSORS[sensor1]['color']
        if mode2 == 'meanstd':
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

        if has_time_gap:
            ax1.text(0.95, -0.08, '(time gap)', transform=ax1.transAxes,
                     fontsize=10, ha='right', va='top')

        if first_title_info and last_title_info:
            yr1, doy1, di1, gi1 = first_title_info
            yr2, doy2, di2, gi2 = last_title_info
            date1 = datetime(yr1, 1, 1) + timedelta(days=doy1 - 1)
            date2 = datetime(yr2, 1, 1) + timedelta(days=doy2 - 1)
            fig.suptitle(
                f'{date1.strftime("%d-%b-%Y")} to {date2.strftime("%d-%b-%Y")} '
                f'(GPI {index0}–{gidx_end - 1})',
                fontsize=13)
        else:
            fig.suptitle(f'No data: GPI {index0}–{gidx_end - 1}', fontsize=13)

        # Update progress bar
        progress_bar.value = frame_idx + 1

    # Generate and save animation
    anim = FuncAnimation(fig, render_frame, frames=n_frames,
                         interval=1000 // fps, repeat=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    anim.save(str(output_path), writer='ffmpeg', fps=fps, dpi=120)
    plt.close(fig)

    # Free cache memory
    _cache.clear()

    t_elapsed = _time.time() - t_start
    file_size = output_path.stat().st_size / (1024 * 1024)
    duration = n_frames / fps
    sec_per_frame = t_elapsed / n_frames if n_frames > 0 else 0

    # Write timing data for future prediction
    timing_path = op.metadata_dir(SITE, "cache") / "bundle_animation_timing.csv"
    timing_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not timing_path.exists()
    with open(timing_path, 'a') as tf:
        if write_header:
            tf.write("timestamp,n_frames,n_profiles,stride,elapsed_sec,sec_per_frame\n")
        tf.write(f"{datetime.now().isoformat()},{n_frames},{n_profiles},"
                 f"{stride},{t_elapsed:.1f},{sec_per_frame:.3f}\n")

    status_label.value = (
        f'Done: {output_path} ({file_size:.1f} MB, '
        f'{n_frames} frames, {duration:.1f}s playback at {fps} fps). '
        f'Render time: {t_elapsed:.0f}s ({sec_per_frame:.2f} s/frame).')

    # Re-enable button
    animate_btn.disabled = False
    animate_btn.button_style = 'success'


animate_btn.on_click(generate_animation)


# == Layout ====================================================================

controls = widgets.VBox([
    widgets.HBox([source_dropdown, exclusion_toggle]),
    widgets.HBox([sensor1_dropdown, sensor2_dropdown]),
    widgets.HBox([low1_slider, high1_slider, mode1_toggle]),
    widgets.HBox([low2_slider, high2_slider, mode2_toggle]),
    widgets.HBox([nProfiles_slider, fps_slider, stride_slider]),
    widgets.HBox([animate_btn, status_label]),
    widgets.HBox([progress_bar, estimate_label]),
])

display(controls)
