"""
mld_config.py — shared constants for the MLD 1D-CNN pipeline.

Predicts per-sensor Mixed Layer Depth (4 heads: temperature, salinity, density,
dissolvedoxygen) from pp06 profiles using a shared 1D-CNN backbone + heatmap-over-depth
heads. See Analysis.md ("Machine Learning methods for automating SP profile annotation")
and BR.md. Code in ~/argosy/mld/; generated data in ~/ooi/mld/.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op

# The 4 MLD sensors (order = head order everywhere).
SENSORS = ["temperature", "salinity", "density", "dissolvedoxygen"]

# Depth grid: 0-200 m, 1 m bins (200 bins). Profiles rarely reach above ~5 m; those
# bins are marked absent via the presence mask rather than fabricated.
DEPTH_MIN = 0.0
DEPTH_MAX = 200.0
DEPTH_BIN = 1.0
N_BINS = int(round((DEPTH_MAX - DEPTH_MIN) / DEPTH_BIN))   # 200
DEPTH_GRID_EDGES = None   # computed in dataset.py via numpy

# Heatmap target: Gaussian bump (sigma in metres = bins) centred on the labeled MLD.
# no_mld_recorded -> flat (all-zero) target.
HEATMAP_SIGMA_M = 4.0

# Input channels per sensor: [filtered value, local std(raw - filtered)]. A presence
# mask (1 where a real sample fell in the bin, else 0) rides alongside as a 3rd plane
# used for masking, not as a learned feature.
N_INPUT_CHANNELS = 2

# ~/ooi/mld/ generated-data subfolders.
MLD_BASE = op.OOI_ROOT / "mld"
LABELS_DIR = MLD_BASE / "labels"        # (optional) consolidated label copies
SPLITS_DIR = MLD_BASE / "splits"        # train/val/test gpi lists
MODELS_DIR = MLD_BASE / "models"        # weights + model cards
INFER_DIR = MLD_BASE / "inference"      # predicted MLD metadata over full record

# Per-site human label CSV (Rob's pass, N=5 block sampling).
def labels_csv(site, who="R", block="block05"):
    return op.metadata_dir(site, "annotations") / f"mld_labels_{site}_{block}_{who}.csv"

def candidates_csv(site, block="block05"):
    return op.metadata_dir(site, "annotations") / f"mld_candidates_{site}_{block}.csv"
