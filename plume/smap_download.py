# smap_download.py — Download SMAP SSS + satellite SST at profiler location via ERDDAP.
# Run this as: %run ~/argosy/plume/smap_download.py
#
# Uses NOAA CoastWatch ERDDAP server to request just the pixels we need.
# Two HTTP requests return full time series in seconds — no bulk download.
#
# Output: ~/ooi/metadata/smap_sss_slopebase.csv  (SSS + SST merged)
#
# Datasets:
#   SSS: SMAP Daily, Global 0.25°, 2015-present (noaacwSMAPsssDaily)
#   SST: NOAA Coral Reef Watch Daily 5km, 1985-present (noaacrwsstDaily)
#
# No authentication required (public ERDDAP server).

import pandas as pd
import numpy as np
from pathlib import Path
from io import StringIO
import urllib.request

# == Configuration =============================================================

OUTPUT_DIR = Path("~/ooi/metadata").expanduser()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Slope Base shallow profiler coordinates
SITE_LAT = 44.53
SITE_LON = -125.39
SITE_NAME = "slopebase"

# Time range (SMAP begins April 2015)
START_DATE = "2015-04-01"
END_DATE = "2026-07-01"   # Safe end date within dataset availability


# == ERDDAP fetch utility ======================================================

def fetch_erddap_csv(base_url, variables, lat, lon, start, end, has_altitude=True):
    """Fetch a time series from ERDDAP griddap for a single lat/lon point."""
    alt_constraint = "[(0)]" if has_altitude else ""

    # Don't request dimension variables explicitly — ERDDAP returns them automatically
    query = (
        f"?{variables}"
        f"[({start}T00:00:00Z):1:({end}T00:00:00Z)]"
        f"{alt_constraint}"
        f"[({lat})]"
        f"[({lon})]"
    )
    url = base_url + query
    print(f"  Fetching: {base_url.split('/')[-1].replace('.csv','')}...")
    print(f"  URL: {url[:200]}...")

    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; argosy-plume/1.0)'
    })
    with urllib.request.urlopen(req, timeout=300) as response:
        csv_text = response.read().decode('utf-8')

    # Parse: line 0 = headers, line 1 = units, lines 2+ = data
    lines = csv_text.strip().split('\n')
    header = lines[0]
    data_lines = lines[2:]
    csv_body = header + '\n' + '\n'.join(data_lines)
    return pd.read_csv(StringIO(csv_body), parse_dates=['time'])


# == Fetch SSS =================================================================

print(f"Requesting satellite data from NOAA CoastWatch ERDDAP...")
print(f"  Site: {SITE_NAME} ({SITE_LAT}N, {SITE_LON}W)")
print(f"  Time: {START_DATE} to {END_DATE}")

# Fetch in yearly chunks to avoid server timeouts
def fetch_yearly_chunks(base_url, variables, lat, lon, start_year, end_year, has_altitude=True):
    """Fetch data in yearly chunks and concatenate."""
    all_dfs = []
    for year in range(start_year, end_year + 1):
        s = f"{year}-01-01"
        e = f"{year}-12-31"
        if year == start_year:
            s = START_DATE
        try:
            chunk = fetch_erddap_csv(base_url, variables, lat, lon, s, e, has_altitude)
            all_dfs.append(chunk)
            print(f"    {year}: {len(chunk)} records")
        except Exception as ex:
            print(f"    {year}: failed ({ex})")
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    return pd.DataFrame()


try:
    sss_df = fetch_yearly_chunks(
        "https://coastwatch.noaa.gov/erddap/griddap/noaacwSMAPsssDaily.csv",
        "sss", SITE_LAT, SITE_LON, 2015, 2026, has_altitude=True
    )
    sss_df = sss_df.rename(columns={'time': 'timestamp', 'sss': 'sss_psu'})
    if 'sss_psu' in sss_df.columns:
        sss_df = sss_df[['timestamp', 'sss_psu']].dropna(subset=['sss_psu'])
        print(f"  SSS total: {len(sss_df)} measurements, range {sss_df['sss_psu'].min():.2f}–{sss_df['sss_psu'].max():.2f} PSU")
    else:
        sss_df = pd.DataFrame(columns=['timestamp', 'sss_psu'])
    sss_df = sss_df.rename(columns={'time': 'timestamp', 'sss': 'sss_psu'})
    sss_df = sss_df[['timestamp', 'sss_psu']].dropna(subset=['sss_psu'])
    print(f"    SSS: {len(sss_df)} measurements, range {sss_df['sss_psu'].min():.2f}–{sss_df['sss_psu'].max():.2f} PSU")
except Exception as e:
    print(f"  SSS fetch failed: {e}")
    print(f"  URL attempted: https://coastwatch.noaa.gov/erddap/griddap/noaacwSMAPsssDaily.csv?time,latitude,longitude,sss[({START_DATE}T00:00:00Z):1:({END_DATE}T00:00:00Z)][({SITE_LAT}):1:({SITE_LAT})][({SITE_LON}):1:({SITE_LON})]")
    sss_df = pd.DataFrame(columns=['timestamp', 'sss_psu'])


# == Fetch SST =================================================================

try:
    sst_df = fetch_yearly_chunks(
        "https://coastwatch.noaa.gov/erddap/griddap/noaacrwsstDaily.csv",
        "analysed_sst", SITE_LAT, SITE_LON, 2015, 2026, has_altitude=False
    )
    sst_df = sst_df.rename(columns={'time': 'timestamp', 'analysed_sst': 'sst_degC'})
    if 'sst_degC' in sst_df.columns:
        sst_df = sst_df[['timestamp', 'sst_degC']].dropna(subset=['sst_degC'])
        print(f"  SST total: {len(sst_df)} measurements, range {sst_df['sst_degC'].min():.1f}–{sst_df['sst_degC'].max():.1f} °C")
    else:
        sst_df = pd.DataFrame(columns=['timestamp', 'sst_degC'])
except Exception as e:
    print(f"  SST fetch failed: {e}")
    sst_df = pd.DataFrame(columns=['timestamp', 'sst_degC'])


# == Merge and save ============================================================

if len(sss_df) > 0 and len(sst_df) > 0:
    sss_df['date'] = pd.to_datetime(sss_df['timestamp']).dt.date
    sst_df['date'] = pd.to_datetime(sst_df['timestamp']).dt.date
    merged = pd.merge(sss_df[['date', 'sss_psu']], sst_df[['date', 'sst_degC']],
                      on='date', how='outer')
    merged['timestamp'] = pd.to_datetime(merged['date'])
    merged['site'] = SITE_NAME
    merged = merged[['timestamp', 'sss_psu', 'sst_degC', 'site']].sort_values('timestamp')
elif len(sss_df) > 0:
    merged = sss_df.copy()
    merged['sst_degC'] = np.nan
    merged['site'] = SITE_NAME
elif len(sst_df) > 0:
    merged = sst_df.copy()
    merged['sss_psu'] = np.nan
    merged['site'] = SITE_NAME
else:
    print("ERROR: No data retrieved.")
    raise SystemExit

# Compute 8-day rolling mean for SSS (reduces noise from daily retrievals)
merged = merged.sort_values('timestamp').reset_index(drop=True)
merged['sss_8day'] = merged['sss_psu'].rolling(window=8, min_periods=4, center=True).mean()

output_path = OUTPUT_DIR / f"smap_sss_{SITE_NAME}.csv"
merged.to_csv(output_path, index=False)

print(f"\nSaved: {output_path}")
print(f"  {len(merged)} rows, columns: {list(merged.columns)}")
print(f"  Time range: {merged['timestamp'].iloc[0]} to {merged['timestamp'].iloc[-1]}")
print(f"  SSS 8-day rolling mean: {merged['sss_8day'].dropna().min():.2f}–{merged['sss_8day'].dropna().max():.2f} PSU")
