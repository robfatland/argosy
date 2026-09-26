"""
inspect.py — visualize MLDNet predictions against profiles (and human labels).

For a given site/year, steps through profiles showing, per sensor: the filtered trace vs
depth, the predicted heatmap (as a shaded band over depth), the picked MLD peak + its
confidence, and — where a human label exists — the human MLD for comparison. Sibling to
VisQCInspector / SignoffQC; the qualitative check you run before trusting the metrics.

Run: python ~/argosy/mld/inspect.py --model <path.pt> --site sb --year 2024
Needs a display (matplotlib TkAgg + python3-tk).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import xarray as xr
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op
from mld.mld_config import SENSORS, N_BINS, labels_csv
from mld.dataset import _bin_profile, _find_shard, BIN_CENTERS
from mld.infer import _gpis_for_year, _build_input
from mld.model import MLDNet, peak_from_heatmap

SENSOR_COLOR = {"temperature": "red", "salinity": "blue",
                "density": "black", "dissolvedoxygen": "green"}

# Fixed x-ranges so structure is visible (not squashed against a 0-based axis).
# None -> adapt to the profile's own data range (with padding).
SENSOR_XRANGE = {
    "salinity": (30.0, 37.0),
    "density": (1020.0, 1030.0),
    "temperature": None,       # adapt to data (roughly 4-16)
    "dissolvedoxygen": None,   # adapt to data
}


def _xrange(sensor, filt):
    """Return (lo, hi) x-limits for a sensor panel."""
    fixed = SENSOR_XRANGE.get(sensor)
    if fixed is not None:
        return fixed
    vals = filt[filt != 0]
    if len(vals) < 2:
        return (0.0, 1.0)
    lo, hi = float(np.min(vals)), float(np.max(vals))
    pad = (hi - lo) * 0.08 if hi > lo else 1.0
    return (lo - pad, hi + pad)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--site", default=op.DEFAULT_SITE)
    ap.add_argument("--year", type=int, required=True)
    args = ap.parse_args()

    model = MLDNet()
    model.load_state_dict(torch.load(args.model, map_location="cpu", weights_only=True))
    model.eval()

    gpis = _gpis_for_year(args.site, args.year)
    if not gpis:
        print(f"no pp06 profiles for {args.site} {args.year}")
        return

    # Human labels (if present) for overlay.
    lab = None
    lc = labels_csv(args.site)
    if lc.exists():
        lab = pd.read_csv(lc)

    state = {"i": 0}
    fig, axes = plt.subplots(1, len(SENSORS), figsize=(20, 8), sharey=True)
    # OS window title (not the in-figure title).
    try:
        fig.canvas.manager.set_window_title("MLD Inspector")
    except Exception:
        pass

    def _daily_index(gpi):
        year_dir = op.postproc_dir("pp06", args.year, args.site)
        for f in year_dir.glob(f"*_{gpi}_*.nc"):
            parts = f.stem.split("_")
            try:
                return int(parts[7])
            except (IndexError, ValueError):
                return None
        return None

    def draw():
        gpi = gpis[state["i"]]
        x, pmask, ts = _build_input(args.site, args.year, gpi, return_mask=True)
        for si, sensor in enumerate(SENSORS):
            ax = axes[si]
            ax.clear()
            ax.set_ylim(N_BINS, 0)
            ax.set_title(sensor, fontsize=9)
            if si == 0:
                ax.set_ylabel("Depth bin (≈ m)")
            if x is None:
                continue
            filt = x[si, 0].copy()
            # Only draw bins that held a REAL sample; blank the fwd/back-filled bins
            # (which otherwise extend the trace up to 0 m where there is no data).
            real = pmask[si] > 0.5
            filt_plot = np.where(real, filt, np.nan)
            ax.plot(filt_plot, np.arange(N_BINS), color=SENSOR_COLOR[sensor], lw=1.0)
            # X-range: fixed sensible defaults per sensor; temperature adapts to data.
            lo, hi = _xrange(sensor, filt[real] if real.any() else filt)
            ax.set_xlim(lo, hi)
            with torch.no_grad():
                pred = model(torch.from_numpy(x[None]))[0, si].numpy()
            # Heatmap overlay: faint band spanning the panel width, alpha = prediction.
            ax.pcolormesh(np.array([lo, hi]), np.arange(N_BINS + 1),
                          pred[:, None], cmap="Oranges", alpha=0.35,
                          shading="flat", vmin=0, vmax=1)
            depth, conf = peak_from_heatmap(pred, BIN_CENTERS, 0.3)
            if depth is not None:
                ax.axhline(depth, color="orange", lw=1.5, label=f"pred {depth:.0f}m ({conf:.2f})")
            else:
                ax.text(0.5, 0.05, f"no-MLD ({conf:.2f})", transform=ax.transAxes,
                        ha="center", color="orange", fontsize=8)
            if lab is not None:
                r = lab[(lab["gpi"] == gpi) & (lab["sensor"] == sensor)]
                if len(r) and not bool(r.iloc[0].get("no_mld_recorded", False)):
                    hd = r.iloc[0]["mld_depth"]
                    if not pd.isna(hd):
                        ax.axhline(hd, color="purple", lw=1.2, ls="--", label=f"human {hd:.0f}m")
            if ax.get_legend_handles_labels()[1]:
                ax.legend(loc="lower right", fontsize=7)
        di = _daily_index(gpi)
        date_str = ts.strftime("%Y-%m-%d") if ts is not None else "?"
        fig.suptitle(f"{args.site} {args.year} | GPI {gpi} | {date_str} | daily {di} "
                     f"| {state['i']+1}/{len(gpis)}", fontsize=13, fontweight="bold")
        fig.canvas.draw_idle()

    def step(d):
        state["i"] = max(0, min(len(gpis) - 1, state["i"] + d))
        draw()

    ax_prev = fig.add_axes([0.35, 0.02, 0.1, 0.05])
    ax_next = fig.add_axes([0.55, 0.02, 0.1, 0.05])
    b_prev = Button(ax_prev, "< Prev")
    b_next = Button(ax_next, "Next >")
    b_prev.on_clicked(lambda e: step(-1))
    b_next.on_clicked(lambda e: step(1))

    draw()
    plt.show()


if __name__ == "__main__":
    main()
