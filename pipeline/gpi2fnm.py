#!/usr/bin/env python
"""
pipeline/gpi2fnm.py — resolve a Global Profile Index (GPI) to profile metadata and the
pp06 shard filenames for every sensor we currently have.

A GPI identifies one shallow-profiler profile at a site. Given the GPI (and the
site), this looks the profile up in the profileIndices table (start/peak/end
times), derives the date, day-of-year, and daily index (which of the day's
profiles this is, 1..9), and builds the pp06 shard filename for each sensor:

    RCA_<site>_sp_<sensor>_<yyyy>_<ddd>_<gpi>_<daily>_V1.nc

The work is in resolve_gpi(), which returns a dict so it can be imported and
reused elsewhere:

    from gpi2fnm import resolve_gpi
    info = resolve_gpi(2047, site="sb")
    info["filenames"]["temperature"]   # -> 'RCA_sb_sp_temperature_...nc'

CLI:
    python pipeline/gpi2fnm.py --gpi 2047                 # Slope Base (default)
    python pipeline/gpi2fnm.py --gpi 16509 --location ab  # Axial Base
    python pipeline/gpi2fnm.py --gpi 2047 --json          # machine-readable
    python pipeline/gpi2fnm.py --gpi 2047 --paths         # full pp06 paths, existing files only

Site codes: sb (Slope Base, default), oo (Oregon Offshore), ab (Axial Base).
"""

import argparse
import glob
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ooipaths as op

# Sensors currently in the pp06 inventory. oo has no pco2; absent sensors simply
# won't have a file on disk, which `--paths` reflects.
PP06_SENSORS = (
    "temperature", "salinity", "density", "dissolvedoxygen",
    "chlora", "cdom", "backscatter", "par", "nitrate", "ph", "pco2",
)

VERSION = "V1"  # pp06 ascent shard version token


def _load_profile_index(site):
    """Concatenate all profileIndices CSVs for a site -> DataFrame with a
    monotonic daily index per calendar day (from the UTC `start` time)."""
    desig = op.site_designator(site)
    idx_dir = op.profile_index_dir(site)
    files = sorted(idx_dir.glob(f"{desig}_profiles_*.csv"))
    files = [f for f in files if not f.name.endswith("_test.csv")]
    if not files:
        raise FileNotFoundError(
            f"No profileIndices CSVs for site {site!r} in {idx_dir} "
            f"(expected {desig}_profiles_<yyyy>.csv)")
    df = pd.concat(
        (pd.read_csv(f, parse_dates=["start", "peak", "end"]) for f in files),
        ignore_index=True)
    df = df.dropna(subset=["profile", "start"]).sort_values("start").reset_index(drop=True)
    df["profile"] = df["profile"].astype(int)
    df["date"] = df["start"].dt.date
    df["daily_index"] = df.groupby("date").cumcount() + 1
    return df


def resolve_gpi(gpi, site="sb", version=VERSION):
    """Resolve a GPI at a site to profile metadata + per-sensor pp06 filenames.

    Returns a dict:
      gpi, site, designator, start, peak, end (ISO UTC strings),
      date (YYYY-MM-DD), year, day_of_year (zero-padded 3-digit string),
      daily_index (1..9), ascent_minutes, descent_minutes,
      filenames: {sensor: filename}, sensors: [...].
    Raises KeyError if the GPI is not in the site's profile index.
    """
    site = op._check_site(site)
    gpi = int(gpi)
    df = _load_profile_index(site)
    hit = df[df["profile"] == gpi]
    if hit.empty:
        lo, hi = int(df["profile"].min()), int(df["profile"].max())
        raise KeyError(f"GPI {gpi} not found for site {site!r} "
                       f"(available range {lo}..{hi}).")
    r = hit.iloc[0]
    start, peak, end = r["start"], r["peak"], r["end"]
    yyyy = f"{start.year:04d}"
    ddd = f"{start.dayofyear:03d}"
    daily = int(r["daily_index"])

    filenames = {
        s: f"RCA_{site}_sp_{s}_{yyyy}_{ddd}_{gpi}_{daily}_{version}.nc"
        for s in PP06_SENSORS
    }
    return {
        "gpi": gpi,
        "site": site,
        "designator": op.site_designator(site),
        "start": start.isoformat(),
        "peak": peak.isoformat() if pd.notna(peak) else None,
        "end": end.isoformat() if pd.notna(end) else None,
        "date": str(r["date"]),
        "year": yyyy,
        "day_of_year": ddd,
        "daily_index": daily,
        "ascent_minutes": round((peak - start).total_seconds() / 60, 1) if pd.notna(peak) else None,
        "descent_minutes": round((end - peak).total_seconds() / 60, 1)
                           if pd.notna(peak) and pd.notna(end) else None,
        "filenames": filenames,
        "sensors": list(PP06_SENSORS),
    }


def pp06_paths(info, existing_only=False):
    """Map each sensor to its full pp06 path for the resolved profile's year.
    If existing_only, include only files that are actually present on disk."""
    year = int(info["year"])
    pdir = op.postproc_dir("pp06", year, info["site"])
    out = {}
    for sensor, fn in info["filenames"].items():
        p = pdir / fn
        if existing_only and not p.exists():
            continue
        out[sensor] = str(p)
    return out


def main():
    ap = argparse.ArgumentParser(
        description="Resolve a GPI to profile metadata and pp06 shard filenames.")
    ap.add_argument("--gpi", type=int, required=True, help="Global Profile Index.")
    ap.add_argument("--location", "--site", dest="site", default="sb",
                    choices=op.SITES, help="Site: sb (default), oo, ab.")
    ap.add_argument("--json", action="store_true", help="Emit JSON.")
    ap.add_argument("--paths", action="store_true",
                    help="Show full pp06 paths that exist on disk.")
    args = ap.parse_args()

    try:
        info = resolve_gpi(args.gpi, site=args.site)
    except (KeyError, FileNotFoundError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        if args.paths:
            info = {**info, "paths_on_disk": pp06_paths(info, existing_only=True)}
        print(json.dumps(info, indent=2))
        return

    print(f"GPI {info['gpi']}  site {info['site']} ({info['designator']})")
    print(f"  date {info['date']}  day-of-year {info['day_of_year']}  "
          f"daily index {info['daily_index']} of 9")
    print(f"  ascent  {info['start']} -> {info['peak']}  ({info['ascent_minutes']} min)")
    print(f"  descent {info['peak']} -> {info['end']}  ({info['descent_minutes']} min)")
    print(f"  pp06 shard filenames ({len(info['filenames'])} sensors):")
    for sensor, fn in info["filenames"].items():
        print(f"    {sensor:16s} {fn}")

    if args.paths:
        present = pp06_paths(info, existing_only=True)
        print(f"\n  pp06 files present on disk ({len(present)} of {len(info['filenames'])}):")
        if present:
            for sensor, p in present.items():
                print(f"    {sensor:16s} {p}")
        else:
            print("    (none found — pp06 for this year/site may not be local)")


if __name__ == "__main__":
    main()
