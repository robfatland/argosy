"""
postprocess_pp06.py — Build the pp06 physical dataset from pp05-qualified shards.

pp06 is a physical copy of redux shard files that pass the pp05 QC manifest,
restricted to the 8 HDS (High Data-density Sampling) scalar sensors.
Additionally, Filter 1 is applied to salinity and density shards to suppress
conductivity cell erratics.

Sensors included (8 HDS):
    temperature, salinity, density, dissolvedoxygen,
    cdom, chlora, backscatter, par

Filter 0: Baseline copy from pp05 manifest (non-salinity, non-density sensors)
Filter 1: MRA walk on salinity; removes erratic samples from salinity AND density.
           Discarded samples logged to pp06_filter1.csv.

Usage:
    source ~/miniconda3/etc/profile.d/conda.sh && conda activate argo-env2
    python postprocess_pp06.py [--dry-run]

Output:
    ~/ooi/postproc/pp06/redux{yyyy}/<shard_files>.nc
    ~/ooi/postproc/pp06/pp06_filter1.csv
"""

import argparse
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

# == Configuration =============================================================

MANIFEST_PATH = Path("~/ooi/metadata/pp05_manifest.csv").expanduser()
OUTPUT_BASE = Path("~/ooi/postproc/pp06").expanduser()

HDS_SENSORS = [
    'temperature', 'salinity', 'density', 'dissolvedoxygen',
    'cdom', 'chlora', 'backscatter', 'par',
    'nitrate', 'pco2', 'ph',
]

# Filter 1 parameters
SALINITY_PPC_LO = 28.0   # physically possible lower bound (PSU)
SALINITY_PPC_HI = 36.0   # physically possible upper bound (PSU)
SALINITY_SSC = 0.3        # sample-to-sample criterion (PSU)
# 0.3 PSU balances: catches the wild excursions (>1 PSU jumps) while
# permitting real halocline gradients (~0.1-0.2 PSU between adjacent samples).
MRA_INIT_CONSECUTIVE = 3  # require N consecutive valid samples to establish MRA


# == Filter 1: MRA walk ========================================================

def apply_filter1(sal_data, depth_data):
    """
    Apply MRA (Most Recent Acceptable) filter to salinity profile.
    
    Returns:
        filtered_mask: boolean array, True = keep, False = discard
        discard_records: list of (sample_idx, value, depth) for discarded samples
    """
    n = len(sal_data)
    keep = np.ones(n, dtype=bool)
    discard_records = []
    
    # Find starting MRA: first sequence of MRA_INIT_CONSECUTIVE valid samples
    mra = None
    mra_start_idx = None
    
    for i in range(n):
        v = sal_data[i]
        if np.isnan(v):
            continue
        if not (SALINITY_PPC_LO <= v <= SALINITY_PPC_HI):
            keep[i] = False
            discard_records.append((i, v, depth_data[i]))
            continue
        
        # Check if we can establish MRA with consecutive valid samples
        if mra is None:
            # Try to find N consecutive PPC-valid samples starting here
            consecutive = 0
            all_valid = True
            for j in range(i, min(i + MRA_INIT_CONSECUTIVE, n)):
                vj = sal_data[j]
                if np.isnan(vj) or not (SALINITY_PPC_LO <= vj <= SALINITY_PPC_HI):
                    all_valid = False
                    break
                if j > i:
                    if abs(vj - sal_data[j-1]) > SALINITY_SSC:
                        all_valid = False
                        break
                consecutive += 1
            
            if all_valid and consecutive >= MRA_INIT_CONSECUTIVE:
                mra = v
                mra_start_idx = i
                break
            else:
                keep[i] = False
                discard_records.append((i, v, depth_data[i]))
    
    if mra is None:
        # No valid starting point found — discard entire profile
        keep[:] = False
        for i in range(n):
            if not np.isnan(sal_data[i]):
                discard_records.append((i, sal_data[i], depth_data[i]))
        return keep, discard_records
    
    # Walk forward from mra_start_idx
    for i in range(mra_start_idx + 1, n):
        v = sal_data[i]
        if np.isnan(v):
            continue
        
        # PPC check
        if not (SALINITY_PPC_LO <= v <= SALINITY_PPC_HI):
            keep[i] = False
            discard_records.append((i, v, depth_data[i]))
            continue
        
        # SSC check
        if abs(v - mra) > SALINITY_SSC:
            keep[i] = False
            discard_records.append((i, v, depth_data[i]))
        else:
            mra = v  # accept: update MRA
    
    return keep, discard_records


# == Main ======================================================================

def main():
    parser = argparse.ArgumentParser(description="Build pp06 from pp05 manifest")
    parser.add_argument('--dry-run', action='store_true',
                        help="Report what would be done without copying/writing files")
    args = parser.parse_args()

    # Load manifest
    if not MANIFEST_PATH.exists():
        print(f"ERROR: pp05 manifest not found at {MANIFEST_PATH}")
        sys.exit(1)

    print(f"Loading pp05 manifest: {MANIFEST_PATH}")
    manifest = pd.read_csv(MANIFEST_PATH)

    # Filter to HDS sensors only
    hds_manifest = manifest[manifest['sensor'].isin(HDS_SENSORS)].copy()
    print(f"  Total manifest entries: {len(manifest)}")
    print(f"  HDS sensor entries: {len(hds_manifest)}")
    print(f"  Sensors: {sorted(hds_manifest['sensor'].unique())}")
    print()

    hds_manifest['year'] = hds_manifest['year'].astype(int)
    years = sorted(hds_manifest['year'].unique())
    print(f"  Years: {years[0]} to {years[-1]} ({len(years)} years)")
    print(f"  Filter 1 params: PPC=[{SALINITY_PPC_LO}, {SALINITY_PPC_HI}], "
          f"SSC={SALINITY_SSC} PSU, init_consecutive={MRA_INIT_CONSECUTIVE}")
    print()

    if args.dry_run:
        print("=== DRY RUN — no files will be written ===\n")

    # Create output directory
    if not args.dry_run:
        OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

    # Filter 1 log
    filter1_log = []

    # Stats
    total_files = len(hds_manifest)
    copied = 0
    filtered = 0
    skipped_missing = 0
    skipped_exists = 0
    errors = 0
    total_samples_discarded = 0

    start_time = time.time()

    for year in years:
        year_df = hds_manifest[hds_manifest['year'] == year]
        out_dir = OUTPUT_BASE / f"redux{year}"

        if not args.dry_run:
            out_dir.mkdir(parents=True, exist_ok=True)

        year_copied = 0
        year_filtered = 0
        year_skipped = 0

        for _, row in year_df.iterrows():
            src_path = Path(row['filepath'])
            dst_path = out_dir / src_path.name
            sensor = row['sensor']

            # Check source exists
            if not src_path.exists():
                skipped_missing += 1
                continue

            # Skip if already exists (idempotent)
            if dst_path.exists():
                skipped_exists += 1
                year_skipped += 1
                continue

            # Determine processing path
            if sensor in ('salinity', 'density'):
                # Filter 1: process salinity; density uses same mask
                if sensor == 'density':
                    # Density is filtered using the salinity mask from the same GI
                    # We handle density after salinity in the paired processing below
                    # For now, skip — it's handled via the salinity path
                    continue

                # Process salinity + paired density
                if args.dry_run:
                    filtered += 2  # salinity + density
                    year_filtered += 2
                    continue

                try:
                    # Open salinity shard
                    ds_sal = xr.open_dataset(src_path)
                    sal_data = ds_sal['salinity'].values.copy()
                    depth_data = ds_sal['depth'].values.copy()

                    # Apply filter
                    keep_mask, discards = apply_filter1(sal_data, depth_data)

                    # Log discards
                    gi = int(row['global_idx'])
                    for (sample_idx, value, depth_val) in discards:
                        filter1_log.append({
                            'sensor': 'salinity',
                            'global_idx': gi,
                            'sample_idx': sample_idx,
                            'value': value,
                            'depth': depth_val,
                        })
                        total_samples_discarded += 1

                    # Write filtered salinity
                    if np.any(keep_mask):
                        ds_sal_filtered = ds_sal.isel(obs=keep_mask) if 'obs' in ds_sal.dims else ds_sal.isel(time=keep_mask)
                        ds_sal_filtered.to_netcdf(dst_path)
                    else:
                        # All data discarded — don't write file
                        pass

                    ds_sal.close()
                    filtered += 1
                    year_filtered += 1

                    # Now handle paired density
                    density_src = src_path.parent / src_path.name.replace('_salinity_', '_density_')
                    density_dst = out_dir / density_src.name

                    if density_src.exists() and not density_dst.exists():
                        ds_den = xr.open_dataset(density_src)

                        # Log density discards (same indices)
                        den_data = ds_den['density'].values
                        for (sample_idx, _, depth_val) in discards:
                            if sample_idx < len(den_data):
                                filter1_log.append({
                                    'sensor': 'density',
                                    'global_idx': gi,
                                    'sample_idx': sample_idx,
                                    'value': den_data[sample_idx] if sample_idx < len(den_data) else np.nan,
                                    'depth': depth_val,
                                })
                                total_samples_discarded += 1

                        # Write filtered density
                        if np.any(keep_mask):
                            ds_den_filtered = ds_den.isel(obs=keep_mask) if 'obs' in ds_den.dims else ds_den.isel(time=keep_mask)
                            ds_den_filtered.to_netcdf(density_dst)

                        ds_den.close()
                        filtered += 1
                        year_filtered += 1

                except Exception as e:
                    print(f"  ERROR processing {src_path.name}: {e}")
                    errors += 1
            else:
                # Filter 0: straight copy for non-conductivity sensors
                if not args.dry_run:
                    try:
                        shutil.copy2(str(src_path), str(dst_path))
                        copied += 1
                        year_copied += 1
                    except Exception as e:
                        print(f"  ERROR copying {src_path.name}: {e}")
                        errors += 1
                else:
                    copied += 1
                    year_copied += 1

        print(f"  redux{year}: {year_copied} copied, {year_filtered} filtered, "
              f"{year_skipped} existed (of {len(year_df)} entries)")

    elapsed = time.time() - start_time

    # Write filter1 log
    if filter1_log and not args.dry_run:
        filter1_df = pd.DataFrame(filter1_log)
        filter1_path = OUTPUT_BASE / 'pp06_filter1.csv'
        filter1_df.to_csv(filter1_path, index=False)
        print(f"\n  Filter 1 log: {filter1_path} ({len(filter1_df)} entries)")

    print()
    print("=== Summary ===")
    print(f"  Total entries processed: {total_files}")
    print(f"  Files copied (Filter 0): {copied}")
    print(f"  Files filtered (Filter 1): {filtered}")
    print(f"  Skipped (already exists): {skipped_exists}")
    print(f"  Skipped (source missing): {skipped_missing}")
    print(f"  Total samples discarded: {total_samples_discarded}")
    print(f"  Errors: {errors}")
    print(f"  Time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")

    if skipped_missing > 0:
        print(f"\n  WARNING: {skipped_missing} source files were missing from redux.")

    if not args.dry_run:
        print(f"\n  Output: {OUTPUT_BASE}")
    else:
        print(f"\n  (Dry run complete — no files were written)")


if __name__ == '__main__':
    main()
