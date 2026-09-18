"""
PreSelectProfiles.py — candidate-profile selection for the MLD annotation workflow.

Produces a reproducible, temporally even sample of shallow-profiler profiles from the
pp06 shard set, one candidate per fixed-width time block, for each site. The candidate
lists are the input to the interactive annotator (MLD.py). Full design: MLDAnnotationPlan.md.

Method (per site):
  - Tile time into fixed-width blocks (--block-days, default 5), block 0 starting on the
    calendar day of the site's FIRST profile (earliest GPI). No shared calendar anchor.
  - A "profile" is a global profile index (GPI). Sensor presence = the pp06 shard FILE
    exists (no valid-data check). Only the four MLD sensors are considered:
    temperature, salinity, density, dissolvedoxygen.
  - Per block: N = number of profiles falling in the block. Prefer the pool of profiles
    with ALL FOUR sensors present ('all4'); if empty, fall back to the 'T_only' pool
    (temperature present). Pick ONE profile at random (seeded) from the chosen pool.
    Blocks with no profiles contribute an N=0 row with no GPI.

Output (per site, working copy): ~/ooi/<site>/metadata/annotations/
    mld_candidates_<site>_block<NN>.csv   (block width baked in; folder created if absent)

Shared canonical copy: `--bless` promotes the working CSVs into the repo folder
  ~/argosy/mld_candidates/ (small, committable manifests). Both annotators (Chuck, Rob)
  label against the BLESSED copies so they sample the SAME profiles — regenerating locally
  is NOT guaranteed identical across machines (it depends on each person's local pp06 set).

Reads only filenames — no NetCDF is opened. Timestamps come from the year + day-of-year
encoded in each shard name:
    RCA_<site>_sp_<sensor>_<yyyy>_<ddd>_<gpi>_<daily>_<version>.nc

Usage:
    python PreSelectProfiles.py                  # all sites, 5-day blocks, seed 0
    python PreSelectProfiles.py --block-days 7   # wider blocks
    python PreSelectProfiles.py --site oo         # single site
    python PreSelectProfiles.py --dry-run         # print summary, write nothing
    python PreSelectProfiles.py --bless           # promote working CSVs to repo mld_candidates/
    python PreSelectProfiles.py --site oo --block-days 7 --bless  # bless a specific set
"""

import argparse
import csv
import re
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from random import Random

# Repo root importable so `import ooipaths` works under %run or headless.
sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op

# The four sensors relevant to MLD (all operate on all 9 daily profiles, ascent).
MLD_SENSORS = ("temperature", "salinity", "density", "dissolvedoxygen")

# Canonical SHARED candidate lists live in the repo (small, diff-friendly, version-worthy
# manifests — a deliberate exception to "no data in ~/argosy", like sensor_exclusions.csv).
# `--bless` copies the working ~/ooi copies here so Chuck and Rob label the SAME profiles.
BLESSED_DIR = op.ARGOSY_ROOT / "mld_candidates"

# Shard filename: RCA_<site>_sp_<sensor>_<yyyy>_<ddd>_<gpi>_<daily>_<version>.nc
_SHARD_RE = re.compile(
    r"^RCA_(?P<site>[a-z]{2})_sp_(?P<sensor>[a-z]+)_"
    r"(?P<year>\d{4})_(?P<ddd>\d{3})_(?P<gpi>\d+)_(?P<daily>\d+)_"
    r"(?P<version>V\d+)\.nc$"
)

CANDIDATE_COLUMNS = [
    "site", "block_id", "block_start", "block_end", "N",
    "selection_tier", "gpi", "timestamp", "daily_index",
    "has_temperature", "has_salinity", "has_density", "has_dissolvedoxygen",
    "seed", "block_width_days",
]


class Profile:
    """One global profile index within a site: its date, daily index, sensor presence."""
    __slots__ = ("gpi", "pdate", "daily_index", "sensors")

    def __init__(self, gpi, pdate, daily_index):
        self.gpi = gpi
        self.pdate = pdate                 # datetime.date (year + day-of-year)
        self.daily_index = daily_index
        self.sensors = set()               # subset of MLD_SENSORS present as files

    @property
    def has_all_four(self):
        return all(s in self.sensors for s in MLD_SENSORS)

    @property
    def has_temperature(self):
        return "temperature" in self.sensors


def _ddd_to_date(year, ddd):
    """Convert (year, day-of-year) to a date. ddd is 1-based (001 = Jan 1)."""
    return date(year, 1, 1) + timedelta(days=ddd - 1)


def scan_site_profiles(site):
    """Scan a site's pp06 shards and build {gpi: Profile} for MLD sensors only.

    Returns a dict keyed by GPI. Later files for the same GPI merge their sensor
    into the profile's presence set. Non-MLD sensors and non-matching names ignored.
    """
    profiles = {}
    pp06_base = op.postproc_base(site) / "pp06"
    if not pp06_base.exists():
        return profiles

    # Year subdirs only (skip stray files like pp06_filter1.csv).
    for year_dir in sorted(p for p in pp06_base.iterdir() if p.is_dir() and p.name.isdigit()):
        for f in year_dir.glob("RCA_*_sp_*.nc"):
            m = _SHARD_RE.match(f.name)
            if not m:
                continue
            sensor = m.group("sensor")
            if sensor not in MLD_SENSORS:
                continue
            gpi = int(m.group("gpi"))
            year = int(m.group("year"))
            ddd = int(m.group("ddd"))
            daily = int(m.group("daily"))
            prof = profiles.get(gpi)
            if prof is None:
                prof = Profile(gpi, _ddd_to_date(year, ddd), daily)
                profiles[gpi] = prof
            prof.sensors.add(sensor)
    return profiles


def build_blocks(profiles, block_days):
    """Tile [first profile date .. last profile date] into fixed-width day blocks.

    Yields (block_id, block_start, block_end_inclusive, [Profile...]) with profiles
    sorted by (date, gpi). Blocks with no profiles yield an empty list. block_end is
    the last calendar day IN the block (block_start + block_days - 1).
    """
    if not profiles:
        return
    ordered = sorted(profiles.values(), key=lambda p: (p.pdate, p.gpi))
    first_day = ordered[0].pdate
    last_day = ordered[-1].pdate

    # Bucket profiles by block index for O(n) assignment.
    by_block = defaultdict(list)
    for p in ordered:
        bidx = (p.pdate - first_day).days // block_days
        by_block[bidx].append(p)

    n_blocks = (last_day - first_day).days // block_days + 1
    for bidx in range(n_blocks):
        block_start = first_day + timedelta(days=bidx * block_days)
        block_end = block_start + timedelta(days=block_days - 1)
        yield bidx, block_start, block_end, by_block.get(bidx, [])


def select_for_block(block_profiles, rng):
    """Apply the all4 -> T_only fallback and pick one profile (seeded rng).

    Returns (selection_tier, chosen_profile) or ('', None) when the block is empty
    of usable profiles. Selection pool ordering:
      1. profiles with all four sensors  -> tier 'all4'
      2. else profiles with temperature   -> tier 'T_only'
    """
    all4 = [p for p in block_profiles if p.has_all_four]
    if all4:
        return "all4", rng.choice(sorted(all4, key=lambda p: p.gpi))
    t_only = [p for p in block_profiles if p.has_temperature]
    if t_only:
        return "T_only", rng.choice(sorted(t_only, key=lambda p: p.gpi))
    return "", None


def candidate_rows_for_site(site, block_days, seed):
    """Build the ordered list of candidate CSV rows for one site."""
    profiles = scan_site_profiles(site)
    rows = []
    # Per-site deterministic RNG (seed + site) so sites are independent yet reproducible.
    rng = Random(f"{seed}:{site}")

    for block_id, b_start, b_end, bprofs in build_blocks(profiles, block_days):
        N = len(bprofs)
        tier, chosen = select_for_block(bprofs, rng)
        row = {
            "site": site,
            "block_id": block_id,
            "block_start": b_start.isoformat(),
            "block_end": b_end.isoformat(),
            "N": N,
            "selection_tier": tier,
            "gpi": "" if chosen is None else chosen.gpi,
            "timestamp": "" if chosen is None else chosen.pdate.isoformat(),
            "daily_index": "" if chosen is None else chosen.daily_index,
            "has_temperature": "" if chosen is None else int("temperature" in chosen.sensors),
            "has_salinity": "" if chosen is None else int("salinity" in chosen.sensors),
            "has_density": "" if chosen is None else int("density" in chosen.sensors),
            "has_dissolvedoxygen": "" if chosen is None else int("dissolvedoxygen" in chosen.sensors),
            "seed": seed,
            "block_width_days": block_days,
        }
        rows.append(row)
    return rows, profiles


def candidate_filename(site, block_days):
    """Canonical candidate CSV name, block width baked in (zero-padded, sort-friendly)."""
    return f"mld_candidates_{site}_block{block_days:02d}.csv"


def write_candidates(site, rows, block_days, dry_run=False):
    """Write the per-site candidate CSV, creating the annotations folder if absent.

    Writes to the DATA tree (~/ooi/<site>/metadata/annotations/). This is the working
    output; the canonical shared copy is produced by the separate --bless step, which
    copies the blessed set into the repo folder ~/argosy/mld_candidates/ (see module
    docstring and MLDAnnotationPlan.md).
    """
    out_dir = op.metadata_dir(site, "annotations")
    out_path = out_dir / candidate_filename(site, block_days)
    if dry_run:
        return out_path
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CANDIDATE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return out_path


def bless(sites, block_days):
    """Copy the working ~/ooi candidate CSVs into the repo folder as the shared set.

    This is the deliberate 'bless these into the repo' step: regeneration writes to the
    data tree, and only an explicit --bless promotes a chosen set to the canonical copy
    that MLD.py reads and that both annotators share via git. Creates the repo folder if
    absent. Returns the list of (src, dst) that were copied.
    """
    import shutil
    BLESSED_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    for site in sites:
        src = op.metadata_dir(site, "annotations") / candidate_filename(site, block_days)
        if not src.exists():
            print(f"  {site}: no working candidate file to bless ({src.name}) — run selection first")
            continue
        dst = BLESSED_DIR / src.name
        shutil.copyfile(src, dst)
        copied.append((src, dst))
        print(f"  blessed {src.name} -> {dst}")
    if copied:
        print(f"Blessed {len(copied)} file(s) into {BLESSED_DIR}. "
              f"Commit them so Chuck and Rob label the same profiles.")
    return copied


def summarize(site, rows):
    """One-line-per-site summary for stdout."""
    total = len(rows)
    empty = sum(1 for r in rows if r["N"] == 0)
    all4 = sum(1 for r in rows if r["selection_tier"] == "all4")
    tonly = sum(1 for r in rows if r["selection_tier"] == "T_only")
    selected = all4 + tonly
    span = ""
    if rows:
        span = f"{rows[0]['block_start']}..{rows[-1]['block_end']}"
    print(f"  {site}: {total} blocks ({span}) | selected {selected} "
          f"(all4={all4}, T_only={tonly}) | empty {empty}")


def main():
    ap = argparse.ArgumentParser(description="Select candidate profiles for MLD annotation.")
    ap.add_argument("--site", choices=op.SITES, default=None,
                    help="Single site (default: all three).")
    ap.add_argument("--block-days", type=int, default=5,
                    help="Block width in days (default 5).")
    ap.add_argument("--seed", type=int, default=0,
                    help="Random seed for reproducible selection (default 0).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print summary without writing CSVs.")
    ap.add_argument("--bless", action="store_true",
                    help="Copy the working ~/ooi candidate CSVs (for the given --site/"
                         "--block-days) into the repo folder mld_candidates/ as the shared, "
                         "committable set. Does not re-run selection.")
    args = ap.parse_args()

    if args.block_days < 1:
        ap.error("--block-days must be >= 1")

    sites = [args.site] if args.site else list(op.SITES)

    if args.bless:
        print(f"PreSelectProfiles --bless — block_days={args.block_days}, sites={sites}")
        bless(sites, args.block_days)
        return

    print(f"PreSelectProfiles — block_days={args.block_days}, seed={args.seed}, "
          f"sites={sites}{' (dry run)' if args.dry_run else ''}")

    for site in sites:
        rows, profiles = candidate_rows_for_site(site, args.block_days, args.seed)
        if not profiles:
            print(f"  {site}: no pp06 profiles found (skipped)")
            continue
        summarize(site, rows)
        out_path = write_candidates(site, rows, args.block_days, dry_run=args.dry_run)
        action = "would write" if args.dry_run else "wrote"
        print(f"    {action} {len(rows)} rows -> {out_path}")


if __name__ == "__main__":
    main()
