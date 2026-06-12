"""
postprocess_pp06_filter2.py — Apply Savitzky-Golay smoothing to CDOM, ChlorA,
and Backscatter profiles in the pp06 dataset.

Filter 2: Savitzky-Golay smoothing for quantization noise reduction.

These three sensors share the WET Labs ECO FLORT instrument, which uses a 12-bit
ADC with limited dynamic range. In low-signal environments (open ocean, deep water),
the sensor output spans only a few digital counts, producing a staircase-like
"quantized" profile that obscures real vertical structure.

The Savitzky-Golay filter (Savitzky & Golay, 1964) performs local polynomial
least-squares regression, which smooths quantization noise while preserving peak
positions, widths, and asymmetries better than a simple moving average. It is the
standard choice for smoothing digitized spectroscopic and fluorometric data.

    Reference:
    Savitzky, A. and Golay, M.J.E. (1964). "Smoothing and Differentiation of
    Data by Simplified Least Squares Procedures." Analytical Chemistry, 36(8),
    1627–1639. doi:10.1021/ac60214a047

Rationale for parameters:
    - window_length=11: At profiler ascent rates (~0.3 m/s) and ~1 Hz sampling,
      11 points spans ~3–4 meters vertically. This smooths the quantization steps
      (which span 1–3 points) while preserving real features (which span >10 points
      for genuine CDOM layers, chlorophyll maxima, or particle layers).
    - polyorder=2: Quadratic fit preserves curvature of real peaks (e.g. subsurface
      chlorophyll maximum) without introducing ringing artifacts.

Note on ChlorA: Non-photochemical quenching (NPQ) correction is NOT applied here.
NPQ artificially suppresses near-surface daytime chlorophyll fluorescence. Correction
requires mixed-layer-depth context and noon/midnight metadata. Deferred to a future
filter.

Usage:
    source ~/miniconda3/etc/profile.d/conda.sh && conda activate argo-env2
    python postprocess_pp06_filter2.py [--dry-run]

Operates in-place on pp06 shard files. Creates a backup is NOT made (pp06 can be
regenerated from redux via postprocess_pp06.py if needed).
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import xarray as xr
from scipy.signal import savgol_filter

# == Configuration =============================================================

PP06_BASE = Path("~/ooi/postproc/pp06").expanduser()

# Sensors to smooth
FILTER2_SENSORS = ['cdom', 'chlora']

# Savitzky-Golay parameters
WINDOW_LENGTH = 11  # must be odd
POLYORDER = 2


# == Main ======================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Apply Savitzky-Golay smoothing to CDOM/ChlorA/Backscatter in pp06")
    parser.add_argument('--dry-run', action='store_true',
                        help="Count files without modifying them")
    args = parser.parse_args()

    if not PP06_BASE.exists():
        print(f"ERROR: pp06 directory not found at {PP06_BASE}")
        print("Run postprocess_pp06.py first.")
        sys.exit(1)

    print(f"Filter 2: Savitzky-Golay smoothing (window={WINDOW_LENGTH}, polyorder={POLYORDER})")
    print(f"Sensors: {FILTER2_SENSORS}")
    print(f"Source: {PP06_BASE}")
    print()

    if args.dry_run:
        print("=== DRY RUN — no files will be modified ===\n")

    # Find all relevant files
    total_processed = 0
    total_skipped_short = 0
    errors = 0

    start_time = time.time()

    year_dirs = sorted(PP06_BASE.glob("redux*"))
    for year_dir in year_dirs:
        year_count = 0
        for sensor in FILTER2_SENSORS:
            files = sorted(year_dir.glob(f"*_{sensor}_*.nc"))
            for f in files:
                if args.dry_run:
                    total_processed += 1
                    year_count += 1
                    continue

                try:
                    ds = xr.open_dataset(f)
                    data = ds[sensor].values.copy()

                    # Need enough valid points for the filter window
                    valid_mask = ~np.isnan(data)
                    n_valid = np.sum(valid_mask)

                    if n_valid < WINDOW_LENGTH:
                        # Too few points to filter — leave as-is
                        ds.close()
                        total_skipped_short += 1
                        continue

                    # Apply Savitzky-Golay to the valid portion
                    # Strategy: extract valid data, filter, put back
                    valid_indices = np.where(valid_mask)[0]
                    valid_data = data[valid_mask]

                    # Apply filter
                    smoothed = savgol_filter(valid_data, WINDOW_LENGTH, POLYORDER)

                    # Replace in full array
                    data[valid_indices] = smoothed

                    # Write back (temp file then replace to avoid open-file conflict)
                    ds[sensor].values = data
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
