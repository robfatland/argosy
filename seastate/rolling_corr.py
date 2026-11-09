"""
rolling_corr.py -- sliding-window correlation of human-labeled MLD with ERA5 forcing, as a
function of DATE, with confidence bands, partial correlations, and a check of how the two
forcings relate to each other.

For each window center date c, take all usable MLD labels with time in [c-W/2, c+W/2) and, PER
SENSOR (T, S, DO label the same profiles, so they are kept separate), compute for q_net and
ustar^3 (trailing means over the LAG hours before each profile; default lags 72 and 168 h):

  rho          Spearman rank correlation of MLD with the forcing.
  ci_lo, ci_hi 90% confidence interval from a DAY-BLOCK BOOTSTRAP: whole label-days are resampled
               with replacement (labels within a day are strongly dependent, so days, not labels,
               are the independent units). Slow-moving forcing is still autocorrelated ACROSS days,
               so the bands are, if anything, a bit too narrow: treat them as a lower bound on
               the uncertainty.
  partial      Spearman PARTIAL correlation of MLD with this forcing while controlling for the
               other forcing (q_net | ustar^3 and ustar^3 | q_net).

Also saved per window: rho between q_net and ustar^3 themselves (do storms come with weak
cooling?), computed on the distinct profile times in the window.

rho < 0 for q_net  : more net heat LOSS over the prior days goes with a DEEPER MLD.
rho > 0 for ustar^3: more wind stirring over the prior days goes with a DEEPER MLD.
Windows with fewer than --min-n labels give NaN.

Outputs (<site> = sb by default), in ~/ooi/<site>/analysis/seastate/ and .../visualizations/
    mld_forcing_rolling_<tag>.csv         per window x sensor x forcing x lag
    mld_forcing_predictors_<tag>.csv      q_net vs ustar^3 per window x lag
    mld_forcing_rolling_<tag>.png         rho for all sensors/lags (as before)
    mld_forcing_rolling_ci_<tag>.png      rho with 90% bands at --ci-lag, one panel per sensor
    mld_forcing_rolling_partial_<tag>.png forcing-vs-forcing correlation and the partials

Usage
    python ~/argosy/seastate/rolling_corr.py --site sb --start 2024-08-01 --end 2024-12-31
    python ~/argosy/seastate/rolling_corr.py --boot 0          # skip the bootstrap (fast)
    python ~/argosy/seastate/rolling_corr.py --window-days 28 --ci-lag 72
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import rankdata

sys.path.insert(0, str(Path("~/argosy").expanduser()))
sys.path.insert(0, str(Path("~/argosy/seastate").expanduser()))
import ooipaths as op  # noqa: E402
import load_era5 as L  # noqa: E402

SENSORS = ("temperature", "salinity", "dissolvedoxygen")
COLORS = {"temperature": "red", "salinity": "green", "dissolvedoxygen": "blue"}
FORCINGS = {"qnet": "q_net (net heat flux, +down)", "ustar3": "ustar^3 (wind mixing energy)"}
OTHER = {"qnet": "ustar3", "ustar3": "qnet"}


def _true(s):
    return s.astype(str).str.strip().str.lower().eq("true")


def load_labels(site, start, end):
    path = op.metadata_dir(site, "annotations") / f"mld_labels_{site}_science_R.csv"
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["timestamp"], format="ISO8601")
    df = df[(df["time"] >= start) & (df["time"] < end) & df["sensor"].isin(SENSORS)]
    df = df[~(_true(df["no_mld_recorded"]) | _true(df["xud_recorded"]))].copy()
    df["mld"] = pd.to_numeric(df["mld_depth"], errors="coerce")
    return df.dropna(subset=["mld"]).sort_values("time").reset_index(drop=True)


def load_forcing(site, start, end):
    years = range(start.year, end.year + 1)
    parts = [L.load_site_year(site, y) for y in years]
    ds = L.xr.concat(parts, dim="time") if len(parts) > 1 else parts[0]
    if "qnet" not in ds:
        raise SystemExit("qnet not available: radiation files missing for these years.")
    f = ds[["ustar", "qnet"]].to_dataframe()
    f["ustar3"] = f["ustar"] ** 3
    return f[["qnet", "ustar3"]]


def attach_trailing(lab, f, lags):
    """Add columns '<forcing>_<lag>' = trailing mean of the forcing over the previous lag hours."""
    for lag in lags:
        tr = f.rolling(f"{lag}h", closed="right").mean()
        for col in FORCINGS:
            lab[f"{col}_{lag}"] = tr[col].reindex(
                lab["time"], method="nearest", tolerance=pd.Timedelta("1h")).values
    return lab


def sp(x, y):
    """Spearman rho (rank correlation); NaN if undefined."""
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3:
        return np.nan
    x, y = x[ok], y[ok]
    if np.ptp(x) == 0 or np.ptp(y) == 0:
        return np.nan
    return float(np.corrcoef(rankdata(x), rankdata(y))[0, 1])


def partial(r_xy, r_xz, r_yz):
    """Partial correlation of x,y given z from the three pairwise correlations."""
    d = (1 - r_xz ** 2) * (1 - r_yz ** 2)
    if not np.isfinite(d) or d <= 1e-12:
        return np.nan
    return (r_xy - r_xz * r_yz) / np.sqrt(d)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", default="sb")
    ap.add_argument("--start", default="2024-08-01")
    ap.add_argument("--end", default="2024-12-31", help="inclusive")
    ap.add_argument("--window-days", type=float, default=21.0)
    ap.add_argument("--step-days", type=float, default=1.0)
    ap.add_argument("--lags", default="72,168", help="trailing-mean lags in hours")
    ap.add_argument("--ci-lag", type=int, default=168, help="lag used in the CI and partial figures")
    ap.add_argument("--min-n", type=int, default=30)
    ap.add_argument("--boot", type=int, default=200, help="bootstrap resamples (0 = skip)")
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    start = pd.Timestamp(args.start)
    end = pd.Timestamp(args.end) + pd.Timedelta(days=1)
    lags = [int(v) for v in args.lags.split(",")]
    if args.ci_lag not in lags:
        raise SystemExit(f"--ci-lag {args.ci_lag} must be one of --lags {lags}")
    W = pd.Timedelta(days=args.window_days)
    rng = np.random.default_rng(args.seed)

    lab = load_labels(args.site, start, end)
    f = load_forcing(args.site, start - pd.Timedelta(days=8), end)   # pad for the 168 h lag
    lab = attach_trailing(lab, f, lags)
    print(f"{args.site}: {len(lab)} usable labels, {start.date()} to {(end - pd.Timedelta(days=1)).date()}")

    t = lab["time"].values
    sens = lab["sensor"].values
    mld = lab["mld"].values
    day = lab["time"].dt.normalize().values.astype("datetime64[D]").astype(np.int64)
    X = {(c, lag): lab[f"{c}_{lag}"].values for c in FORCINGS for lag in lags}
    keys = list(X)

    centers = pd.date_range(start + W / 2, end - W / 2, freq=f"{args.step_days}D")
    rows, prow = [], []
    for ci, c in enumerate(centers):
        lo, hi = np.datetime64(c - W / 2), np.datetime64(c + W / 2)
        inwin = (t >= lo) & (t < hi)
        # forcing-vs-forcing on distinct profile times (not per sensor)
        _, first = np.unique(t[inwin], return_index=True)
        widx = np.where(inwin)[0][first]
        for lag in lags:
            prow.append({"center": c, "lag_h": lag,
                         "rho_qnet_ustar3": sp(X[("qnet", lag)][widx], X[("ustar3", lag)][widx]),
                         "n_days": len(np.unique(day[widx]))})
        for s in SENSORS:
            idx = np.where(inwin & (sens == s))[0]
            n = len(idx)
            nd = len(np.unique(day[idx])) if n else 0
            if n < args.min_n:
                for col in FORCINGS:
                    for lag in lags:
                        rows.append({"center": c, "sensor": s, "forcing": col, "lag_h": lag,
                                     "rho": np.nan, "ci_lo": np.nan, "ci_hi": np.nan,
                                     "partial": np.nan, "n": n, "n_days": nd})
                continue
            y = mld[idx]
            Xi = {k: X[k][idx] for k in keys}
            base = {k: sp(Xi[k], y) for k in keys}
            cross = {lag: sp(Xi[("qnet", lag)], Xi[("ustar3", lag)]) for lag in lags}
            lo_ci = {k: np.nan for k in keys}
            hi_ci = {k: np.nan for k in keys}
            if args.boot > 0 and nd >= 5:
                ud, inv = np.unique(day[idx], return_inverse=True)
                groups = [np.where(inv == k)[0] for k in range(len(ud))]
                bt = np.empty((args.boot, len(keys)))
                for b in range(args.boot):
                    pick = rng.integers(0, len(ud), len(ud))
                    ii = np.concatenate([groups[k] for k in pick])
                    yy = y[ii]
                    for j, k in enumerate(keys):
                        bt[b, j] = sp(Xi[k][ii], yy)
                with np.errstate(all="ignore"):
                    lo5, hi95 = np.nanpercentile(bt, [5, 95], axis=0)
                lo_ci = dict(zip(keys, lo5))
                hi_ci = dict(zip(keys, hi95))
            for col in FORCINGS:
                for lag in lags:
                    k, ko = (col, lag), (OTHER[col], lag)
                    rows.append({"center": c, "sensor": s, "forcing": col, "lag_h": lag,
                                 "rho": base[k], "ci_lo": lo_ci[k], "ci_hi": hi_ci[k],
                                 "partial": partial(base[k], cross[lag], base[ko]),
                                 "n": n, "n_days": nd})
        if ci % 20 == 0:
            print(f"  window {ci + 1}/{len(centers)} ({c.date()})", flush=True)

    res, pred = pd.DataFrame(rows), pd.DataFrame(prow)
    tag = f"{args.site}_{start:%Y-%m-%d}_{(end - pd.Timedelta(days=1)):%Y-%m-%d}"
    adir = op.analysis_dir("seastate", args.site)
    adir.mkdir(parents=True, exist_ok=True)
    vdir = op.visualizations_dir(args.site)
    vdir.mkdir(parents=True, exist_ok=True)
    res.to_csv(adir / f"mld_forcing_rolling_{tag}.csv", index=False)
    pred.to_csv(adir / f"mld_forcing_predictors_{tag}.csv", index=False)

    # ---------------- figure 1: all sensors and lags ----------------
    fig, ax = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    styles = {lags[0]: "-", lags[-1]: "--"}
    for k, col in enumerate(FORCINGS):
        for s in SENSORS:
            for lag in lags:
                g = res[(res["forcing"] == col) & (res["sensor"] == s) & (res["lag_h"] == lag)]
                ax[k].plot(g["center"], g["rho"], styles.get(lag, ":"), color=COLORS[s], lw=1.3,
                           label=f"{s[:4]} {lag} h" if k == 0 else None)
        ax[k].axhline(0, color="k", lw=0.6)
        ax[k].set_ylim(-1, 1)
        ax[k].set_ylabel(f"Spearman rho\nMLD vs {col}")
        ax[k].set_title(FORCINGS[col], fontsize=9, loc="left")
        ax[k].grid(alpha=0.3)
    ax[0].legend(ncol=3, fontsize=7, loc="lower left")
    for s in SENSORS:
        g = res[(res["forcing"] == "qnet") & (res["sensor"] == s) & (res["lag_h"] == lags[0])]
        ax[2].plot(g["center"], g["n"], color=COLORS[s], lw=1.3, label=f"{s[:4]} n")
        ax[2].plot(g["center"], g["n_days"], color=COLORS[s], lw=1.0, ls=":")
    ax[2].axhline(args.min_n, color="gray", lw=0.6, ls="--")
    ax[2].set_ylabel("labels in window\n(solid n, dotted days)")
    ax[2].legend(ncol=3, fontsize=7)
    ax[2].grid(alpha=0.3)
    ax[0].set_title(f"{args.site}: {args.window_days:g}-day sliding window; blank where n < {args.min_n}",
                    fontsize=10)
    fig.tight_layout()
    fig.savefig(vdir / f"mld_forcing_rolling_{tag}.png", dpi=120)
    plt.close(fig)

    # ---------------- figure 2: rho with 90% bands ----------------
    fig, ax = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    fcol = {"qnet": "tab:red", "ustar3": "tab:blue"}
    for k, s in enumerate(SENSORS):
        for col in FORCINGS:
            g = res[(res["forcing"] == col) & (res["sensor"] == s) & (res["lag_h"] == args.ci_lag)]
            ax[k].plot(g["center"], g["rho"], color=fcol[col], lw=1.5, label=col)
            ax[k].fill_between(g["center"], g["ci_lo"], g["ci_hi"], color=fcol[col], alpha=0.18, lw=0)
        ax[k].axhline(0, color="k", lw=0.6)
        ax[k].set_ylim(-1, 1)
        ax[k].set_ylabel(f"{s}\nrho")
        ax[k].grid(alpha=0.3)
    ax[0].legend(ncol=2, fontsize=8, loc="lower left")
    ax[0].set_title(f"{args.site}: rho at {args.ci_lag} h lag with 90% day-block bootstrap bands "
                    f"({args.boot} resamples); a band that excludes 0 is a robust sign", fontsize=9)
    fig.tight_layout()
    fig.savefig(vdir / f"mld_forcing_rolling_ci_{tag}.png", dpi=120)
    plt.close(fig)

    # ---------------- figure 3: forcing-vs-forcing and partials ----------------
    fig, ax = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    for lag in lags:
        g = pred[pred["lag_h"] == lag]
        ax[0].plot(g["center"], g["rho_qnet_ustar3"], styles.get(lag, ":"), color="k", lw=1.4,
                   label=f"{lag} h")
    ax[0].axhline(0, color="k", lw=0.6)
    ax[0].set_ylim(-1, 1)
    ax[0].set_ylabel("rho(q_net, ustar^3)\nbetween the forcings")
    ax[0].legend(fontsize=8)
    ax[0].grid(alpha=0.3)
    ax[0].set_title("Do the two forcings move together? (positive: windy weeks are also warmer / less cooling)",
                    fontsize=9, loc="left")
    for k, col in ((1, "qnet"), (2, "ustar3")):
        for s in SENSORS:
            g = res[(res["forcing"] == col) & (res["sensor"] == s) & (res["lag_h"] == args.ci_lag)]
            ax[k].plot(g["center"], g["partial"], color=COLORS[s], lw=1.3, label=s[:4])
            ax[k].plot(g["center"], g["rho"], color=COLORS[s], lw=0.7, ls=":")
        ax[k].axhline(0, color="k", lw=0.6)
        ax[k].set_ylim(-1, 1)
        ax[k].set_ylabel(f"MLD vs {col}\n(solid: partial, dotted: plain)")
        ax[k].set_title(f"{col} controlling for {OTHER[col]} ({args.ci_lag} h lag)", fontsize=9, loc="left")
        ax[k].grid(alpha=0.3)
    ax[1].legend(ncol=3, fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(vdir / f"mld_forcing_rolling_partial_{tag}.png", dpi=120)
    plt.close(fig)

    # ---------------- printed summaries ----------------
    res["month"] = res["center"].dt.strftime("%Y-%m")
    pred["month"] = pred["center"].dt.strftime("%Y-%m")
    v = res.dropna(subset=["rho"])
    print("\nMean rolling rho by month (all lags)")
    print(v.groupby(["forcing", "lag_h", "sensor", "month"])["rho"].mean().unstack("month").round(2).to_string())
    if args.boot > 0:
        w = v[v["lag_h"] == args.ci_lag].dropna(subset=["ci_lo", "ci_hi"]).copy()
        w["sig_neg"] = w["ci_hi"] < 0
        w["sig_pos"] = w["ci_lo"] > 0
        print(f"\nShare of windows whose 90% band excludes zero, by month ({args.ci_lag} h lag)")
        print("  (neg = band entirely below 0, pos = entirely above 0)")
        for flag in ("sig_neg", "sig_pos"):
            print(f"  {flag}:")
            print(w.groupby(["forcing", "sensor", "month"])[flag].mean().unstack("month").round(2).to_string())
    print(f"\nMean partial correlation by month ({args.ci_lag} h lag): forcing | the other forcing")
    q = v[v["lag_h"] == args.ci_lag]
    print(q.groupby(["forcing", "sensor", "month"])["partial"].mean().unstack("month").round(2).to_string())
    print("\nMean rho(q_net, ustar^3) between the forcings, by month")
    print(pred.dropna(subset=["rho_qnet_ustar3"]).groupby(["lag_h", "month"])["rho_qnet_ustar3"]
          .mean().unstack("month").round(2).to_string())
    print(f"\nsaved CSVs to {adir}\nsaved figures to {vdir} (tag {tag})")


if __name__ == "__main__":
    main()
