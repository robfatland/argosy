"""
Scan CDOM, Chlorophyll-A, Backscatter, DO, and PAR for anomalous periods.
Use sensor-specific criteria to flag potential exclusion candidates.
"""
import glob
import numpy as np
import xarray as xr
from datetime import datetime, timedelta
from pathlib import Path

redux_base = Path("/home/rob/ooi/redux")

# Sensors to scan with their anomaly criteria
# For each: check if daily median falls outside expected range
SCAN_CONFIG = {
    'cdom': {'var': 'cdom', 'med_low': -0.5, 'med_high': 6.0, 'min_thresh': -2.0},
    'chlora': {'var': 'chlora', 'med_low': -0.1, 'med_high': 5.0, 'min_thresh': -1.0},
    'backscatter': {'var': 'backscatter', 'med_low': -0.0001, 'med_high': 0.004, 'min_thresh': -0.001},
    'dissolvedoxygen': {'var': 'dissolvedoxygen', 'med_low': 30.0, 'med_high': 320.0, 'min_thresh': 0.0},
    'par': {'var': 'par', 'med_low': -1.0, 'med_high': 500.0, 'min_thresh': -5.0},
}

for sensor_name, config in SCAN_CONFIG.items():
    print(f"\n{'='*60}")
    print(f"  {sensor_name.upper()} — scanning for anomalies")
    print(f"  Criteria: median outside [{config['med_low']}, {config['med_high']}]")
    print(f"            OR min < {config['min_thresh']}")
    print(f"{'='*60}")
    
    anomalous_days = []
    
    for year in range(2015, 2026):
        redux_dir = redux_base / f"redux{year}"
        if not redux_dir.exists():
            continue
        
        days_in_year = 366 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 365
        
        for doy in range(1, days_in_year + 1):
            try:
                files = sorted(redux_dir.glob(f"RCA_sb_sp_{sensor_name}_{year}_{doy}_*_V1.nc"))
            except OSError:
                continue
            if not files:
                continue
            
            day_vals = []
            for f in files:
                try:
                    ds = xr.open_dataset(f)
                    vals = ds[config['var']].values
                    valid = vals[~np.isnan(vals)]
                    if len(valid) > 0:
                        day_vals.extend(valid.tolist())
                    ds.close()
                except:
                    continue
            
            if not day_vals:
                continue
            
            arr = np.array(day_vals)
            median_val = np.median(arr)
            min_val = np.min(arr)
            max_val = np.max(arr)
            
            flagged = False
            if median_val < config['med_low'] or median_val > config['med_high']:
                flagged = True
            if min_val < config['min_thresh']:
                flagged = True
            
            if flagged:
                date = datetime(year, 1, 1) + timedelta(days=doy - 1)
                anomalous_days.append((date, median_val, min_val, max_val, len(files)))
    
    if not anomalous_days:
        print("  No anomalies found.")
        continue
    
    # Group into windows
    windows = []
    ws = anomalous_days[0][0]
    we = anomalous_days[0][0]
    worst_med = anomalous_days[0][1]
    worst_min = anomalous_days[0][2]
    
    for i in range(1, len(anomalous_days)):
        date = anomalous_days[i][0]
        if (date - we).days <= 2:
            we = date
            worst_med = min(worst_med, anomalous_days[i][1]) if anomalous_days[i][1] < config['med_low'] else max(worst_med, anomalous_days[i][1])
            worst_min = min(worst_min, anomalous_days[i][2])
        else:
            windows.append((ws, we, worst_med, worst_min))
            ws = date
            we = date
            worst_med = anomalous_days[i][1]
            worst_min = anomalous_days[i][2]
    windows.append((ws, we, worst_med, worst_min))
    
    print(f"\n  Found {len(anomalous_days)} anomalous days in {len(windows)} windows:")
    print(f"  {'Start':<12} {'End':<12} {'Days':>5} {'Worst med':>10} {'Worst min':>10}")
    for ws, we, wm, wmn in windows:
        days = (we - ws).days + 1
        print(f"  {ws.strftime('%Y-%m-%d'):<12} {we.strftime('%Y-%m-%d'):<12} {days:>5} {wm:>10.4f} {wmn:>10.4f}")
