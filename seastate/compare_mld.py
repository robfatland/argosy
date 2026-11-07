"""
compare_mld.py -- first look: human-labeled MLD vs ERA5 forcing for one site-month.

Reads the 'science' MLD label CSV (dense, ~every profile for a month) and the ERA5 hourly
series from load_era5.py, then:
  1. plots MLD (per sensor) over time with wind speed, Hs, ustar^3 and turbulent heat flux;
  2. for each profile time, computes TRAILING-window means of the forcing (windows in hours)
     and prints Spearman correlations with MLD.

Times: label timestamps and ERA5 valid_time are both treated as UTC (naive).
Excluded from MLD: rows flagged no_mld_recorded or xud_recorded, and non-numeric depths.
Heat flux: qturb = latent+sensible; qsw = net solar; qnet = qsw+qlw+qturb (full budget, when the
shared radiation files exist). Correlations are printed PER SENSOR (no triple-counting).

Usage:
    python ~/argosy/seastate/compare_mld.py --site sb --month 2024-01
    python ~/argosy/seastate/compare_mld.py --site sb --month 2024-01 --sensor temperature
Output PNG: ~/ooi/<site>/visualizations/mld_vs_era5_<site>_<yyyy-mm>.png
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path("~/argosy").expanduser()))
sys.path.insert(0, str(Path("~/argosy/seastate").expanduser()))
import ooipaths as op  # noqa: E402
import load_era5 as L  # noqa: E402

WINDOWS_H = (6, 24, 72, 168)   # trailing windows for forcing means
FORCING = {                    # column -> label (radiation rows appear if the files exist)
    "wspd": "wind speed",
    "ustar3": "ustar^3 (mixing energy)",
    "swh": "Hs",
    "qturb": "q_turb latent+sens (+down)",
    "qsw": "q_sw solar (+down)",
    "qnet": "q_net total (+down)",
}
COLORS = {"temperature": "tab:red", "salinity": "tab:green", "dissolvedoxygen": "tab:blue"}


def load_labels(site, month, sensor=None):
    path = op.metadata_dir(site, "annotations") / f"mld_labels_{site}_science_R.csv"
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["timestamp"], format="ISO8601")
    df = df[df["time"].dt.strftime("%Y-%m") == month]
    bad = df["no_mld_recorded"].astype(str).eq("True") | df["xud_recorded"].astype(str).eq("True")
    df = df[~bad].copy()
    df["mld"] = pd.to_numeric(df["mld_depth"], errors="coerce")
    df = df.dropna(subset=["mld"])
    if sensor:
        df = df[df["sensor"] == sensor]
    return df.sort_values("time")


def load_forcing(site, month):
    """Hourly ERA5 as a DataFrame, padded with the previous month for trailing windows."""
    year = int(month[:4])
    ds = L.load_site_year(site, year)
    if int(month[5:7]) == 1 and year > 2014:
        ds = L.xr.concat([L.load_site_year(site, year - 1), ds], dim="time")
    cols = [c for c in ("wspd", "ustar", "swh", "qturb", "qsw", "qnet") if c in ds]
    f = ds[cols].to_dataframe()
    f["ustar3"] = f["ustar"] ** 3
    return f


def trailing(f, window_h):
    return f.rolling(f"{window_h}h", closed="right").mean()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", default="sb")
    ap.add_argument("--month", default="2024-01", help="YYYY-MM")
    ap.add_argument("--sensor", default=None, help="restrict correlations to one sensor")
    args = ap.parse_args()

    lab = load_labels(args.site, args.month)
    f = load_forcing(args.site, args.month)
    print(f"{args.site} {args.month}: {len(lab)} usable MLD labels "
          f"({lab.groupby('sensor').size().to_dict()})")

    # ---- plot -------------------------------------------------------------
    t0 = pd.Timestamp(args.month + "-01")
    t1 = t0 + pd.offsets.MonthEnd(1) + pd.Timedelta(days=1)
    fm = f.loc[t0:t1]
    fig, ax = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
    for s, g in lab.groupby("sensor"):
        ax[0].plot(g["time"], g["mld"], ".", ms=4, color=COLORS.get(s), label=s)
    ax[0].invert_yaxis()
    ax[0].set_ylabel("MLD (m)")
    ax[0].legend(loc="lower right", ncol=3, fontsize=8)
    ax[1].plot(fm.index, fm["wspd"], lw=0.8, color="k")
    ax[1].set_ylabel("wind (m/s)")
    a2 = ax[1].twinx()
    a2.plot(fm.index, fm["swh"], lw=0.8, color="tab:purple")
    a2.set_ylabel("Hs (m)", color="tab:purple")
    ax[2].plot(fm.index, fm["ustar3"], lw=0.8, color="tab:orange")
    ax[2].set_ylabel("ustar^3 (m3/s3)")
    if "qnet" in fm:
        ax[3].plot(fm.index, fm["qsw"], lw=0.6, color="gold", label="q_sw (solar)")
        ax[3].plot(fm.index, fm["qnet"], lw=0.9, color="tab:red", label="q_net")
        ax[3].legend(loc="upper right", fontsize=8, ncol=2)
    else:
        ax[3].plot(fm.index, fm["qturb"], lw=0.8, color="tab:red")
    ax[3].axhline(0, color="k", lw=0.5)
    ax[3].set_ylabel("heat flux (W/m2, +down)")
    ax[0].set_title(f"MLD vs ERA5 forcing -- {args.site} {args.month}")
    fig.tight_layout()
    out = op.visualizations_dir(args.site) / f"mld_vs_era5_{args.site}_{args.month}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=120)
    print(f"saved {out}")

    # ---- trailing-window Spearman correlations ----------------------------
    # One table per sensor (the three sensors label the SAME profiles, so pooling them would
    # triple-count and overstate significance).
    sensors = [args.sensor] if args.sensor else ["temperature", "salinity", "dissolvedoxygen"]
    for sens in sensors:
        sub = lab[lab["sensor"] == sens]
        print(f"\n[{sens}] Spearman rho: MLD vs trailing-window mean of forcing  (n={len(sub)})")
        print("(rho > 0: stronger / more-downward forcing <-> deeper MLD)")
        print("forcing".ljust(28) + "".join(f"{w:>7d}h" for w in WINDOWS_H))
        for col, name in FORCING.items():
            if col not in f:
                continue
            row = name.ljust(28)
            for w in WINDOWS_H:
                tr = trailing(f[[col]], w)[col]
                x = tr.reindex(sub["time"], method="nearest",
                               tolerance=pd.Timedelta("1h")).values
                ok = np.isfinite(x)
                rho = spearmanr(x[ok], sub["mld"].values[ok])[0] if ok.sum() > 10 else np.nan
                row += f"{rho:8.2f}"
            print(row)


if __name__ == "__main__":
    main()
