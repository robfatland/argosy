# VisQCInspector.py — Interactive profile inspector for visual QC (standalone GUI).
# Run: python ~/argosy/iw/VisQCInspector.py
#
# 4 sensor traces (T, S, DO, density) on shared depth axis with independent x-axes.
# Axes auto-scale to the data range of the current profile.
# Sensor toggles turn traces on/off. Sensor selector chooses which cline to edit.
# Thermocline boundary lines adjustable per sensor cline.
#
# Uses matplotlib TkAgg backend. Requires: sudo apt install python3-tk

import numpy as np
import xarray as xr
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, CheckButtons, RadioButtons
import pandas as pd
from pathlib import Path

# == Configuration =============================================================

PP06_BASE = Path("~/ooi/postproc/pp06").expanduser()
SITE_NAME = "slopebase"
CLINE_CSV = Path(f"~/ooi/metadata/cline_extract_{SITE_NAME}.csv").expanduser()

START_DATE = "2024-01-01"
LINE_STEP = 1.0 / 3.0
MAX_DEPTH = 120.0

SENSORS = ['temperature', 'salinity', 'dissolvedoxygen', 'density']
SENSOR_LABELS = {'temperature': 'Temp (C)', 'salinity': 'Sal (PSU)',
                 'dissolvedoxygen': 'DO (umol/kg)', 'density': 'Density (kg/m3)'}
SENSOR_COLORS = {'temperature': 'red', 'salinity': 'blue',
                 'dissolvedoxygen': 'green', 'density': 'purple'}
# Cline column mapping: sensor -> (depth_col, thickness_col)
CLINE_COLS = {
    'temperature': ('thermocline_depth', 'thermocline_thickness'),
    'salinity': ('halocline_depth', 'halocline_thickness'),
    'dissolvedoxygen': ('oxycline_depth', 'oxycline_thickness'),
    'density': ('pycnocline_depth', 'pycnocline_thickness'),
}


# == Load cline metadata =======================================================

cline_df = pd.read_csv(CLINE_CSV, parse_dates=['timestamp'])
cline_df = cline_df.sort_values('timestamp').reset_index(drop=True)
mask = cline_df['timestamp'] >= pd.Timestamp(START_DATE)
cline_df = cline_df[mask].reset_index(drop=True)
print(f"Loaded {len(cline_df)} profiles from {START_DATE} onward")


# == Build GPI to file lookup ==================================================

gpi_files = {}
for year in range(2015, 2026):
    redux_dir = PP06_BASE / f"redux{year}"
    if not redux_dir.exists():
        continue
    for sensor in SENSORS:
        for f in redux_dir.glob(f"*_{sensor}_*.nc"):
            parts = f.stem.split('_')
            gpi = int(parts[6])
            if gpi not in gpi_files:
                gpi_files[gpi] = {}
            gpi_files[gpi][sensor] = f


# == Profile loading ===========================================================

def load_sensor(gpi, sensor):
    """Load one sensor profile. Returns (depth, values) or (None, None)."""
    if gpi not in gpi_files or sensor not in gpi_files[gpi]:
        return None, None
    try:
        ds = xr.open_dataset(gpi_files[gpi][sensor])
        vals = ds[sensor].values
        depth = np.abs(ds['depth'].values)
        ds.close()
        valid = ~(np.isnan(vals) | np.isnan(depth))
        vals, depth = vals[valid], depth[valid]
        sort_idx = np.argsort(depth)
        return depth[sort_idx], vals[sort_idx]
    except Exception:
        return None, None


# == State =====================================================================

current_idx = 0
active_sensor = 'temperature'
show_sensor = {s: True for s in SENSORS}

# Per-sensor cline line positions: {sensor: (upper_depth, lower_depth)}
cline_positions = {s: (0.0, 0.0) for s in SENSORS}
cline_defaults = {s: (0.0, 0.0) for s in SENSORS}


def load_cline_state(idx):
    """Load cline positions from metadata for all sensors."""
    row = cline_df.iloc[idx]
    for sensor in SENSORS:
        depth_col, thick_col = CLINE_COLS[sensor]
        d = row.get(depth_col, np.nan)
        t = row.get(thick_col, np.nan)
        if np.isnan(d) or np.isnan(t):
            cline_positions[sensor] = (40.0, 60.0)
            cline_defaults[sensor] = (40.0, 60.0)
        else:
            half = t / 2.0
            cline_positions[sensor] = (d - half, d + half)
            cline_defaults[sensor] = (d - half, d + half)


# == GUI =======================================================================

fig = plt.figure(figsize=(11, 10.35))

# Position window near top-left of screen
mng = plt.get_current_fig_manager()
try:
    mng.window.wm_geometry("+50+10")
except Exception:
    pass

# Main plot with 4 x-axes
ax_main = fig.add_axes([0.12, 0.20, 0.76, 0.58])

# Create twin axes for the other sensors
ax_sal = ax_main.twiny()
ax_do = ax_main.twiny()
ax_den = ax_main.twiny()

# Navigation
ax_prev = fig.add_axes([0.03, 0.03, 0.05, 0.035])
ax_next = fig.add_axes([0.09, 0.03, 0.05, 0.035])
btn_prev = Button(ax_prev, '<')
btn_next = Button(ax_next, '>')

# Sensor selector (radio buttons)
ax_radio = fig.add_axes([0.03, 0.08, 0.12, 0.12])
radio = RadioButtons(ax_radio, ['Temp', 'Sal', 'DO', 'Density'], active=0)
radio_map = {'Temp': 'temperature', 'Sal': 'salinity',
             'DO': 'dissolvedoxygen', 'Density': 'density'}

# Sensor toggles
ax_toggles = fig.add_axes([0.18, 0.08, 0.12, 0.12])
chk_sensors = CheckButtons(ax_toggles, ['Temp', 'Sal', 'DO', 'Dens'],
                           [True, True, True, True])
toggle_map = ['temperature', 'salinity', 'dissolvedoxygen', 'density']

# Line Controls
fig.text(0.45, 0.14, 'Upper', fontsize=9, ha='center')
ax_u_up = fig.add_axes([0.38, 0.03, 0.04, 0.035])
ax_u_dn = fig.add_axes([0.43, 0.03, 0.04, 0.035])
ax_u_rst = fig.add_axes([0.48, 0.03, 0.04, 0.035])
btn_u_up = Button(ax_u_up, '^')
btn_u_dn = Button(ax_u_dn, 'v')
btn_u_rst = Button(ax_u_rst, 'R')

fig.text(0.70, 0.14, 'Lower', fontsize=9, ha='center')
ax_l_up = fig.add_axes([0.63, 0.03, 0.04, 0.035])
ax_l_dn = fig.add_axes([0.68, 0.03, 0.04, 0.035])
ax_l_rst = fig.add_axes([0.73, 0.03, 0.04, 0.035])
btn_l_up = Button(ax_l_up, '^')
btn_l_dn = Button(ax_l_dn, 'v')
btn_l_rst = Button(ax_l_rst, 'R')

# Line artists
upper_hline = None
lower_hline = None

# Click-to-set toggle: which line does a click move?
click_target = 'upper'  # 'upper' or 'lower'
ax_click_tog = fig.add_axes([0.82, 0.03, 0.14, 0.08])
radio_click = RadioButtons(ax_click_tog, ['Click→Upper', 'Click→Lower'], active=0)


# == Drawing ===================================================================

def draw_profile(idx):
    """Draw all sensor traces and cline lines for profile at idx."""
    global current_idx, upper_hline, lower_hline
    current_idx = idx

    ax_main.clear()
    ax_sal.clear()
    ax_do.clear()
    ax_den.clear()

    if idx < 0 or idx >= len(cline_df):
        ax_main.text(0.5, 0.5, 'No more profiles', ha='center', va='center',
                     transform=ax_main.transAxes)
        fig.canvas.draw_idle()
        return

    row = cline_df.iloc[idx]
    gpi = int(row['gpi'])
    timestamp = row['timestamp']
    load_cline_state(idx)

    # Load and plot each sensor
    axes_map = {'temperature': ax_main, 'salinity': ax_sal,
                'dissolvedoxygen': ax_do, 'density': ax_den}

    for sensor in SENSORS:
        ax = axes_map[sensor]
        depth, vals = load_sensor(gpi, sensor)
        if depth is not None and len(depth) > 0 and show_sensor[sensor]:
            ax.plot(vals, depth, color=SENSOR_COLORS[sensor], linewidth=1.0)
            # Auto-scale x-axis to data range with 5% padding
            vmin, vmax = np.nanmin(vals), np.nanmax(vals)
            pad = (vmax - vmin) * 0.05 if vmax > vmin else 1.0
            ax.set_xlim(vmin - pad, vmax + pad)
        else:
            # Set a default range if no data
            ax.set_xlim(0, 1)

    # Axis labels and colors
    ax_main.set_xlabel(SENSOR_LABELS['temperature'], color=SENSOR_COLORS['temperature'])
    ax_main.tick_params(axis='x', labelcolor=SENSOR_COLORS['temperature'])
    ax_main.set_ylabel('Depth (m)')
    ax_main.set_ylim(MAX_DEPTH, 0)
    ax_main.grid(True, alpha=0.3)

    # Stack top axes with explicit pad values
    ax_sal.set_xlabel(SENSOR_LABELS['salinity'], color=SENSOR_COLORS['salinity'], labelpad=2)
    ax_sal.tick_params(axis='x', labelcolor=SENSOR_COLORS['salinity'], pad=1)
    ax_sal.xaxis.set_label_position('top')
    ax_sal.xaxis.tick_top()
    ax_sal.spines['top'].set_position(('outward', 0))

    ax_do.set_xlabel(SENSOR_LABELS['dissolvedoxygen'], color=SENSOR_COLORS['dissolvedoxygen'], labelpad=2)
    ax_do.tick_params(axis='x', labelcolor=SENSOR_COLORS['dissolvedoxygen'], pad=1)
    ax_do.xaxis.set_label_position('top')
    ax_do.xaxis.tick_top()
    ax_do.spines['top'].set_position(('outward', 36))

    ax_den.set_xlabel(SENSOR_LABELS['density'], color=SENSOR_COLORS['density'], labelpad=2)
    ax_den.tick_params(axis='x', labelcolor=SENSOR_COLORS['density'], pad=1)
    ax_den.xaxis.set_label_position('top')
    ax_den.xaxis.tick_top()
    ax_den.spines['top'].set_position(('outward', 72))

    # Cline boundary lines for active sensor
    u, l = cline_positions[active_sensor]
    upper_hline = ax_main.axhline(u, color='black', linewidth=1.2, linestyle='-')
    lower_hline = ax_main.axhline(l, color='black', linewidth=1.2, linestyle='-')

    title = (f"GPI {gpi}  |  {timestamp.strftime('%Y-%m-%d %H:%M')}  |  "
             f"[{idx+1}/{len(cline_df)}]  |  Editing: {active_sensor}")
    fig.suptitle(title, fontsize=10, y=0.97)

    fig.canvas.draw_idle()


def update_lines():
    """Update line positions from cline_positions for active sensor."""
    u, l = cline_positions[active_sensor]
    if upper_hline:
        upper_hline.set_ydata([u, u])
    if lower_hline:
        lower_hline.set_ydata([l, l])
    fig.canvas.draw_idle()


# == Callbacks =================================================================

def on_next(event):
    if current_idx < len(cline_df) - 1:
        draw_profile(current_idx + 1)

def on_prev(event):
    if current_idx > 0:
        draw_profile(current_idx - 1)

def on_u_up(event):
    u, l = cline_positions[active_sensor]
    cline_positions[active_sensor] = (u - LINE_STEP, l)
    update_lines()

def on_u_dn(event):
    u, l = cline_positions[active_sensor]
    cline_positions[active_sensor] = (u + LINE_STEP, l)
    update_lines()

def on_u_rst(event):
    u, l = cline_positions[active_sensor]
    ud, _ = cline_defaults[active_sensor]
    cline_positions[active_sensor] = (ud, l)
    update_lines()

def on_l_up(event):
    u, l = cline_positions[active_sensor]
    cline_positions[active_sensor] = (u, l - LINE_STEP)
    update_lines()

def on_l_dn(event):
    u, l = cline_positions[active_sensor]
    cline_positions[active_sensor] = (u, l + LINE_STEP)
    update_lines()

def on_l_rst(event):
    u, l = cline_positions[active_sensor]
    _, ld = cline_defaults[active_sensor]
    cline_positions[active_sensor] = (u, ld)
    update_lines()

def on_sensor_select(label):
    global active_sensor
    active_sensor = radio_map[label]
    # Auto-solo: show only the selected sensor trace
    for s in SENSORS:
        show_sensor[s] = (s == active_sensor)
    draw_profile(current_idx)

def on_toggle(label):
    idx = ['Temp', 'Sal', 'DO', 'Dens'].index(label)
    sensor = toggle_map[idx]
    show_sensor[sensor] = not show_sensor[sensor]
    draw_profile(current_idx)


btn_next.on_clicked(on_next)
btn_prev.on_clicked(on_prev)
btn_u_up.on_clicked(on_u_up)
btn_u_dn.on_clicked(on_u_dn)
btn_u_rst.on_clicked(on_u_rst)
btn_l_up.on_clicked(on_l_up)
btn_l_dn.on_clicked(on_l_dn)
btn_l_rst.on_clicked(on_l_rst)
radio.on_clicked(on_sensor_select)
chk_sensors.on_clicked(on_toggle)

def on_click_toggle(label):
    global click_target
    if 'Upper' in label:
        click_target = 'upper'
    else:
        click_target = 'lower'

radio_click.on_clicked(on_click_toggle)

def on_click(event):
    """Handle click in the plot area to set a cline boundary line, then toggle target."""
    global click_target
    # Only respond to clicks inside the main axes
    if event.inaxes not in (ax_main, ax_sal, ax_do, ax_den):
        return
    if event.button not in (1, 3):
        return

    depth_clicked = event.ydata
    if depth_clicked is None:
        return

    print(f"  Click at depth {depth_clicked:.1f}m -> {click_target} line")

    u, l = cline_positions[active_sensor]
    if click_target == 'upper':
        cline_positions[active_sensor] = (depth_clicked, l)
        click_target = 'lower'
        radio_click.set_active(1)
    else:
        cline_positions[active_sensor] = (u, depth_clicked)
        click_target = 'upper'
        radio_click.set_active(0)
    update_lines()

fig.canvas.mpl_connect('button_press_event', on_click)

# Initial draw
draw_profile(0)
plt.show()
