# SGA Sensor Presence/Absence Chart
# Shows when each of the 7 sensors has data in pp06 over a specified time range.
# Horizontal axis: time. Vertical: stacked rows for each sensor.
# Each profile with data for a given sensor is marked as a thin vertical line.
#
# Run this as: %run /home/rob/argosy/sga/sga_sensor_presence.py
#
# Input: start month (MM-YYYY) and end month (MM-YYYY)

import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import pandas as pd

# Configuration
DATA_BASE = Path("~/ooi/postproc/pp06").expanduser()
SENSORS = ['temperature', 'salinity', 'density', 'dissolvedoxygen',
           'cdom', 'chlora', 'backscatter']

# Get time range from user
start_input = input("Start month (MM-YYYY, default 08-2023): ").strip() or "08-2023"
end_input = input("End month (MM-YYYY, default 09-2024): ").strip() or "09-2024"

# Parse into date range
start_month, start_year = int(start_input.split('-')[0]), int(start_input.split('-')[1])
end_month, end_year = int(end_input.split('-')[0]), int(end_input.split('-')[1])

# Start date is 1st of start month; end date is last day of end month
start_date = datetime(start_year, start_month, 1)
if end_month == 12:
    end_date = datetime(end_year + 1, 1, 1)
else:
    end_date = datetime(end_year, end_month + 1, 1)

print(f"\nTime range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
print(f"Sensors: {SENSORS}")
print(f"Data source: {DATA_BASE}")

# Determine which year folders to scan
years_to_scan = list(range(start_year, end_year + 1))

# For each sensor, collect the dates of all profiles within the time range
sensor_dates = {sensor: [] for sensor in SENSORS}

for year in years_to_scan:
    redux_dir = DATA_BASE / f"redux{year}"
    if not redux_dir.exists():
        continue

    for sensor in SENSORS:
        files = list(redux_dir.glob(f"*_{sensor}_*.nc"))
        for f in files:
            parts = f.stem.split('_')
            file_year = int(parts[4])
            doy = int(parts[5])

            # Convert year + doy to datetime
            profile_date = datetime(file_year, 1, 1) + pd.Timedelta(days=doy - 1)

            # Filter to time range
            if start_date <= profile_date < end_date:
                sensor_dates[sensor].append(profile_date)

# Report counts
print("\nProfiles in time range:")
for sensor in SENSORS:
    print(f"  {sensor}: {len(sensor_dates[sensor])}")

# Create the presence/absence chart
fig, ax = plt.subplots(figsize=(14, 5))

y_positions = list(range(len(SENSORS)))
colors = ['red', 'blue', 'black', 'darkblue', 'darkcyan', 'green', 'gray']

for i, sensor in enumerate(SENSORS):
    dates = sorted(sensor_dates[sensor])
    if dates:
        # Plot each profile date as a thin vertical tick mark
        for d in dates:
            ax.plot([d, d], [i - 0.35, i + 0.35], '-', color=colors[i],
                    linewidth=0.3, alpha=0.6)

# Format axes
ax.set_yticks(y_positions)
ax.set_yticklabels([s.capitalize() for s in SENSORS])
ax.set_xlim(start_date, end_date)
ax.set_xlabel('Date')
ax.set_title(f'Sensor Data Presence in pp06 ({start_date.strftime("%b %Y")} - '
             f'{(end_date - pd.Timedelta(days=1)).strftime("%b %Y")})')
ax.grid(True, axis='x', alpha=0.3)

plt.tight_layout()

# Save
SGA_DIR = Path('~/ooi/analysis/sga').expanduser()
SGA_DIR.mkdir(parents=True, exist_ok=True)
plt.savefig(SGA_DIR / 'sensor_presence.png', dpi=150, bbox_inches='tight')
plt.show()

print(f"\nChart saved to {SGA_DIR / 'sensor_presence.png'}")
