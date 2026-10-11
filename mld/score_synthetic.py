"""
score_synthetic.py — ZEROTH-ORDER ACCEPTANCE TEST for the MLD 1-D CNN.

Runs a trained MLDNet over the synthetic shadow dataset (~/ooi/synthetic/, written by
synthetic.py) and scores predicted MLD against the KNOWN ground-truth labels. The question:
can the model nail easy/textbook cases? See SyntheticMLDPlan.md "Zeroth-order acceptance test".

Scoring:
  - MLD-present: correct if |pred_mld - true_mld| <= TOL_M (default 5 m).
  - no-MLD: correct if the model abstains (pred below confidence floor).
  - Reports overall + per-sensor accuracy, MAE on hits, and a confusion of MLD/no-MLD calls.

This reads the synthetic parallel tree directly (not via ooipaths site paths, since `synthetic`
is deliberately NOT a registered site). It reuses dataset._bin_profile so synthetic data goes
through the exact same binning/filter path as real training data.

Run:  python ~/argosy/mld/score_synthetic.py --model ~/ooi/mld/models/mldnet_<stamp>.pt
      (omit --model to auto-pick the newest mldnet_*.pt)
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
from mld.mld_config import SENSORS, N_BINS, MODELS_DIR
from mld.dataset import _bin_profile, BIN_CENTERS
from mld.model import MLDNet, peak_from_heatmap

SYN_ROOT = op.OOI_ROOT / "synthetic"
SYN_PP06 = SYN_ROOT / "postproc" / "pp06"
SYN_LABELS = SYN_ROOT / "metadata" / "annotations" / "mld_labels_synthetic_block00_synthetic.csv"
TOL_M = 5.0
MIN_CONF = 0.30


def _find_syn_shard(gpi, sensor):
    """Locate a synthetic shard for (gpi, sensor) anywhere under the synthetic pp06 tree."""
    for yd in sorted(SYN_PP06.glob("[0-9]*")):
        hits = list(yd.glob(f"*_{sensor}_*_{gpi}_*.nc"))
        if hits:
            return hits[0]
    return None


def _build_input(gpi):
    """Same 3-sensor input the trainer/infer build, from synthetic shards."""
    x = np.zeros((len(SENSORS), 2, N_BINS), np.float32)
    any_ = False
    for si, sensor in enumerate(SENSORS):
        shard = _find_syn_shard(gpi, sensor)
        if shard is None:
            continue
        try:
            ds = xr.open_dataset(shard)
            depth = np.abs(ds["depth"].values)
            value = ds[sensor].values
            ds.close()
        except Exception:
            continue
        filt, lstd, _ = _bin_profile(depth, value, "adaptive_savgol_mad", 51, 2.0)
        x[si, 0] = filt
        x[si, 1] = lstd
        any_ = True
    return (x if any_ else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--tol", type=float, default=TOL_M)
    args = ap.parse_args()

    mpath = Path(args.model).expanduser() if args.model else max(
        MODELS_DIR.glob("mldnet_*.pt"), key=lambda p: p.stat().st_mtime)
    print(f"model: {mpath.name}   tolerance: +/-{args.tol} m")

    model = MLDNet()
    model.load_state_dict(torch.load(mpath, map_location="cpu"))
    model.eval()

    lab = pd.read_csv(SYN_LABELS)
    # pivot to per-gpi truth
    results = []   # (sensor, kind, correct, pred, true, err)
    for gpi, grp in lab.groupby("gpi"):
        x = _build_input(int(gpi))
        if x is None:
            continue
        with torch.no_grad():
            pred = model(torch.from_numpy(x[None]))[0].numpy()   # [n_sensors, N_BINS]
        for si, sensor in enumerate(SENSORS):
            row = grp[grp["sensor"] == sensor]
            if len(row) == 0:
                continue
            row = row.iloc[0]
            true_nomld = bool(row["no_mld_recorded"])
            true_mld = None if true_nomld else float(row["mld_depth"])
            p_depth, p_conf = peak_from_heatmap(pred[si], BIN_CENTERS, MIN_CONF)
            if true_nomld:
                correct = (p_depth is None)
                results.append((sensor, "no-MLD", correct, p_depth, None, np.nan))
            else:
                if p_depth is None:
                    results.append((sensor, "MLD", False, None, true_mld, np.nan))
                else:
                    err = abs(p_depth - true_mld)
                    results.append((sensor, "MLD", err <= args.tol, p_depth, true_mld, err))

    df = pd.DataFrame(results, columns=["sensor", "kind", "correct", "pred", "true", "err"])

    def pct(mask):
        sub = df[mask]
        return (100.0 * sub["correct"].mean()) if len(sub) else float("nan"), len(sub)

    print("\n=== Zeroth-order acceptance test ===")
    for kind in ("MLD", "no-MLD"):
        acc, n = pct(df["kind"] == kind)
        print(f"  {kind:7} overall: {acc:5.1f}%  (n={n})")
    print("  per sensor (MLD-present, within tol):")
    for sensor in SENSORS:
        acc, n = pct((df["sensor"] == sensor) & (df["kind"] == "MLD"))
        print(f"     {sensor:16} {acc:5.1f}%  (n={n})")
    print("  per sensor (no-MLD abstention):")
    for sensor in SENSORS:
        acc, n = pct((df["sensor"] == sensor) & (df["kind"] == "no-MLD"))
        print(f"     {sensor:16} {acc:5.1f}%  (n={n})")
    hits = df[(df["kind"] == "MLD") & df["err"].notna()]
    print(f"\n  MAE on resolved MLD picks: {hits['err'].mean():.2f} m  (n={len(hits)})")
    overall, n = pct(df.index.notna())
    print(f"  OVERALL correct: {overall:.1f}%  (n={n})")

    # how far off are the misses?
    miss = df[(df["kind"] == "MLD") & (~df["correct"]) & df["err"].notna()]
    if len(miss):
        print(f"  worst MLD errors (m): {np.sort(miss['err'].values)[::-1][:5].round(1).tolist()}")


if __name__ == "__main__":
    main()
