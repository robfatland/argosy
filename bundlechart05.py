# Jupyter cell version of the bundle plot visualization 
#   - dynamic sensor selection
#   - midnight / noon annotation
#   - sensor count
#     - 8/11 scalar (missing pCO2, nitrate, PAR)
#     - 0/4 vector (no vel, spec.irr., oa, ba)

import matplotlib.pyplot as plt
import xarray as xr
from pathlib import Path
import ipywidgets as widgets
from IPython.display import display
import numpy as np
from datetime import datetime, timedelta
import pandas as pd
from zoneinfo import ZoneInfo

def get_input_with_default(prompt, default):
    """Get user input with default value."""
    response = input(f"{prompt} ").strip()
    return response if response else str(default)

# Oregon Slope Base timezone info
OREGON_TZ = ZoneInfo('America/Los_Angeles')

# Sensor configuration with colors that work well on white background
SENSORS = {
    'temperature': {'low': 7.0, 'high': 20.0, 'units': '°C', 'color': 'red'},
    'salinity': {'low': 32.0, 'high': 34.0, 'units': 'PSU', 'color': 'blue'},
    'density': {'low': 1024.0, 'high': 1028.0, 'units': 'kg/m³', 'color': 'black'},
    'dissolvedoxygen': {'low': 50.0, 'high': 300.0, 'units': 'µmol/kg', 'color': 'darkblue'},
    'cdom': {'low': 0.0, 'high': 2.5, 'units': 'ppb', 'color': 'brown'},
    'chlora': {'low': 0.0, 'high': 1.5, 'units': 'µg/L', 'color': 'green'},
    'backscatter': {'low': 0.0, 'high': 0.002, 'units': 'm⁻¹sr⁻¹', 'color': 'gray'},
    'ph': {'low': 7.6, 'high': 8.2, 'units': '', 'color': 'purple'},
}

# Get year range
start_year = int(get_input_with_default("Start year (default 2015):", "2015"))
end_year = int(get_input_with_default(f"End year (default {start_year}):", str(start_year)))

print(f"\nScanning redux folders from {start_year} to {end_year}...")
available_years = []
for year in range(start_year, end_year + 1):
    redux_dir = Path(f"~/ooi/redux/redux{year}").expanduser()
    if redux_dir.exists():
        profile_count = len(list(redux_dir.glob("*.nc")))
        if profile_count > 0:
            print(f"  redux{year}: {profile_count} profiles")
            available_years.append(year)

if not available_years:
    print("No years found")
else:
    print(f"\nUsing years: {available_years}")
    
    # Hardcoded to 2 sensors
    num_sensors = 2
    
    # Load profile files for all sensors
    all_profile_files = {}
    for sensor in SENSORS.keys():
        profile_files = []
        for year in available_years:
            redux_dir = Path(f"~/ooi/redux/redux{year}").expanduser()
            year_files = sorted(list(redux_dir.glob(f"*_{sensor}_*.nc")))
            profile_files.extend(year_files)
        all_profile_files[sensor] = profile_files
        print(f"{sensor}: {len(profile_files)} profiles")
    
    # Use the sensor with most profiles for indexing
    max_profiles = max(len(files) for files in all_profile_files.values())
    
    # Annotation data
    annotation_df = None
    annotation_enabled = False
    
    if max_profiles == 0:
        print("No profiles found")
    else:
        def extract_profile_info(filename):
            """Extract year, day, and profile number from filename."""
            parts = filename.stem.split('_')
            year = int(parts[4])
            doy = int(parts[5])
            profile_idx = int(parts[6])
            profile_num = int(parts[7])
            return year, doy, profile_idx, profile_num
        
        def check_time_gap(files, start_idx, end_idx):
            """Check if there's a >2 day gap between consecutive profiles."""
            if len(files) == 0 or start_idx >= len(files):
                return False
            for i in range(start_idx, min(end_idx - 1, len(files) - 1)):
                parts1 = files[i].stem.split('_')
                parts2 = files[i + 1].stem.split('_')
                
                year1, doy1 = int(parts1[4]), int(parts1[5])
                year2, doy2 = int(parts2[4]), int(parts2[5])
                
                date1 = datetime(year1, 1, 1) + timedelta(days=doy1 - 1)
                date2 = datetime(year2, 1, 1) + timedelta(days=doy2 - 1)
                
                if (date2 - date1).days > 2:
                    return True
            return False
        
        def check_noon_midnight(ds):
            """Check if profile spans local noon or midnight."""
            try:
                start_time = pd.to_datetime(ds.time.values[0])
                end_time = pd.to_datetime(ds.time.values[-1])
                peak_time = pd.to_datetime(ds.time.values[len(ds.time.values)//2])
                
                start_local = start_time.tz_localize('UTC').astimezone(OREGON_TZ)
                end_local = end_time.tz_localize('UTC').astimezone(OREGON_TZ)
                peak_local = peak_time.tz_localize('UTC').astimezone(OREGON_TZ)
                
                window_start = start_local - timedelta(minutes=30)
                window_end = end_local + timedelta(minutes=30)
                
                local_midnight = start_local.replace(hour=0, minute=0, second=0, microsecond=0)
                local_noon = start_local.replace(hour=12, minute=0, second=0, microsecond=0)
                
                if window_start <= local_midnight <= window_end:
                    return 'MIDNIGHT', peak_local
                
                if window_start <= local_noon <= window_end:
                    return 'NOON', peak_local
                    
            except Exception as e:
                print(f"Error in check_noon_midnight: {e}")
            
            return None, None
        
        def plot_bundle(sensor1, sensor2, low1, high1, mode1, low2, high2, mode2, nProfiles, index0):
            """Plot a bundle of consecutive profiles."""
            
            if nProfiles == 0:
                plt.figure(figsize=(10.2, 6.8))
                plt.title('nProfiles = 0', fontsize=14)
                plt.text(0.5, 0.5, 'Select nProfiles > 0', ha='center', va='center', transform=plt.gca().transAxes)
                plt.show()
                return
            
            start_idx = index0 - 1
            end_idx = min(start_idx + nProfiles, max_profiles)
            
            if start_idx >= max_profiles:
                plt.figure(figsize=(10.2, 6.8))
                plt.title('no data', fontsize=14)
                plt.text(0.5, 0.5, f'Index {index0} exceeds available profiles', ha='center', va='center', transform=plt.gca().transAxes)
                plt.show()
                return
            
            # Get selected sensors
            selected_sensors = [sensor1, sensor2]
            sensor_configs = [
                {'name': sensor1, 'low': low1, 'high': high1, 'units': SENSORS[sensor1]['units'], 
                 'color': SENSORS[sensor1]['color'], 'mode': mode1},
                {'name': sensor2, 'low': low2, 'high': high2, 'units': SENSORS[sensor2]['units'], 
                 'color': SENSORS[sensor2]['color'], 'mode': mode2}
            ]
            
            # Create figure with 85% of original size (12x8 -> 10.2x6.8)
            fig, ax1 = plt.subplots(figsize=(10.2, 6.8))
            ax2 = ax1.twiny()
            axes = [ax1, ax2]
            
            # Check for time gap
            first_sensor_files = all_profile_files[sensor1]
            has_time_gap = check_time_gap(first_sensor_files, start_idx, end_idx)
            
            # Check for noon/midnight if single profile
            noon_midnight_label = None
            peak_time_local = None
            current_profile_idx = None
            if nProfiles == 1 and start_idx < len(first_sensor_files):
                try:
                    ds = xr.open_dataset(first_sensor_files[start_idx])
                    noon_midnight_label, peak_time_local = check_noon_midnight(ds)
                    _, _, current_profile_idx, _ = extract_profile_info(first_sensor_files[start_idx])
                except Exception:
                    pass
            
            # Plot each sensor
            for sensor_idx, (sensor, config, ax) in enumerate(zip(selected_sensors, sensor_configs, axes)):
                profile_files = all_profile_files[sensor]
                
                if config['mode'] == 'bundle':
                    for i in range(start_idx, min(end_idx, len(profile_files))):
                        try:
                            ds = xr.open_dataset(profile_files[i])
                            sensor_data = ds[sensor].values
                            depth = ds['depth'].values
                            
                            valid_mask = ~(np.isnan(sensor_data) | np.isnan(depth))
                            if np.any(valid_mask):
                                data_clean = sensor_data[valid_mask]
                                depth_clean = depth[valid_mask]
                                ax.plot(data_clean, depth_clean, '-', color=config['color'], markersize=1, alpha=0.6, linewidth=1)
                        except Exception:
                            continue
                else:
                    depth_grid = np.linspace(0, 200, 200)
                    interpolated_data = []
                    
                    for i in range(start_idx, min(end_idx, len(profile_files))):
                        try:
                            ds = xr.open_dataset(profile_files[i])
                            sensor_data = ds[sensor].values
                            depth = ds['depth'].values
                            
                            valid_mask = ~(np.isnan(sensor_data) | np.isnan(depth))
                            if np.any(valid_mask) and len(depth[valid_mask]) > 1:
                                depth_clean = depth[valid_mask]
                                data_clean = sensor_data[valid_mask]
                                
                                sort_idx = np.argsort(depth_clean)
                                depth_sorted = depth_clean[sort_idx]
                                data_sorted = data_clean[sort_idx]
                                
                                interp_data = np.interp(depth_grid, depth_sorted, data_sorted, left=np.nan, right=np.nan)
                                
                                if np.any(~np.isnan(interp_data)):
                                    interpolated_data.append(interp_data)
                        except Exception:
                            continue
                    
                    if len(interpolated_data) >= 2:
                        data_array = np.array(interpolated_data)
                        valid_counts = np.sum(~np.isnan(data_array), axis=0)
                        
                        if np.any(valid_counts >= 2):
                            mask = valid_counts >= 2
                            mean = np.full(len(depth_grid), np.nan)
                            std = np.full(len(depth_grid), np.nan)
                            
                            mean[mask] = np.nanmean(data_array[:, mask], axis=0)
                            std[mask] = np.nanstd(data_array[:, mask], axis=0)
                            
                            valid = ~np.isnan(mean)
                            if np.any(valid):
                                ax.plot(mean[valid], depth_grid[valid], '-', color='black', linewidth=3)
                                ax.plot((mean + std)[valid], depth_grid[valid], '-', color='black', linewidth=1, alpha=0.7)
                                ax.plot((mean - std)[valid], depth_grid[valid], '-', color='black', linewidth=1, alpha=0.7)
                    elif len(interpolated_data) == 1:
                        data_array = np.array(interpolated_data)
                        mean = data_array[0]
                        valid = ~np.isnan(mean)
                        if np.any(valid):
                            ax.plot(mean[valid], depth_grid[valid], '-', color='black', linewidth=3)
                
                # Plot annotations if enabled
                if annotation_enabled and annotation_df is not None and nProfiles == 1 and current_profile_idx is not None:
                    sensor_annotations = annotation_df[
                        (annotation_df['shard'] == sensor) & 
                        (annotation_df['profile'] == current_profile_idx)
                    ]
                    
                    for _, row in sensor_annotations.iterrows():
                        try:
                            depth_val = row.get('depth', 180)
                            if pd.isna(depth_val):
                                depth_val = 180
                            
                            value_val = row.get('value', np.nan)
                            text_val = row.get('text', '')
                            
                            if pd.notna(text_val) and text_val:
                                if pd.notna(value_val):
                                    ax.text(value_val, depth_val, text_val, fontsize=10, ha='center')
                            else:
                                if pd.isna(value_val):
                                    continue
                                
                                color_val = row.get('color', config['color'])
                                if pd.isna(color_val):
                                    color_val = config['color']
                                
                                markersize_val = row.get('markersize', 9)
                                if pd.isna(markersize_val):
                                    markersize_val = 9
                                
                                opacity_val = row.get('opacity', 1.0)
                                if pd.isna(opacity_val):
                                    opacity_val = 1.0
                                
                                ax.plot(value_val, depth_val, 'o', color=color_val, 
                                       markersize=markersize_val, alpha=opacity_val)
                        except Exception as e:
                            print(f"Error rendering annotation: {e}")
                
                # Set up axes
                ax.set_xlabel(f'{config["name"].capitalize()} ({config["units"]})', fontsize=12, color=config['color'])
                ax.set_xlim(config['low'], config['high'])
                ax.tick_params(axis='x', labelcolor=config['color'])
                
                if sensor_idx == 1:
                    ax.xaxis.set_label_position('top')
            
            # Set y-axis
            ax1.set_ylabel('Depth (m)', fontsize=12)
            ax1.set_ylim(200, 0)
            ax1.grid(True, alpha=0.3)
            
            # Add Time Gap warning
            if has_time_gap:
                ax1.text(0.95, 0.05, 'Time Gap', transform=ax1.transAxes,
                       fontsize=20, fontweight='bold', ha='right', va='bottom',
                       bbox=dict(boxstyle='round', facecolor='white', edgecolor='black', linewidth=2))
            
            # Add NOON/MIDNIGHT label
            if noon_midnight_label:
                label_text = f"{noon_midnight_label}\n{peak_time_local.strftime('%H:%M:%S')}"
                ax1.text(0.95, 0.15, label_text, transform=ax1.transAxes,
                       fontsize=20, fontweight='bold', ha='right', va='bottom')
           
            # Title
            if len(first_sensor_files) > start_idx:
                year, doy, profile_idx, profile_num = extract_profile_info(first_sensor_files[start_idx])
                if nProfiles == 1:
                    title = f'{year}-{doy:03d}-{profile_num} ({profile_idx})'
                else:
                    last_idx = min(end_idx - 1, len(first_sensor_files) - 1)
                    last_year, last_doy, last_profile_idx, last_profile_num = extract_profile_info(first_sensor_files[last_idx])
                    title = f'{year}-{doy:03d}-{profile_num} through {last_year}-{last_doy:03d}-{last_profile_num} ({profile_idx} through {last_profile_idx})'
                fig.suptitle(title, fontsize=14)
            else:
                fig.suptitle('no data', fontsize=14)
            
            plt.tight_layout()
            plt.show()
        
        def load_annotations(b):
            """Load annotation file."""
            global annotation_df, annotation_enabled
            
            annotation_file = annotation_path.value.strip()
            if not annotation_file:
                print("No annotation file specified")
                return
            
            try:
                file_path = Path(annotation_file).expanduser()
                if not file_path.exists():
                    print(f"File not found: {file_path}")
                    return
                
                df = pd.read_csv(file_path)
                
                required_cols = ['shard', 'profile', 'depth', 'value', 'color', 'markersize', 'opacity', 'text']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    print(f"Missing required columns: {missing_cols}")
                    return
                
                if df['shard'].isna().any() or df['profile'].isna().any():
                    print("Error: shard and profile fields cannot be empty")
                    return
                
                annotation_df = df
                annotation_enabled = not annotation_enabled
                
                if annotation_enabled:
                    print(f"Annotations loaded and enabled: {len(df)} rows")
                    annotation_btn.description = "Annotation: ON"
                else:
                    print("Annotations disabled")
                    annotation_btn.description = "Annotation: OFF"
                
            except Exception as e:
                print(f"Error loading annotations: {e}")
        
        # Create sensor selection dropdowns
        sensor_list = list(SENSORS.keys())
        sensor1_dropdown = widgets.Dropdown(options=sensor_list, value='temperature', description='Sensor 1:')
        sensor2_dropdown = widgets.Dropdown(options=sensor_list, value='salinity', description='Sensor 2:')
        
        # Range sliders and mode toggle for sensor 1
        low1_slider = widgets.FloatSlider(value=SENSORS['temperature']['low'], min=0, max=SENSORS['temperature']['high'], 
                                          step=SENSORS['temperature']['high']/100, description='Sensor 1 low:', 
                                          continuous_update=False, readout_format='.3f')
        high1_slider = widgets.FloatSlider(value=SENSORS['temperature']['high'], min=SENSORS['temperature']['high']/2, 
                                           max=2*SENSORS['temperature']['high'], step=SENSORS['temperature']['high']/100,
                                           description='Sensor 1 high:', continuous_update=False, readout_format='.3f')
        mode1_toggle = widgets.ToggleButtons(options=['bundle', 'meanstd'], value='bundle', description='Sensor 1 mode:')
        
        # Range sliders and mode toggle for sensor 2
        low2_slider = widgets.FloatSlider(value=SENSORS['salinity']['low'], min=0, max=SENSORS['salinity']['high'],
                                          step=SENSORS['salinity']['high']/100, description='Sensor 2 low:', 
                                          continuous_update=False, readout_format='.3f')
        high2_slider = widgets.FloatSlider(value=SENSORS['salinity']['high'], min=SENSORS['salinity']['high']/2, 
                                           max=2*SENSORS['salinity']['high'], step=SENSORS['salinity']['high']/100,
                                           description='Sensor 2 high:', continuous_update=False, readout_format='.3f')
        mode2_toggle = widgets.ToggleButtons(options=['bundle', 'meanstd'], value='bundle', description='Sensor 2 mode:')
        
        # Profile navigation sliders
        nProfiles_slider = widgets.IntSlider(value=1, min=0, max=180, step=1, description='nProfiles:', continuous_update=True)
        index0_slider = widgets.IntSlider(value=1, min=1, max=max_profiles, step=1, description='index0:', continuous_update=True)
        
        # Update slider ranges when sensor selection changes
        def update_sensor1_sliders(change):
            sensor = change['new']
            low1_slider.value = SENSORS[sensor]['low']
            low1_slider.min = 0
            low1_slider.max = SENSORS[sensor]['high']
            low1_slider.step = SENSORS[sensor]['high'] / 100
            high1_slider.value = SENSORS[sensor]['high']
            high1_slider.min = SENSORS[sensor]['high'] / 2
            high1_slider.max = 2 * SENSORS[sensor]['high']
            high1_slider.step = SENSORS[sensor]['high'] / 100
        
        def update_sensor2_sliders(change):
            sensor = change['new']
            low2_slider.value = SENSORS[sensor]['low']
            low2_slider.min = 0
            low2_slider.max = SENSORS[sensor]['high']
            low2_slider.step = SENSORS[sensor]['high'] / 100
            high2_slider.value = SENSORS[sensor]['high']
            high2_slider.min = SENSORS[sensor]['high'] / 2
            high2_slider.max = 2 * SENSORS[sensor]['high']
            high2_slider.step = SENSORS[sensor]['high'] / 100
        
        sensor1_dropdown.observe(update_sensor1_sliders, names='value')
        sensor2_dropdown.observe(update_sensor2_sliders, names='value')
        
        # Annotation widgets
        annotation_path = widgets.Text(value='', placeholder='~/argosy/annotation.csv', description='Annotation file:', 
                                       style={'description_width': 'initial'})
        annotation_btn = widgets.Button(description='Annotation: OFF')
        annotation_btn.on_click(load_annotations)
        
        # Navigation buttons
        def on_minus_minus(b):
            step = max(1, nProfiles_slider.value // 2)
            index0_slider.value = max(1, index0_slider.value - step)
        
        def on_minus(b):
            index0_slider.value = max(1, index0_slider.value - 1)
        
        def on_plus(b):
            index0_slider.value = min(max_profiles, index0_slider.value + 1)
        
        def on_plus_plus(b):
            step = max(1, nProfiles_slider.value // 2)
            index0_slider.value = min(max_profiles, index0_slider.value + step)
        
        btn_minus_minus = widgets.Button(description='--')
        btn_minus = widgets.Button(description='-')
        btn_plus = widgets.Button(description='+')
        btn_plus_plus = widgets.Button(description='++')
        
        btn_minus_minus.on_click(on_minus_minus)
        btn_minus.on_click(on_minus)
        btn_plus.on_click(on_plus)
        btn_plus_plus.on_click(on_plus_plus)
        
        nav_buttons = widgets.HBox([btn_minus_minus, btn_minus, btn_plus, btn_plus_plus])
        annotation_box = widgets.HBox([annotation_path, annotation_btn])
        
        # Create interactive plot with nProfiles and index0 at the end
        interactive_plot = widgets.interactive(plot_bundle, 
                                               sensor1=sensor1_dropdown, sensor2=sensor2_dropdown,
                                               low1=low1_slider, high1=high1_slider, mode1=mode1_toggle,
                                               low2=low2_slider, high2=high2_slider, mode2=mode2_toggle,
                                               nProfiles=nProfiles_slider, index0=index0_slider)
        
        # Display widgets
        display(interactive_plot)
        display(nav_buttons)
        display(annotation_box)
