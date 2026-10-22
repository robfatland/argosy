"""
train.py — train the MLD 1D-CNN (shared backbone + 4 heatmap heads) on human labels.

Split: BY TIME BLOCK, not random — profiles near each other in time are near-duplicates
(same water mass/season), so a random split would leak. We sort labeled profiles by
timestamp and assign contiguous time-blocks to train/val/test (default 70/15/15).

CPU is fine (small model, ~2k labels). Writes weights + a model card to ~/ooi/mld/models/.

Run: python ~/argosy/mld/train.py [--epochs 60] [--sites sb oo ab]
"""
import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# --include-noise adds the roughness (MAD) channel: 2 input channels/sensor instead of 1.
# Default is 1 (filtered only). mld_config reads MLD_INPUT_CHANNELS at import time, so we must
# set it BEFORE importing mld_config below — hence this tiny pre-parse.
_pre = argparse.ArgumentParser(add_help=False)
_pre.add_argument("--include-noise", action="store_true")
_pre_args, _ = _pre.parse_known_args()
if _pre_args.include_noise:
    os.environ["MLD_INPUT_CHANNELS"] = "2"

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

sys.path.insert(0, str(Path("~/argosy").expanduser()))
from mld.mld_config import SENSORS, N_BINS, N_INPUT_CHANNELS, MODELS_DIR
from mld.dataset import load_examples, BIN_CENTERS
from mld.model import MLDNet, mld_loss, predict

DC = np.asarray(BIN_CENTERS)


class ExampleDS(Dataset):
    """Yields (input, true_bin[S] long, present[S] float, has_label[S] float).
    true_bin = argmax of the Gaussian target heatmap (= the true MLD bin) where present;
    present = labeled AND not no-MLD."""
    def __init__(self, examples):
        self.ex = examples

    def __len__(self):
        return len(self.ex)

    def __getitem__(self, i):
        e = self.ex[i]
        hl = e["has_label"].astype(np.float32)
        present = (e["has_label"] & ~e["is_nomld"]).astype(np.float32)
        true_bin = e["target"].argmax(axis=1).astype(np.int64)   # [S]
        return (torch.from_numpy(e["input"]),
                torch.from_numpy(true_bin),
                torch.from_numpy(present),
                torch.from_numpy(hl))


def time_block_split(examples, frac=(0.70, 0.15, 0.15), n_blocks=20, seed=0):
    """Sort by timestamp, cut into n_blocks contiguous blocks, assign whole blocks to
    train/val/test so temporally-adjacent (near-duplicate) profiles stay together."""
    ex = sorted(examples, key=lambda e: e["timestamp"])
    blocks = np.array_split(np.arange(len(ex)), n_blocks)
    rng = np.random.default_rng(seed)
    order = rng.permutation(n_blocks)
    n_tr = int(round(frac[0] * n_blocks))
    n_va = int(round(frac[1] * n_blocks))
    tr_b, va_b, te_b = order[:n_tr], order[n_tr:n_tr + n_va], order[n_tr + n_va:]
    pick = lambda bs: [ex[i] for b in bs for i in blocks[b]]
    return pick(tr_b), pick(va_b), pick(te_b)


def evaluate(model, loader):
    """Mean masked loss + MLD MAE (metres). Also returns matched/possible counts so the
    caller can reject a degenerate epoch (near-empty denominator or an all-abstain model
    that happens to match a couple of profiles exactly -> spurious MAE 0).
    Returns (loss, mae, n_matched, n_possible) where n_possible = labeled profiles that
    HAVE a real (non-flat) target MLD, n_matched = those where the model also emits a peak."""
    model.eval()
    tot, n, abs_err, n_matched, n_possible = 0.0, 0, 0.0, 0, 0
    with torch.no_grad():
        for x, tb, pres, hl in loader:
            loc, pres_logit = model(x)
            tot += mld_loss(loc, pres_logit, tb, pres, hl, DC).item() * x.shape[0]
            n += x.shape[0]
            for bi in range(x.shape[0]):
                dec = predict(loc[bi], pres_logit[bi], DC)   # [(depth|None, P(pres), conf)]
                for si in range(len(SENSORS)):
                    if pres[bi, si] < 0.5:
                        continue           # no-MLD target — not an MAE case
                    n_possible += 1
                    depth = dec[si][0]
                    if depth is not None:
                        true_depth = float(DC[int(tb[bi, si])])
                        abs_err += abs(depth - true_depth); n_matched += 1
    mae = abs_err / n_matched if n_matched else float("nan")
    return tot / max(n, 1), mae, n_matched, n_possible


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--sites", nargs="*", default=["sb", "oo", "ab"])
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--include-noise", action="store_true",
                    help="add the roughness/MAD channel (2 input channels/sensor; default 1 = "
                         "filtered only). Handled before imports; listed here for --help.")
    args = ap.parse_args()

    ch_desc = "filtered only" if N_INPUT_CHANNELS == 1 else "filtered + roughness"
    print(f"input channels/sensor: {N_INPUT_CHANNELS} ({ch_desc})  "
          f"[--include-noise to add the roughness channel]")

    examples = load_examples(sites=tuple(args.sites))
    if len(examples) < 10:
        print("Not enough labeled examples to train.")
        return
    tr, va, te = time_block_split(examples)
    print(f"split: train {len(tr)}  val {len(va)}  test {len(te)}")

    tr_dl = DataLoader(ExampleDS(tr), batch_size=args.batch, shuffle=True)
    va_dl = DataLoader(ExampleDS(va), batch_size=args.batch)
    te_dl = DataLoader(ExampleDS(te), batch_size=args.batch)

    model = MLDNet()
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    # Drop LR to 1/5 at 60% through to calm the late-training val-MAE thrash.
    sched = torch.optim.lr_scheduler.MultiStepLR(opt, milestones=[int(0.6 * args.epochs)], gamma=0.2)
    # Select the best checkpoint by val MAE (the quantity we actually care about —
    # peak-localization in metres), NOT val loss. val_loss and val_MAE diverge: loss keeps
    # falling while MAE thrashes, so picking on loss saved a high-MAE epoch. Ignore the early
    # epochs whose MAE is NaN (no confident peaks yet).
    best_mae, best_loss_at_best, best_state, best_ep, best_cov = float("inf"), None, None, -1, 0.0
    for ep in range(args.epochs):
        model.train()
        for x, tb, pres, hl in tr_dl:
            opt.zero_grad()
            loc, pres_logit = model(x)
            loss = mld_loss(loc, pres_logit, tb, pres, hl, DC)
            loss.backward(); opt.step()
        sched.step()
        va_loss, va_mae, n_match, n_poss = evaluate(model, va_dl)
        cov = n_match / n_poss if n_poss else 0.0
        # An epoch is ELIGIBLE for "best" only if the model emits a confident peak on a solid
        # share of the profiles that actually have an MLD — guards against the degenerate case
        # where a near-empty denominator (or an all-abstain model matching 1-2 profiles) yields
        # a spurious MAE ~0. Require >=60% coverage AND >=20 matched pairs.
        eligible = (not math.isnan(va_mae)) and cov >= 0.60 and n_match >= 20
        if eligible and va_mae < best_mae:
            best_mae, best_loss_at_best, best_cov = va_mae, va_loss, cov
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            best_ep = ep
        if ep % 5 == 0 or ep == args.epochs - 1:
            print(f"epoch {ep:3d}  val_loss {va_loss:.4f}  val_MAE(m) {va_mae:.2f}  "
                  f"coverage {cov:.0%} ({n_match}/{n_poss})")

    if best_state is None:
        print("WARNING: no epoch met the eligibility bar (coverage>=60%, >=20 matched); "
              "keeping final-epoch weights. Model likely under-confident.")
    else:
        print(f"best val_MAE {best_mae:.2f} m at epoch {best_ep} "
              f"(val_loss {best_loss_at_best:.4f}, coverage {best_cov:.0%})")
        model.load_state_dict(best_state)
    te_loss, te_mae, te_match, te_poss = evaluate(model, te_dl)
    te_cov = te_match / te_poss if te_poss else 0.0
    print(f"TEST  loss {te_loss:.4f}  MAE(m) {te_mae:.2f}  "
          f"coverage {te_cov:.0%} ({te_match}/{te_poss})")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    wpath = MODELS_DIR / f"mldnet_{stamp}.pt"
    torch.save(model.state_dict(), wpath)
    card = dict(created=stamp, sensors=SENSORS, n_bins=N_BINS, sites=args.sites,
                input_channels=N_INPUT_CHANNELS,
                input_channel_desc=ch_desc,
                n_train=len(tr), n_val=len(va), n_test=len(te),
                selected_by="val_MAE (coverage>=60%, >=20 matched)",
                best_val_mae_m=(None if best_state is None else best_mae), best_epoch=best_ep,
                val_loss_at_best=best_loss_at_best,
                test_loss=te_loss, test_mae_m=te_mae, test_coverage=round(te_cov, 3),
                epochs=args.epochs, lr=args.lr, split="time-block 70/15/15",
                arch=f"shared 1D-CNN backbone + {len(SENSORS)} heatmap heads")
    (MODELS_DIR / f"mldnet_{stamp}.json").write_text(json.dumps(card, indent=2))
    print(f"saved {wpath}")


if __name__ == "__main__":
    main()
