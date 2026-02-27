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
S3_BUCKET = 'epipelargosy'  # Your bucket name
YEARS = range(2024, 2025)
LOG_FILE = Path.home() / 'redux_sync.log'
MAX_ERRORS = 20

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

def sync_redux_to_s3():
    """Sync all redux folders to S3."""
    
    total_copied = 0
    total_skipped = 0
    total_errors = 0
    
    log(f"Starting sync at {time.time()}")
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
        
        log(f"Synching year {year} begin at time {time.time()}")
        year_start = time.time()
        
        # Get all NetCDF files in local directory
        local_files = list(local_dir.glob('RCA_sb_sp_*.nc'))
        
        if not local_files:
            log(f"Year {year}: No files found")
            continue
        
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
        
        year_elapsed = time.time() - year_start
        log(f"Synching year {year} complete at time {time.time()}")
        log(f"Year {year}: {year_copied} copied, {year_skipped} skipped, {year_errors} errors ({year_elapsed:.1f}s)")
        
        total_copied += year_copied
        total_skipped += year_skipped
    
    log(f"Sync complete at {time.time()}")
    log(f"Total: {total_copied} copied, {total_skipped} skipped, {total_errors} errors")
    
    if total_errors >= MAX_ERRORS:
        log(f"STOPPED DUE TO ERROR LIMIT")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(sync_redux_to_s3())

