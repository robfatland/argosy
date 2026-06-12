"""
postprocess_pp06_filter3.py — Despike optical backscatter profiles in pp06
using the rolling-minimum baseline method of Briggs et al. (2011).

Filter 3: Backscatter despiking via rolling-minimum baseline extraction.

The ECO FLORT backscatter sensor measures the particulate backscattering
coefficient (bbp). In profile data, the signal has two components:

  1. A smooth baseline representing the background suspended particle field
     (the "left edge" in bundle charts — the minimum envelope).
  2. Positive spikes caused by individual large particles (marine snow,
     zooplankton, detritus) transiting the sensor's narrow optical beam.

For water-column characterization (e.g. SGA feature matrix), we want the
baseline only. The spikes represent stochastic particle encounters, not the
continuous field state.

Method (Briggs et al. 2011):
  - Compute a rolling minimum over a depth window. This tracks the spike-free
    baseline because the minimum in any window is unlikely to be contaminated
    by a transient particle spike.
  - The rolling minimum IS the despiked output.

    Reference:
    Briggs, N., Perry, M.J., Cetinić, I., Lee, C., D'Asaro, E., Gray, A.M.,
    and Rehm, E. (2011). "High-resolution observations of aggregate flux
    during a sub-polar North Atlantic spring bloom." Deep-Sea Research Part I,
    58(12), 1169–1186. doi:10.1016/j.dsr.2011.09.007

    Also implemented in: GliderTools Python package
    (glidertools.cleaning.despike, glidertools.processing.calc_backscatter)

Rationale for parameters:
    - window_size=11: Same vertical span (~3–4 m) used for Savitzky-Golay in
      Filter 2. Large enough to always contain spike-free samples (spikes are
      typically 1–3 points wide), small enough to track real vertical gradients
      in the baseline (which vary over 10–50 m scales).

Usage:
    source ~/miniconda3/etc/profile.d/conda.sh && conda activate argo-env2
    python postprocess_pp06_filter3.py [--dry-run]

Operates in-place on pp06 backscatter shard files.
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import xarray as xr
from scipy.ndimage import minimum_filter1d

# == Configuration =============================================================

PP06_BASE = Path("~/ooi/postproc/pp06").expanduser()

# Rolling minimum window size (number of samples)
WINDOW_SIZE = 11


# == Main ======================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Despike backscatter in pp06 via rolling-minimum baseline (Briggs 2011)")
    parser.add_argument('--dry-run', action='store_true',
                        help="Count files without modifying them")
    args = parser.parse_args()

    if not PP06_BASE.exists():
        print(f"ERROR: pp06 directory not found at {PP06_BASE}")
        print("Run postprocess_pp06.py first.")
        sys.exit(1)

    print(f"Filter 3: Backscatter despiking — rolling minimum baseline")
    print(f"  Method: Briggs et al. (2011)")
    print(f"  Window size: {WINDOW_SIZE} samples")
    print(f"  Source: {PP06_BASE}")
    print()

    if args.dry_run:
        print("=== DRY RUN — no files will be modified ===\n")

    total_processed = 0
    total_skipped_short = 0
    errors = 0

    start_time = time.time()

    year_dirs = sorted(PP06_BASE.glob("redux*"))
    for year_dir in year_dirs:
        year_count = 0
        files = sorted(year_dir.glob("*_backscatter_*.nc"))

        for f in files:
            if args.dry_run:
                total_processed += 1
                year_count += 1
                continue

            try:
                ds = xr.open_dataset(f)
                data = ds['backscatter'].values.copy()

                # Need enough valid points for the rolling window
                valid_mask = ~np.isnan(data)
                n_valid = np.sum(valid_mask)

                if n_valid < WINDOW_SIZE:
                    ds.close()
                    total_skipped_short += 1
                    continue

                # Apply rolling minimum to valid data only
                valid_indices = np.where(valid_mask)[0]
                valid_data = data[valid_mask]

                # Rolling minimum (baseline extraction)
                baseline = minimum_filter1d(valid_data, size=WINDOW_SIZE)

                # Replace valid data with baseline
                data[valid_indices] = baseline

                # Write back (temp file then replace to avoid open-file conflict)
                ds['backscatter'].values = data
                tmp_path = f.with_suffix('.nc.tmp')
                ds.to_netcdf(tmp_path)
                ds.close()
                tmp_path.replace(f)

                total_processed += 1
                year_count += 1

            except Exception as e:
                print(f"  ERROR: {f.name}: {e}")
                errors += 1

        print(f"  {year_dir.name}: {year_count} files processed")

    elapsed = time.time() - start_time

    print()
    print("=== Summary ===")
    print(f"  Files processed: {total_processed}")
    print(f"  Skipped (too few points): {total_skipped_short}")
    print(f"  Errors: {errors}")
    print(f"  Time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")

    if not args.dry_run:
        print(f"\n  Modified in place: {PP06_BASE}")
    else:
        print(f"\n  (Dry run complete — no files modified)")


if __name__ == '__main__':
    main()
