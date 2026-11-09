"""
compare_era5_mooring.py -- how well does ERA5 match the real Oregon Offshore surface mooring?

Compares ERA5 hourly fields at the Oregon Offshore (oo) site with the OOI Endurance surface
mooring CE04OSSM (same site, ~0.1 deg away):

    waves   WAVSS statistics   vs ERA5  swh (Hs), mwp (mean period), mwd (mean direction)
    wind    METBK met_wind10m  vs ERA5  wind speed (from u10, v10)
    stress  METBK met_mommflx  vs ERA5  ustar^3  (mooring: u* = sqrt(|momentum flux| / rho_water))
    solar   METBK met_netsirr_hourly vs ERA5 qsw  (net shortwave, W/m2, + down)
    IR      METBK met_netlirr  vs ERA5  qlw   (net longwave)
    fluxes  METBK met_latnflx, met_sensflx, met_heatflx vs ERA5 qlat, qsens, qnet

Inputs: the files fetched from the OOI M2M API into
    ~/ooi/oo/metadata/external/endurance/   (wavss_statistics__*.nc, metbk_hourly__*metbk_hourly*.nc)
and the ERA5 payloads loaded by load_era5.py.

Time alignment: mooring records are averaged into hour bins [h, h+1). Instantaneous ERA5 fields
(wind, waves) at time h are paired with bin h. ERA5 fluxes are accumulations over the hour ENDING at
their time stamp, so flux bin h is paired with ERA5 time h+1.

SIGN CONVENTIONS of the OOI flux variables are not verified: the summary reports a correlation and a
slope, so a negative correlation means the mooring variable has the opposite sign convention.
Fill values and physically impossible values are dropped; QARTOD flags are not applied.

Outputs: ~/ooi/oo/visualizations/era5_vs_mooring_{scatter,timeseries}_oo_<year>.png and
         ~/ooi/oo/analysis/seastate/era5_vs_mooring_oo_<year>.csv; prints a summary table.

Usage:
    python ~/argosy/seastate/compare_era5_mooring.py
    python ~/argosy/seastate/compare_era5_mooring.py --focus-start 2024-08-01 --inspect
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from scipy.stats import rankdata

sys.path.insert(0, str(Path("~/argosy").expanduser()))
sys.path.insert(0, str(Path("~/argosy/seastate").expanduser()))
import ooipaths as op  # noqa: E402
import load_era5 as L  # noqa: E402

SITE = "oo"
RHO_W = 1025.0
BAD_WORDS = ("_qc_", "qartod", "executed", "_results", "timestamp", "driver", "ingestion",
             "preferred", "port_", "serial", "string")


# --------------------------------------------------------------------------- mooring data
def ext_dir():
    return op.metadata_dir(SITE, "external") / "endurance"


def read_stream(glob_pat):
    """Concatenate all deployment files matching glob_pat into one hourly-mean DataFrame."""
    frames = []
    for fp in sorted(ext_dir().glob(glob_pat)):
        try:
            ds = xr.open_dataset(fp)
        except Exception:
            ds = xr.open_dataset(fp, decode_times=False)
            ds["time"] = pd.to_datetime(ds["time"].values, unit="s", origin="1900-01-01")
        if "obs" in ds.dims and "time" in ds:
            ds = ds.swap_dims({"obs": "time"})
        cols = {}
        for name, v in ds.data_vars.items():
            if v.dims == ("time",) and np.issubdtype(v.dtype, np.number):
                cols[name] = v.values.astype(float)
        df = pd.DataFrame(cols, index=pd.to_datetime(ds["time"].values))
        frames.append(df)
    if not frames:
        raise SystemExit(f"No files match {glob_pat} in {ext_dir()}")
    df = pd.concat(frames).sort_index()
    df = df[~df.index.duplicated(keep="first")]
    df = df.mask(df.abs() > 1e9)                       # leftover fill values
    return df.resample("1h").mean()


def find(df, *cands):
    """Find a column by exact name, then suffix, then substring; skip QC/bookkeeping columns."""
    ok = [c for c in df.columns if not any(b in c.lower() for b in BAD_WORDS)]
    for how in ("eq", "end", "in"):
        for cand in cands:
            for c in ok:
                lc, lcand = c.lower(), cand.lower()
                if (how == "eq" and lc == lcand) or (how == "end" and lc.endswith(lcand)) \
                        or (how == "in" and lcand in lc):
                    return c
    return None


# --------------------------------------------------------------------------- statistics
def stats(x, y, circular=False):
    """x = mooring, y = ERA5."""
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    n = len(x)
    if n < 10:
        return dict(n=n, bias=np.nan, rmse=np.nan, r=np.nan, rho=np.nan, slope=np.nan)
    if circular:
        d = (y - x + 180.0) % 360.0 - 180.0
        return dict(n=n, bias=float(d.mean()), rmse=float(np.sqrt((d ** 2).mean())),
                    r=np.nan, rho=np.nan, slope=np.nan)
    r = float(np.corrcoef(x, y)[0, 1]) if np.ptp(x) > 0 and np.ptp(y) > 0 else np.nan
    rho = float(np.corrcoef(rankdata(x), rankdata(y))[0, 1]) if np.isfinite(r) else np.nan
    slope = float(np.polyfit(x, y, 1)[0]) if np.ptp(x) > 0 else np.nan
    return dict(n=n, bias=float((y - x).mean()), rmse=float(np.sqrt(((y - x) ** 2).mean())),
                r=r, rho=rho, slope=slope)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument("--focus-start", default="2024-08-01",
                    help="second summary row restricted to [focus-start, end of year] (MLD label period)")
    ap.add_argument("--inspect", action="store_true", help="print the variable names found in each stream")
    args = ap.parse_args()

    wav = read_stream("wavss_statistics__*wavss_a_dcl_statistics*.nc")
    met = read_stream("metbk_hourly__*metbk_hourly_*.nc")
    if args.inspect:
        print("WAVSS columns:", ", ".join(wav.columns))
        print("METBK columns:", ", ".join(met.columns))
    print(f"mooring hours: waves {wav.index.min()} to {wav.index.max()} ({wav.notna().any(axis=1).sum()} h);"
          f" met {met.index.min()} to {met.index.max()} ({met.notna().any(axis=1).sum()} h)")

    ds = L.load_site_year(SITE, args.year)
    era = ds[["swh", "mwp", "mwd", "wspd", "ustar", "qsw", "qlw", "qlat", "qsens", "qnet"]].to_dataframe()
    era["ustar3"] = era["ustar"] ** 3

    # (label, stream df, candidate names, transform, era5 col, flux?, circular?, unit)
    spec = [
        ("Hs (significant)", wav, ["significant_wave_height"], None, "swh", False, False, "m"),
        ("Hs (Hmo)", wav, ["wave_height_hmo"], None, "swh", False, False, "m"),
        ("mean period", wav, ["mean_wave_period"], None, "mwp", False, False, "s"),
        ("mean spectral period", wav, ["mean_spectral_period"], None, "mwp", False, False, "s"),
        ("wave direction", wav, ["mean_direction"], None, "mwd", False, True, "deg"),
        ("10 m wind speed", met, ["met_wind10m"], None, "wspd", False, False, "m/s"),
        ("ustar^3", met, ["met_mommflx"], lambda v: (np.sqrt(np.abs(v) / RHO_W)) ** 3, "ustar3",
         False, False, "m3/s3"),
        ("net shortwave", met, ["met_netsirr_hourly", "met_netsirr"], None, "qsw", True, False, "W/m2"),
        ("net longwave", met, ["met_netlirr"], None, "qlw", True, False, "W/m2"),
        ("latent flux", met, ["met_latnflx"], None, "qlat", True, False, "W/m2"),
        ("sensible flux", met, ["met_sensflx"], None, "qsens", True, False, "W/m2"),
        ("net heat flux", met, ["met_heatflx"], None, "qnet", True, False, "W/m2"),
    ]
    focus = pd.Timestamp(args.focus_start)
    paired, rows = {}, []
    for label, df, cands, fn, ecol, is_flux, circ, unit in spec:
        col = find(df, *cands)
        if col is None:
            print(f"  [not found] {label}: none of {cands}")
            continue
        x = df[col].copy()
        if fn is not None:
            x = fn(x)
        if is_flux:
            x.index = x.index + pd.Timedelta(hours=1)        # hour [h,h+1) <-> ERA5 accumulation ending h+1
        pair = pd.concat({"moor": x, "era5": era[ecol]}, axis=1).dropna()
        pair = pair[(pair.index.year == args.year)]
        paired[label] = (pair, unit, circ, col)
        for nm, sub in (("all", pair), (f"since {focus.date()}", pair[pair.index >= focus])):
            s = stats(sub["moor"].values, sub["era5"].values, circ)
            rows.append({"quantity": label, "mooring_var": col, "period": nm, "unit": unit, **s})
    res = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print("\nERA5 (y) vs mooring (x). bias = mean(ERA5 - mooring); rho = Spearman; slope = OLS of ERA5 on mooring")
    print(res.round(3).to_string(index=False))

    adir = op.analysis_dir("seastate", SITE)
    adir.mkdir(parents=True, exist_ok=True)
    vdir = op.visualizations_dir(SITE)
    vdir.mkdir(parents=True, exist_ok=True)
    res.to_csv(adir / f"era5_vs_mooring_{SITE}_{args.year}.csv", index=False)

    # ---- scatter grid ----
    show = [k for k in ("Hs (significant)", "mean period", "wave direction", "10 m wind speed", "ustar^3",
                        "net shortwave", "net longwave", "net heat flux") if k in paired]
    nc = 4
    nr = int(np.ceil(len(show) / nc))
    fig, axs = plt.subplots(nr, nc, figsize=(4.2 * nc, 4 * nr), squeeze=False)
    for ax in axs.ravel():
        ax.set_visible(False)
    for ax, k in zip(axs.ravel(), show):
        pair, unit, circ, col = paired[k]
        ax.set_visible(True)
        ax.plot(pair["moor"], pair["era5"], ".", ms=2, alpha=0.25)
        lim = [np.nanmin([pair["moor"].min(), pair["era5"].min()]), np.nanmax([pair["moor"].max(), pair["era5"].max()])]
        ax.plot(lim, lim, "k-", lw=0.8)
        s = stats(pair["moor"].values, pair["era5"].values, circ)
        ax.set_title(f"{k}\nn={s['n']}  bias={s['bias']:.2f}  rmse={s['rmse']:.2f}"
                     + ("" if circ else f"  r={s['r']:.2f}"), fontsize=9)
        ax.set_xlabel(f"mooring {col} ({unit})", fontsize=8)
        ax.set_ylabel(f"ERA5 ({unit})", fontsize=8)
        ax.grid(alpha=0.3)
    fig.suptitle(f"ERA5 vs CE04OSSM mooring, Oregon Offshore, {args.year}", y=1.0)
    fig.tight_layout()
    fig.savefig(vdir / f"era5_vs_mooring_scatter_{SITE}_{args.year}.png", dpi=110)
    plt.close(fig)

    # ---- time series in the MLD label period ----
    ts = [k for k in ("Hs (significant)", "10 m wind speed", "net shortwave", "net heat flux") if k in paired]
    if ts:
        fig, axs = plt.subplots(len(ts), 1, figsize=(12, 2.8 * len(ts)), sharex=True, squeeze=False)
        for ax, k in zip(axs.ravel(), ts):
            pair, unit, circ, col = paired[k]
            sub = pair[pair.index >= focus]
            daily = k in ("net shortwave", "net heat flux")
            if daily:
                sub = sub.resample("1D").mean()
            ax.plot(sub.index, sub["moor"], color="k", lw=1.0, label="mooring")
            ax.plot(sub.index, sub["era5"], color="tab:red", lw=1.0, label="ERA5")
            ax.set_ylabel(f"{k}\n({unit}{', daily mean' if daily else ''})", fontsize=8)
            ax.grid(alpha=0.3)
        axs[0, 0].legend(ncol=2, fontsize=8)
        fig.tight_layout()
        fig.savefig(vdir / f"era5_vs_mooring_timeseries_{SITE}_{args.year}.png", dpi=110)
        plt.close(fig)
    print(f"\nsaved figures to {vdir}\nsaved table to {adir / f'era5_vs_mooring_{SITE}_{args.year}.csv'}")


if __name__ == "__main__":
    main()
