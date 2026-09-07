# fetch_sss.py — Download SMAP SSS time series at profiler location via ERDDAP.
# Run this as: %run ~/argosy/plume/fetch_sss.py
#
# Fetches SMAP daily SSS in yearly chunks, computes 8-day rolling mean.
# Merges with any existing data in the output CSV (fills gaps).
#
# Output: ~/ooi/<site>/metadata/external/satellite_sss_slopebase.csv
#
# Dataset: SMAP SSS Daily, Global 0.25° (noaacwSMAPsssDaily)
# Variable: sss (with altitude dimension = 0)
# No authentication required.

import pandas as pd
import sys
import numpy as np
from pathlib import Path
from io import StringIO
import urllib.request

# Make the repo root importable so `import ooipaths` works under %run.
sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op
SITE = op.DEFAULT_SITE

# == Configuration =============================================================

OUTPUT_DIR = op.metadata_dir(SITE, "external")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH = OUTPUT_DIR / "satellite_sss_slopebase.csv"

SITE_LAT = 44.53
SITE_LON = -125.39
SITE_NAME = "slopebase"

START_YEAR = 2015
END_YEAR = 2026
END_MONTH_DAY = "08-01"

ERDDAP_BASE = "https://coastwatch.noaa.gov/erddap/griddap/noaacwSMAPsssDaily.csv"
VARIABLE = "sss"


# == ERDDAP fetch ==============================================================

def fetch_year(year):
    """Fetch one year of SSS from ERDDAP. Returns DataFrame or None."""
    start = f"{year}-01-01"
    if year == START_YEAR:
        start = "2015-04-01"  # SMAP begins April 2015
    if year == END_YEAR:
        end = f"{year}-{END_MONTH_DAY}"
    else:
        end = f"{year}-12-31"

    # SSS dataset has altitude dimension
    query = (
        f"?{VARIABLE}"
        f"[({start}T00:00:00Z):1:({end}T00:00:00Z)]"
        f"[(0)]"
        f"[({SITE_LAT})]"
        f"[({SITE_LON})]"
    )
    url = ERDDAP_BASE + query

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; argosy-plume/1.0)'
        })
        with urllib.request.urlopen(req, timeout=300) as response:
            csv_text = response.read().decode('utf-8')

        lines = csv_text.strip().split('\n')
        header = lines[0]
        data_lines = lines[2:]
        csv_body = header + '\n' + '\n'.join(data_lines)
        df = pd.read_csv(StringIO(csv_body), parse_dates=['time'])
        df = df.rename(columns={'time': 'timestamp', VARIABLE: 'sss_psu'})
        df = df[['timestamp', 'sss_psu']].dropna(subset=['sss_psu'])
        return df
    except Exception as e:
        print(f"    {year}: FAILED ({e})")
        return None


# == Load existing data ========================================================

existing_df = None
if OUTPUT_PATH.exists():
    existing_df = pd.read_csv(OUTPUT_PATH, parse_dates=['timestamp'])
    print(f"Existing SSS file: {len(existing_df)} records")
else:
    print("No existing SSS file — fetching fresh.")


# == Fetch all years ===========================================================

print(f"\nFetching SSS from NOAA CoastWatch ERDDAP ({START_YEAR}–{END_YEAR})...")
print(f"  Site: {SITE_NAME} ({SITE_LAT}N, {SITE_LON}W)")

all_chunks = []
for year in range(START_YEAR, END_YEAR + 1):
    chunk = fetch_year(year)
    if chunk is not None and len(chunk) > 0:
        print(f"    {year}: {len(chunk)} records")
        all_chunks.append(chunk)
    else:
        print(f"    {year}: no data")

if not all_chunks:
    print("ERROR: No SSS data retrieved at all.")
    raise SystemExit

new_df = pd.concat(all_chunks, ignore_index=True)
new_df['site'] = SITE_NAME
print(f"\n  New fetch: {len(new_df)} total records")
print(f"  Range: {new_df['sss_psu'].min():.2f}–{new_df['sss_psu'].max():.2f} PSU")


# == Merge with existing =======================================================

if existing_df is not None and len(existing_df) > 0:
    existing_dates = set(existing_df['timestamp'].dt.date)
    new_dates = set(new_df['timestamp'].dt.date)
    new_only = new_dates - existing_dates
    print(f"  New dates (gap fill): {len(new_only)} dates")

    existing_df['date'] = existing_df['timestamp'].dt.date
    new_df['date'] = new_df['timestamp'].dt.date
    existing_keep = existing_df[~existing_df['date'].isin(new_dates)].drop(columns='date')
    new_df = new_df.drop(columns='date')
    merged = pd.concat([existing_keep, new_df], ignore_index=True)
    merged = merged.sort_values('timestamp').reset_index(drop=True)
else:
    merged = new_df.sort_values('timestamp').reset_index(drop=True)


# == Compute 8-day rolling mean ================================================

merged['sss_8day'] = merged['sss_psu'].rolling(window=8, min_periods=4, center=True).mean()


# == Save ======================================================================

merged.to_csv(OUTPUT_PATH, index=False)
print(f"\nSaved: {OUTPUT_PATH}")
print(f"  {len(merged)} records, columns: {list(merged.columns)}")
print(f"  Time: {merged['timestamp'].iloc[0]} to {merged['timestamp'].iloc[-1]}")
print(f"  SSS 8-day range: {merged['sss_8day'].dropna().min():.2f}–{merged['sss_8day'].dropna().max():.2f} PSU")
