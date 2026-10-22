"""
diagnose.py — two cheap MLD-model diagnostics against the synthetic set (known truth).

(A) HEATMAP SHAPE: for a few synthetic MLD-present profiles, load the given trained model and
    print the predicted heatmap's peak location, peak height, and spread (how diffuse) next to
    the true z0. Distinguishes "sharp peak at wrong depth" (data/feature bug) from "diffuse blob"
    (loss-design bug — the hedging hypothesis in MLDModelReflection.md).

(B) TINY-BATCH OVERFIT: take ~12 synthetic profiles and train a FRESH model on ONLY them for
    many steps. If the pipeline can memorize a tiny set to sharp correct peaks, the architecture
    is capable and the problem is objective/scale. If it CANNOT, the bug is architectural/loss.

Run:  python ~/argosy/mld/diagnose.py --model ~/ooi/mld/models/mldnet_<ts>.pt
      python ~/argosy/mld/diagnose.py --model <...> --include-noise
(Default channels=1; pass --include-noise to match a 2-channel model for part A.)
"""
import argparse
import os
import sys
from pathlib import Path

_pre = argparse.ArgumentParser(add_help=False)
_pre.add_argument("--include-noise", action="store_true")
_pa, _ = _pre.parse_known_args()
if _pa.include_noise:
    os.environ["MLD_INPUT_CHANNELS"] = "2"

import numpy as np
import pandas as pd
import torch
import xarray as xr

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op
from mld.mld_config import SENSORS, N_BINS, N_INPUT_CHANNELS, HEATMAP_SIGMA_M, DEPTH_BIN
from mld.dataset import _bin_profile, _flag_true, _heatmap, BIN_CENTERS
from mld.model import MLDNet, mld_loss, predict, _soft_argmax_depth

SYN_PP06 = op.OOI_ROOT / "synthetic" / "postproc" / "pp06"
SYN_LABELS = (op.OOI_ROOT / "synthetic" / "metadata" / "annotations"
              / "mld_labels_synthetic_block00_synthetic.csv")


def _find(sensor, gpi):
    hits = list(SYN_PP06.glob(f"*/RCA_synthetic_sp_{sensor}_*_{gpi}_*.nc"))
    return hits[0] if hits else None


def _example(grp):
    """Build arrays for one synthetic GPI group:
       x[n_sensors,C,N_BINS], true_bin[n_sensors] long, present[n_sensors] float,
       has_label[n_sensors] float, truth[n_sensors] (metres or None)."""
    x = np.zeros((len(SENSORS), N_INPUT_CHANNELS, N_BINS), np.float32)
    true_bin = np.zeros(len(SENSORS), np.int64)
    present = np.zeros(len(SENSORS), np.float32)
    hl = np.zeros(len(SENSORS), np.float32)
    truth = [None] * len(SENSORS)
    for si, sensor in enumerate(SENSORS):
        row = grp[grp["sensor"] == sensor]
        if len(row) == 0:
            continue
        row = row.iloc[0]
        sh = _find(sensor, int(grp.name))
        if sh is None:
            continue
        ds = xr.open_dataset(sh); depth = np.abs(ds["depth"].values); val = ds[sensor].values; ds.close()
        filt, lstd, _ = _bin_profile(depth, val, "adaptive_savgol_mad", 59, 2)
        x[si, 0] = filt
        if N_INPUT_CHANNELS == 2:
            x[si, 1] = lstd
        nm = _flag_true(row.get("no_mld_recorded", False))
        md = row.get("mld_depth")
        t = None if (nm or pd.isna(md) or str(md).strip() == "") else float(md)
        hl[si] = 1.0
        if t is not None:
            present[si] = 1.0
            true_bin[si] = int(np.clip(round(t / DEPTH_BIN), 0, N_BINS - 1))
            truth[si] = t
    return x, true_bin, present, hl, truth


def _spread(hm):
    """Std-dev (m) of the heatmap treated as a mass distribution — small = sharp peak,
    large = diffuse blob. Returns np.nan if the heatmap has ~no mass."""
    w = hm.astype(float)
    s = w.sum()
    if s < 1e-6:
        return float("nan")
    c = BIN_CENTERS
    mean = (w * c).sum() / s
    var = (w * (c - mean) ** 2).sum() / s
    return float(np.sqrt(var))


def part_A(model, lab, k=8):
    print("== (A) softmax-over-depth distribution on synthetic MLD-present profiles ==")
    print("   spread = std-dev (m) of the softmax pmf: small = sharp/committed, large = diffuse")
    present = lab[~lab["no_mld_recorded"].apply(_flag_true)]
    gpis = present["gpi"].unique()[:k]
    model.eval()
    with torch.no_grad():
        for gpi in gpis:
            grp = lab[lab["gpi"] == gpi]; grp.name = gpi
            x, true_bin, pres, hl, truth = _example(grp)
            loc, pres_logit = model(torch.from_numpy(x[None]))
            dec = predict(loc[0], pres_logit[0], BIN_CENTERS)
            parts = []
            for si, sensor in enumerate(SENSORS):
                if not hl[si] or truth[si] is None:
                    continue
                p = torch.softmax(loc[0, si], dim=0).numpy()
                depth, pr, conf = dec[si]
                parts.append(f"{sensor[:4]}: true {truth[si]:5.1f}  "
                             f"pred {('--' if depth is None else f'{depth:5.1f}')}  "
                             f"P(pres) {pr:.2f}  spread {_spread(p):4.1f}m")
            print(f"  GPI {int(gpi)}  " + " | ".join(parts))


def part_B(lab, steps=400, k=12):
    print(f"\n== (B) tiny-batch overfit: FRESH model on {k} synthetic profiles, {steps} steps ==")
    print("   (new objective: softmax-CE + soft-argmax distance + presence BCE)")
    present = lab[~lab["no_mld_recorded"].apply(_flag_true)]
    gpis = present["gpi"].unique()[:k]
    X, TB, P, H, truths = [], [], [], [], []
    for gpi in gpis:
        grp = lab[lab["gpi"] == gpi]; grp.name = gpi
        x, true_bin, pres, hl, truth = _example(grp)
        X.append(x); TB.append(true_bin); P.append(pres); H.append(hl); truths.append(truth)
    X = torch.from_numpy(np.stack(X))
    TB = torch.from_numpy(np.stack(TB))
    P = torch.from_numpy(np.stack(P))
    H = torch.from_numpy(np.stack(H))
    dc = np.asarray(BIN_CENTERS)

    model = MLDNet()
    opt = torch.optim.Adam(model.parameters(), lr=3e-3)
    for step in range(steps):
        opt.zero_grad()
        loc, pres_logit = model(X)
        loss = mld_loss(loc, pres_logit, TB, P, H, dc)
        loss.backward(); opt.step()
        if step % 100 == 0 or step == steps - 1:
            print(f"  step {step:4d}  loss {loss.item():.4f}")

    model.eval()
    errs = []
    with torch.no_grad():
        loc, pres_logit = model(X)
        for i in range(len(gpis)):
            dec = predict(loc[i], pres_logit[i], dc)
            for si in range(len(SENSORS)):
                if not H[i, si] or truths[i][si] is None:
                    continue
                depth = dec[si][0]
                if depth is not None:
                    errs.append(abs(depth - truths[i][si]))
    errs = np.array(errs)
    print(f"  after overfit: mean |pred-true| = {errs.mean():.2f} m  (max {errs.max():.2f} m)  "
          f"over {len(errs)} committed sensor-profiles")
    print("  PASS if ~<1 m: the new objective CAN localize a tiny clean set -> proceed to full "
          "retrain. FAIL if not: deeper problem.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None,
                    help="trained .pt for part A (must match the NEW architecture). Omit to run "
                         "only part B, the tiny-batch overfit gate for the new objective.")
    ap.add_argument("--include-noise", action="store_true")
    ap.add_argument("--steps", type=int, default=400)
    args = ap.parse_args()

    if not SYN_LABELS.exists():
        print(f"No synthetic labels at {SYN_LABELS}; run mld/synthetic.py first."); return
    lab = pd.read_csv(SYN_LABELS)

    if args.model:
        try:
            model = MLDNet()
            model.load_state_dict(torch.load(args.model, map_location="cpu", weights_only=True))
            print(f"model: {args.model}  (channels={N_INPUT_CHANNELS})\n")
            part_A(model, lab)
        except Exception as e:
            print(f"(skipping part A: could not load {args.model} into current architecture: {e})")
    part_B(lab, steps=args.steps)


if __name__ == "__main__":
    main()
