"""
model.py — shared 1D-CNN backbone + 4 per-sensor heatmap heads.

Input : [batch, 2, N_BINS]  per sensor (filtered value, local std). All 4 sensors share
        ONE backbone (so each head benefits from cross-sensor features via joint training);
        at forward time we run the backbone per sensor-channel-pair and each head reads the
        shared features. Simpler + effective first cut: stack the 4 sensors' 2-ch inputs into
        an 8-ch input, one backbone, 4 heads each emitting a heatmap over depth.
Output: [batch, 4, N_BINS]  one heatmap per sensor (sigmoid 0..1).

Loss   : per-bin BCE, MASKED to sensors whose label is present for that profile (absent
         sensors contribute nothing). "no MLD" is a flat (all-zero) target — learned like
         any other target, no special class.
"""
import torch
import torch.nn as nn

from mld.mld_config import SENSORS, N_BINS

N_SENSORS = len(SENSORS)


class MLDNet(nn.Module):
    def __init__(self, n_bins=N_BINS, n_sensors=N_SENSORS, width=32):
        super().__init__()
        in_ch = n_sensors * 2   # 4 sensors x {filtered, localstd}
        # Backbone: stacked 1D convolutions (padding keeps length = n_bins).
        self.backbone = nn.Sequential(
            nn.Conv1d(in_ch, width, kernel_size=7, padding=3), nn.ReLU(),
            nn.Conv1d(width, width, kernel_size=7, padding=3), nn.ReLU(),
            nn.Conv1d(width, width, kernel_size=7, padding=3), nn.ReLU(),
            nn.Conv1d(width, width, kernel_size=5, padding=2), nn.ReLU(),
        )
        # One heatmap head per sensor: 1x1 conv to a single depth-channel.
        self.heads = nn.ModuleList(
            [nn.Conv1d(width, 1, kernel_size=1) for _ in range(n_sensors)])

    def forward(self, x):
        # x: [B, n_sensors, 2, N_BINS] -> [B, n_sensors*2, N_BINS]
        b = x.shape[0]
        x = x.reshape(b, -1, x.shape[-1])
        feats = self.backbone(x)                       # [B, width, N_BINS]
        outs = [head(feats) for head in self.heads]    # each [B, 1, N_BINS]
        return torch.sigmoid(torch.cat(outs, dim=1))   # [B, n_sensors, N_BINS]


def masked_heatmap_loss(pred, target, has_label):
    """pred/target: [B, n_sensors, N_BINS]; has_label: [B, n_sensors] bool.
    Per-bin BCE averaged only over (batch, sensor) pairs that have a label."""
    bce = nn.functional.binary_cross_entropy(pred, target, reduction="none")  # [B,S,N]
    per_sensor = bce.mean(dim=2)                                              # [B,S]
    m = has_label.float()
    denom = m.sum().clamp(min=1.0)
    return (per_sensor * m).sum() / denom


def peak_from_heatmap(heatmap, depth_centers, min_conf=0.3):
    """Turn one predicted heatmap (np array [N_BINS]) into (mld_depth, confidence).
    Confidence = peak height (0..1). Returns (None, conf) if below min_conf => 'no MLD'."""
    import numpy as np
    i = int(np.argmax(heatmap))
    conf = float(heatmap[i])
    if conf < min_conf:
        return None, conf
    return float(depth_centers[i]), conf
