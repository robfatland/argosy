Jupyter cell code for sharding sensor data with direction support (ascent/descent):

```python
import pandas as pd
import xarray as xr
from pathlib import Path
import numpy as np

def get_input_with_default(prompt, default):
    """Get user input with default value."""
    response = input(f"{prompt} ").strip().lower()
    return response if response else default

def load_profile_indices(year):
    """Load profile indices for given year."""
    profile_file = Path(f"~/profileIndices/RS01SBPS_profiles_{year}.csv").expanduser()
    if not profile_file.exists():
        return None
    return pd.read_csv(profile_file)

# Sensor mapping: input variable -> (output variable name, direction)
# direction: 'ascent' = start to peak, 'descent' = peak to end
SENSOR_MAP = {
    'sea_water_temperature': ('temperature', 'ascent'),
    'sea_water_practical_salinity': ('salinity', 'ascent'),
    'sea_water_density': ('density', 'ascent'),
    'corrected_dissolved_oxygen': ('dissolvedoxygen', 'ascent'),
    'fluorometric_cdom': ('cdom', 'ascent'),
    'fluorometric_chlorophyll_a': ('chlora', 'ascent'),
    'optical_backscatter': ('backscatter', 'ascent'),
    'ph_seawater': ('ph', 'descent'),
    'pco2_seawater': ('pco2', 'descent')
}

# Instrument configuration: folder suffix -> file pattern
INSTRUMENTS = {
    'ctd': 'CTDPF',
    'flor': 'FLORT',
    'ph': 'PHSEN',
    'pco2': 'PCO2W'
}

def process_multi_sensor_redux(instrument='ctd'):
    """Process source files for multiple sensor types."""

    if instrument not in INSTRUMENTS:
        print(f"Unknown instrument: {instrument}")
        return

    file_pattern = INSTRUMENTS[instrument]

    # Determine which sensors to process based on instrument
    if instrument == 'ctd':
        active_sensors = {k: v for k, v in SENSOR_MAP.items() if v[0] in ['temperature', 'salinity', 'density', 'dissolvedoxygen']}
    elif instrument == 'flor':
        active_sensors = {k: v for k, v in SENSOR_MAP.items() if v[0] in ['cdom', 'chlora', 'backscatter']}
    elif instrument == 'ph':
        active_sensors = {k: v for k, v in SENSOR_MAP.items() if v[0] in ['ph']}
    elif instrument == 'pco2':
        active_sensors = {k: v for k, v in SENSOR_MAP.items() if v[0] in ['pco2']}
    else:
        active_sensors = SENSOR_MAP

    # Scan for source folders
    base_folder = Path("~/ooidata/rca/sb/scalar").expanduser()

    print(f"Scanning for {instrument} source folders...")
    available_years = []
    for year in range(2014, 2027):
        source_folder = base_folder / f"{year}_{instrument}"
        if source_folder.exists():
            file_count = len(list(source_folder.glob(f"*{file_pattern}*.nc")))
            if file_count > 0:
                print(f"  {year}_{instrument}: {file_count} files")
                response = get_input_with_default(f"    Process {year}? [y/n] (default y):", "y")
                if response == 'y':
                    available_years.append(year)

    if not available_years:
        print("No years selected")
        return

    print(f"\nSelected years: {available_years}")

    # Create output directories
    for year in range(2014, 2027):
        output_dir = Path(f"~/redux{year}").expanduser()
        output_dir.mkdir(exist_ok=True)

    # Statistics
    stats = {sensor[0]: {'attempted': 0, 'written': 0, 'skipped': 0} for sensor in active_sensors.values()}

    # Process each year
    for folder_year in available_years:
        source_folder = base_folder / f"{folder_year}_{instrument}"
        source_files = sorted(list(source_folder.glob(f"*{file_pattern}*.nc")))

        print(f"\n=== Processing {folder_year}_{instrument} ({len(source_files)} files) ===")

        for file_idx, file_path in enumerate(source_files, 1):
            if file_idx % 5 == 0:
                print(f"  File {file_idx}/{len(source_files)}")

            try:
                ds = xr.open_dataset(file_path)
                ds = ds.swap_dims({'obs': 'time'})

                start_time = pd.to_datetime(ds.time.values[0])
                end_time = pd.to_datetime(ds.time.values[-1])

                # Process each year in the file
                for year in range(start_time.year, end_time.year + 1):
                    profiles_df = load_profile_indices(year)
                    if profiles_df is None:
                        continue

                    daily_profiles = {}

                    for _, profile_row in profiles_df.iterrows():
                        profile_index = profile_row['profile']
                        start_str = profile_row['start']
                        peak_str = profile_row['peak']
                        end_str = profile_row['end']

                        start_time_profile = pd.to_datetime(start_str)
                        peak_time_profile = pd.to_datetime(peak_str)
                        end_time_profile = pd.to_datetime(end_str)

                        # Track daily profile sequence
                        date_key = start_time_profile.date()
                        if date_key not in daily_profiles:
                            daily_profiles[date_key] = 0
                        daily_profiles[date_key] += 1
                        daily_sequence = daily_profiles[date_key]

                        # Process each sensor type
                        for input_var, (output_var, direction) in active_sensors.items():
                            stats[output_var]['attempted'] += 1

                            # Determine time slice based on direction
                            if direction == 'ascent':
                                slice_start = start_time_profile
                                slice_end = peak_time_profile
                            else:  # descent
                                slice_start = peak_time_profile
                                slice_end = end_time_profile

                            try:
                                profile_data = ds.sel(time=slice(slice_start, slice_end))

                                if len(profile_data.time) == 0:
                                    continue

                                # Check if variable exists in data
                                if input_var not in profile_data.data_vars:
                                    continue

                                # Determine output folder based on profile year
                                profile_year = start_time_profile.year
                                output_dir = Path(f"~/redux{profile_year}").expanduser()
                                julian_day = start_time_profile.timetuple().tm_yday

                                # Generate filename
                                filename = f"RCA_sb_sp_{output_var}_{profile_year}_{julian_day:03d}_{profile_index}_{daily_sequence}_V1.nc"
                                output_path = output_dir / filename

                                # Skip if file already exists
                                if output_path.exists():
                                    stats[output_var]['skipped'] += 1
                                    continue

                                # Create dataset with renamed variable
                                sensor_ds = xr.Dataset({
                                    output_var: profile_data[input_var]
                                })

                                # Add depth coordinate if available
                                if 'depth' in profile_data.coords:
                                    sensor_ds = sensor_ds.assign_coords(depth=profile_data['depth'])

                                # Remove unwanted variables
                                for var in ['lat', 'lon', 'obs']:
                                    if var in sensor_ds.coords:
                                        sensor_ds = sensor_ds.drop_vars(var)
                                    if var in sensor_ds.data_vars:
                                        sensor_ds = sensor_ds.drop_vars(var)

                                # Write file
                                sensor_ds.to_netcdf(output_path)
                                stats[output_var]['written'] += 1

                            except Exception:
                                continue

            except Exception as e:
                continue

    # Print statistics
    print(f"\n=== Processing Complete ===")
    for sensor, counts in stats.items():
        print(f"\n{sensor}:")
        print(f"  Attempted: {counts['attempted']}")
        print(f"  Written: {counts['written']}")
        print(f"  Skipped (already exist): {counts['skipped']}")

    # Report files by year and sensor
    print("\n=== Files by Year ===")
    for year in range(2014, 2027):
        output_dir = Path(f"~/redux{year}").expanduser()
        if output_dir.exists():
            sensor_counts = {}
            for sensor_info in active_sensors.values():
                sensor = sensor_info[0]
                count = len(list(output_dir.glob(f"*_{sensor}_*.nc")))
                if count > 0:
                    sensor_counts[sensor] = count

            if sensor_counts:
                print(f"\n{year}:")
                for sensor, count in sensor_counts.items():
                    print(f"  {sensor}: {count}")

# Run the sharding task
#   'ctd' for CTD sensors (4 sensors: temperature, salinity, density, dissolvedoxygen - all ascent)
#   'flor' for fluorometer (3 sensors: cdom, chlora, backscatter - all ascent)
#   'ph' for pH (1 sensor: ph - descent)
#   'pco2' for pCO2 (1 sensor: pco2 - descent)
process_multi_sensor_redux('ph')
```
