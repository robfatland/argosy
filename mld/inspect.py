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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--site", default=op.DEFAULT_SITE)
    ap.add_argument("--year", type=int, required=True)
    args = ap.parse_args()

    model = MLDNet()
    model.load_state_dict(torch.load(args.model, map_location="cpu"))
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
    fig.suptitle("MLD prediction inspector", fontsize=14, fontweight="bold")

    def draw():
        gpi = gpis[state["i"]]
        x, ts = _build_input(args.site, args.year, gpi)
        for si, sensor in enumerate(SENSORS):
            ax = axes[si]
            ax.clear()
            ax.set_ylim(N_BINS, 0)
            ax.set_title(sensor, fontsize=9)
            if si == 0:
                ax.set_ylabel("Depth bin (≈ m)")
            if x is None:
                continue
            filt = x[si, 0]
            ax.plot(filt, np.arange(N_BINS), color=SENSOR_COLOR[sensor], lw=1.0)
            with torch.no_grad():
                pred = model(torch.from_numpy(x[None]))[0, si].numpy()
            # Heatmap as a shaded band on the right side of the panel.
            ax.barh(np.arange(N_BINS), pred * (filt.max() - filt.min() + 1e-6) * 0.3 + filt.min(),
                    height=1.0, color="orange", alpha=0.25)
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
            ax.legend(loc="lower right", fontsize=7)
        fig.suptitle(f"MLD inspector | {args.site} {args.year} | GPI {gpi} "
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
