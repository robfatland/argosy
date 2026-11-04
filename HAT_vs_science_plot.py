#!/usr/bin/env python
"""
HAT_vs_science_plot.py — visual comparison of MLD estimates for one month at Slope Base:
Holte & Talley "synth" (density/T/S) MLD vs the hand-labeled science MLDs for temperature,
salinity, and dissolved oxygen.

One line per source, markers + connecting lines, plotted against GPI (profile index) along x.
Depth axis is inverted (shallow at top). Science "No MLD" / "No Usable Data" profiles have no
depth and are drawn as small ticks along the bottom so the abstain pattern is visible.

Usage (argosy env):
    python HAT_vs_science_plot.py                 # August (default), site sb
    python HAT_vs_science_plot.py --month October
    python HAT_vs_science_plot.py --month August --site sb

Reads:
    ~/ooi/<site>/metadata/features/HAT_mld_sb_synth_<Month>_2024.csv   (gpi, MLD)
    ~/ooi/<site>/metadata/annotations/mld_labels_<site>_science_R.csv  (per-sensor labels)
Writes PNG:
    ~/ooi/<site>/visualizations/hat_vs_science_<site>_<month>_2024.png
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # headless; must precede pyplot import
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op

SENSORS = ("temperature", "salinity", "dissolvedoxygen")
# source -> (label, color, marker)
STYLE = {
    "synth":           ("Synth (Holte & Talley)", "black",     "D"),
    "temperature":     ("Temperature",            "#d62728",   "o"),
    "salinity":        ("Salinity",               "#1f77b4",   "s"),
    "dissolvedoxygen": ("Dissolved oxygen",       "#2ca02c",   "^"),
}


def load(site, month):
    feat = op.metadata_dir(site, "features")
    hat = pd.read_csv(feat / f"HAT_mld_sb_synth_{month}_2024.csv")
    hat.columns = [c.strip().lower() for c in hat.columns]
    hat = hat.rename(columns={"mld": "synth"})[["gpi", "synth"]]

    lab = pd.read_csv(op.metadata_dir(site, "annotations") / f"mld_labels_{site}_science_R.csv")
    lab["timestamp"] = pd.to_datetime(lab["timestamp"], format="ISO8601", errors="coerce")
    mnum = pd.to_datetime(month + " 2024", format="%B %Y").month
    lab = lab[(lab["timestamp"].dt.year == 2024) & (lab["timestamp"].dt.month == mnum)]

    def truthy(s):
        return s.astype(str).str.strip().str.lower().isin(("true", "1"))
    lab = lab[lab["sensor"].isin(SENSORS)].copy()
    lab["abstain"] = (truthy(lab.get("no_mld_recorded", False))
                      | truthy(lab.get("xud_recorded", False)))
    lab["mld"] = pd.to_numeric(lab["mld_depth"], errors="coerce")

    df = hat.copy()
    abstain = {}
    for s in SENSORS:
        sub = lab[lab["sensor"] == s].drop_duplicates("gpi").set_index("gpi")
        df[s] = df["gpi"].map(sub["mld"])
        abstain[s] = set(sub.index[sub["abstain"]])
        # include science-only gpis (not in HAT) so nothing is dropped
        extra = sorted(set(sub.index) - set(df["gpi"]))
        if extra:
            add = pd.DataFrame({"gpi": extra})
            df = pd.concat([df, add], ignore_index=True)
            df[s] = df["gpi"].map(sub["mld"].to_dict()).where(df[s].isna(), df[s])
    return df.sort_values("gpi").reset_index(drop=True), abstain


def main():
    ap = argparse.ArgumentParser(description="Plot HAT vs per-sensor science MLD for a month.")
    ap.add_argument("--month", default="August")
    ap.add_argument("--site", default="sb", choices=op.SITES)
    args = ap.parse_args()

    df, abstain = load(args.site, args.month)
    x = df["gpi"].values

    fig, ax = plt.subplots(figsize=(15, 7))
    for key in ("synth", *SENSORS):
        label, color, marker = STYLE[key]
        y = df[key].values.astype(float)
        m = np.isfinite(y)
        n = int(m.sum())
        ax.plot(x[m], y[m], marker=marker, color=color, lw=1.0, ms=5, alpha=0.85,
                label=f"{label} (n={n})")

    # abstain ticks for science sensors, along the bottom
    ymax = np.nanmax([np.nanmax(df[k]) for k in ("synth", *SENSORS)]) + 5
    base = ymax - 2
    for i, s in enumerate(SENSORS):
        gp = sorted(abstain[s])
        if gp:
            ax.scatter(gp, [base + i * 1.5] * len(gp), marker="x",
                       color=STYLE[s][1], s=25, alpha=0.6,
                       label=f"{STYLE[s][0]} No-MLD/XUD (n={len(gp)})")

    ax.set_ylim(ymax, 0)                      # depth increases downward
    ax.set_xlabel("GPI (profile index)")
    ax.set_ylabel("MLD depth (m)")
    ax.set_title(f"MLD comparison — {args.site} {args.month} 2024\n"
                 f"Holte & Talley (density/T/S) vs hand-labeled per-sensor science MLD")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, ncol=2, loc="lower right")
    fig.tight_layout()

    out = op.visualizations_dir(args.site) / f"hat_vs_science_{args.site}_{args.month}_2024.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"wrote {out}")
    print(f"  profiles plotted: {len(df)};  "
          + ", ".join(f"{STYLE[k][0]} {int(df[k].notna().sum())}" for k in ('synth', *SENSORS)))


if __name__ == "__main__":
    main()
