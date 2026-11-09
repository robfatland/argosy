"""
compare_sp_argo.py -- three small adjoint plots comparing the OOI Regional Cabled Array shallow
profiler (SP) with a typical GO-BGC (Biogeochemical-Argo) float.

  left   : samples per meter (x)       vs profiles per day (y)          [log, log]
  middle : number of sensors (x)       vs mission duration, years (y)   [linear]
  right  : area covered, km^2 (x, log) vs depth, m (y, 0 at the top)

Each axis is ticked twice, once at the SP value (blue) and once at the Argo value (orange), and
the two symbols are labeled. Guides run from each symbol to its ticks.

The numbers, their sources, and which are GUESSES are in the dict below and in README.md. The
figure title says "(some guesses made)" until every guess is replaced by a sourced value.

Output: ~/argosy/images/sp_vs_argo.png   (images/ holds copies of key charts for the repo)

Usage:  python ~/argosy/argo/compare_sp_argo.py [--out PATH]
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator

SP_COL, AR_COL = "#1f3a93", "#d9541e"

# value, plus how sure we are: "src" = sourced, "guess" = placeholder to refine
V = {
    # shallow profiler
    "sp_samples_per_m": (22.0, "src"),        # measured via M2M: GPI 18478, 4020 samples / 182 m = 22.1
    "sp_profiles_per_day": (9.0, "src"),
    "sp_sensors": (17, "src"),                # per Rob: ADCP counted twice
    "sp_years": (11.0, "src"),                # 2015 to 2026, continuing
    "sp_area_km2": (3.14159 * 0.005 ** 2, "src"),   # disc 10 m across: pi * (5 m)^2 = 78.5 m^2
    "sp_depth_m": (200.0, "src"),
    # GO-BGC Argo
    "ar_samples_per_m": (0.5, "guess"),       # ~2 m vertical spacing over a 2000 m profile
    "ar_profiles_per_day": (0.1, "src"),      # one profile every 10 days
    "ar_sensors": (6, "src"),                 # CTD + O2, NO3, pH, chlorophyll, backscatter (floats near our sites)
    "ar_years": (5.0, "guess"),               # nominal lifetime of a BGC float
    "ar_area_one_km2": (3.0e5, "guess"),      # footprint of one float over its life (~500 km x 600 km)
    "ar_area_all_km2": (3.6e8, "src"),        # global ocean surface area (the array aims to be global)
    "ar_depth_m": (2000.0, "src"),
    "ar_n_floats": (500, "src"),              # funded GO-BGC array size
}


def val(k):
    return V[k][0]


def sci(v):
    m, e = f"{v:.1e}".split("e")
    return rf"${float(m):g}\times10^{{{int(e)}}}$"


def two_ticks(ax, which, items, rotation=0):
    """items = [(value, label, color), ...]; tick the axis only at those values."""
    items = sorted(items, key=lambda t: t[0])
    pos, lab, col = zip(*items)
    if which == "x":
        ax.set_xticks(pos)
        ax.set_xticklabels(lab, rotation=rotation, ha="right" if rotation else "center")
        ax.xaxis.set_minor_locator(NullLocator())
        labels = ax.get_xticklabels()
    else:
        ax.set_yticks(pos)
        ax.set_yticklabels(lab)
        ax.yaxis.set_minor_locator(NullLocator())
        labels = ax.get_yticklabels()
    for t, c in zip(labels, col):
        t.set_color(c)
        t.set_fontweight("bold")


def guides(ax, x, y, color, x0, y0):
    ax.plot([x, x], [y0, y], ":", color=color, lw=1.4, zorder=1)
    ax.plot([x0, x], [y, y], ":", color=color, lw=1.4, zorder=1)


def tag(ax, x, y, text, color, dx=10, dy=8, ha="left"):
    ax.annotate(text, (x, y), textcoords="offset points", xytext=(dx, dy), fontsize=14,
                fontweight="bold", color=color, ha=ha)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(Path("~/argosy/images/sp_vs_argo.png").expanduser()))
    args = ap.parse_args()

    W, H = 9.9, 5.2                                    # inches
    fig = plt.figure(figsize=(W, H))
    box = 2.0                                          # each plot is 2 x 2 inches
    lefts = [0.95, 4.15, 7.35]
    axs = [fig.add_axes([l / W, 1.9 / H, box / W, box / H]) for l in lefts]
    for ax in axs:
        ax.tick_params(labelsize=12, length=5)
        ax.xaxis.label.set_size(13)
        ax.yaxis.label.set_size(13)

    # ---------------- left: samples per meter vs profiles per day ----------------
    ax = axs[0]
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(0.1, 100)
    ax.set_ylim(0.03, 30)
    sx, sy = val("sp_samples_per_m"), val("sp_profiles_per_day")
    ax_, ay_ = val("ar_samples_per_m"), val("ar_profiles_per_day")
    guides(ax, sx, sy, SP_COL, 0.1, 0.03)
    guides(ax, ax_, ay_, AR_COL, 0.1, 0.03)
    ax.plot(sx, sy, "^", ms=12.6, color=SP_COL, zorder=3)
    ax.plot(ax_, ay_, "o", ms=9.8, color=AR_COL, zorder=3)
    tag(ax, sx, sy, "SP", SP_COL, dx=-8, dy=10, ha="right")
    tag(ax, ax_, ay_, "Argo", AR_COL, dx=10, dy=10)
    two_ticks(ax, "x", [(sx, f"{sx:g}", SP_COL), (ax_, f"{ax_:g}", AR_COL)])
    two_ticks(ax, "y", [(sy, f"{sy:g}", SP_COL), (ay_, f"{ay_:g}", AR_COL)])
    ax.set_xlabel("samples per meter")
    ax.set_ylabel("profiles per day")

    # ---------------- middle: sensors vs mission duration ----------------
    ax = axs[1]
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 15)
    sx, sy = val("sp_sensors"), val("sp_years")
    ax_, ay_ = val("ar_sensors"), val("ar_years")
    guides(ax, sx, sy, SP_COL, 0, 0)
    guides(ax, ax_, ay_, AR_COL, 0, 0)
    ax.plot(sx, sy, "^", ms=12.6, color=SP_COL, zorder=3)
    ax.plot(ax_, ay_, "o", ms=9.8, color=AR_COL, zorder=3)
    for xx, yy, cc in ((sx, sy, SP_COL), (ax_, ay_, AR_COL)):   # dotted "continues" tails
        ax.plot([xx, xx], [yy + 0.8, yy + 3.2], linestyle=(0, (0.1, 2.6)), lw=4, color=cc,
                dash_capstyle="round")
    tag(ax, sx, sy, "SP", SP_COL, dx=-8, dy=-4, ha="right")
    tag(ax, ax_, ay_, "Argo", AR_COL, dx=10, dy=8)
    two_ticks(ax, "x", [(sx, f"{sx:g}", SP_COL), (ax_, f"{ax_:g}", AR_COL)])
    two_ticks(ax, "y", [(sy, f"{sy:g}", SP_COL), (ay_, f"{ay_:g}", AR_COL)])
    ax.set_xlabel("number of sensors")
    ax.set_ylabel("mission (years)")

    # ---------------- right: area vs depth ----------------
    ax = axs[2]
    ax.set_xscale("log")
    ax.set_xlim(1e-6, 1e10)
    ax.set_ylim(2450, 0)                                # 0 at the top; room for labels below
    a_sp, d_sp = val("sp_area_km2"), val("sp_depth_m")
    a_1, a_all, d_ar = val("ar_area_one_km2"), val("ar_area_all_km2"), val("ar_depth_m")
    ax.plot([a_sp, a_sp], [0, d_sp], lw=7, color=SP_COL, solid_capstyle="butt", zorder=3)
    ax.plot([a_1, a_1], [0, d_ar], lw=7, color=AR_COL, solid_capstyle="butt", zorder=3)
    ax.plot([a_all, a_all], [0, d_ar], lw=7, color=AR_COL, solid_capstyle="butt", alpha=0.55,
            zorder=3)
    ax.annotate("SP", (a_sp, d_sp), textcoords="offset points", xytext=(8, 4), fontsize=14,
                fontweight="bold", color=SP_COL)
    for a_x, lab in ((a_1, "1"), (a_all, f"{val('ar_n_floats')}")):   # float counts, under the stripes
        ax.annotate(lab, (a_x, d_ar), textcoords="offset points", xytext=(0, -5), fontsize=11,
                    color="black", ha="center", va="top")
    two_ticks(ax, "x", [(a_sp, sci(a_sp), SP_COL), (a_1, sci(a_1), AR_COL),
                        (a_all, sci(a_all), AR_COL)], rotation=40)
    two_ticks(ax, "y", [(0, "0", "black"), (d_sp, f"{d_sp:g}", SP_COL), (d_ar, f"{d_ar:g}", AR_COL)])
    ax.set_xlabel("area (km$^2$)")
    ax.set_ylabel("depth (m)")

    fig.suptitle("Argo and Shallow Profiler: Complementary Operation", fontsize=16, y=0.97)
    note = ("SP (blue triangle): 1 Hz CTD at 4.5 cm/s ascent = 22 samples/m (measured); 9 profiles/day; 17 sensors (ADCP "
            "counted twice); 11 years and continuing (dots); footprint = disc 10 m across; 0-200 m.\n"
            "Argo (orange circle): profile every 10 days to 2000 m; 6 sensors (CTD + oxygen, nitrate, pH, "
            "chlorophyll, backscatter); 500-float array (right panel: 1 float, and 500).\n"
            "GUESSES: Argo 0.5 samples/m, 5-year life, and 3e5 km$^2$ for one float's lifetime footprint; "
            "'all floats' area = global ocean, 3.6e8 km$^2$.")
    fig.text(0.02, 0.02, note, fontsize=7.5, va="bottom", ha="left", wrap=True)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
