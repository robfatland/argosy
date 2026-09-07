# curtain_batch.py — Generate yearly single-sensor curtain plots in batch mode.
#
# Usage:
#   python ~/argosy/vis/curtain_batch.py -sensor=temperature
#   python ~/argosy/vis/curtain_batch.py -sensor=all
#
# Produces one PNG per year (2015–2025) for the specified sensor.
# Output: ~/ooi/visualizations/OneCurtainPlot_SlopeBase_<start>_<end>_<sensor>.png
#
# Data source: pp06 (hardcoded; noted to stdout)

import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

# Import shared rendering logic
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path("~/argosy").expanduser()))
import ooipaths as op
from curtain_core import (
    SENSOR_CONFIGS, SENSOR_ALIASES, VALID_SENSOR_NAMES,
    load_profiles, render_curtain,
)

# == Configuration =============================================================

SITE = op.DEFAULT_SITE
DATA_BASE = op.postproc_base(SITE) / "pp06"
OUTPUT_DIR = op.visualizations_dir(SITE)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOCATION = "SlopeBase"
YEARS = list(range(2015, 2026))  # 2015 through 2025


# == Parse command line ========================================================

sensor_arg = None
for arg in sys.argv[1:]:
    if arg.startswith('-sensor='):
        sensor_arg = arg.split('=', 1)[1].strip().lower()

if sensor_arg is None:
    print("Usage: python curtain_batch.py -sensor=<name>")
    print()
    print("Valid sensor names:")
    for name in VALID_SENSOR_NAMES:
        print(f"  {name}")
    print(f"  all  (processes all {len(VALID_SENSOR_NAMES)} sensors)")
    print()
    print("Aliases: oxygen -> dissolvedoxygen")
    sys.exit(1)

# Resolve aliases
if sensor_arg in SENSOR_ALIASES:
    sensor_arg = SENSOR_ALIASES[sensor_arg]

# Build sensor list
if sensor_arg == 'all':
    sensors_to_process = VALID_SENSOR_NAMES
else:
    if sensor_arg not in SENSOR_CONFIGS:
        print(f"ERROR: Unknown sensor '{sensor_arg}'")
        print(f"Valid options: {', '.join(VALID_SENSOR_NAMES)}, all")
        sys.exit(1)
    sensors_to_process = [sensor_arg]


# == Main loop =================================================================

print(f"Data source: pp06 ({DATA_BASE})")
print(f"Sensors: {', '.join(sensors_to_process)}")
print(f"Years: {YEARS[0]}–{YEARS[-1]}")
print()

total_plots = len(sensors_to_process) * len(YEARS)
plot_count = 0

for sensor_name in sensors_to_process:
    sensor_config = SENSOR_CONFIGS[sensor_name]

    for year in YEARS:
        plot_count += 1
        time_start = datetime(year, 1, 1)
        time_end = datetime(year, 12, 31)

        print(f"[{plot_count}/{total_plots}] {sensor_name} {year}...", end=' ', flush=True)

        # Load profiles
        profile_columns = load_profiles(sensor_config, DATA_BASE, time_start, time_end)

        if not profile_columns:
            print("no data, skipped.")
            continue

        # Render
        fig, ax = plt.subplots(1, 1, figsize=(20, 6))
        render_curtain(ax, fig, sensor_config, profile_columns, time_start, time_end)
        plt.tight_layout()

        # Save
        s_tag = time_start.strftime("%Y%m%d")
        e_tag = time_end.strftime("%Y%m%d")
        filename = f"OneCurtainPlot_{LOCATION}_{s_tag}_{e_tag}_{sensor_name}.png"
        output_path = OUTPUT_DIR / filename
        fig.savefig(output_path, dpi=150, facecolor="white")
        plt.close(fig)

        print(f"{len(profile_columns)} profiles -> {filename}")

print(f"\nDone. {plot_count} plots generated in {OUTPUT_DIR}")
