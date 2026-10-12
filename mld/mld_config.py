"""
mld_config.py — shared constants for the MLD 1D-CNN pipeline.

Predicts per-sensor Mixed Layer Depth (heads = temperature, salinity, dissolvedoxygen;
density dropped 2026-10-10 as a derived/redundant feature) from pp06 profiles using a shared
1D-CNN backbone + heatmap-over-depth heads. See Analysis.md ("Machine Learning methods for
automating SP profile annotation") and BR.md. Code in ~/argosy/mld/; generated data in ~/ooi/mld/.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op

# The MLD sensors (order = head order everywhere).
# Density was DROPPED 2026-10-10: it is derived from T, S, depth (TEOS-10), so as an input it
# adds no information and as a prediction head it re-learns a known function. A density MLD, if
# wanted, is COMPUTED from predicted T/S, not learned. See SyntheticMLDPlan.md + WorkingWithAgenticAI.md L3.
SENSORS = ["temperature", "salinity", "dissolvedoxygen"]

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

# Input channels per sensor:
#   1 (DEFAULT) -> [filtered value] only.
#   2           -> [filtered value, local roughness = std/MAD of (raw - filtered)].
# The roughness channel is a HYPOTHESIS (the annotator used "scratchiness" as a cue). Default is
# 1 so the noise channel must be CONSCIOUSLY opted into. Override via the MLD_INPUT_CHANNELS env
# var (e.g. `MLD_INPUT_CHANNELS=2 python mld/train.py`) or train.py's --input-channels flag.
# A presence mask rides alongside for masking, not as a learned feature.
N_INPUT_CHANNELS = int(os.environ.get("MLD_INPUT_CHANNELS", "1"))
if N_INPUT_CHANNELS not in (1, 2):
    raise ValueError(f"MLD_INPUT_CHANNELS must be 1 or 2, got {N_INPUT_CHANNELS}")

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
