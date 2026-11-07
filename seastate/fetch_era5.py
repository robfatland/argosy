"""
fetch_era5.py -- download ERA5 hourly POINT time-series for the shallow-profiler
sites (sb, oo, ab) from the Copernicus Climate Data Store.

Dataset: reanalysis-era5-single-levels-timeseries
    "ERA5 hourly time-series data on single levels from 1940 to present".
This is the POINT product: you give a single (lon, lat) and it returns a ready-made
time series at the nearest grid cell -- no area box, no spatial reduction. Lighter and
simpler than the gridded reanalysis-era5-single-levels for our 3-points-long-record case.

Purpose: provide an independent (non-OOI) sea-state + wind + flux record to compare
against mixed-layer depth (MLD) seasonality. See Umbrella.md -> "ERA5 sea state".

Output (never inside ~/argosy):
    ~/ooi/<site>/metadata/external/era5/era5_<site>_<yyyy>.nc   (one file per site-year)

Grid note: atmospheric variables (u10, v10, stress, fluxes) are on a 0.25 deg grid; wave
variables are on a 0.5 deg grid. CDS may therefore return a ZIP of several tables/NetCDFs
for one request. We save the raw payload as-is; the loader (future) merges on time.

Accumulated fields (metss, mntss, slhf, sshf, ssr, str) are hourly ACCUMULATIONS:
divide by 3600 s for W m-2 (heat) or N m-2 (stress). Heat flux sign is positive downward.

Prerequisites (one-time):
    1. CDS account; on the dataset page click "Accept terms" (free, instant, tied to
       your account -- the API uses the same account).
       https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries
    2. ~/.cdsapirc containing:
           url: https://cds.climate.copernicus.eu/api
           key: <your personal access token>
    3. pip install cdsapi

Usage:
    python ~/argosy/era5/fetch_era5.py --dry-run
    python ~/argosy/era5/fetch_era5.py --site oo --years 2024
    python ~/argosy/era5/fetch_era5.py --site all

Re-running skips site-years whose output already exists.
"""
import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op  # noqa: E402

DATASET = "reanalysis-era5-single-levels-timeseries"

# Profiler coordinates (OOIObservatory.md / Umbrella.md), decimal degrees.
SITE_LATLON = {
    "sb": (44.52897, -125.38966),
    "oo": (44.37415, -124.95648),
    "ab": (45.83049, -129.75326),
}

# All variables in one request; CDS splits grids into separate tables as needed.
# NOTE: this POINT product carries only the subset below. Variables the gridded product
# has but the timeseries product does NOT serve (confirmed empirically Nov 2026, silently
# dropped from the response): peak_wave_period, significant_height_of_wind_waves,
# significant_height_of_total_swell, the turbulent surface stress pair, and the two net
# radiation terms. So we derive wind stress / u* from u10,v10 in the loader, and we have
# only the TURBULENT (latent+sensible) part of the heat budget, not the full net flux.
VARIABLES = [
    # waves (0.5 deg grid) -> swh, mwp, mwd
    "significant_height_of_combined_wind_waves_and_swell",
    "mean_wave_period",
    "mean_wave_direction",
    # 10 m wind (0.25 deg grid) -> u10, v10
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    # turbulent surface heat fluxes (accumulated J m-2, positive downward) -> slhf, sshf
    "surface_latent_heat_flux",
    "surface_sensible_heat_flux",
]

FIRST_YEAR = 2014   # earliest shallow-profiler data (ab begins Dec 2014)


def out_dir(site):
    d = op.metadata_dir(site, "external") / "era5"
    d.mkdir(parents=True, exist_ok=True)
    return d


def date_interval(year, today):
    """'YYYY-01-01/YYYY-12-31', clipped to yesterday for the current year.
    Returns None if the year has no completed days yet."""
    start = dt.date(year, 1, 1)
    end = dt.date(year, 12, 31)
    last = today - dt.timedelta(days=1)   # ERA5T lags ~5 days; yesterday is safe-ish
    if year == today.year:
        if last < start:
            return None
        end = min(end, last)
    return f"{start.isoformat()}/{end.isoformat()}"


def fetch_one(client, site, year, interval, target):
    lon, lat = SITE_LATLON[site][1], SITE_LATLON[site][0]
    request = {
        "variable": VARIABLES,
        "location": {"longitude": lon, "latitude": lat},
        "date": [interval],
        "data_format": "netcdf",
    }
    tmp = target.with_suffix(".part")
    result = client.retrieve(DATASET, request)
    result.download(str(tmp))
    # CDS may hand back a ZIP (mixed grids) even when netcdf is asked. Keep whatever
    # came: a plain .nc gets the final name; a zip is parked with a .zip suffix for
    # the loader to crack open.
    import zipfile
    if zipfile.is_zipfile(tmp):
        final = target.with_suffix(".zip")
        tmp.rename(final)
        print(f"    (zip payload) -> {final.name}")
    else:
        tmp.rename(target)
        print(f"    -> {target.name}")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", default="all", help="sb | oo | ab | all (default all)")
    ap.add_argument("--years", default=None,
                    help="e.g. 2024 or 2020-2024 (default FIRST_YEAR..current)")
    ap.add_argument("--dry-run", action="store_true",
                    help="list requests, download nothing")
    args = ap.parse_args()

    today = dt.date.today()
    sites = list(SITE_LATLON) if args.site == "all" else [args.site]
    if args.years is None:
        years = range(FIRST_YEAR, today.year + 1)
    elif "-" in args.years:
        a, b = args.years.split("-")
        years = range(int(a), int(b) + 1)
    else:
        years = [int(args.years)]

    client = None
    if not args.dry_run:
        import cdsapi
        client = cdsapi.Client()

    for site in sites:
        for year in years:
            interval = date_interval(year, today)
            if interval is None:
                continue
            target = out_dir(site) / f"era5_{site}_{year}.nc"
            if target.exists() or target.with_suffix(".zip").exists():
                print(f"skip   {target.name} (exists)")
                continue
            print(f"{'would fetch' if args.dry_run else 'fetch'} {target.name}  "
                  f"date={interval}")
            if not args.dry_run:
                fetch_one(client, site, year, interval, target)


if __name__ == "__main__":
    main()
