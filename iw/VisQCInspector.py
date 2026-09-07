# VisQCInspector.py — Interactive profile inspector/annotator for visual QC (standalone GUI).
# Run: python ~/argosy/iw/VisQCInspector.py
#   Site   : reads op.DEFAULT_SITE (set ARGOSY_SITE=oo|ab to change).
#   Start  : VISQC_START_DATE env var (default 2024-01-01).
#
# LEFT panel : 4 sensor traces (T, S, DO, density) on a shared depth axis, independent
#   x-axes, auto-scaled per profile. Sensor toggles turn traces on/off; the sensor
#   selector chooses which cline to edit. Two adjustable cline boundary lines (upper/
#   lower) per sensor cline (nudge buttons or click-to-set).
# RIGHT panel: potential density sigma-0 (TEOS-10 via gsw) vs depth for the same profile
#   (computed from the S + T shards). Skipped with a note if gsw is unavailable.
#
# Decisions: Accept / Correct / Discard buttons append one row per (gpi, sensor) to the
#   visitation CSV at metadata/annotations/visqc_visitation_<site>.csv (re-deciding
#   overwrites the prior row). Accept/Discard auto-advance to the next profile.
#
# Uses matplotlib TkAgg backend (genuinely interactive — needs a display). Requires:
#   sudo apt install python3-tk ; gsw (for the potential-density panel).

import os
import sys
from datetime import datetime, timezone
import numpy as np
import xarray as xr
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, CheckButtons, RadioButtons
import pandas as pd
from pathlib import Path

# Potential density (TEOS-10). Optional: if gsw is missing the right panel is skipped.
try:
    import gsw
    HAVE_GSW = True
except Exception:
    HAVE_GSW = False

# Make the repo root importable so `import ooipaths` works under %run.
sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op
SITE = op.DEFAULT_SITE

# == Configuration =============================================================

PP06_BASE = op.postproc_base(SITE) / "pp06"
# cline_extract CSVs are keyed by the 2-letter site code (was hardcoded 'slopebase').
CLINE_CSV = op.metadata_dir(SITE, "features") / f"cline_extract_{SITE}.csv"
# Human QC decisions land in metadata/annotations/ (per the metadata-subfolder convention).
VISITATION_CSV = op.metadata_dir(SITE, "annotations") / f"visqc_visitation_{SITE}.csv"

# Nominal site position for TEOS-10 pressure/absolute-salinity conversion.
# (Small errors here have negligible effect on sigma-0 over 0-200 m.)
SITE_LATLON = {"sb": (44.529, -125.390), "oo": (44.374, -124.956), "ab": (45.830, -129.753)}
SITE_LAT, SITE_LON = SITE_LATLON.get(SITE, (45.0, -125.0))

# START_DATE is configurable via env (VISQC_START_DATE); default keeps prior behavior.
START_DATE = os.environ.get("VISQC_START_DATE", "2024-01-01")
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
    redux_dir = op.postproc_dir("pp06", year, SITE)
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


def compute_potential_density(gpi):
    """Potential density anomaly sigma-0 (kg/m^3) vs depth for a profile.

    Loads salinity + temperature shards for the GPI, interpolates temperature onto
    salinity's depth grid, converts practical salinity + in-situ temperature +
    pressure to TEOS-10 Absolute Salinity / Conservative Temperature, and returns
    (depth, sigma0). Returns (None, None) if gsw is unavailable or inputs are missing.
    """
    if not HAVE_GSW:
        return None, None
    sal_depth, sal = load_sensor(gpi, 'salinity')
    tmp_depth, tmp = load_sensor(gpi, 'temperature')
    if sal_depth is None or tmp_depth is None or len(sal_depth) < 2 or len(tmp_depth) < 2:
        return None, None
    # Put temperature on salinity's depth grid (both sorted ascending by load_sensor).
    t_on_sal = np.interp(sal_depth, tmp_depth, tmp, left=np.nan, right=np.nan)
    valid = ~(np.isnan(sal) | np.isnan(t_on_sal))
    if valid.sum() < 2:
        return None, None
    d = sal_depth[valid]
    sp = sal[valid]
    t = t_on_sal[valid]
    # depth is positive-down (load_sensor uses abs); gsw wants z negative-down.
    p = gsw.p_from_z(-d, SITE_LAT)
    SA = gsw.SA_from_SP(sp, p, SITE_LON, SITE_LAT)
    CT = gsw.CT_from_t(SA, t, p)
    sigma0 = gsw.sigma0(SA, CT)
    return d, sigma0


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

fig = plt.figure(figsize=(22, 13.0))

# Position window near top-left of screen
mng = plt.get_current_fig_manager()
try:
    mng.window.wm_geometry("+50+10")
except Exception:
    pass

# Charts sit in the UPPER portion; the band below y~0.28 is reserved for controls so
# the charts' bottom x-axis labels don't collide with the widgets/status text.
CHART_BOTTOM = 0.30
CHART_HEIGHT = 0.48

# Left plot with 4 x-axes (T/S/DO/density traces)
ax_main = fig.add_axes([0.08, CHART_BOTTOM, 0.40, CHART_HEIGHT])

# Create twin axes for the other sensors
ax_sal = ax_main.twiny()
ax_do = ax_main.twiny()
ax_den = ax_main.twiny()

# Right plot: potential density (sigma-0) vs depth. Same size as the left plot.
ax_pden = fig.add_axes([0.56, CHART_BOTTOM, 0.40, CHART_HEIGHT])

# All controls live in the reserved band y in [0.04, 0.26] (below the charts, whose
# bottom x-axis labels sit just under CHART_BOTTOM=0.32). Two rows keep it uncluttered.

# Navigation (upper control row)
ax_prev = fig.add_axes([0.03, 0.20, 0.05, 0.04])
ax_next = fig.add_axes([0.09, 0.20, 0.05, 0.04])
btn_prev = Button(ax_prev, '<')
btn_next = Button(ax_next, '>')

# Sensor selector (radio buttons)
ax_radio = fig.add_axes([0.03, 0.06, 0.12, 0.12])
radio = RadioButtons(ax_radio, ['Temp', 'Sal', 'DO', 'Density'], active=0)
radio_map = {'Temp': 'temperature', 'Sal': 'salinity',
             'DO': 'dissolvedoxygen', 'Density': 'density'}

# Sensor toggles
ax_toggles = fig.add_axes([0.18, 0.06, 0.12, 0.12])
chk_sensors = CheckButtons(ax_toggles, ['Temp', 'Sal', 'DO', 'Dens'],
                           [True, True, True, True])
toggle_map = ['temperature', 'salinity', 'dissolvedoxygen', 'density']

# Line Controls — Upper group
fig.text(0.45, 0.155, 'Upper', fontsize=9, ha='center')
ax_u_up = fig.add_axes([0.38, 0.10, 0.04, 0.04])
ax_u_dn = fig.add_axes([0.43, 0.10, 0.04, 0.04])
ax_u_rst = fig.add_axes([0.48, 0.10, 0.04, 0.04])
btn_u_up = Button(ax_u_up, '^')
btn_u_dn = Button(ax_u_dn, 'v')
btn_u_rst = Button(ax_u_rst, 'R')

# Line Controls — Lower group
fig.text(0.70, 0.155, 'Lower', fontsize=9, ha='center')
ax_l_up = fig.add_axes([0.63, 0.10, 0.04, 0.04])
ax_l_dn = fig.add_axes([0.68, 0.10, 0.04, 0.04])
ax_l_rst = fig.add_axes([0.73, 0.10, 0.04, 0.04])
btn_l_up = Button(ax_l_up, '^')
btn_l_dn = Button(ax_l_dn, 'v')
btn_l_rst = Button(ax_l_rst, 'R')

# Line artists
upper_hline = None
lower_hline = None

# Click-to-set toggle: which line does a click move?
click_target = 'upper'  # 'upper' or 'lower'
ax_click_tog = fig.add_axes([0.80, 0.155, 0.14, 0.08])
radio_click = RadioButtons(ax_click_tog, ['Click→Upper', 'Click→Lower'], active=0)

# Decision buttons: record accept / correct / discard for the current profile.
ax_accept = fig.add_axes([0.80, 0.10, 0.045, 0.04])
ax_correct = fig.add_axes([0.848, 0.10, 0.045, 0.04])
ax_discard = fig.add_axes([0.896, 0.10, 0.045, 0.04])
btn_accept = Button(ax_accept, 'Accept', color='#c8e6c9', hovercolor='#a5d6a7')
btn_correct = Button(ax_correct, 'Correct', color='#fff9c4', hovercolor='#fff59d')
btn_discard = Button(ax_discard, 'Discard', color='#ffcdd2', hovercolor='#ef9a9a')

# Status line (shows the last decision written) — just below the decision buttons.
status_text = fig.text(0.80, 0.06, '', fontsize=8, color='#333')


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

    # Right panel: potential density (sigma-0)
    ax_pden.clear()
    ax_pden.set_ylim(MAX_DEPTH, 0)
    ax_pden.set_ylabel('Depth (m)')
    ax_pden.grid(True, alpha=0.3)
    if not HAVE_GSW:
        ax_pden.set_title('Potential density\n(gsw not installed)', fontsize=9)
    else:
        pd_depth, sigma0 = compute_potential_density(gpi)
        if pd_depth is not None and len(pd_depth) > 0:
            ax_pden.plot(sigma0, pd_depth, color='darkorange', linewidth=1.0)
            vmin, vmax = np.nanmin(sigma0), np.nanmax(sigma0)
            pad = (vmax - vmin) * 0.05 if vmax > vmin else 0.5
            ax_pden.set_xlim(vmin - pad, vmax + pad)
            ax_pden.set_xlabel('Potential density σ₀ (kg/m³)', color='darkorange')
            ax_pden.tick_params(axis='x', labelcolor='darkorange')
        else:
            ax_pden.set_xlabel('Potential density σ₀ (kg/m³)', color='darkorange')
            ax_pden.text(0.5, 0.5, 'no T+S overlap', ha='center', va='center',
                         transform=ax_pden.transAxes, fontsize=9, color='gray')

    title = (f"GPI {gpi}  |  {timestamp.strftime('%Y-%m-%d %H:%M')}  |  "
             f"[{idx+1}/{len(cline_df)}]  |  Editing: {active_sensor}")
    fig.suptitle(title, fontsize=15, fontweight='bold', y=0.97)

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


# == Decision recording ========================================================

VISITATION_COLUMNS = [
    'timestamp', 'gpi', 'sensor', 'decision',
    'upper_depth', 'lower_depth', 'cline_depth', 'cline_thickness', 'reviewed_at',
]


def record_decision(decision):
    """Append (or replace) a visitation row for the current profile + active sensor.

    decision: 'accept' | 'correct' | 'discard'. For accept/correct the cline depth
    and thickness are derived from the current upper/lower line positions; for discard
    they are recorded as NaN. Re-deciding the same (gpi, sensor) overwrites the prior row.
    """
    if current_idx < 0 or current_idx >= len(cline_df):
        return
    row = cline_df.iloc[current_idx]
    gpi = int(row['gpi'])
    timestamp = pd.Timestamp(row['timestamp'])
    u, l = cline_positions[active_sensor]
    if decision == 'discard':
        cline_depth = np.nan
        cline_thickness = np.nan
    else:
        lo, hi = sorted((u, l))
        cline_depth = (lo + hi) / 2.0
        cline_thickness = hi - lo
    new_row = {
        'timestamp': timestamp.isoformat(),
        'gpi': gpi,
        'sensor': active_sensor,
        'decision': decision,
        'upper_depth': round(float(u), 3),
        'lower_depth': round(float(l), 3),
        'cline_depth': round(float(cline_depth), 3) if not np.isnan(cline_depth) else np.nan,
        'cline_thickness': round(float(cline_thickness), 3) if not np.isnan(cline_thickness) else np.nan,
        'reviewed_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }

    VISITATION_CSV.parent.mkdir(parents=True, exist_ok=True)
    if VISITATION_CSV.exists():
        vdf = pd.read_csv(VISITATION_CSV)
    else:
        vdf = pd.DataFrame(columns=VISITATION_COLUMNS)
    # One decision per (gpi, sensor): drop any prior row for this pair, then append.
    if len(vdf):
        vdf = vdf[~((vdf['gpi'] == gpi) & (vdf['sensor'] == active_sensor))]
    vdf = pd.concat([vdf, pd.DataFrame([new_row])], ignore_index=True)
    vdf = vdf[VISITATION_COLUMNS]
    vdf.to_csv(VISITATION_CSV, index=False)

    status_text.set_text(f"{decision.upper()} gpi={gpi} {active_sensor} "
                         f"(d={new_row['cline_depth']}, t={new_row['cline_thickness']}) "
                         f"-> {VISITATION_CSV.name}")
    print(f"  wrote {decision} for gpi={gpi} sensor={active_sensor} -> {VISITATION_CSV}")
    fig.canvas.draw_idle()


def on_accept(event):
    record_decision('accept')
    # Advance to the next profile after accepting (common review flow).
    if current_idx < len(cline_df) - 1:
        draw_profile(current_idx + 1)


def on_correct(event):
    record_decision('correct')


def on_discard(event):
    record_decision('discard')
    if current_idx < len(cline_df) - 1:
        draw_profile(current_idx + 1)


btn_accept.on_clicked(on_accept)
btn_correct.on_clicked(on_correct)
btn_discard.on_clicked(on_discard)

# Initial draw
draw_profile(0)
plt.show()
