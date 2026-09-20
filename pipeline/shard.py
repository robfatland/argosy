"""
pipeline/shard.py — Shard OOINET source files into per-sensor, per-profile redux files.

Single source of truth for the sharding logic (extracted from DataSharding.ipynb so the
notebook and the cloud/EC2 job call the SAME code). Site-parameterized via ooipaths;
runs locally (notebook `%run` / import) or headless on EC2.

For each instrument's source files it walks the profile index (start/peak/end times per
profile), slices the ascent (start→peak) or descent (peak→end) window per sensor, renames
the science variable, and writes one NetCDF shard per (sensor, profile):
  RCA_<site>_sp_<sensor>_<yyyy>_<ddd>_<gpi>_<daily>_V1.nc  ->  ooipaths.redux_dir(year, site)

Direction: default 'ascent' (primary dataset, start→peak, version V1). Pass direction='descent'
(CLI --direction descent) to recover the 8 HSD sensors on the peak→end window into the parallel
redux_descent tree with version V1D — a second-class companion dataset (see DescentData.md).

Restart-tolerant: existing shard files are skipped (supports incremental top-ups —
re-running after new source data only writes the new shards).
"""

import sys
from pathlib import Path

# Repo root importable so `import ooipaths` works under %run or headless.
sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op

try:
    import pandas as pd
    import xarray as xr
except Exception:  # pragma: no cover
    pd = None
    xr = None

# input science variable -> (output shard sensor name, profile direction)
# direction: 'ascent' = start→peak, 'descent' = peak→end
SENSOR_MAP = {
    "sea_water_temperature":         ("temperature",     "ascent"),
    "sea_water_practical_salinity":  ("salinity",        "ascent"),
    "sea_water_density":             ("density",         "ascent"),
    "corrected_dissolved_oxygen":    ("dissolvedoxygen", "ascent"),
    "fluorometric_cdom":             ("cdom",            "ascent"),
    "fluorometric_chlorophyll_a":    ("chlora",          "ascent"),
    "optical_backscatter":           ("backscatter",     "ascent"),
    "ph_seawater":                   ("ph",              "descent"),
    "pco2_seawater":                 ("pco2",            "descent"),
    "salinity_corrected_nitrate":    ("nitrate",         "ascent"),
    "par_counts_output":             ("par",             "ascent"),
}

# instrument key -> OOINET filename token
INSTRUMENTS = {
    "ctd": "CTDPF", "flor": "FLORT", "ph": "PHSEN",
    "pco2": "PCO2W", "nitr": "NUTNR", "par": "PARAD",
}

# which output sensors each instrument produces
INSTRUMENT_SENSORS = {
    "ctd":  {"temperature", "salinity", "density", "dissolvedoxygen"},
    "flor": {"cdom", "chlora", "backscatter"},
    "ph":   {"ph"},
    "pco2": {"pco2"},
    "nitr": {"nitrate"},
    "par":  {"par"},
}

# DESCENT recovery (see DescentData.md): the 8 HSD scalar sensors that normally operate on
# ASCENT are re-sharded on the DESCENT window (peak→end) into a parallel redux_descent tree
# with version token V1D. Excluded from descent recovery: nitrate (ascent-only) and pH/pCO2
# (already descent as their primary mode — a descent copy would be redundant).
DESCENT_SENSORS = frozenset({
    "temperature", "salinity", "density", "dissolvedoxygen",
    "cdom", "chlora", "backscatter", "par",
})


def load_profile_indices(year, site=op.DEFAULT_SITE):
    """Profile index CSV (start/peak/end per profile) for a year, or None."""
    f = op.profile_index_dir(site) / f"{op.site_designator(site)}_profiles_{year}.csv"
    return pd.read_csv(f) if f.exists() else None


def _active_sensors(instrument):
    """SENSOR_MAP entries this instrument produces."""
    want = INSTRUMENT_SENSORS.get(instrument, set())
    return {k: v for k, v in SENSOR_MAP.items() if v[0] in want}


def process_instrument(instrument, site=op.DEFAULT_SITE, sensors=None, years=None,
                       direction="ascent"):
    """Shard source files for one instrument at one site into redux.
    `sensors`:   optional set of output sensor names to restrict to (e.g. {'dissolvedoxygen'}).
    `years`:     optional set of ints to restrict source folders + profile-index years.
    `direction`: 'ascent' (default) writes the primary redux tree (start→peak, version V1);
                 'descent' re-shards the 8 HSD sensors on peak→end into the parallel
                 redux_descent tree (version V1D). See DescentData.md."""
    if xr is None:
        print("xarray/pandas not available; cannot shard.")
        return
    if instrument not in INSTRUMENTS:
        print(f"Unknown instrument: {instrument}")
        return
    op._check_direction(direction)
    version = op.redux_version(direction)

    token = INSTRUMENTS[instrument]
    active = _active_sensors(instrument)
    # In descent mode, restrict to the HSD sensors that get a descent copy (skip
    # nitrate + the already-descent pH/pCO2), and FORCE the slice window to descent.
    if direction == "descent":
        active = {k: v for k, v in active.items() if v[0] in DESCENT_SENSORS}
        if not active:
            print(f"  ({instrument} has no descent-recovery sensors; skipping)")
            return
    if sensors:
        sensors = set(sensors)
        active = {k: v for k, v in active.items() if v[0] in sensors}
        if not active:
            print(f"  (no {instrument} sensors match {sorted(sensors)})")
            return
    year_filter = set(years) if years else None
    base = op.ooinet_dir(site, channel="scalar")

    print(f"Scanning {instrument} source folders (site={site}, direction={direction})"
          + (f" sensors={sorted(v[0] for v in active.values())}" if sensors else "")
          + (f" years={sorted(year_filter)}" if year_filter else "") + "...")
    src_years = []
    for year in range(2014, 2027):
        if year_filter is not None and year not in year_filter:
            continue
        folder = base / f"{year}_{instrument}"
        if folder.exists() and any(folder.glob(f"*{token}*.nc")):
            n = len(list(folder.glob(f"*{token}*.nc")))
            print(f"  {year}_{instrument}: {n} files")
            src_years.append(year)
    if not src_years:
        print("  (no source years found)")
        return

    for year in range(2014, 2027):
        op.redux_dir(year, site, direction).mkdir(parents=True, exist_ok=True)

    stats = {v[0]: {"attempted": 0, "written": 0, "skipped": 0} for v in active.values()}

    for fy in src_years:
        files = sorted((base / f"{fy}_{instrument}").glob(f"*{token}*.nc"))
        print(f"\n=== {fy}_{instrument} ({len(files)} files) ===")
        for fi, fpath in enumerate(files, 1):
            if fi % 5 == 0:
                print(f"  file {fi}/{len(files)}")
            try:
                ds = xr.open_dataset(fpath).swap_dims({"obs": "time"})
                start_time = pd.to_datetime(ds.time.values[0])
                end_time = pd.to_datetime(ds.time.values[-1])
            except Exception:
                continue

            for year in range(start_time.year, end_time.year + 1):
                if year_filter is not None and year not in year_filter:
                    continue
                profiles = load_profile_indices(year, site)
                if profiles is None:
                    continue
                daily = {}
                for _, row in profiles.iterrows():
                    gpi = row["profile"]
                    p_start = pd.to_datetime(row["start"])
                    p_peak = pd.to_datetime(row["peak"])
                    p_end = pd.to_datetime(row["end"])
                    dk = p_start.date()
                    daily[dk] = daily.get(dk, 0) + 1
                    daily_seq = daily[dk]

                    for in_var, (out_var, native_dir) in active.items():
                        stats[out_var]["attempted"] += 1
                        # The requested `direction` sets the window. In ascent mode the
                        # per-sensor native direction still governs (so pH/pCO2 slice
                        # peak→end); in descent mode every active (HSD) sensor slices
                        # peak→end. See DescentData.md.
                        slice_dir = native_dir if direction == "ascent" else "descent"
                        s0, s1 = ((p_start, p_peak) if slice_dir == "ascent"
                                  else (p_peak, p_end))
                        try:
                            pdata = ds.sel(time=slice(s0, s1))
                            if len(pdata.time) == 0 or in_var not in pdata.data_vars:
                                continue
                            p_year = p_start.year
                            out_dir = op.redux_dir(p_year, site, direction)
                            jday = p_start.timetuple().tm_yday
                            fname = (f"RCA_{site}_sp_{out_var}_{p_year}_{jday:03d}_"
                                     f"{gpi}_{daily_seq}_{version}.nc")
                            out_path = out_dir / fname
                            if out_path.exists():
                                stats[out_var]["skipped"] += 1
                                continue
                            sensor_ds = xr.Dataset({out_var: pdata[in_var]})
                            if "depth" in pdata.coords:
                                sensor_ds = sensor_ds.assign_coords(depth=pdata["depth"])
                            for v in ("lat", "lon", "obs"):
                                if v in sensor_ds.coords:
                                    sensor_ds = sensor_ds.drop_vars(v)
                                if v in sensor_ds.data_vars:
                                    sensor_ds = sensor_ds.drop_vars(v)
                            sensor_ds.to_netcdf(out_path)
                            stats[out_var]["written"] += 1
                        except Exception:
                            continue

    print("\n=== Sharding complete ===")
    for sensor, c in stats.items():
        print(f"  {sensor:16s} attempted={c['attempted']:6d} "
              f"written={c['written']:6d} skipped={c['skipped']:6d}")


def shard_all(site=op.DEFAULT_SITE, instruments=None, sensors=None, years=None,
              direction="ascent"):
    """Shard every (or the given) instrument for a site, optionally limited to
    specific output sensors and/or years. `direction`='descent' recovers the 8 HSD
    sensors on the descent window into redux_descent (see DescentData.md); in that
    mode ph/pco2/nitr instruments are skipped automatically."""
    op._check_direction(direction)
    for inst in (instruments or list(INSTRUMENTS)):
        process_instrument(inst, site=site, sensors=sensors, years=years,
                           direction=direction)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Shard OOINET source -> redux (Phase 1).")
    ap.add_argument("--site", default=op.DEFAULT_SITE, help="site code (sb/oo/ab)")
    ap.add_argument("--instruments", nargs="*", default=None,
                    help=f"subset of {list(INSTRUMENTS)}; default all")
    ap.add_argument("--sensors", nargs="*", default=None,
                    help="restrict to these output sensors, e.g. --sensors dissolvedoxygen")
    ap.add_argument("--years", nargs="*", type=int, default=None,
                    help="restrict to these years, e.g. --years 2016")
    ap.add_argument("--direction", choices=("ascent", "descent"), default="ascent",
                    help="'descent' recovers the 8 HSD sensors on peak→end into "
                         "redux_descent (V1D); default ascent")
    args = ap.parse_args()
    shard_all(site=args.site, instruments=args.instruments,
              sensors=args.sensors, years=args.years, direction=args.direction)
