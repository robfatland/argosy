# cline_plot.py — Plot cline extraction results with interactive time sliders.
# Run: %run ~/argosy/iw/cline_plot.py
#
# Three panels:
#   1. Pycnocline + thermocline depth (inverted y-axis)
#   2. Mixed layer depth (inverted y-axis)
#   3. Pycnocline + thermocline strength
#
# Time range controlled by two date sliders.
# Output: inline display + PNG to ~/ooi/visualizations/

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import ipywidgets as widgets
from IPython.display import display, clear_output

# == Configuration =============================================================

CSV_PATH = Path("~/ooi/metadata/cline_extract_slopebase.csv").expanduser()
OUTPUT_DIR = Path("~/ooi/visualizations").expanduser()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SITE_NAME = "slopebase"
GAP_THRESHOLD_HOURS = 24
DEPTH_CLIP_MAX = 180.0


# == Load data =================================================================

df_all = pd.read_csv(CSV_PATH, parse_dates=['timestamp'])
df_all = df_all.sort_values('timestamp').reset_index(drop=True)

print(f"Loaded {len(df_all)} records from {CSV_PATH.name}")
print(f"  Time range: {df_all['timestamp'].iloc[0]} to {df_all['timestamp'].iloc[-1]}")


# == Gap-aware plotting ========================================================

def plot_gapped(ax, timestamps, values, color, label, linewidth=0.8, linestyle='-'):
    """Plot a time series with breaks at gaps > GAP_THRESHOLD_HOURS."""
    valid = values.notna()
    t = timestamps[valid].values
    v = values[valid].values

    if len(t) == 0:
        return

    dt_hours = np.diff(t).astype('timedelta64[h]').astype(float)
    gap_indices = np.where(dt_hours > GAP_THRESHOLD_HOURS)[0]
    segments = np.split(np.arange(len(t)), gap_indices + 1)

    for seg in segments:
        if len(seg) < 2:
            continue
        ax.plot(t[seg], v[seg], color=color, linewidth=linewidth,
                linestyle=linestyle, label=label)
        label = None


# == Plotting function =========================================================

def make_plot(start_date, end_date):
    """Generate the 3-panel plot for the given time range."""
    # Ensure start < end
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    mask = (df_all['timestamp'] >= start_date) & (df_all['timestamp'] <= end_date)
    df = df_all[mask].copy().reset_index(drop=True)

    if len(df) == 0:
        print("No data in selected range.")
        return

    # Filter depths: clip + rolling median
    pyc_depth = df['pycnocline_depth'].where(df['pycnocline_depth'] <= DEPTH_CLIP_MAX)
    therm_depth = df['thermocline_depth'].where(df['thermocline_depth'] <= DEPTH_CLIP_MAX)
    mld = df['mld'].where(df['mld'] <= DEPTH_CLIP_MAX)

    pyc_depth = pyc_depth.rolling(5, center=True, min_periods=3).median()
    therm_depth = therm_depth.rolling(5, center=True, min_periods=3).median()
    mld = mld.rolling(5, center=True, min_periods=3).median()

    # Filter thickness: rolling median (9-point, ~1 day at 9 profiles/day)
    pyc_thick = df['pycnocline_thickness'].rolling(9, center=True, min_periods=5).median()
    therm_thick = df['thermocline_thickness'].rolling(9, center=True, min_periods=5).median()

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 12), sharex=True)
    fig.suptitle(f"Cline Analysis: {SITE_NAME} ({start_date.date()} to {end_date.date()})",
                 fontsize=13)

    # Panel 1: Pycnocline + Thermocline depth as scatter with thickness error bars
    valid_pyc = pyc_depth.notna() & pyc_thick.notna()
    valid_therm = therm_depth.notna() & therm_thick.notna()

    if valid_pyc.sum() > 0:
        ax1.errorbar(df['timestamp'][valid_pyc].values, pyc_depth[valid_pyc].values,
                     yerr=pyc_thick[valid_pyc].values / 2,
                     fmt='.', color='black', markersize=2, elinewidth=0.3,
                     alpha=0.5, label='Pycnocline', capsize=0)
    if valid_therm.sum() > 0:
        ax1.errorbar(df['timestamp'][valid_therm].values, therm_depth[valid_therm].values,
                     yerr=therm_thick[valid_therm].values / 2,
                     fmt='.', color='red', markersize=2, elinewidth=0.3,
                     alpha=0.5, label='Thermocline', capsize=0)
    ax1.set_ylabel('Depth (m)')
    ax1.set_ylim(200, 0)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='lower right', fontsize=8)

    # Panel 2: Mixed Layer Depth
    plot_gapped(ax2, df['timestamp'], mld, 'gray', 'MLD', linewidth=1.0)
    ax2.set_ylabel('MLD (m)')
    ax2.set_ylim(150, 0)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='lower right', fontsize=8)

    # Panel 3: Cline thickness (filtered)
    plot_gapped(ax3, df['timestamp'], pyc_thick, 'black', 'Pycnocline', linewidth=1.0)
    plot_gapped(ax3, df['timestamp'], therm_thick, 'red', 'Thermocline', linewidth=0.8)
    ax3.set_ylabel('Thickness (m)')
    ax3.set_ylim(bottom=0)
    ax3.set_xlabel('Date')
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc='upper right', fontsize=8)

    plt.tight_layout()

    # Save
    output_path = OUTPUT_DIR / f"cline_extract_{SITE_NAME}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")

    plt.show()


# == Slider UI =================================================================

from datetime import date, timedelta

# SelectionSlider with date strings for the full range
date_range = pd.date_range('2015-01-01', '2025-12-31', freq='D')
date_options = [(d.strftime('%Y-%m-%d'), d) for d in date_range]

start_slider = widgets.SelectionSlider(
    options=date_options,
    value=pd.Timestamp('2024-01-01'),
    description='Start:',
    continuous_update=False,
    layout=widgets.Layout(width='500px'),
    style={'description_width': 'initial'},
)

end_slider = widgets.SelectionSlider(
    options=date_options,
    value=pd.Timestamp('2024-05-01'),
    description='End:',
    continuous_update=False,
    layout=widgets.Layout(width='500px'),
    style={'description_width': 'initial'},
)

plot_button = widgets.Button(description='Plot', button_style='success')
out = widgets.Output()


def on_plot_click(b):
    with out:
        clear_output(wait=True)
        s = pd.Timestamp(start_slider.value)
        e = pd.Timestamp(end_slider.value)
        make_plot(s, e)


plot_button.on_click(on_plot_click)

display(widgets.VBox([
    widgets.HBox([start_slider, end_slider, plot_button]),
    out
]))

# Initial plot
with out:
    make_plot(pd.Timestamp('2024-01-01'), pd.Timestamp('2024-05-01'))
