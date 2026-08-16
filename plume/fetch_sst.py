# fetch_sst.py — Download satellite SST time series at profiler location via ERDDAP.
# Run this as: %run ~/argosy/plume/fetch_sst.py
#
# Fetches NOAA Coral Reef Watch daily SST in yearly chunks.
# Merges with any existing data in the output CSV (fills gaps, doesn't overwrite).
#
# Output: ~/ooi/metadata/satellite_sst_slopebase.csv
#
# Dataset: NOAA CRW Daily Global 5km SST (noaacrwsstDaily)
# Variable: analysed_sst
# No authentication required.

import pandas as pd
import numpy as np
from pathlib import Path
from io import StringIO
import urllib.request

# == Configuration =============================================================

OUTPUT_DIR = Path("~/ooi/metadata").expanduser()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH = OUTPUT_DIR / "satellite_sst_slopebase.csv"

SITE_LAT = 44.53
SITE_LON = -125.39
SITE_NAME = "slopebase"

START_YEAR = 2015
END_YEAR = 2026
END_MONTH_DAY = "08-01"  # safe end for current year

ERDDAP_BASE = "https://coastwatch.noaa.gov/erddap/griddap/noaacrwsstDaily.csv"
VARIABLE = "analysed_sst"


# == ERDDAP fetch ==============================================================

def fetch_year(year):
    """Fetch one year of SST from ERDDAP. Returns DataFrame or None."""
    start = f"{year}-01-01"
    if year == END_YEAR:
        end = f"{year}-{END_MONTH_DAY}"
    else:
        end = f"{year}-12-31"

    query = (
        f"?{VARIABLE}"
        f"[({start}T00:00:00Z):1:({end}T00:00:00Z)]"
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
        data_lines = lines[2:]  # skip units row
        csv_body = header + '\n' + '\n'.join(data_lines)
        df = pd.read_csv(StringIO(csv_body), parse_dates=['time'])
        df = df.rename(columns={'time': 'timestamp', VARIABLE: 'sst_degC'})
        df = df[['timestamp', 'sst_degC']].dropna(subset=['sst_degC'])
        return df
    except Exception as e:
        print(f"    {year}: FAILED ({e})")
        return None


# == Load existing data ========================================================

existing_df = None
if OUTPUT_PATH.exists():
    existing_df = pd.read_csv(OUTPUT_PATH, parse_dates=['timestamp'])
    print(f"Existing SST file: {len(existing_df)} records")
    print(f"  Range: {existing_df['timestamp'].iloc[0]} to {existing_df['timestamp'].iloc[-1]}")
else:
    print("No existing SST file — fetching fresh.")


# == Fetch all years ===========================================================

print(f"\nFetching SST from NOAA CoastWatch ERDDAP ({START_YEAR}–{END_YEAR})...")
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
    print("ERROR: No SST data retrieved at all.")
    raise SystemExit

new_df = pd.concat(all_chunks, ignore_index=True)
new_df['site'] = SITE_NAME
print(f"\n  New fetch: {len(new_df)} total records")
print(f"  Range: {new_df['sst_degC'].min():.2f}–{new_df['sst_degC'].max():.2f} °C")


# == Merge with existing =======================================================

if existing_df is not None and len(existing_df) > 0:
    # Compare: dates in new that are also in existing
    existing_dates = set(existing_df['timestamp'].dt.date)
    new_dates = set(new_df['timestamp'].dt.date)
    overlap = existing_dates & new_dates
    new_only = new_dates - existing_dates
    print(f"\n  Overlap with existing: {len(overlap)} dates")
    print(f"  New dates (gap fill): {len(new_only)} dates")

    # Merge: prefer new data where both exist (fresh fetch)
    existing_df['date'] = existing_df['timestamp'].dt.date
    new_df['date'] = new_df['timestamp'].dt.date

    # Drop existing rows that overlap with new fetch, then concat
    existing_keep = existing_df[~existing_df['date'].isin(new_dates)].drop(columns='date')
    new_df = new_df.drop(columns='date')
    merged = pd.concat([existing_keep, new_df], ignore_index=True)
    merged = merged.sort_values('timestamp').reset_index(drop=True)
else:
    merged = new_df.sort_values('timestamp').reset_index(drop=True)


# == Save ======================================================================

merged.to_csv(OUTPUT_PATH, index=False)
print(f"\nSaved: {OUTPUT_PATH}")
print(f"  {len(merged)} records, columns: {list(merged.columns)}")
print(f"  Time: {merged['timestamp'].iloc[0]} to {merged['timestamp'].iloc[-1]}")
