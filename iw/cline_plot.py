# cline_plot.py — Plot cline extraction results as time series.
#
# Consumes the cline_extract output (metadata/features/cline_extract_<site>.csv) and
# renders three stacked panels vs time:
#   1. Pycnocline + thermocline depth (inverted y-axis), thickness as error bars
#   2. Mixed layer depth (inverted y-axis)
#   3. Pycnocline + thermocline thickness
#
# DUAL MODE:
#   - Notebook:   %run ~/argosy/iw/cline_plot.py   → interactive ipywidgets date sliders
#                 + inline display (and each Plot also saves a PNG).
#   - Standalone: python ~/argosy/iw/cline_plot.py [--start YYYY-MM-DD] [--end YYYY-MM-DD]
#                 → headless (Agg), saves a PNG to the visualizations folder, no window.
#
# Site via ARGOSY_SITE (default sb). Date range defaults to the FULL span present in the
# CSV (no more hardcoded 2024 window); override with --start/--end (standalone) or the
# sliders (notebook).
#
# Output PNG: ~/ooi/<site>/visualizations/cline_extract_<site>_<start>_<end>.png

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# --- Detect run context: notebook (IPython) vs standalone -------------------------
def _in_notebook():
    try:
        from IPython import get_ipython
        ip = get_ipython()
        return ip is not None and ip.__class__.__name__ == "ZMQInteractiveShell"
    except Exception:
        return False

IN_NOTEBOOK = _in_notebook()

# Backend must be chosen BEFORE importing pyplot. Standalone = Agg (headless, WSL-safe
# per project convention); notebook = leave default so inline works.
import matplotlib
if not IN_NOTEBOOK:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Make the repo root importable so `import ooipaths` works under %run / python.
sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op

# == Configuration =============================================================

SITE = op.DEFAULT_SITE
# cline_extract CSVs are keyed by the 2-letter site code (was hardcoded 'slopebase').
CSV_PATH = op.metadata_dir(SITE, "features") / f"cline_extract_{SITE}.csv"
OUTPUT_DIR = op.visualizations_dir(SITE)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

GAP_THRESHOLD_HOURS = 24
DEPTH_CLIP_MAX = 180.0


# == Load data =================================================================

def load_data():
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"cline_extract CSV not found: {CSV_PATH}\n"
            f"  Run iw/cline_extract.py (ARGOSY_SITE={SITE}) first.")
    df = pd.read_csv(CSV_PATH, parse_dates=['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    print(f"Loaded {len(df)} records from {CSV_PATH.name}")
    if len(df):
        print(f"  Time range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
    return df


df_all = load_data()

# Full data span, used as the default plotting window (replaces the old hardcoded 2024).
DATA_START = df_all['timestamp'].min() if len(df_all) else pd.Timestamp('2015-01-01')
DATA_END = df_all['timestamp'].max() if len(df_all) else pd.Timestamp('2025-12-31')


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

def make_plot(start_date, end_date, show=True):
    """Generate the 3-panel plot for the given time range. Returns the saved PNG path
    (or None if no data). `show`: display interactively (notebook) if True."""
    start_date, end_date = pd.Timestamp(start_date), pd.Timestamp(end_date)
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    mask = (df_all['timestamp'] >= start_date) & (df_all['timestamp'] <= end_date)
    df = df_all[mask].copy().reset_index(drop=True)
    if len(df) == 0:
        print("No data in selected range.")
        return None

    pyc_depth = df['pycnocline_depth'].where(df['pycnocline_depth'] <= DEPTH_CLIP_MAX)
    therm_depth = df['thermocline_depth'].where(df['thermocline_depth'] <= DEPTH_CLIP_MAX)
    mld = df['mld'].where(df['mld'] <= DEPTH_CLIP_MAX)

    pyc_depth = pyc_depth.rolling(5, center=True, min_periods=3).median()
    therm_depth = therm_depth.rolling(5, center=True, min_periods=3).median()
    mld = mld.rolling(5, center=True, min_periods=3).median()

    pyc_thick = df['pycnocline_thickness'].rolling(9, center=True, min_periods=5).median()
    therm_thick = df['thermocline_thickness'].rolling(9, center=True, min_periods=5).median()

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 12), sharex=True)
    fig.suptitle(f"Cline Analysis: {SITE} ({start_date.date()} to {end_date.date()})",
                 fontsize=13)

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

    plot_gapped(ax2, df['timestamp'], mld, 'gray', 'MLD', linewidth=1.0)
    ax2.set_ylabel('MLD (m)')
    ax2.set_ylim(150, 0)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='lower right', fontsize=8)

    plot_gapped(ax3, df['timestamp'], pyc_thick, 'black', 'Pycnocline', linewidth=1.0)
    plot_gapped(ax3, df['timestamp'], therm_thick, 'red', 'Thermocline', linewidth=0.8)
    ax3.set_ylabel('Thickness (m)')
    ax3.set_ylim(bottom=0)
    ax3.set_xlabel('Date')
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc='upper right', fontsize=8)

    plt.tight_layout()

    output_path = (OUTPUT_DIR /
                   f"cline_extract_{SITE}_{start_date.strftime('%Y%m%d')}_"
                   f"{end_date.strftime('%Y%m%d')}.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")

    if show and IN_NOTEBOOK:
        plt.show()
    else:
        plt.close(fig)
    return output_path


# == Notebook UI (sliders) — only wired up when running inside a notebook ======

def _launch_notebook_ui():
    import ipywidgets as widgets
    from IPython.display import display, clear_output

    date_range = pd.date_range(DATA_START.normalize(), DATA_END.normalize(), freq='D')
    date_options = [(d.strftime('%Y-%m-%d'), d) for d in date_range]

    start_slider = widgets.SelectionSlider(
        options=date_options, value=date_options[0][1], description='Start:',
        continuous_update=False, layout=widgets.Layout(width='500px'),
        style={'description_width': 'initial'})
    end_slider = widgets.SelectionSlider(
        options=date_options, value=date_options[-1][1], description='End:',
        continuous_update=False, layout=widgets.Layout(width='500px'),
        style={'description_width': 'initial'})
    plot_button = widgets.Button(description='Plot', button_style='success')
    out = widgets.Output()

    def on_plot_click(b):
        with out:
            clear_output(wait=True)
            make_plot(start_slider.value, end_slider.value)

    plot_button.on_click(on_plot_click)
    display(widgets.VBox([widgets.HBox([start_slider, end_slider, plot_button]), out]))
    with out:
        make_plot(DATA_START, DATA_END)


# == Entry point ===============================================================

if IN_NOTEBOOK:
    _launch_notebook_ui()
else:
    ap = argparse.ArgumentParser(description="Plot cline_extract time series (standalone).")
    ap.add_argument('--start', default=None, help="start date YYYY-MM-DD (default: data start)")
    ap.add_argument('--end', default=None, help="end date YYYY-MM-DD (default: data end)")
    args = ap.parse_args()
    s = pd.Timestamp(args.start) if args.start else DATA_START
    e = pd.Timestamp(args.end) if args.end else DATA_END
    make_plot(s, e, show=False)
