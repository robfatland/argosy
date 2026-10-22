"""
synthetic.py — generate a SHADOW dataset of artificial pp06 profiles with KNOWN MLD ground
truth, written as real pp06-format NetCDF shards in a parallel universe (~/ooi/synthetic/).

Why: train the MLD 1-D CNN on real human-labeled pp06, then run it against these synthetic
profiles to probe generalization across the MLD operating envelope. Because we KNOW the MLD at
generation time, the generator IS the annotator — it writes the label CSV in the same pass (no
MLD.py hand-labeling). See SyntheticMLDPlan.md for the full design + decisions.

Key properties (all from SyntheticMLDPlan.md):
  - Sensors T, S, DO are synthesized; DENSITY is DERIVED via TEOS-10 (gsw) and written as a shard
    for completeness, but gets NO label row (density dropped from the model as a redundant feature).
  - Temperature is the baseline MLD (elbow at z0); S and DO elbow depths ~ Gaussian(z0, 4 m).
    T cline decreasing, S increasing, DO decreasing. Sharp elbow rolling to zero-gradient in the
    deepest ~20 m.
  - Shallowest sampled depth d_min ~ triangular(5, 20, 40). Deepest ~195-199 m. Irregular sampling,
    per-profile sample count ~ U(200, 3000) to mimic real shards.
  - Mixed-layer STEM carries smooth low-frequency noise (feeds the model's roughness channel);
    below-cline noise ~0 (tunable).
  - 80% MLD-present, 20% no-MLD. No-MLD = already-in-gradient from the top, no constant layer.
  - Synthetic GPIs in a reserved high band (>= 900000); synthetic time frame starts year 9000.
  - Shards are RAW (depth,value) samples over a `time` axis — NOT pre-binned; the existing
    dataset._bin_profile does the binning, exactly like real data.

Output tree (parallel universe, never inside a real site):
  ~/ooi/synthetic/postproc/pp06/<9000+>/RCA_synthetic_sp_<sensor>_<yyyy>_<ddd>_<gpi>_<daily>_V1.nc
  ~/ooi/synthetic/metadata/annotations/mld_labels_synthetic_block00_synthetic.csv
  ~/ooi/synthetic/metadata/annotations/mld_candidates_synthetic_block00.csv

Run:  python ~/argosy/mld/synthetic.py            # generate full sweep
      python ~/argosy/mld/synthetic.py --dry-run  # report plan + a few profiles, write nothing
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op

try:
    import gsw
except Exception:
    gsw = None

# ── parallel-universe location (NOT a registered ooipaths site) ───────────────
SYN_ROOT = op.OOI_ROOT / "synthetic"
SYN_PP06 = SYN_ROOT / "postproc" / "pp06"
SYN_ANNOT = SYN_ROOT / "metadata" / "annotations"
GPI_BASE = 900000          # reserved synthetic GPI band
YEAR_BASE = 9000           # synthetic time frame start
WHO = "synthetic"
FILTER_KEY, FILTER_P1, FILTER_P2 = "adaptive_savgol_mad", 59, 2  # label convention

# ── real per-sensor envelopes (from ArchetypeValuePuller.py, oo pp06, 2026-10-10) ──
# surface value, deep asymptote, and the 3 cline-magnitude sweep levels (low/mid/high).
# direction encoded by surface vs deep sign.
ENV = {
    "temperature":     dict(units="degrees_Celsius", surf=12.0, deep=8.0,
                            long_name="Seawater Temperature", standard_name="sea_water_temperature",
                            mag_levels=(2.8, 3.9, 4.9), noise=0.10),
    "salinity":        dict(units="1", surf=32.55, deep=33.90,
                            long_name="Practical Salinity", standard_name="sea_water_practical_salinity",
                            mag_levels=(1.3, 1.35, 1.4), noise=0.04),
    "dissolvedoxygen": dict(units="umol kg-1", surf=265.0, deep=120.0,
                            long_name="Dissolved Oxygen - Pressure Temp Sal Corrected (CTD)",
                            standard_name=None, mag_levels=(138.0, 142.0, 146.0), noise=4.0),
}
SYNTH_SENSORS = ["temperature", "salinity", "dissolvedoxygen"]  # density derived separately

# per-site latitude for gsw pressure (approx platform lat; see Umbrella.md / RCA site tables)
SITE_LAT = {"sb": 44.52897, "oo": 44.37415, "ab": 45.83049}

# ── sweep axes (SyntheticMLDPlan.md) ──────────────────────────────────────────
Z0_LEVELS = [20.0, 35.0, 50.0, 65.0, 80.0]       # T baseline MLD depth (m)
MAG_LEVELS = [0, 1, 2]                            # index into each sensor's mag_levels
# Cline transition scale (m) = tanh e-folding; LARGER == GENTLER slope. Widened 2026-10-10
# (was 3/6/12) because the cline was dominating the signal as a near-vertical cliff.
SHARP_LEVELS = {"sharp": 10.0, "medium": 18.0, "gradual": 28.0}
# Elbow radius (m) sweep: how rounded the stem->cline corner is, INDEPENDENT of cline slope.
# 1 = near-sharp corner, 8 = broadly rounded. Added as a sweep axis 2026-10-10.
ELBOW_LEVELS = {"tight": 1.0, "round": 3.0, "broad": 6.0}
REPLICATES = 10                                  # per (z0 x mag x sharp x elbow) combo
# No-MLD block: generated as a CONTIGUOUS GPI block AFTER all MLD-present profiles (2026-10-10),
# so no-MLD cases occupy a known, selectable range. Set N_NOMLD = 0 to disable.
N_NOMLD = 300


def _tanh_cline(depth, z0, surf, deep, sharpness, elbow_r=0.0, rollover_m=20.0, dmax=199.0):
    """Textbook MLD profile:
      - FLAT `surf` for all depth <= z0 (the mixed-layer STEM — genuinely constant),
      - a ROUNDED elbow of radius `elbow_r` m at z0 (softplus knee),
      - below z0 a one-sided tanh descending toward `deep` with e-folding `sharpness`
        (larger == gentler); the whole cline lives BELOW the elbow,
      - gradient forced flat in the deepest `rollover_m`.
    `depth` ascends 0->dmax. (Previous version centred the tanh on z0, so half the
    transition sat ABOVE z0 and ate the stem at shallow z0 — fixed 2026-10-10.)"""
    # One-sided transition with a ROUNDED elbow. `elbow_r` (m) = elbow radius:
    #   elbow_r -> 0 : hard corner at z0 (single-pixel elbow), the previous behavior,
    #   elbow_r > 0  : softplus knee rounds the corner over ~elbow_r metres, then feeds into
    #                  the same tanh cline slope (`sharpness`) below. Elbow radius and cline
    #                  slope are INDEPENDENT knobs.
    if elbow_r <= 0:
        below = np.maximum(depth - z0, 0.0)
    else:
        # Softplus is symmetric about its centre, so centring it on z0 would round the corner
        # on BOTH sides and soften the last ~elbow_r m of the (supposedly flat) stem. Shift the
        # knee centre DOWN by ~4*elbow_r so deviation from flat above z0 is negligible: the stem
        # stays flat right up to z0 (the MLD), and the rounding happens just BELOW z0 feeding
        # into the cline. (4x, up from 3x, to keep a broad elbow from inclining a short shallow
        # stem.) Clip the exponent to avoid overflow for deep points.
        d = depth - (z0 + 4.0 * elbow_r)
        xr = d / elbow_r
        knee = np.where(xr > 30, d, elbow_r * np.log1p(np.exp(np.clip(xr, -30, 30))))
        below = np.maximum(knee, 0.0)
    frac = np.tanh(below / sharpness)                          # 0 at/above z0 -> 1 deep
    val = surf + (deep - surf) * frac
    # Force zero gradient in the last rollover_m: hold the value reached at (dmax - rollover_m).
    hold_from = dmax - rollover_m
    v_hold = surf + (deep - surf) * np.tanh(max(hold_from - z0, 0.0) / sharpness)
    val = np.where(depth >= hold_from, v_hold, val)
    return val


def _gradient_only(depth, surf, deep, dmin, dmax=199.0, inflect=False, rng=None):
    """No-MLD profile: NO flat stem — already in a gradient at the shallowest point, with a
    GRADUAL roll to a flat deep asymptote near dmax. Zero additive noise.

    Spec (2026-10-10): on a chart with the sensor value-range on x and 0..200 m on y, each
    normalized to [0,1], the ABSOLUTE initial slope |d(value_norm)/d(depth_norm)| at the top
    must exceed 1/6. We build the shape in normalized space to enforce that geometrically, then
    scale back to physical units.

      - `inflect=False`: a single concave bend — steep at the top, easing to flat at depth.
      - `inflect=True` : an S-shape with a mid-profile inflection (steep top, a gentler middle
        'knee', then re-steepening and finally flattening) — still no flat stem up top.
    """
    span = max(dmax - dmin, 1.0)
    t = np.clip((depth - dmin) / span, 0.0, 1.0)          # 0 at top .. 1 at bottom (normalized depth)

    if not inflect:
        # Concave profile: f(0)=0, f(1)=1, flat at t=1 (f'(1)=0), steep at t=0.
        # f(t) = 1 - (1-t)^k. f'(0) = k  -> initial normalized slope = k * (value_norm span=1).
        # Pick k in [2.0, 3.5] so initial slope k >> 1/6 (comfortably steep), flat at depth.
        k = 2.0 + (0.0 if rng is None else rng.uniform(0.0, 1.5))
        f = 1.0 - (1.0 - t) ** k
    else:
        # S-shape with an inflection but STILL steep at the very top (no flat stem). Blend a
        # steep top segment with a smootherstep middle so there is a visible knee, then flatten.
        k = 2.0 + (0.0 if rng is None else rng.uniform(0.0, 1.0))
        top = 1.0 - (1.0 - t) ** k                        # steep-at-top, concave
        smoother = t * t * (3.0 - 2.0 * t)                # S-curve (inflection at t=0.5)
        w = t                                             # weight shifts top->S with depth
        f = (1.0 - w) * top + w * smoother
        # guarantee flat asymptote: ease the last 10% to df/dt -> 0
        tail = np.clip((t - 0.9) / 0.1, 0.0, 1.0)
        f = f * (1.0 - tail) + 1.0 * tail
    return surf + (deep - surf) * f


def _smooth_noise(n, amp, rng, scale=12):
    """Smooth low-frequency wander (not white): cumulative-ish via filtered gaussian."""
    if amp <= 0 or n == 0:
        return np.zeros(n)
    raw = rng.standard_normal(n)
    # moving-average smooth to kill high-freq content
    k = max(3, int(scale))
    kernel = np.ones(k) / k
    sm = np.convolve(raw, kernel, mode="same")
    sm = sm / (np.std(sm) + 1e-9) * amp
    return sm


def _make_profile(rng, z0, mag_idx, sharpness, is_nomld, elbow_r=0.0, inflect=False):
    """Build one synthetic profile across the 3 sensors + derived density.
    Returns dict: depth[n], per-sensor value[n], per-sensor true MLD (or None), d_min."""
    dmin = float(np.clip(rng.triangular(5, 20, 40), 5, 40))
    dmax = float(rng.uniform(195, 199))
    # MLD-present profiles need a real mixed-layer STEM above the elbow. If the drawn d_min
    # lands too close to (or below) z0, there is no textbook mixed layer — redraw d_min shallow
    # enough to leave >= MIN_STEM_M of constant layer above the shallowest sensor elbow.
    MIN_STEM_M = 10.0                             # every sensor's mixed layer >= this
    # Elbow jitter scaled to z0 so shallow profiles don't get wild S/DO offsets:
    # sd = min(4 m, 0.15*z0).  (At z0=20 -> 3 m; at z0>=27 -> 4 m.)
    jit_sd = min(4.0, 0.15 * z0)
    n = int(rng.integers(200, 3000))
    # Ascent sampling: depth descends over time (deep->shallow) with jitter; store ascending-depth
    # order is handled by dataset (_bin_profile sorts). We emit as a time series deep->shallow.
    # elbow per sensor: T at z0; S, DO ~ Gaussian(z0, jit_sd)
    z0_sensor = {
        "temperature": z0,
        "salinity": float(rng.normal(z0, jit_sd)),
        "dissolvedoxygen": float(rng.normal(z0, jit_sd)),
    }
    # Guarantee a >= MIN_STEM_M mixed layer for EVERY sensor on MLD-present profiles:
    # push d_min shallow enough that even the shallowest elbow has >= MIN_STEM_M above it.
    if not is_nomld:
        shallowest_elbow = min(z0_sensor.values())
        ceiling = shallowest_elbow - MIN_STEM_M
        if dmin > ceiling:
            lo, hi = 5.0, max(5.5, ceiling)
            mode = min(20.0, hi)
            dmin = float(np.clip(rng.triangular(lo, max(lo, min(mode, hi)), hi), lo, hi))

    depth = np.sort(rng.uniform(dmin, dmax, n))        # ascending depth
    out = {"depth": depth, "dmin": dmin, "dmax": dmax, "mld": {}}
    for s in SYNTH_SENSORS:
        e = ENV[s]
        mag = e["mag_levels"][mag_idx]
        # orient surface/deep so the cline direction matches the sensor; magnitude = |surf-deep|
        if e["surf"] >= e["deep"]:   # decreasing (T, DO)
            surf, deep = e["surf"], e["surf"] - mag
        else:                        # increasing (S)
            surf, deep = e["surf"], e["surf"] + mag
        if is_nomld:
            val = _gradient_only(depth, surf, deep, dmin, dmax, inflect=inflect, rng=rng)
            mld = None
        else:
            zs = min(z0_sensor[s], dmax - 25.0)   # keep elbow off the deep rollover; stem
            zs = max(zs, dmin + MIN_STEM_M)       # already guaranteed >= MIN_STEM_M above dmin
            val = _tanh_cline(depth, zs, surf, deep, sharpness, elbow_r=elbow_r, dmax=dmax)
            mld = zs
            # NOISE OFF (2026-10-10): no additive noise, not even in the unfiltered signal.
            # (The stem-noise machinery is retained below for later re-enabling.)
            # stem = depth < zs
            # val = val + np.where(stem, _smooth_noise(n, e["noise"], rng), 0.0)
        out[s] = val
        out["mld"][s] = mld
    return out


def _derive_density(depth, temp, sal, lat):
    """In-situ density via TEOS-10 from synthetic T (practical) and S (practical)."""
    if gsw is None:
        return None
    p = gsw.p_from_z(-np.abs(depth), lat)           # pressure (dbar) from depth
    SA = gsw.SA_from_SP(sal, p, 0.0, lat)           # absolute salinity (lon~0 ok offshore)
    CT = gsw.CT_from_t(SA, temp, p)                 # conservative temp
    return gsw.rho(SA, CT, p)                        # in-situ density kg m-3


def _write_shard(path, sensor, depth, value, year, units, long_name, standard_name):
    """Write one pp06-format shard: dims (time,), data_vars depth + <sensor>, time coord."""
    n = len(depth)
    # NOTE: numpy/xarray store datetimes as ns-since-1970 int64, which overflows past ~year 2262.
    # Our sentinel year (9000+) lives in the FILENAME and the label CSV (as a string) — that is
    # what marks data synthetic. The time VALUES inside the NetCDF are never used for MLD (only
    # depth + the sensor var are), so we store an in-bounds placeholder time here.
    stored_year = min(year, 2200)
    t0 = np.datetime64(f"{stored_year:04d}-01-01T00:00:00", "ns")
    times = t0 + (np.arange(n) * np.timedelta64(1, "s")).astype("timedelta64[ns]")
    attrs = {"units": units, "long_name": long_name}
    if standard_name:
        attrs["standard_name"] = standard_name
    ds = xr.Dataset(
        {sensor: ("time", value.astype("float64"), attrs),
         "depth": ("time", np.abs(depth).astype("float64"),
                   {"units": "m", "long_name": "Depth calculated from pressure"})},
        coords={"time": ("time", times, {"long_name": "time", "standard_name": "time"})},
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(path)
    ds.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--clean", action="store_true",
                    help="delete the existing synthetic tree (~/ooi/synthetic/) before generating")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--lat-site", default="oo", choices=list(SITE_LAT),
                    help="which site's latitude to use for gsw density (default oo)")
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    lat = SITE_LAT[args.lat_site]

    if args.clean and not args.dry_run:
        import shutil
        # Scoped strictly to the synthetic parallel universe — never a real site tree.
        assert SYN_ROOT.name == "synthetic" and SYN_ROOT.parent == op.OOI_ROOT, \
            f"refusing to clean unexpected path {SYN_ROOT}"
        if SYN_ROOT.exists():
            shutil.rmtree(SYN_ROOT)
            print(f"cleaned {SYN_ROOT}")
        else:
            print(f"(nothing to clean; {SYN_ROOT} does not exist)")

    # build the sweep plan
    combos = [(z0, m, name, sc, ename, er)
              for z0 in Z0_LEVELS for m in MAG_LEVELS
              for name, sc in SHARP_LEVELS.items()
              for ename, er in ELBOW_LEVELS.items()]
    n_present = len(combos) * REPLICATES
    n_nomld = N_NOMLD
    total = n_present + n_nomld
    print(f"sweep: {len(combos)} combos x {REPLICATES} replicates = {n_present} MLD-present")
    print(f"       + {n_nomld} no-MLD (contiguous block AFTER) = {total} profiles total")
    print(f"       lat={lat} ({args.lat_site})  gsw={'OK' if gsw else 'MISSING'}")
    if gsw is None:
        print("  WARNING: gsw not importable — density shards will be SKIPPED.")

    # assign GPIs and spread across synthetic years 9000.. (daily_index cycles 1..9)
    label_rows, cand_rows = [], []
    gpi = GPI_BASE
    made = 0

    def emit(profile, present):
        nonlocal gpi, made
        year = YEAR_BASE + (made // 3285)           # ~9/day*365 -> roll year like real GPIs
        ddd = (made % 365) + 1
        daily = (made % 9) + 1
        depth = profile["depth"]
        # sensor shards
        for s in SYNTH_SENSORS:
            e = ENV[s]
            fn = f"RCA_synthetic_sp_{s}_{year}_{ddd:03d}_{gpi}_{daily}_V1.nc"
            path = SYN_PP06 / str(year) / fn
            if not args.dry_run:
                _write_shard(path, s, depth, profile[s], year,
                             e["units"], e["long_name"], e["standard_name"])
            mld = profile["mld"][s]
            label_rows.append(dict(
                timestamp=f"{year:04d}-01-01T00:00:00", gpi=gpi, sensor=s, who=WHO,
                mld_depth=(np.nan if mld is None else round(mld, 2)),
                no_mld_recorded=bool(mld is None),
                filter_key=FILTER_KEY, filter_p1=FILTER_P1, filter_p2=FILTER_P2))
        # density shard (derived) — NO label row
        temp, sal = profile["temperature"], profile["salinity"]
        dens = _derive_density(depth, temp, sal, lat)
        if dens is not None and not args.dry_run:
            fn = f"RCA_synthetic_sp_density_{year}_{ddd:03d}_{gpi}_{daily}_V1.nc"
            _write_shard(SYN_PP06 / str(year) / fn, "density", depth, dens, year,
                         "kg m-3", "Seawater Density", "sea_water_density")
        cand_rows.append(dict(gpi=gpi, year=year, is_nomld=(not present),
                              dmin=round(profile["dmin"], 1)))
        gpi += 1
        made += 1

    # MLD-present profiles across the sweep
    for (z0, m, name, sc, ename, er) in combos:
        for _ in range(REPLICATES):
            prof = _make_profile(rng, z0, m, sc, is_nomld=False, elbow_r=er)
            if args.dry_run and made < 3:
                _report(prof, z0, f"{name}/elbow={ename}({er:.0f}m)")
            emit(prof, present=True)
    # ── No-MLD block: contiguous, AFTER all MLD-present profiles ──
    # No elbow/z0 applies (no mixed layer). Vary magnitude + the inflection flag so examples
    # differ; alternate inflect True/False so BOTH shapes are present (user wants both).
    nomld_start_gpi = gpi
    for i in range(n_nomld):
        m = int(rng.integers(0, len(MAG_LEVELS)))
        inflect = bool(i % 2)                       # half plain-concave, half with an inflection
        prof = _make_profile(rng, 50.0, m, 6.0, is_nomld=True, inflect=inflect)
        if args.dry_run and i < 2:
            _report(prof, 0.0, f"NO-MLD inflect={inflect}")
        emit(prof, present=False)
    nomld_end_gpi = gpi - 1

    if args.dry_run:
        print(f"\nDRY RUN — would write {made} profiles x 4 shards + "
              f"{len(label_rows)} label rows. Nothing written.")
        return

    SYN_ANNOT.mkdir(parents=True, exist_ok=True)
    lab = pd.DataFrame(label_rows)
    lab.to_csv(SYN_ANNOT / f"mld_labels_synthetic_block00_{WHO}.csv", index=False)
    pd.DataFrame(cand_rows).to_csv(SYN_ANNOT / "mld_candidates_synthetic_block00.csv", index=False)
    n_present_lab = int((~lab["no_mld_recorded"]).sum())
    print(f"\nwrote {made} profiles -> {SYN_PP06}")
    print(f"labels: {len(lab)} rows ({n_present_lab} MLD, {len(lab)-n_present_lab} no-MLD) "
          f"-> {SYN_ANNOT}")
    if n_nomld:
        print(f"no-MLD GPI block: {nomld_start_gpi}..{nomld_end_gpi}")


def _report(prof, z0, sharp):
    import numpy as _np
    d = prof["depth"]
    def _f(v, nd=1):  # format a possibly-None MLD (no-MLD profiles have None)
        return "none" if v is None else f"{v:.{nd}f}"
    m = prof["mld"]
    print(f"  profile z0={z0} sharp={sharp} dmin={prof['dmin']:.1f} n={len(d)} "
          f"mld(T/S/DO)={_f(m['temperature'])}/{_f(m['salinity'])}/{_f(m['dissolvedoxygen'])}  "
          f"T[{_np.min(prof['temperature']):.1f},{_np.max(prof['temperature']):.1f}] "
          f"DO[{_np.min(prof['dissolvedoxygen']):.0f},{_np.max(prof['dissolvedoxygen']):.0f}]")


if __name__ == "__main__":
    main()
