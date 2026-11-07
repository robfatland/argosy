"""
fetch_era5_radiation.py -- download ERA5 net surface radiation (solar + thermal) covering
ALL THREE shallow-profiler sites in ONE shared box, from the GRIDDED CDS dataset.

Why a second fetcher: the point product (fetch_era5.py) does not serve radiation. Solar
heating is the main summer stratifier, so without it the surface heat budget is incomplete.
With slhf/sshf from the point product:   Q_net = ssr + str + slhf + sshf  (W m-2, + down).

SPEED DESIGN (rewritten Nov 2026):
  The gridded dataset is slow per request (~20 min) because the CDS does the work per hour,
  roughly independent of box size. So we:
    (1) request ONE box spanning all 3 sites instead of 3 separate boxes -> ~3x fewer requests;
    (2) submit several YEARS concurrently (a small thread pool) -> wall-clock ~ one request,
        not the serial sum. CDS runs them in parallel on its side; each thread just polls.
  One shared file per year:  ~/ooi/era5_shared/era5rad_shared_<yyyy>.nc
  (Shared across sites, so it lives at an ooi-root 'era5_shared' dir, NOT under a single site.)
  The loader crops each site's nearest cell.

Dataset: reanalysis-era5-single-levels (gridded; its own "Accept terms" click).
Variables: ssr (net shortwave), str (net longwave). Hourly ACCUMULATIONS in J m-2;
divide by 3600 for W m-2. Positive = downward.

Usage:
    python ~/argosy/seastate/fetch_era5_radiation.py --dry-run
    python ~/argosy/seastate/fetch_era5_radiation.py --years 2024
    python ~/argosy/seastate/fetch_era5_radiation.py                 # all years, 3 at a time
    python ~/argosy/seastate/fetch_era5_radiation.py --workers 4

Re-running skips years whose output already exists.
"""
import argparse
import datetime as dt
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op  # noqa: E402

DATASET = "reanalysis-era5-single-levels"

# Site coordinates (for reference / the loader): sb 44.53,-125.39  oo 44.37,-124.96
# ab 45.83,-129.75. One box with a small margin covers all three.
SHARED_AREA = [46.3, -130.2, 44.0, -124.6]   # N, W, S, E

VARIABLES = [
    "surface_net_solar_radiation",
    "surface_net_thermal_radiation",
]

FIRST_YEAR = 2014


def shared_dir():
    d = op.OOI_ROOT / "era5_shared"
    d.mkdir(parents=True, exist_ok=True)
    return d


def months_for_year(year, today):
    if year < today.year:
        return list(range(1, 13))
    return list(range(1, today.month))


def build_request(year, months):
    return {
        "product_type": ["reanalysis"],
        "variable": VARIABLES,
        "year": [str(year)],
        "month": [f"{m:02d}" for m in months],
        "day": [f"{d:02d}" for d in range(1, 32)],
        "time": [f"{h:02d}:00" for h in range(24)],
        "area": SHARED_AREA,
        "data_format": "netcdf",
        "download_format": "unarchived",
    }


def fetch_year(year, months, target):
    """Submit and download one year. Own cdsapi client per thread (not thread-safe to share)."""
    import cdsapi
    client = cdsapi.Client()
    tmp = target.with_suffix(".part")
    client.retrieve(DATASET, build_request(year, months)).download(str(tmp))
    if zipfile.is_zipfile(tmp):
        final = target.with_suffix(".zip")
        tmp.rename(final)
        return f"{year}: zip -> {final.name}"
    tmp.rename(target)
    return f"{year}: -> {target.name}"


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", default=None,
                    help="e.g. 2024 or 2020-2024 (default FIRST_YEAR..current)")
    ap.add_argument("--workers", type=int, default=3,
                    help="concurrent year-requests (default 3)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    today = dt.date.today()
    if args.years is None:
        years = range(FIRST_YEAR, today.year + 1)
    elif "-" in args.years:
        a, b = args.years.split("-")
        years = range(int(a), int(b) + 1)
    else:
        years = [int(args.years)]

    jobs = []  # (year, months, target)
    for year in years:
        months = months_for_year(year, today)
        if not months:
            continue
        target = shared_dir() / f"era5rad_shared_{year}.nc"
        if target.exists() or target.with_suffix(".zip").exists():
            print(f"skip   {target.name} (exists)")
            continue
        jobs.append((year, months, target))
        print(f"{'would fetch' if args.dry_run else 'queue'} {target.name}  "
              f"months={months[0]}-{months[-1]}")

    if args.dry_run or not jobs:
        if not jobs:
            print("nothing to fetch.")
        return

    print(f"\nsubmitting {len(jobs)} year-requests, {args.workers} at a time "
          f"(box {SHARED_AREA} covers sb/oo/ab)...")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(fetch_year, y, m, t): y for (y, m, t) in jobs}
        for fut in as_completed(futs):
            year = futs[fut]
            try:
                print("done " + fut.result())
            except Exception as e:
                print(f"FAIL {year}: {e}")


if __name__ == "__main__":
    main()
