"""
dataset.py — build MLD training examples from pp06 shards + human label CSVs.

For each labeled profile (one GPI may have labels for several of the 4 sensors):
  - load each sensor's pp06 shard, bin onto the 0-200 m / 1 m grid (200 bins),
  - per bin: filtered value (adaptive Savitzky-Golay per the label's recorded filter
    params) and local std of (raw - filtered)  -> 2-channel input,
  - a presence mask (which bins held a real sample),
  - convert the human mld_depth to a Gaussian target heatmap (flat if no_mld_recorded).

Emits one example per GPI carrying all available sensors + a per-sensor label-present mask
(so the shared-backbone model can skip heads with no label for that GPI).

Filter note: the labels store filter_key/filter_p1/filter_p2 (e.g. adaptive_savgol_std,
51, 0.891). We reproduce the SAME filter used at labeling time so the input matches what the
human saw. If SciPy/params are unavailable we fall back to a plain Savitzky-Golay.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op
from mld.mld_config import (SENSORS, N_BINS, DEPTH_MIN, DEPTH_MAX, DEPTH_BIN,
                            HEATMAP_SIGMA_M, labels_csv)

try:
    from scipy.signal import savgol_filter
except Exception:
    savgol_filter = None

# Bin centres (0.5, 1.5, ... 199.5) and edges for np.digitize.
BIN_EDGES = np.linspace(DEPTH_MIN, DEPTH_MAX, N_BINS + 1)
BIN_CENTERS = 0.5 * (BIN_EDGES[:-1] + BIN_EDGES[1:])


def _odd(x):
    x = int(round(x))
    return x if x % 2 == 1 else x + 1


def adaptive_savgol(values, filter_key, p1, p2):
    """EXACT port of MLD.py's filter (the tool that produced the human labels), so the
    training 'filtered' channel matches what the annotator saw. Returns (filtered, rough)
    where `rough` is the local roughness (residual-from-light; MAD*1.4826 for _mad).
    Default filter for the R labels: adaptive_savgol_mad."""
    n = len(values)
    if savgol_filter is None or filter_key in (None, "None") or n < 5:
        return values.copy(), np.zeros(n)
    try:
        win = _odd(p1)
        win = max(3, min(win, n if n % 2 == 1 else n - 1))
        if filter_key == "savgol":
            poly = max(1, min(int(round(p2)), win - 1))
            f = savgol_filter(values, win, poly)
            return f, np.abs(values - f)
        # adaptive_savgol_std / _mad
        heavy_win = _odd(min(win * 3, n if n % 2 == 1 else n - 1))
        heavy_win = max(win, heavy_win)
        light = savgol_filter(values, win, min(2, win - 1))
        heavy = savgol_filter(values, heavy_win, min(2, heavy_win - 1))
        resid = values - light
        win_r = _odd(win)  # rolling window (odd, centered) — matches the per-point half-window
        s = pd.Series(resid)
        if filter_key == "adaptive_savgol_mad":
            med = s.rolling(win_r, center=True, min_periods=1).median()
            rough = (s - med).abs().rolling(win_r, center=True, min_periods=1).median().values * 1.4826
        else:
            rough = s.rolling(win_r, center=True, min_periods=1).std().fillna(0.0).values
        rmax = np.max(rough) if np.max(rough) > 0 else 1.0
        w = np.clip((rough / rmax) * float(p2), 0.0, 1.0)
        filtered = (1.0 - w) * light + w * heavy
        return filtered, rough
    except Exception:
        return values.copy(), np.zeros(n)


def _bin_profile(depth, value, filter_key="adaptive_savgol_mad", p1=51, p2=2.0):
    """Bin one sensor profile onto the depth grid. Returns (filtered[N_BINS],
    localstd[N_BINS], mask[N_BINS]). `localstd` = local roughness from the SAME filter
    used at labeling time (residual-from-light; MAD-based for _mad) — the jitter signal
    the annotator saw, which marks cline onset."""
    filtered = np.full(N_BINS, np.nan)
    localstd = np.zeros(N_BINS)
    mask = np.zeros(N_BINS, dtype=np.float32)

    good = ~(np.isnan(depth) | np.isnan(value))
    depth, value = depth[good], value[good]
    if len(value) < 5:
        return filtered, localstd, mask

    # Sort shallow->deep for a stable filter, then bin.
    order = np.argsort(depth)
    d, v = depth[order], value[order]
    vf, rough = adaptive_savgol(v, filter_key, p1, p2)

    idx = np.digitize(d, BIN_EDGES) - 1
    idx = np.clip(idx, 0, N_BINS - 1)
    for b in range(N_BINS):
        sel = idx == b
        if not np.any(sel):
            continue
        filtered[b] = np.mean(vf[sel])
        localstd[b] = np.mean(rough[sel])
        mask[b] = 1.0
    # Fill unobserved bins with the nearest observed filtered value (mask stays 0 so
    # the model can down-weight them); simplest is forward/back fill.
    filled = pd.Series(filtered).ffill().bfill().values
    filtered = np.where(np.isnan(filled), 0.0, filled)
    return filtered.astype(np.float32), localstd.astype(np.float32), mask


def _heatmap(mld_depth, no_mld):
    """Gaussian target centred at mld_depth (flat zeros if no MLD)."""
    hm = np.zeros(N_BINS, dtype=np.float32)
    if no_mld or mld_depth is None or np.isnan(mld_depth):
        return hm
    sigma = HEATMAP_SIGMA_M / DEPTH_BIN
    hm = np.exp(-0.5 * ((BIN_CENTERS - mld_depth) / sigma) ** 2).astype(np.float32)
    return hm


def load_examples(sites=("sb", "oo", "ab"), who="R"):
    """Return a list of example dicts, one per labeled GPI:
       { site, gpi, timestamp,
         input:  [n_sensors, 2, N_BINS] float32,
         mask:   [n_sensors, N_BINS]    float32   (bin presence),
         target: [n_sensors, N_BINS]    float32   (heatmaps),
         has_label: [n_sensors] bool,             (label present for this sensor?)
         is_nomld:  [n_sensors] bool }
    """
    examples = []
    for site in sites:
        csv = labels_csv(site, who)
        if not csv.exists():
            print(f"  no labels for {site}: {csv.name}")
            continue
        lab = pd.read_csv(csv, parse_dates=["timestamp"])
        for gpi, grp in lab.groupby("gpi"):
            year = pd.Timestamp(grp["timestamp"].iloc[0]).year
            ex_in = np.zeros((len(SENSORS), 2, N_BINS), np.float32)
            ex_mask = np.zeros((len(SENSORS), N_BINS), np.float32)
            ex_tgt = np.zeros((len(SENSORS), N_BINS), np.float32)
            has_label = np.zeros(len(SENSORS), bool)
            is_nomld = np.zeros(len(SENSORS), bool)
            any_sensor = False
            for si, sensor in enumerate(SENSORS):
                row = grp[grp["sensor"] == sensor]
                if len(row) == 0:
                    continue
                row = row.iloc[0]
                shard = _find_shard(site, year, sensor, int(gpi))
                if shard is None:
                    continue
                try:
                    ds = xr.open_dataset(shard)
                    depth = np.abs(ds["depth"].values)
                    value = ds[sensor].values
                    ds.close()
                except Exception:
                    continue
                filt, lstd, mask = _bin_profile(
                    depth, value,
                    filter_key=str(row.get("filter_key", "adaptive_savgol_mad")),
                    p1=row.get("filter_p1", 51), p2=row.get("filter_p2", 2.0))
                ex_in[si, 0] = filt
                ex_in[si, 1] = lstd
                ex_mask[si] = mask
                nomld = bool(row.get("no_mld_recorded", False))
                ex_tgt[si] = _heatmap(row.get("mld_depth"), nomld)
                has_label[si] = True
                is_nomld[si] = nomld
                any_sensor = True
            if any_sensor:
                examples.append(dict(site=site, gpi=int(gpi),
                                     timestamp=pd.Timestamp(grp["timestamp"].iloc[0]),
                                     input=ex_in, mask=ex_mask, target=ex_tgt,
                                     has_label=has_label, is_nomld=is_nomld))
    print(f"loaded {len(examples)} labeled profiles across {list(sites)}")
    return examples


def _find_shard(site, year, sensor, gpi):
    """Locate the pp06 shard for (site, year, sensor, gpi)."""
    year_dir = op.postproc_dir("pp06", year, site)
    if not year_dir.exists():
        return None
    hits = list(year_dir.glob(f"*_{sensor}_{year}_*_{gpi}_*.nc"))
    return hits[0] if hits else None


if __name__ == "__main__":
    # Dry run: load and report shapes, no training.
    exs = load_examples()
    if exs:
        e = exs[0]
        print("example0:", e["site"], "gpi", e["gpi"],
              "input", e["input"].shape, "target", e["target"].shape,
              "has_label", e["has_label"].tolist(), "is_nomld", e["is_nomld"].tolist())
        import numpy as _np
        n_lab = sum(int(e["has_label"].sum()) for e in exs)
        n_nomld = sum(int((_np.array(e["is_nomld"]) & _np.array(e["has_label"])).sum()) for e in exs)
        print(f"total sensor-labels: {n_lab}, of which no-MLD: {n_nomld}")
