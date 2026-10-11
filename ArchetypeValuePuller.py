"""
ArchetypeValuePuller.py — read the clean MLD archetype shards (from MLDObservations.md)
and report, per (site, gpi, sensor): units, surface value (mean of bins < 15 m), deep
asymptote (mean of the deepest ~20 m), full value span, and depth coverage.

Purpose: ground the synthetic-dataset value envelopes (surface value, deep asymptote, and
implied cline magnitude) in REAL pp06 numbers rather than literature guesses, since the
MLD 1D-CNN appears to take inputs in raw physical units (no per-sensor standardization).

pp06 is read via ooipaths; density is derived in the pipeline, not needed here.

Run (WSL / argosy conda env):
    source ~/miniconda3/etc/profile.d/conda.sh && conda activate argosy
    python ~/argosy/ArchetypeValuePuller.py
"""
import sys
from pathlib import Path

import numpy as np
import xarray as xr

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op

# Clean-MLD archetypes from MLDObservations.md "Good archetype profiles"
# (No-MLD rows omitted — no mixed-layer value/asymptote to characterize).
# (site, gpi, sensor_varname, human_mld_m)
ARCHETYPES = [
    ("oo", 567, "temperature", 55.0),
    ("oo", 881, "temperature", 52.6),
    ("oo", 1027, "temperature", 47.4),
    ("oo", 2561, "temperature", 61.1),
    ("oo", 2547, "salinity", 61.8),
    ("oo", 2561, "salinity", 61.8),
    ("oo", 2667, "salinity", 72.0),
    ("oo", 3913, "salinity", 24.0),
    ("oo", 2667, "dissolvedoxygen", 72.4),
    ("oo", 2747, "dissolvedoxygen", 55.2),
    ("oo", 4443, "dissolvedoxygen", 63.8),
]

SURFACE_SPAN_M = 10.0  # "surface" = shallowest this-many metres OF THIS PROFILE
DEEP_SPAN_M = 20.0     # "deep asymptote" = deepest this-many metres


def _find_shard(site, gpi, sensor):
    base = op.postproc_base(site) / "pp06"
    if not base.exists():
        return None
    for yd in sorted(base.glob("[0-9][0-9][0-9][0-9]")):
        hits = list(yd.glob(f"*_{sensor}_*_{gpi}_*.nc"))
        if hits:
            return hits[0]
    return None


def main():
    print(f"{'site':4} {'gpi':>5} {'sensor':16} {'units':10} "
          f"{'dmin':>6} {'surf':>8} {'deep':>8} {'cline|d|':>9} {'min':>8} {'max':>8} {'depth(m)':>12} mld")
    print("-" * 118)
    for site, gpi, sensor, mld in ARCHETYPES:
        shard = _find_shard(site, gpi, sensor)
        if shard is None:
            print(f"{site:4} {gpi:>5} {sensor:16} NOT FOUND")
            continue
        try:
            ds = xr.open_dataset(shard)
            d = np.abs(ds["depth"].values)
            v = ds[sensor].values
            units = ds[sensor].attrs.get("units", "?")
            ds.close()
        except Exception as e:
            print(f"{site:4} {gpi:>5} {sensor:16} ERROR {e}")
            continue
        good = ~(np.isnan(d) | np.isnan(v))
        d, v = d[good], v[good]
        if len(v) < 5:
            print(f"{site:4} {gpi:>5} {sensor:16} too few points")
            continue
        o = np.argsort(d)
        d, v = d[o], v[o]
        # "surface" = mean over the shallowest SURFACE_SPAN_M metres THIS profile actually
        # sampled (relative to its own d_min), so profiles starting deep than a fixed cutoff
        # still yield a value instead of NaN.
        dmin = d.min()
        surf = np.nanmean(v[d <= dmin + SURFACE_SPAN_M])
        deep = np.nanmean(v[d > d.max() - DEEP_SPAN_M])
        cline = abs(deep - surf)
        print(f"{site:4} {gpi:>5} {sensor:16} {str(units):10} "
              f"{dmin:6.0f} {surf:8.2f} {deep:8.2f} {cline:9.2f} {np.nanmin(v):8.2f} {np.nanmax(v):8.2f} "
              f"{d.min():5.0f}-{d.max():<6.0f} {mld}")


if __name__ == "__main__":
    main()
