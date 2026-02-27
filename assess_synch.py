#!/usr/bin/env python3
"""
Assess sync status between local redux folders and S3.
Shows file counts for each sensor type by year.
Asterisk (*) indicates mismatch between local and S3.
"""

from pathlib import Path
import sys

# Configuration
LOCAL_BASE = Path.home()
S3_BASE = Path.home() / 's3'
YEARS = range(2015, 2027)
SENSORS = ['density', 'dissolvedoxygen', 'salinity', 'temperature']

def count_files(base_path, year, sensor):
    """Count NetCDF files for given year and sensor."""
    folder = base_path / f'redux{year}'
    if not folder.exists():
        return 0
    return len(list(folder.glob(f'RCA_sb_sp_{sensor}_*.nc')))

def main():
    # Print header
    print(f"{'Year':<7}", end='')
    for sensor in SENSORS:
        print(f"  {sensor[:4]}-local {sensor[:4]}-s3", end='')
    print()
    print("-" * 85)
    sys.stdout.flush()
    
    # Print data for each year
    for year in YEARS:
        has_mismatch = False
        
        # Check for mismatches first
        for sensor in SENSORS:
            local_count = count_files(LOCAL_BASE, year, sensor)
            s3_count = count_files(S3_BASE, year, sensor)
            if local_count != s3_count:
                has_mismatch = True
                break
        
        # Print year with asterisk if mismatch
        year_str = f"{year}*" if has_mismatch else str(year)
        print(f"{year_str:<7}", end='')
        
        # Print counts
        for sensor in SENSORS:
            local_count = count_files(LOCAL_BASE, year, sensor)
            s3_count = count_files(S3_BASE, year, sensor)
            print(f"  {local_count:>10} {s3_count:>7}", end='')
        
        print()
        sys.stdout.flush()

if __name__ == '__main__':
    main()

