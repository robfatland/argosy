#!/usr/bin/env python3
"""
Sync redux NetCDF files from localhost to S3 using AWS CLI.
Stops after 20 cumulative errors. Logs progress to file.
"""

from pathlib import Path
import subprocess
import time
from datetime import datetime

# Configuration
LOCAL_BASE = Path.home()
S3_BUCKET = 'epipelargosy'
YEARS = range(2015, 2026)
LOG_FILE = Path.home() / 'redux_sync.log'
MAX_ERRORS = 20

# Sensor types in alphabetical order
SENSORS = ['density', 'dissolvedoxygen', 'salinity', 'temperature', 'cdom', 'chlora', 'backscatter']

def log(message):
    """Write message to log file and print to console."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}\n"
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_line)
    
    print(log_line.strip())

def file_exists_s3(s3_path):
    """Check if file exists in S3 using AWS CLI."""
    try:
        result = subprocess.run(
            ['aws', 's3', 'ls', s3_path],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except:
        return False

def parse_filename(filename):
    """Parse redux filename to extract sorting keys.
    Returns (sensor_index, julian_day, profile_index) or None if invalid.
    """
    try:
        parts = filename.stem.split('_')
        if len(parts) < 8:
            return None
        
        sensor = parts[3]
        julian_day = int(parts[5])
        profile_index = int(parts[6])  # changed from day-relative index to global / absolute index
        
        if sensor not in SENSORS:
            return None
        
        sensor_index = SENSORS.index(sensor)
        return (julian_day, profile_index, sensor_index)
    except:
        return None

def sync_redux_to_s3():
    """Sync all redux folders to S3."""
    
    total_copied = 0
    total_skipped = 0
    total_errors = 0
    
    start_time = datetime.now()
    log(f"Starting sync at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Local base: {LOCAL_BASE}")
    log(f"S3 bucket: s3://{S3_BUCKET}")
    log(f"Log file: {LOG_FILE}")
    
    for year in YEARS:
        if total_errors >= MAX_ERRORS:
            log(f"ERROR LIMIT REACHED: {total_errors} errors. Stopping sync.")
            break
        
        local_dir = LOCAL_BASE / f'redux{year}'
        
        if not local_dir.exists():
            log(f"Skipping {year}: local directory not found")
            continue
        
        year_start_time = datetime.now()
        log(f"Synching year {year} begin at {year_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Get all NetCDF files and sort them
        local_files = list(local_dir.glob('RCA_sb_sp_*.nc'))
        
        if not local_files:
            log(f"Year {year}: No files found")
            continue
        
        # Sort files by julian day, profile index, sensor
        sorted_files = []
        for f in local_files:
            sort_key = parse_filename(f)
            if sort_key:
                sorted_files.append((sort_key, f))
        
        sorted_files.sort(key=lambda x: x[0])
        local_files = [f for _, f in sorted_files]
        
        year_copied = 0
        year_skipped = 0
        year_errors = 0
        
        for local_file in local_files:
            if total_errors >= MAX_ERRORS:
                log(f"ERROR LIMIT REACHED during year {year}. Stopping.")
                break
            
            s3_path = f"s3://{S3_BUCKET}/redux{year}/{local_file.name}"
            
            # Skip if file already exists on S3
            if file_exists_s3(s3_path):
                year_skipped += 1
                continue
            
            try:
                log(f"Copying: {local_file.name}")
                
                result = subprocess.run(
                    ['aws', 's3', 'cp', str(local_file), s3_path],
                    capture_output=True,
                    timeout=300,
                    text=True
                )
                
                if result.returncode == 0:
                    year_copied += 1
                else:
                    raise Exception(f"AWS CLI error: {result.stderr}")
                    
            except Exception as e:
                log(f"ERROR copying {local_file.name}: {e}")
                year_errors += 1
                total_errors += 1
        
        year_end_time = datetime.now()
        year_elapsed = (year_end_time - year_start_time).total_seconds()
        log(f"Synching year {year} complete at {year_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        log(f"Year {year}: {year_copied} copied, {year_skipped} skipped, {year_errors} errors ({year_elapsed:.1f}s)")
        
        total_copied += year_copied
        total_skipped += year_skipped
    
    end_time = datetime.now()
    log(f"Sync complete at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Total: {total_copied} copied, {total_skipped} skipped, {total_errors} errors")
    
    if total_errors >= MAX_ERRORS:
        log(f"STOPPED DUE TO ERROR LIMIT")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(sync_redux_to_s3())
