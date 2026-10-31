"""
mld_coverage.py — "MLD Coverage" chart: where in time do MLD labels exist?

9 stacked rows sharing one time axis: sites oo / sb / ab (top to bottom), each with
temperature / salinity / dissolved oxygen. The y axis carries NO meaning: each label source
gets its own fixed micro-lane within a row so sources can coexist without overplotting.

Marker encoding (color = source):
    filled circle  = MLD value recorded
    hollow circle  = No MLD (no_mld_recorded)
    small x        = No Usable Data (xud_recorded)

Label sources live in SOURCES below; adding one (e.g. Holte & Talley 2009 results, cyan)
is a single registry entry once its output location is decided.

Usage (headless, Agg):
    source ~/miniconda3/etc/profile.d/conda.sh && conda activate argosy
    python ~/argosy/vis/mld_coverage.py

Output: ~/ooi/visualizations/mld_coverage.png  (+ copy in ~/argosy/images/)
"""

import matplotlib
matplotlib.use("Agg")  # headless; must precede pyplot import
import matplotlib.pyplot as plt

import shutil
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op

# == Configuration =============================================================

TITLE = "MLD Coverage"
T_START = pd.Timestamp("2014-12-01")
T_END = pd.Timestamp(datetime.now().date())
WHO = "R"

SITE_ORDER = ("oo", "sb", "ab")  # top -> bottom
SENSORS = (("temperature", "Temperature"),
           ("salinity", "Salinity"),
           ("dissolvedoxygen", "Dissolved Oxygen"))

# Label-source registry. `path(site)` returns the label CSV for that site (may not exist).
# `lane` is the micro-vertical offset within each row (y has no physical meaning).
SOURCES = [
    {"name": "training", "color": "green", "lane": 0.0,
     "path": lambda s: op.metadata_dir(s, "annotations") / f"mld_labels_{s}_block05_{WHO}.csv"},
    {"name": "science", "color": "blue", "lane": 1.0,
     "path": lambda s: op.metadata_dir(s, "annotations") / f"mld_labels_{s}_science_{WHO}.csv"},
    # {"name": "holte_talley", "color": "cyan", "lane": 2.0,
    #  "path": lambda s: <TBD>},
]

MARKER_SIZE = 6      # scatter area (pt^2); dense 11-yr rows need small markers
LANE_PAD = 0.6       # y padding above/below the outermost lanes

OUT_DIR = op.OOI_ROOT / "visualizations"
OUT_PNG = OUT_DIR / "mld_coverage.png"
REPO_COPY = op.ARGOSY_ROOT / "images" / "mld_coverage.png"


# == Data ======================================================================

def _truthy(col):
    """CSV booleans arrive as bool or 'True'/'False' strings (seeded rows); normalize."""
    return col.astype(str).str.strip().str.lower().isin(("true", "1"))


def load_source(src, site):
    """Return a DataFrame (timestamp, sensor, state) for one source+site, or None."""
    p = src["path"](site)
    if not p.exists():
        return None
    df = pd.read_csv(p)
    if "who" in df.columns:
        df = df[df["who"].astype(str) == WHO]
    # Science CSVs mix date-only seeded rows (2024-01-22T00:00:00) with full-precision
    # science-mode rows (2024-01-30T15:48:00.692126208); ISO8601 parses both. Without it
    # pandas infers one format from row 0 and coerces the rest to NaT.
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601", errors="coerce")
    n_bad = df["timestamp"].isna().sum()
    if n_bad:
        print(f"WARNING: {p.name}: {n_bad} unparseable timestamps dropped")
    df = df.dropna(subset=["timestamp"])
    no_mld = _truthy(df["no_mld_recorded"]) if "no_mld_recorded" in df else False
    xud = _truthy(df["xud_recorded"]) if "xud_recorded" in df else False
    state = pd.Series("value", index=df.index)
    state[no_mld] = "no_mld"
    state[xud] = "xud"  # xud takes precedence over no_mld if both set
    df["state"] = state
    return df[["timestamp", "sensor", "state"]]


# == Plot ======================================================================

def main():
    n_rows = len(SITE_ORDER) * len(SENSORS)
    fig, axes = plt.subplots(n_rows, 1, figsize=(16, 11), sharex=True)
    fig.suptitle(TITLE, fontsize=16, fontweight="bold")

    lanes = [s["lane"] for s in SOURCES]
    counts = []  # (site, sensor, source, state, n) for the console summary

    data = {(src["name"], site): load_source(src, site)
            for src in SOURCES for site in SITE_ORDER}

    row = 0
    for site in SITE_ORDER:
        for key, label in SENSORS:
            ax = axes[row]
            for src in SOURCES:
                df = data[(src["name"], site)]
                if df is None:
                    continue
                d = df[df["sensor"] == key]
                y = src["lane"]
                c = src["color"]
                for state, kw in (
                        ("value", dict(marker="o", facecolors=c, edgecolors=c)),
                        ("no_mld", dict(marker="o", facecolors="none", edgecolors=c)),
                        ("xud", dict(marker="x", c=c))):
                    t = d.loc[d["state"] == state, "timestamp"]
                    counts.append((site, key, src["name"], state, len(t)))
                    if len(t):
                        ax.scatter(t, [y] * len(t), s=MARKER_SIZE, linewidths=0.6, **kw)

            ax.set_ylim(min(lanes) - LANE_PAD, max(lanes) + LANE_PAD)
            ax.set_yticks([])
            ax.set_ylabel(f"{site}  {label}", rotation=0, ha="right", va="center", fontsize=9)
            ax.grid(axis="x", alpha=0.3)
            # Visually separate site groups: heavier line under the last row of a site.
            if key == SENSORS[-1][0] and row < n_rows - 1:
                ax.spines["bottom"].set_linewidth(2.0)
            row += 1

    axes[-1].set_xlim(T_START, T_END)
    axes[-1].set_xlabel("Time (UTC)")

    # Legend: color = source, marker = label state.
    handles = [plt.Line2D([], [], ls="", marker="o", color=s["color"], label=s["name"])
               for s in SOURCES]
    handles += [
        plt.Line2D([], [], ls="", marker="o", color="k", label="MLD value"),
        plt.Line2D([], [], ls="", marker="o", mfc="none", color="k", label="No MLD"),
        plt.Line2D([], [], ls="", marker="x", color="k", label="No usable data"),
    ]
    fig.legend(handles=handles, loc="upper right", ncol=len(handles), fontsize=9, frameon=False)

    fig.tight_layout(rect=(0.03, 0, 1, 0.95))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PNG, dpi=150)
    REPO_COPY.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(OUT_PNG, REPO_COPY)
    print(f"wrote {OUT_PNG}\ncopied -> {REPO_COPY}")

    # Console summary: per row, per source, value / no_mld / xud counts.
    summ = (pd.DataFrame(counts, columns=["site", "sensor", "source", "state", "n"])
            .pivot_table(index=["site", "sensor", "source"], columns="state",
                         values="n", aggfunc="sum", fill_value=0))
    print("\nLabel counts (who=%s):" % WHO)
    print(summ.to_string())

    # Spot check: science coverage in a given month (Jan 2024 sb is the first test).
    sci = data[("science", "sb")]
    if sci is not None:
        jan = sci[(sci["timestamp"] >= "2024-01-01") & (sci["timestamp"] < "2024-02-01")]
        print("\nsb science, Jan 2024: rows per sensor:",
              jan.groupby("sensor").size().to_dict(),
              "| distinct days:", jan["timestamp"].dt.date.nunique())


if __name__ == "__main__":
    main()
