"""
infer.py — run a trained MLDNet over pp06 profiles and write MLD metadata.

For each GPI in the requested site/years, builds the same 4-sensor input the trainer used,
predicts 4 heatmaps, and extracts (mld_depth, confidence) per sensor from each heatmap peak
(confidence below threshold => 'no MLD' for that sensor). Writes one row per (gpi, sensor).

This is the published metadata product: ~/ooi/mld/inference/mld_pred_<site>_<year>.csv
columns: site, gpi, timestamp, sensor, mld_depth, confidence, no_mld

Run: python ~/argosy/mld/infer.py --model <path.pt> --site sb --years 2018 2019
     (omit --years to do all years present in pp06)
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import xarray as xr

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op
from mld.mld_config import SENSORS, N_BINS, INFER_DIR
from mld.dataset import _bin_profile, _find_shard, BIN_CENTERS
from mld.model import MLDNet, peak_from_heatmap

MIN_CONF = 0.30


def _gpis_for_year(site, year):
    """All GPIs present in pp06 for a year (union across sensors)."""
    year_dir = op.postproc_dir("pp06", year, site)
    if not year_dir.exists():
        return []
    gpis = set()
    for f in year_dir.glob("*.nc"):
        parts = f.stem.split("_")
        try:
            gpis.add(int(parts[6]))
        except (IndexError, ValueError):
            pass
    return sorted(gpis)


def _build_input(site, year, gpi, return_mask=False):
    x = np.zeros((len(SENSORS), 2, N_BINS), np.float32)
    pmask = np.zeros((len(SENSORS), N_BINS), np.float32)
    ts = None
    any_ = False
    for si, sensor in enumerate(SENSORS):
        shard = _find_shard(site, year, sensor, gpi)
        if shard is None:
            continue
        try:
            ds = xr.open_dataset(shard)
            depth = np.abs(ds["depth"].values)
            value = ds[sensor].values
            if ts is None and ds.sizes.get("time"):
                ts = pd.Timestamp(ds["time"].values[0])
            ds.close()
        except Exception:
            continue
        # Use the SAME filter the labels were made with (adaptive_savgol_mad, p1=51, p2=2).
        filt, lstd, m = _bin_profile(depth, value, "adaptive_savgol_mad", 51, 2.0)
        x[si, 0] = filt
        x[si, 1] = lstd
        pmask[si] = m
        any_ = True
    if not any_:
        return (None, None, ts) if return_mask else (None, ts)
    return (x, pmask, ts) if return_mask else (x, ts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--site", default=op.DEFAULT_SITE)
    ap.add_argument("--years", nargs="*", type=int, default=None)
    args = ap.parse_args()

    model = MLDNet()
    model.load_state_dict(torch.load(args.model, map_location="cpu"))
    model.eval()

    years = args.years
    if years is None:
        base = op.postproc_base(args.site) / "pp06"
        years = sorted(int(d.name) for d in base.glob("[0-9][0-9][0-9][0-9]") if d.is_dir())

    INFER_DIR.mkdir(parents=True, exist_ok=True)
    for year in years:
        rows = []
        gpis = _gpis_for_year(args.site, year)
        for gpi in gpis:
            x, ts = _build_input(args.site, year, gpi)
            if x is None:
                continue
            with torch.no_grad():
                pred = model(torch.from_numpy(x[None]))[0].numpy()   # [4, N_BINS]
            for si, sensor in enumerate(SENSORS):
                depth, conf = peak_from_heatmap(pred[si], BIN_CENTERS, MIN_CONF)
                rows.append(dict(site=args.site, gpi=gpi,
                                 timestamp=ts.isoformat() if ts is not None else "",
                                 sensor=sensor,
                                 mld_depth=(round(depth, 2) if depth is not None else np.nan),
                                 confidence=round(conf, 3),
                                 no_mld=(depth is None)))
        if rows:
            out = INFER_DIR / f"mld_pred_{args.site}_{year}.csv"
            pd.DataFrame(rows).to_csv(out, index=False)
            print(f"{year}: {len(gpis)} profiles -> {out}")


if __name__ == "__main__":
    main()
