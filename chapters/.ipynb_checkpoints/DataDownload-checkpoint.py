#!/usr/bin/env python
# coding: utf-8

# # Data Download
#
#
# This notebook copies datasets from OOINET to localhost.
#
#
# The data order is manual.
# The resulting links are placed in the text file `~/argosy/download_link_list.txt`: One URL per line:
#
#
# ```
# https://downloads.oceanobservatories.org/async_results/kilroy1618@gmail.com/20260207T235914738Z-RS01SBPS-SF01A-2A-CTDPFA102-streamed-ctdpf_sbe43_sample
# ```
#
# We want the code in the cell below to read this file and go to each link in succession,
# downloading the data to a corresponding localhost folder.

# In[8]:


import requests
from pathlib import Path
from bs4 import BeautifulSoup
import re

def parse_year_from_filename(filename):
    """Extract year from NetCDF filename."""
    pattern = r'_(\d{4})\d{2}\d{2}T\d{6}\.\d+-\d{8}T\d{6}\.\d+\.nc$'
    match = re.search(pattern, filename)
    if match:
        return int(match.group(1))
    return None

def is_file_complete(filepath):
    """Check if file exists and is non-zero size."""
    if not filepath.exists():
        return False
    return filepath.stat().st_size > 0

def download_file(url, destination):
    """Download a file from URL to destination."""
    temp_file = destination.with_suffix('.tmp')
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        with open(temp_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        temp_file.rename(destination)
        return True
    except Exception as e:
        print(f"    Error: {e}")
        if temp_file.exists():
            temp_file.unlink()
        return False

def bulk_download(instrument="ctd", ooi_instrument="CTDPF"):
    """Bulk download instrument files from URL list with restart tolerance."""

    print(f"Running bulk_download for instrument type = {instrument} (OOI: {ooi_instrument})")

    # Read URL list
    url_list_file = Path("~/argosy/download_link_list.txt").expanduser()
    if not url_list_file.exists():
        print(f"File not found: {url_list_file}")
        return

    with open(url_list_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"Found {len(urls)} URLs to process\n")

    # Base folder for all instrument/year source data
    base_folder = Path("~/ooi/ooinet/rca/SlopeBase/scalar").expanduser()

    if not base_folder.exists():
        print(f"Base folder does not exist: {base_folder}")
        return

    # Create year folders as needed
    for year in range(2014, 2027):
        year_folder = base_folder / f"{year}_{instrument}"
        year_folder.mkdir(exist_ok=True)

    total_downloaded = 0
    total_skipped    = 0
    total_complete   = 0

    for url_idx, url in enumerate(urls, 1):
        print(f"=== URL {url_idx}/{len(urls)} ===")
        print(f"{url}")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            soup  = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a')

            nc_files = [
                link.get('href', '') for link in links
                if link.get('href', '').endswith('.nc')
                and not link.get('href', '').endswith('.ncml')
                and ooi_instrument in link.get('href', '')
            ]

            already_downloaded = 0
            to_download = []

            for filename in nc_files:
                year = parse_year_from_filename(filename)
                if year is None:
                    continue
                dest_file = base_folder / f"{year}_{instrument}" / filename
                if is_file_complete(dest_file):
                    already_downloaded += 1
                else:
                    to_download.append((filename, year))

            print(f"  Total .nc files:       {len(nc_files)}")
            print(f"  Already downloaded:    {already_downloaded}")
            print(f"  Remaining to download: {len(to_download)}")

            total_complete += already_downloaded

            if not to_download:
                print(f"  All files complete, skipping\n")
                continue

            for file_idx, (filename, year) in enumerate(to_download, 1):
                dest_file = base_folder / f"{year}_{instrument}" / filename
                file_url  = url.rstrip('/') + '/' + filename
                print(f"  [{file_idx}/{len(to_download)}] {filename} -> {year}_{instrument}/")

                if download_file(file_url, dest_file):
                    total_downloaded += 1
                    print(f"    Complete: {dest_file.stat().st_size / (1024*1024):.1f} MB")
                else:
                    total_skipped += 1

            print()

        except Exception as e:
            print(f"  Error processing URL: {e}\n")
            continue

    print(f"=== Download Summary ===")
    print(f"Files already complete:  {total_complete}")
    print(f"Files newly downloaded:  {total_downloaded}")
    print(f"Files failed/skipped:    {total_skipped}")

    print("\nTotal files by year:")
    for year in range(2014, 2027):
        year_folder = base_folder / f"{year}_{instrument}"
        if year_folder.exists():
            count = len(list(year_folder.glob("*.nc")))
            if count > 0:
                print(f"  {year}: {count} files")


# Instrument key -> OOI instrument code mapping (from Sensor Table):
#   ctd   -> CTDPF
#   flor  -> FLORT
#   ph    -> PHSEN
#   pco2  -> PCO2W
#   nitr  -> NUTNR
#   par   -> PARAD
#   vel   -> VELPT
#   irr   -> SPKIR
#   oa/ba -> OPTAA

# Run the bulk download - uncomment as needed:
# bulk_download("ctd",  "CTDPF")
# bulk_download("flor", "FLORT")
# bulk_download("ph",   "PHSEN")
# bulk_download("pco2", "PCO2W")
# bulk_download("nitr", "NUTNR")
# bulk_download("par",  "PARAD")
# bulk_download("vel",  "VELPT")
# bulk_download("irr",  "SPKIR")
