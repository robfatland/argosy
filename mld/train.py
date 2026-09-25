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
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

sys.path.insert(0, str(Path("~/argosy").expanduser()))
from mld.mld_config import SENSORS, N_BINS, MODELS_DIR
from mld.dataset import load_examples, BIN_CENTERS
from mld.model import MLDNet, masked_heatmap_loss, peak_from_heatmap


class ExampleDS(Dataset):
    def __init__(self, examples):
        self.ex = examples

    def __len__(self):
        return len(self.ex)

    def __getitem__(self, i):
        e = self.ex[i]
        return (torch.from_numpy(e["input"]),
                torch.from_numpy(e["target"]),
                torch.from_numpy(e["has_label"].astype(np.float32)))


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
    """Mean masked loss + coarse MLD MAE (metres) over labeled, non-flat sensors."""
    model.eval()
    tot, n, abs_err, n_err = 0.0, 0, 0.0, 0
    with torch.no_grad():
        for x, y, hl in loader:
            p = model(x)
            tot += masked_heatmap_loss(p, y, hl).item() * x.shape[0]
            n += x.shape[0]
            for bi in range(x.shape[0]):
                for si in range(len(SENSORS)):
                    if hl[bi, si] < 0.5:
                        continue
                    t_depth, _ = peak_from_heatmap(y[bi, si].numpy(), BIN_CENTERS, 0.5)
                    p_depth, _ = peak_from_heatmap(p[bi, si].numpy(), BIN_CENTERS, 0.3)
                    if t_depth is not None and p_depth is not None:
                        abs_err += abs(t_depth - p_depth); n_err += 1
    mae = abs_err / n_err if n_err else float("nan")
    return tot / max(n, 1), mae


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--sites", nargs="*", default=["sb", "oo", "ab"])
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--batch", type=int, default=16)
    args = ap.parse_args()

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
    best_va, best_state = float("inf"), None
    for ep in range(args.epochs):
        model.train()
        for x, y, hl in tr_dl:
            opt.zero_grad()
            loss = masked_heatmap_loss(model(x), y, hl)
            loss.backward(); opt.step()
        va_loss, va_mae = evaluate(model, va_dl)
        if va_loss < best_va:
            best_va, best_state = va_loss, {k: v.clone() for k, v in model.state_dict().items()}
        if ep % 5 == 0 or ep == args.epochs - 1:
            print(f"epoch {ep:3d}  val_loss {va_loss:.4f}  val_MAE(m) {va_mae:.2f}")

    if best_state is not None:
        model.load_state_dict(best_state)
    te_loss, te_mae = evaluate(model, te_dl)
    print(f"TEST  loss {te_loss:.4f}  MAE(m) {te_mae:.2f}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    wpath = MODELS_DIR / f"mldnet_{stamp}.pt"
    torch.save(model.state_dict(), wpath)
    card = dict(created=stamp, sensors=SENSORS, n_bins=N_BINS, sites=args.sites,
                n_train=len(tr), n_val=len(va), n_test=len(te),
                val_loss=best_va, test_loss=te_loss, test_mae_m=te_mae,
                epochs=args.epochs, lr=args.lr, split="time-block 70/15/15",
                arch="shared 1D-CNN backbone + 4 heatmap heads")
    (MODELS_DIR / f"mldnet_{stamp}.json").write_text(json.dumps(card, indent=2))
    print(f"saved {wpath}")


if __name__ == "__main__":
    main()
