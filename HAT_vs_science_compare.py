#!/usr/bin/env python
"""
HAT_vs_science_compare.py — compare Holte & Talley (density/T/S synthesized) MLD against the
hand-labeled science-mode MLDs (per sensor: temperature, salinity, dissolvedoxygen) for a given
month at Slope Base.

HAT gives ONE MLD per profile (gpi). The science labels give one MLD per sensor. So per gpi we
compare the single HAT value against up to three sensor values. Science rows that are "No MLD"
(no_mld_recorded) or "No Usable Data" (xud_recorded) have no depth and are reported separately,
not treated as zero.

Usage:
    python HAT_vs_science_compare.py --month August        # default site sb, 2024
    python HAT_vs_science_compare.py --month October --site sb

Writes a tidy join to  ~/ooi/<site>/metadata/features/hat_vs_science_<site>_<month>_2024.csv
and prints a per-sensor summary.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op

SENSORS = ("temperature", "salinity", "dissolvedoxygen")


def load_hat(site, month):
    p = op.metadata_dir(site, "features") / f"HAT_mld_sb_synth_{month}_2024.csv"
    df = pd.read_csv(p)
    df.columns = [c.strip().lower() for c in df.columns]   # gpi, mld
    return df.rename(columns={"mld": "hat_mld"})[["gpi", "hat_mld"]]


def load_science_month(site, month):
    """Science labels for the given month, wide by sensor. Returns per-gpi columns:
    <sensor>_mld (NaN if no numeric depth) and <sensor>_state (value/no_mld/xud/absent)."""
    p = op.metadata_dir(site, "annotations") / f"mld_labels_{site}_science_R.csv"
    df = pd.read_csv(p)
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601", errors="coerce")
    month_num = pd.to_datetime(month + " 2024", format="%B %Y").month
    df = df[(df["timestamp"].dt.year == 2024) & (df["timestamp"].dt.month == month_num)]

    def truthy(s):
        return s.astype(str).str.strip().str.lower().isin(("true", "1"))

    df = df[df["sensor"].isin(SENSORS)].copy()
    df["no_mld"] = truthy(df["no_mld_recorded"]) if "no_mld_recorded" in df else False
    df["xud"] = truthy(df["xud_recorded"]) if "xud_recorded" in df else False
    df["state"] = np.where(df["xud"], "xud", np.where(df["no_mld"], "no_mld", "value"))
    df["mld"] = pd.to_numeric(df["mld_depth"], errors="coerce")

    out = pd.DataFrame({"gpi": sorted(df["gpi"].unique())}).set_index("gpi")
    for s in SENSORS:
        sub = df[df["sensor"] == s].drop_duplicates("gpi").set_index("gpi")
        out[f"{s}_mld"] = sub["mld"]
        out[f"{s}_state"] = sub["state"].reindex(out.index).fillna("absent")
    return out.reset_index()


def main():
    ap = argparse.ArgumentParser(description="Compare HAT MLD vs per-sensor science MLD.")
    ap.add_argument("--month", default="August", help="Month name (e.g. August, October).")
    ap.add_argument("--site", default="sb", choices=op.SITES)
    args = ap.parse_args()

    hat = load_hat(args.site, args.month)
    sci = load_science_month(args.site, args.month)
    merged = hat.merge(sci, on="gpi", how="outer").sort_values("gpi")

    for s in SENSORS:
        merged[f"{s}_diff"] = merged[f"{s}_mld"] - merged["hat_mld"]   # science - HAT

    out_path = op.metadata_dir(args.site, "features") / \
        f"hat_vs_science_{args.site}_{args.month}_2024.csv"
    merged.to_csv(out_path, index=False)

    print(f"HAT vs science MLD — {args.site} {args.month} 2024")
    print(f"  HAT profiles: {hat['gpi'].notna().sum()};  science profiles in month: {len(sci)};"
          f"  gpis in common: {hat.merge(sci, on='gpi')['gpi'].nunique()}")
    print(f"  wrote {out_path}\n")

    print(f"  {'sensor':16s} {'n cmp':>5s} {'science−HAT mean':>16s} {'median':>8s} "
          f"{'RMSE':>7s} {'no_mld':>7s} {'xud':>4s} {'absent':>7s}")
    for s in SENSORS:
        st = merged[f"{s}_state"]
        both = merged["hat_mld"].notna() & merged[f"{s}_mld"].notna()
        d = merged.loc[both, f"{s}_diff"]
        n = int(both.sum())
        mean = f"{d.mean():+.2f}" if n else "—"
        med = f"{d.median():+.2f}" if n else "—"
        rmse = f"{np.sqrt((d**2).mean()):.2f}" if n else "—"
        print(f"  {s:16s} {n:5d} {mean:>16s} {med:>8s} {rmse:>7s} "
              f"{int((st=='no_mld').sum()):7d} {int((st=='xud').sum()):4d} "
              f"{int((st=='absent').sum()):7d}")

    print("\n  (diff = science MLD − HAT MLD, metres. HAT is one density/T/S MLD per profile;")
    print("   science is per-sensor. no_mld/xud/absent science rows are excluded from the stats.)")


if __name__ == "__main__":
    main()
