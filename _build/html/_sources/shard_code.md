Jupyter cell code customized to shard ph data from data variable `ph_seawater`: 


```
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

# Sensor mapping: input variable -> output variable name
SENSOR_MAP = {
    'sea_water_temperature': 'temperature',
    'sea_water_practical_salinity': 'salinity',
    'sea_water_density': 'density',
    'corrected_dissolved_oxygen': 'dissolvedoxygen',
    'fluorometric_cdom': 'cdom',
    'fluorometric_chlorophyll_a': 'chlora',
    'optical_backscatter': 'backscatter',
    'ph_seawater': 'ph'                                                 # add sensor here
}

# Instrument configuration: folder suffix -> file pattern
INSTRUMENTS = {
    'ctd': 'CTDPF',
    'flor': 'FLORT',
    'ph': 'PHSEN'                                                       # add instrument here
}

def process_multi_sensor_redux(instrument='ctd'):
    """Process source files for multiple sensor types."""
    
    if instrument not in INSTRUMENTS:
        print(f"Unknown instrument: {instrument}")
        return
    
    file_pattern = INSTRUMENTS[instrument]
    
    # Determine which sensors to process based on instrument
    if instrument == 'ctd':
        active_sensors = {k: v for k, v in SENSOR_MAP.items() if v in ['temperature', 'salinity', 'density', 'dissolvedoxygen']}
    elif instrument == 'flor':
        active_sensors = {k: v for k, v in SENSOR_MAP.items() if v in ['cdom', 'chlora', 'backscatter']}
    elif instrument == 'ph':
        active_sensors = {k: v for k, v in SENSOR_MAP.items() if v in ['ph']}
    else:                                                                                                       # add instrument here
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
    stats = {sensor: {'attempted': 0, 'written': 0, 'skipped': 0} for sensor in active_sensors.values()}
    
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
                        
                        start_time_profile = pd.to_datetime(start_str)
                        peak_time_profile = pd.to_datetime(peak_str)
                        
                        # Track daily profile sequence
                        date_key = start_time_profile.date()
                        if date_key not in daily_profiles:
                            daily_profiles[date_key] = 0
                        daily_profiles[date_key] += 1
                        daily_sequence = daily_profiles[date_key]
                        
                        try:
                            profile_data = ds.sel(time=slice(start_time_profile, peak_time_profile))
                            
                            if len(profile_data.time) == 0:
                                continue
                            
                            # Determine output folder based on profile year
                            profile_year = start_time_profile.year
                            output_dir = Path(f"~/redux{profile_year}").expanduser()
                            julian_day = start_time_profile.timetuple().tm_yday
                            
                            # Process each sensor type
                            for input_var, output_var in active_sensors.items():
                                stats[output_var]['attempted'] += 1
                                
                                # Generate filename
                                filename = f"RCA_sb_sp_{output_var}_{profile_year}_{julian_day:03d}_{profile_index}_{daily_sequence}_V1.nc"
                                output_path = output_dir / filename
                                
                                # Skip if file already exists
                                if output_path.exists():
                                    stats[output_var]['skipped'] += 1
                                    continue
                                
                                # Check if variable exists in data
                                if input_var not in profile_data.data_vars:
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
            for sensor in active_sensors.values():
                count = len(list(output_dir.glob(f"*_{sensor}_*.nc")))
                if count > 0:
                    sensor_counts[sensor] = count
            
            if sensor_counts:
                print(f"\n{year}:")
                for sensor, count in sensor_counts.items():
                    print(f"  {sensor}: {count}")

# Run the sharding task
#   'ctd' for CTD sensors (4 sensors: density, dissolved oxygen, salinity, temperature)
#   'flor' for fluorometer (3 sensors: cdom, chlor-a, backscatter)
#   'ph' for pH (1 sensor: ph)
process_multi_sensor_redux('ph')
```