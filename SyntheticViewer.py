"""
SyntheticViewer.py — minimal VIEW-ONLY inspector for the synthetic MLD shadow dataset.

One temperature panel. Filter fixed = adaptive_savgol_mad (window 59, adaptivity 2), always on.
Raw trace in RED, filtered trace in BLACK. Ground-truth MLD drawn as a dashed line + badge.
One "Next" button. Purpose: click through synthetic temperature profiles and confirm they look
like textbook MLD archetypes.

Reads the parallel-universe tree ~/ooi/synthetic/. Reuses MLD.py's filter.

Run:  python ~/argosy/SyntheticViewer.py
      python ~/argosy/SyntheticViewer.py --dump      # headless PNGs instead of GUI
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op
from MLD import apply_filter, SENSOR_COLORS, SENSOR_LABELS

SENSOR = "temperature"                       # interactive viewer is temperature-only
ALL_SENSORS = ("temperature", "salinity", "density", "dissolvedoxygen")
FILTER_KEY, P1, P2 = "adaptive_savgol_mad", 59.0, 2.0
SYN_PP06 = op.OOI_ROOT / "synthetic" / "postproc" / "pp06"
SYN_LABELS = op.OOI_ROOT / "synthetic" / "metadata" / "annotations" / "mld_labels_synthetic_block00_synthetic.csv"
MAX_DEPTH = 200.0


def build_index(sensor=SENSOR):
    idx = {}
    if not SYN_PP06.exists():
        raise SystemExit(f"No synthetic data at {SYN_PP06} — run mld/synthetic.py first.")
    for year_dir in sorted(p for p in SYN_PP06.iterdir() if p.is_dir()):
        for f in year_dir.glob(f"RCA_synthetic_sp_{sensor}_*.nc"):
            parts = f.stem.split("_")
            try:
                gpi = int(parts[6])
            except (IndexError, ValueError):
                continue
            idx[gpi] = f
    return idx


def load_profile(index, gpi, sensor=SENSOR):
    f = index.get(gpi)
    if f is None:
        return None, None
    try:
        with xr.open_dataset(f) as ds:
            vals = ds[sensor].values
            depth = np.abs(ds["depth"].values)
    except Exception:
        return None, None
    valid = ~(np.isnan(vals) | np.isnan(depth))
    vals, depth = vals[valid], depth[valid]
    order = np.argsort(depth)
    return depth[order], vals[order]


def true_mld(labels, gpi, sensor=SENSOR):
    if labels.empty:
        return None, False
    r = labels[(labels["gpi"] == gpi) & (labels["sensor"] == sensor)]
    if len(r) == 0:
        return None, False
    r = r.iloc[0]
    if bool(r["no_mld_recorded"]):
        return None, True
    try:
        return float(r["mld_depth"]), True
    except (ValueError, TypeError):
        return None, True


def render(ax, index, labels, gpi, sensor=SENSOR):
    ax.clear()
    depth, raw = load_profile(index, gpi, sensor)
    mld, labeled = true_mld(labels, gpi, sensor)
    if depth is not None and len(depth):
        # Data is NOISE-FREE (synthetic), so raw IS the clean signal — show it alone, no
        # filter. (Filtering a clean curve only adds blend artifacts; restore raw-vs-filtered
        # when additive noise is re-enabled.)
        ax.plot(raw, depth, color="black", lw=1.4, zorder=2)
        if mld is not None:
            ax.axhline(mld, color="black", ls="--", lw=1.1)
            # BLUE DOT on the trace at the MLD depth — visual check that the MLD metadata
            # lands where the elbow actually is for each elbow curvature.
            xval = float(np.interp(mld, depth, raw))
            ax.plot([xval], [mld], "o", color="blue", markersize=9,
                    markeredgecolor="black", zorder=5)
    else:
        ax.text(0.5, 0.5, f"no {sensor} data", ha="center", va="center",
                transform=ax.transAxes)
    badge = (f"MLD = {mld:.1f} m" if mld is not None
             else "No MLD" if labeled else "(no label)")
    ax.text(0.97, 0.04, badge, ha="right", va="bottom", fontsize=11, fontweight="bold",
            transform=ax.transAxes, bbox=dict(boxstyle="round", fc="white", alpha=0.85))
    ax.set_ylim(MAX_DEPTH, 0)
    ax.set_xlabel(SENSOR_LABELS[sensor], color=SENSOR_COLORS[sensor])
    ax.set_ylabel("Depth (m)")
    ax.grid(True, alpha=0.3)


class Viewer:
    def __init__(self, start_gpi=None):
        self.index = build_index()
        self.labels = pd.read_csv(SYN_LABELS) if SYN_LABELS.exists() else pd.DataFrame()
        self.gpis = sorted(self.index)
        if not self.gpis:
            raise SystemExit("No synthetic temperature profiles found.")
        self.idx = self.gpis.index(int(start_gpi)) if (start_gpi and int(start_gpi) in self.index) else 0

        self.fig = plt.figure(figsize=(8, 9))
        self.ax = self.fig.add_axes([0.14, 0.18, 0.80, 0.74])
        ax_next = self.fig.add_axes([0.80, 0.04, 0.14, 0.06])
        self.btn = Button(ax_next, "Next ▶")
        self.btn.on_clicked(self._next)
        self._draw()

    def _next(self, _event):
        self.idx = (self.idx + 1) % len(self.gpis)
        self._draw()

    def _draw(self):
        gpi = self.gpis[self.idx]
        render(self.ax, self.index, self.labels, gpi)
        self.fig.suptitle(f"SYNTHETIC temperature  GPI {gpi}  [{self.idx + 1}/{len(self.gpis)}]"
                          f"  (raw, noise-free)",
                          fontsize=11, fontweight="bold")
        self.fig.canvas.draw_idle()


def dump_pngs(gpis, outdir):
    """One PNG per (gpi, sensor) across all 4 sensors. With the default 10 gpis -> 40 images."""
    matplotlib.use("Agg")
    import matplotlib.pyplot as _plt
    labels = pd.read_csv(SYN_LABELS) if SYN_LABELS.exists() else pd.DataFrame()
    outdir = Path(outdir).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)
    for sensor in ALL_SENSORS:
        index = build_index(sensor)
        for gpi in gpis:
            fig = _plt.figure(figsize=(8, 9))
            ax = fig.add_subplot(111)
            render(ax, index, labels, gpi, sensor)
            fig.suptitle(f"SYNTHETIC {sensor}  GPI {gpi}", fontsize=12, fontweight="bold")
            out = outdir / f"syn_{sensor}_{gpi}.png"
            fig.savefig(out, dpi=90)
            _plt.close(fig)
            print(f"wrote {out}", flush=True)


def _nomld_gpis():
    """GPIs whose label is no_mld_recorded (the No-MLD block)."""
    if not SYN_LABELS.exists():
        return []
    lab = pd.read_csv(SYN_LABELS)
    return sorted(lab[lab["no_mld_recorded"] == True]["gpi"].unique())  # noqa: E712


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-gpi", type=int, default=None)
    ap.add_argument("--dump", action="store_true",
                    help="dump MLD-present examples: 10 gpis x 4 sensors = 40 PNGs")
    ap.add_argument("--dumpNoMLD", action="store_true",
                    help="dump No-MLD examples: 6 gpis x 4 sensors = 24 PNGs")
    ap.add_argument("--dump-dir", default=str(op.OOI_ROOT / "synthetic" / "preview"))
    args = ap.parse_args()

    if args.dump:
        index = build_index()
        gpis = sorted(index)
        # 10 gpis spread across the sweep (doubled from 5) x 4 sensors = 40 images.
        fracs = (0.0, 0.11, 0.22, 0.33, 0.44, 0.55, 0.66, 0.77, 0.88, 0.98)
        sample = sorted(set(gpis[min(int(f * len(gpis)), len(gpis) - 1)] for f in fracs))
        print(f"dumping {len(sample)} gpis x {len(ALL_SENSORS)} sensors = "
              f"{len(sample) * len(ALL_SENSORS)} images: gpis={sample}")
        dump_pngs(sample, args.dump_dir)
        return

    if args.dumpNoMLD:
        nomld = _nomld_gpis()
        if not nomld:
            raise SystemExit("No No-MLD profiles found — regenerate with N_NOMLD > 0.")
        # 6 gpis spread across the No-MLD block x 4 sensors = 24 images.
        fracs = (0.0, 0.2, 0.4, 0.6, 0.8, 0.99)
        sample = sorted(set(nomld[min(int(f * len(nomld)), len(nomld) - 1)] for f in fracs))
        print(f"dumping {len(sample)} No-MLD gpis x {len(ALL_SENSORS)} sensors = "
              f"{len(sample) * len(ALL_SENSORS)} images: gpis={sample}")
        dump_pngs(sample, args.dump_dir)
        return

    Viewer(args.start_gpi)
    plt.show()


if __name__ == "__main__":
    main()
