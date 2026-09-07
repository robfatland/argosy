# Bundle animation: Temperature profile time-lapse for Oregon Slope Base
# Run this as: %run ~/argosy/vis/bundle_animation.py
#
# Inputs (interactive):
#   - Data source (redux/pp01/pp02/pp05/pp06)
#   - Year selection
#   - Date range, bundle size, frame delay
#   - Display mode: bundle overlay or mean±std
#   - TMLD overlay option
#
# Output:
#   - MP4 animation: ~/ooi/visualizations/bundle_animation.mp4

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import xarray as xr
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.interpolate import interp1d


# == Data source selection ======================================================

source_choice = input("Data source (redux/pp01/pp02/pp05/pp06, default redux): ").strip().lower()
if source_choice in ('pp01', 'pp02', 'pp05'):
    DATA_BASE = Path(f"~/ooi/postproc/{source_choice}/redux").expanduser()
elif source_choice == 'pp06':
    DATA_BASE = Path("~/ooi/postproc/pp06/redux").expanduser()
else:
    source_choice = "redux"
    DATA_BASE = Path("~/ooi/redux").expanduser()


# == Utilities ==================================================================

def get_input_with_default(prompt, default):
    """Get user input with default value."""
    response = input(f"{prompt} ").strip()
    return response if response else default


def load_tmld_data():
    """Load TMLD data if available."""
    try:
        return pd.read_csv(Path("~/argosy/TMLD/tmld_estimates.csv").expanduser())
    except FileNotFoundError:
        return pd.DataFrame()


def check_time_gap(files, start_idx, end_idx):
    """Check if there's a >2 day gap between consecutive profiles."""
    for i in range(start_idx, end_idx - 1):
        parts1 = files[i].stem.split('_')
        parts2 = files[i + 1].stem.split('_')

        year1, doy1 = int(parts1[4]), int(parts1[5])
        year2, doy2 = int(parts2[4]), int(parts2[5])

        date1 = datetime(year1, 1, 1) + timedelta(days=doy1 - 1)
        date2 = datetime(year2, 1, 1) + timedelta(days=doy2 - 1)

        if (date2 - date1).days > 2:
            return True

    return False


def calculate_mean_profile(files, start_idx, end_idx):
    """Calculate mean and std profiles from bundle."""
    depth_grid = np.linspace(0, 200, 201)
    temp_profiles = []

    for i in range(start_idx, end_idx):
        try:
            ds = xr.open_dataset(files[i])
            temperature = ds['temperature'].values
            depth = ds['depth'].values

            valid_mask = ~(np.isnan(temperature) | np.isnan(depth))
            if np.any(valid_mask):
                temp_clean = temperature[valid_mask]
                depth_clean = depth[valid_mask]

                if len(temp_clean) > 1:
                    f = interp1d(depth_clean, temp_clean, bounds_error=False, fill_value=np.nan)
                    temp_interp = f(depth_grid)
                    if not np.all(np.isnan(temp_interp)):
                        temp_profiles.append(temp_interp)
        except Exception:
            continue

    if len(temp_profiles) < 2:
        return None, None, None

    temp_array = np.array(temp_profiles)

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        mean_temp = np.nanmean(temp_array, axis=0)
        std_temp = np.nanstd(temp_array, axis=0, ddof=1)

    if np.all(np.isnan(mean_temp)):
        return None, None, None

    return depth_grid, mean_temp, std_temp


# == Main animation =============================================================

def create_animated_bundle_file():
    """Create animated bundle plot with mean profile option."""

    # Scan for populated year folders
    print("Scanning for redux folders...")
    available_years = []
    for year in range(2014, 2027):
        redux_dir = DATA_BASE / f"redux{year}"
        if redux_dir.exists():
            profile_count = len(list(redux_dir.glob("*.nc")))
            if profile_count > 0:
                print(f"  redux{year}: {profile_count} profiles")
                response = get_input_with_default(f"    Include {year}? [y/n] (default y):", "y").lower()
                if response == 'y':
                    available_years.append(year)

    if not available_years:
        print("No years selected")
        return

    print(f"\nSelected years: {available_years}")

    # Load all profile files from selected years
    profile_files = []
    for year in available_years:
        redux_dir = DATA_BASE / f"redux{year}"
        year_files = sorted(list(redux_dir.glob("*.nc")))
        profile_files.extend(year_files)

    print(f"Total profiles loaded: {len(profile_files)}")

    # Determine default date range from available files
    if profile_files:
        first_parts = profile_files[0].stem.split('_')
        last_parts = profile_files[-1].stem.split('_')

        first_year, first_doy = int(first_parts[4]), int(first_parts[5])
        last_year, last_doy = int(last_parts[4]), int(last_parts[5])

        default_start = datetime(first_year, 1, 1) + timedelta(days=first_doy - 1)
        default_end = datetime(last_year, 1, 1) + timedelta(days=last_doy - 1)

        default_start_str = default_start.strftime("%d-%b-%Y").upper()
        default_end_str = default_end.strftime("%d-%b-%Y").upper()
    else:
        default_start_str = "01-JAN-2018"
        default_end_str = "31-DEC-2018"

    # Get user inputs
    show_mean = get_input_with_default(
        "Display mean profile? [y/n] (default y - shows mean):", "y").lower() == 'y'
    show_tmld = get_input_with_default(
        "Include TMLD estimate in the visualization? Default is no. [y/n]", "n").lower() == 'y'
    n_profiles = int(get_input_with_default(
        "How many profiles in the bundle? Default is 18 (two days)", "18"))
    delay = float(get_input_with_default(
        "How many seconds delay between frames? (0.05 sec):", "0.05"))
    start_date = get_input_with_default(f"Start date (default {default_start_str}):", default_start_str)
    end_date = get_input_with_default(f"End date (default {default_end_str}):", default_end_str)

    # Parse dates
    start_dt = datetime.strptime(start_date, "%d-%b-%Y")
    end_dt = datetime.strptime(end_date, "%d-%b-%Y")

    tmld_df = load_tmld_data() if show_tmld else pd.DataFrame()

    # Filter files by date range
    filtered_files = []
    for file in profile_files:
        parts = file.stem.split('_')
        year = int(parts[4])
        doy = int(parts[5])
        file_date = datetime(year, 1, 1) + timedelta(days=doy - 1)
        if start_dt <= file_date <= end_dt:
            filtered_files.append(file)

    if len(filtered_files) < n_profiles:
        print(f"Only {len(filtered_files)} profiles found in date range")
        return

    print(f"Creating animation with {len(filtered_files)} profiles...")
    display_mode = "Mean Profile" if show_mean else "Bundle"
    print(f"Display mode: {display_mode}")

    # Set up the figure
    fig, ax = plt.subplots(figsize=(12, 8))
    total_frames = len(filtered_files) - n_profiles + 1

    def animate_frame(frame):
        """Animation function."""
        ax.clear()
        ax.set_xlim(7, 20)
        ax.set_ylim(200, 0)
        ax.set_xlabel('Temperature (°C)', fontsize=12)
        ax.set_ylabel('Depth (m)', fontsize=12)
        ax.grid(True, alpha=0.3)

        start_idx = frame
        end_idx = min(start_idx + n_profiles, len(filtered_files))

        if start_idx >= len(filtered_files):
            return

        has_time_gap = check_time_gap(filtered_files, start_idx, end_idx)

        if show_mean:
            depth_grid, mean_temp, std_temp = calculate_mean_profile(
                filtered_files, start_idx, end_idx)

            if depth_grid is not None:
                ax.plot(mean_temp, depth_grid, 'b-', linewidth=3, label='Mean')
                valid_mask = ~np.isnan(mean_temp) & ~np.isnan(std_temp)
                ax.plot(mean_temp[valid_mask] + std_temp[valid_mask],
                        depth_grid[valid_mask], 'b-', linewidth=1, alpha=0.5, label='+1 Std')
                ax.plot(mean_temp[valid_mask] - std_temp[valid_mask],
                        depth_grid[valid_mask], 'b-', linewidth=1, alpha=0.5, label='-1 Std')
                ax.legend(loc='lower right')
        else:
            for i in range(start_idx, end_idx):
                try:
                    ds = xr.open_dataset(filtered_files[i])
                    temperature = ds['temperature'].values
                    depth = ds['depth'].values

                    valid_mask = ~(np.isnan(temperature) | np.isnan(depth))
                    if np.any(valid_mask):
                        temp_clean = temperature[valid_mask]
                        depth_clean = depth[valid_mask]
                        ax.plot(temp_clean, depth_clean, '-', linewidth=1, alpha=0.7)

                        if show_tmld and not tmld_df.empty:
                            profile_idx = i + 1
                            tmld_row = tmld_df[tmld_df['profile_index'] == profile_idx]
                            if not tmld_row.empty and not np.isnan(
                                    tmld_row.iloc[0]['Estimated_TMLD']):
                                tmld_depth = tmld_row.iloc[0]['Estimated_TMLD']
                                tmld_temp = tmld_row.iloc[0]['temperature_at_TMLD']
                                if 7 <= tmld_temp <= 20:
                                    ax.plot(tmld_temp, tmld_depth, 'ro',
                                            markersize=4, alpha=0.8)
                except Exception:
                    continue

        if has_time_gap:
            ax.text(0.95, 0.05, 'Time Gap', transform=ax.transAxes,
                    fontsize=20, fontweight='bold', ha='right', va='bottom',
                    bbox=dict(boxstyle='round', facecolor='white',
                              edgecolor='black', linewidth=2))

        if end_idx > start_idx:
            first_parts = filtered_files[start_idx].stem.split('_')
            last_parts = filtered_files[end_idx - 1].stem.split('_')
            first_year, first_doy = int(first_parts[4]), int(first_parts[5])
            last_year, last_doy = int(last_parts[4]), int(last_parts[5])

            first_date = datetime(first_year, 1, 1) + timedelta(days=first_doy - 1)
            last_date = datetime(last_year, 1, 1) + timedelta(days=last_doy - 1)

            mode_str = " (Mean)" if show_mean else ""
            tmld_status = " (TMLD)" if show_tmld and not show_mean else ""
            title = (f'Bundle Animation{mode_str}{tmld_status}: '
                     f'{first_date.strftime("%d-%b-%Y")} to '
                     f'{last_date.strftime("%d-%b-%Y")}')
            ax.set_title(title, fontsize=14)

    # Create animation
    anim = animation.FuncAnimation(fig, animate_frame, frames=total_frames,
                                   interval=delay * 1000, repeat=True, blit=False)

    # Save animation
    output_file = Path("~/ooi/visualizations/bundle_animation.mp4").expanduser()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    print(f"Saving animation to {output_file}...")

    try:
        anim.save(str(output_file), writer='ffmpeg', fps=int(1 / delay), dpi=100)

        if output_file.exists():
            file_size = output_file.stat().st_size / (1024 * 1024)
            print(f"Animation saved: {output_file}")
            print(f"Size: {file_size:.1f} MB, Frames: {total_frames}")
        else:
            print("Error: Output file was not created")

    except Exception as e:
        print(f"Error saving animation: {e}")
        print("Note: ffmpeg must be installed for MP4 output")

    plt.close(fig)


# Run
create_animated_bundle_file()
