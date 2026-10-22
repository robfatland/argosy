"""
model.py — shared 1D-CNN backbone + per-sensor heatmap heads (one per sensor in SENSORS).

As of 2026-10-10 SENSORS = [temperature, salinity, dissolvedoxygen] (density dropped — see
mld_config.py). So this is a 3-head / 6-input-channel model; counts derive from len(SENSORS),
not hardcoded.

Input : [batch, 2, N_BINS]  per sensor (filtered value, local std). All sensors share ONE
        backbone (so each head benefits from cross-sensor features via joint training). We stack
        the sensors' 2-ch inputs into a (len(SENSORS)*2)-ch input, one backbone, one head per
        sensor each emitting a heatmap over depth.
Output: [batch, n_sensors, N_BINS]  one heatmap per sensor (sigmoid 0..1).

Loss   : per-bin BCE, MASKED to sensors whose label is present for that profile (absent
         sensors contribute nothing). "no MLD" is a flat (all-zero) target — learned like
         any other target, no special class.
"""
import torch
import torch.nn as nn

from mld.mld_config import SENSORS, N_BINS, N_INPUT_CHANNELS

N_SENSORS = len(SENSORS)


# ── Objective redesign 2026-10-13 (see MLDModelReflection.md) ────────────────────
# The old head emitted a per-bin sigmoid "heatmap" trained with BCE vs a Gaussian bump. That
# objective has a comfortable HEDGING minimum (a diffuse low blob beats a confident sharp peak),
# confirmed by the tiny-batch overfit failing to reach <1 m. Replaced with:
#   - LOCALIZATION: each head emits raw logits over depth; softmax-over-depth makes a true
#     probability distribution (mass conserved, so a blob everywhere is NOT free), trained with
#     cross-entropy to the true depth bin PLUS a soft-argmax distance term (directly rewards the
#     expected depth being near truth). This structurally forbids the hedge.
#   - PRESENCE: a separate scalar head per sensor (is there an MLD at all?) trained with BCE —
#     a full-strength abstain gradient, not 4-bins-of-120 as before.

class MLDNet(nn.Module):
    def __init__(self, n_bins=N_BINS, n_sensors=N_SENSORS, width=32, in_channels=N_INPUT_CHANNELS):
        super().__init__()
        self.n_bins = n_bins
        self.n_sensors = n_sensors
        in_ch = n_sensors * in_channels
        self.backbone = nn.Sequential(
            nn.Conv1d(in_ch, width, kernel_size=7, padding=3), nn.ReLU(),
            nn.Conv1d(width, width, kernel_size=7, padding=3), nn.ReLU(),
            nn.Conv1d(width, width, kernel_size=7, padding=3), nn.ReLU(),
            nn.Conv1d(width, width, kernel_size=5, padding=2), nn.ReLU(),
        )
        # Localization: per-sensor 1-wide conv -> raw logits over depth (NO sigmoid).
        self.loc_heads = nn.ModuleList(
            [nn.Conv1d(width, 1, kernel_size=1) for _ in range(n_sensors)])
        # Presence: per-sensor scalar logit from globally-pooled features.
        self.pres_heads = nn.ModuleList(
            [nn.Linear(width, 1) for _ in range(n_sensors)])

    def forward(self, x):
        """Returns (loc_logits, pres_logits):
           loc_logits  : [B, n_sensors, N_BINS]  (raw; apply softmax over depth for a pmf)
           pres_logits : [B, n_sensors]          (raw; sigmoid for P(MLD present))."""
        b = x.shape[0]
        x = x.reshape(b, -1, x.shape[-1])
        feats = self.backbone(x)                            # [B, width, N_BINS]
        loc = torch.cat([h(feats) for h in self.loc_heads], dim=1)   # [B, S, N_BINS]
        pooled = feats.mean(dim=2)                           # [B, width]
        pres = torch.cat([h(pooled) for h in self.pres_heads], dim=1)  # [B, S]
        return loc, pres


def _soft_argmax_depth(loc_logits, depth_centers):
    """Expected depth under softmax-over-depth. loc_logits [B,S,N] -> [B,S] (metres)."""
    p = torch.softmax(loc_logits, dim=2)                     # [B,S,N]
    dc = torch.as_tensor(depth_centers, dtype=p.dtype, device=p.device)
    return (p * dc).sum(dim=2)


def mld_loss(loc_logits, pres_logits, true_bin, present, has_label,
             depth_centers, w_ce=1.0, w_dist=0.05, w_pres=1.0):
    """Composite objective.
      loc_logits [B,S,N], pres_logits [B,S]
      true_bin   [B,S] long  : index of the true MLD bin (ignored where not present)
      present    [B,S] float : 1 if this sensor has a REAL MLD, 0 if no-MLD
      has_label  [B,S] float : 1 if this sensor was labeled at all (present or no-MLD)
    Localization terms apply ONLY where present==1 & has_label==1.
    Presence BCE applies wherever has_label==1."""
    B, S, N = loc_logits.shape
    loc_mask = (present * has_label)                         # [B,S]
    # Cross-entropy of softmax-over-depth to the true bin.
    logp = torch.log_softmax(loc_logits, dim=2)             # [B,S,N]
    ce = -logp.gather(2, true_bin.clamp(0, N - 1).unsqueeze(2)).squeeze(2)  # [B,S]
    # Soft-argmax distance (metres) to true depth.
    dc = torch.as_tensor(depth_centers, dtype=loc_logits.dtype, device=loc_logits.device)
    exp_depth = (torch.softmax(loc_logits, dim=2) * dc).sum(dim=2)          # [B,S]
    true_depth = dc[true_bin.clamp(0, N - 1)]                              # [B,S]
    dist = (exp_depth - true_depth).abs()                                  # [B,S]
    loc_term = (w_ce * ce + w_dist * dist) * loc_mask
    loc_den = loc_mask.sum().clamp(min=1.0)
    # Presence BCE over all labeled sensors.
    pres_bce = nn.functional.binary_cross_entropy_with_logits(
        pres_logits, present, reduction="none") * has_label               # [B,S]
    pres_den = has_label.sum().clamp(min=1.0)
    return loc_term.sum() / loc_den + w_pres * (pres_bce.sum() / pres_den)


def predict(loc_logits, pres_logits, depth_centers, pres_thresh=0.5):
    """Decode one or a batch into (depth or None, presence_prob, confidence).
    Works on torch tensors [S,N]/[S] for a single example. Returns lists over sensors."""
    import numpy as np
    loc = loc_logits.detach().cpu().numpy()
    pres = torch.sigmoid(pres_logits).detach().cpu().numpy()
    out = []
    for si in range(loc.shape[0]):
        p = np.exp(loc[si] - loc[si].max()); p /= p.sum()
        i = int(np.argmax(p))
        depth = float(depth_centers[i])
        pr = float(pres[si])
        out.append((depth if pr >= pres_thresh else None, pr, float(p[i])))
    return out


def peak_from_heatmap(heatmap, depth_centers, min_conf=0.3):
    """DEPRECATED (old sigmoid-heatmap decode). Kept for any legacy caller; prefer predict()."""
    import numpy as np
    i = int(np.argmax(heatmap))
    conf = float(heatmap[i])
    if conf < min_conf:
        return None, conf
    return float(depth_centers[i]), conf
