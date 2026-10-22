"""
eval_synthetic.py — run a trained MLDNet against the synthetic shadow dataset (known truth).

Trains on real pp06; this evaluates on ~/ooi/synthetic/ where we KNOW the MLD, so the error
reflects MODEL capability, not label noise. Reports, per sensor and overall:
  - MAE (m) over matched profiles (true MLD present AND model emits a confident peak),
  - coverage (fraction of true-MLD profiles the model committed to),
  - no-MLD abstention rate (fraction of true-no-MLD profiles the model correctly left flat),
  - a breakdown by true MLD depth z0 (how error varies across the operating envelope).

Honors --include-noise exactly like train.py (must match the model being evaluated).

Run: python ~/argosy/mld/eval_synthetic.py --model ~/ooi/mld/models/mldnet_<ts>.pt
     python ~/argosy/mld/eval_synthetic.py --model <...> --include-noise   # for a noise model
"""
import argparse
import os
import sys
from pathlib import Path

_pre = argparse.ArgumentParser(add_help=False)
_pre.add_argument("--include-noise", action="store_true")
_pre_args, _ = _pre.parse_known_args()
if _pre_args.include_noise:
    os.environ["MLD_INPUT_CHANNELS"] = "2"

import numpy as np
import pandas as pd
import torch
import xarray as xr

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op
from mld.mld_config import SENSORS, N_BINS, N_INPUT_CHANNELS, MLD_LABEL_MAX
from mld.dataset import _bin_profile, _flag_true, BIN_CENTERS
from mld.model import MLDNet, predict

SYN_PP06 = op.OOI_ROOT / "synthetic" / "postproc" / "pp06"
SYN_LABELS = (op.OOI_ROOT / "synthetic" / "metadata" / "annotations"
              / "mld_labels_synthetic_block00_synthetic.csv")
PEAK_MIN_CONF = 0.30


def _find_syn_shard(sensor, gpi):
    hits = list(SYN_PP06.glob(f"*/RCA_synthetic_sp_{sensor}_*_{gpi}_*.nc"))
    return hits[0] if hits else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--include-noise", action="store_true",
                    help="use the 2-channel (filtered+roughness) input; must match the model.")
    args = ap.parse_args()

    if not SYN_LABELS.exists():
        print(f"No synthetic labels at {SYN_LABELS}. Run mld/synthetic.py first.")
        return
    lab = pd.read_csv(SYN_LABELS)

    model = MLDNet()
    model.load_state_dict(torch.load(args.model, map_location="cpu", weights_only=True))
    model.eval()
    print(f"model: {args.model}")
    print(f"input channels/sensor: {N_INPUT_CHANNELS} "
          f"({'filtered only' if N_INPUT_CHANNELS == 1 else 'filtered + roughness'})")

    # Per-sensor accumulators + a z0-stratified MAE table (true-MLD profiles only).
    abs_err = {s: 0.0 for s in SENSORS}
    n_match = {s: 0 for s in SENSORS}
    n_poss = {s: 0 for s in SENSORS}
    nomld_total = {s: 0 for s in SENSORS}
    nomld_correct = {s: 0 for s in SENSORS}
    by_z0 = {}   # rounded true depth -> [abs_err_sum, matched]

    with torch.no_grad():
        for gpi, grp in lab.groupby("gpi"):
            x = np.zeros((len(SENSORS), N_INPUT_CHANNELS, N_BINS), np.float32)
            present = [False] * len(SENSORS)
            truth = [None] * len(SENSORS)
            is_nomld = [False] * len(SENSORS)
            for si, sensor in enumerate(SENSORS):
                row = grp[grp["sensor"] == sensor]
                if len(row) == 0:
                    continue
                row = row.iloc[0]
                shard = _find_syn_shard(sensor, int(gpi))
                if shard is None:
                    continue
                try:
                    ds = xr.open_dataset(shard)
                    depth = np.abs(ds["depth"].values)
                    value = ds[sensor].values
                    ds.close()
                except Exception:
                    continue
                filt, lstd, _ = _bin_profile(depth, value, "adaptive_savgol_mad", 59, 2)
                x[si, 0] = filt
                if N_INPUT_CHANNELS == 2:
                    x[si, 1] = lstd
                present[si] = True
                nm = _flag_true(row.get("no_mld_recorded", False))
                is_nomld[si] = nm
                md = row.get("mld_depth")
                truth[si] = None if (nm or pd.isna(md) or str(md).strip() == "") else float(md)

            if not any(present):
                continue
            loc, pres_logit = model(torch.from_numpy(x[None]))
            dec = predict(loc[0], pres_logit[0], BIN_CENTERS)    # [(depth|None, P(pres), conf)]
            for si, sensor in enumerate(SENSORS):
                if not present[si]:
                    continue
                p_depth = dec[si][0]
                if is_nomld[si]:
                    nomld_total[sensor] += 1
                    if p_depth is None:
                        nomld_correct[sensor] += 1
                    continue
                t = truth[si]
                if t is None or t > MLD_LABEL_MAX:   # excluded-by-rule depths
                    continue
                n_poss[sensor] += 1
                if p_depth is not None:
                    e = abs(p_depth - t)
                    abs_err[sensor] += e
                    n_match[sensor] += 1
                    z0b = int(round(t / 10.0) * 10)
                    by_z0.setdefault(z0b, [0.0, 0])
                    by_z0[z0b][0] += e
                    by_z0[z0b][1] += 1

    print("\n== per-sensor (true-MLD profiles) ==")
    tot_err = tot_match = tot_poss = 0
    for s in SENSORS:
        mae = abs_err[s] / n_match[s] if n_match[s] else float("nan")
        cov = n_match[s] / n_poss[s] if n_poss[s] else 0.0
        print(f"  {s:16s} MAE {mae:5.2f} m   coverage {cov:4.0%} ({n_match[s]}/{n_poss[s]})")
        tot_err += abs_err[s]; tot_match += n_match[s]; tot_poss += n_poss[s]
    omae = tot_err / tot_match if tot_match else float("nan")
    print(f"  {'OVERALL':16s} MAE {omae:5.2f} m   coverage {tot_match/tot_poss:4.0%} "
          f"({tot_match}/{tot_poss})")

    print("\n== no-MLD abstention (correctly flat) ==")
    for s in SENSORS:
        tot = nomld_total[s]
        rate = nomld_correct[s] / tot if tot else float("nan")
        print(f"  {s:16s} {rate:4.0%} ({nomld_correct[s]}/{tot})")

    print("\n== MAE by true depth z0 (matched) ==")
    for z0b in sorted(by_z0):
        e, m = by_z0[z0b]
        print(f"  z0~{z0b:3d} m   MAE {e/m:5.2f} m   (n={m})")


if __name__ == "__main__":
    main()
