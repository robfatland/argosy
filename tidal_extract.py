"""
tidal_extract.py

Extract tidal harmonic constituents from TPXO10-atlas-v2 at the three OOI/RCA
shallow profiler sites, save to JSON, and provide a self-contained prediction
function. After running this script successfully, the 30 GB TPXO data can be deleted.

Sites:
  Oregon Offshore    44.37N  124.96W
  Oregon Slope Base  44.53N  125.39W
  Axial Base         45.83N  129.75W

TPXO10 data location: ~/D/TPXO10_atlas_v2_nc/TPXO10_atlas_v2_nc/
"""

import numpy as np
import xarray as xr
import json
from pathlib import Path
from datetime import datetime, timezone

# --- Configuration ---

TPXO_DIR = Path.home() / "D" / "TPXO10_atlas_v2_nc" / "TPXO10_atlas_v2_nc"
OUTPUT_JSON = Path(__file__).parent / "tidal_constituents.json"

# Constituent names (matching TPXO10 file naming)
CONSTITUENTS = [
    "m2", "s2", "n2", "k2", "k1", "o1", "p1", "q1",
    "2n2", "m4", "ms4", "mn4", "mm", "mf"
]

# Constituent angular speeds (degrees/hour) — standard astronomical values
OMEGA = {
    "m2":   28.984104,
    "s2":   30.000000,
    "n2":   28.439730,
    "k2":   30.082137,
    "k1":   15.041069,
    "o1":   13.943036,
    "p1":   14.958931,
    "q1":   13.398661,
    "2n2":  27.895355,
    "m4":   57.968208,
    "ms4":  58.984104,
    "mn4":  57.423834,
    "mm":    0.544375,
    "mf":    1.098033,
}

# Site coordinates
SITES = {
    "Oregon Offshore":    {"lat": 44.37, "lon": -124.96},
    "Oregon Slope Base":  {"lat": 44.53, "lon": -125.39},
    "Axial Base":         {"lat": 45.83, "lon": -129.75},
}


def find_nearest_indices(lon_z, lat_z, target_lon, target_lat):
    """Find nearest grid indices for a target point.
    
    TPXO uses 0-360 longitude convention.
    lon_z shape: (nx,) or (nx, ny) — first axis is longitude
    lat_z shape: (ny,) or (nx, ny) — second axis is latitude
    """
    # Convert target longitude to 0-360
    tlon = target_lon % 360
    
    # Handle 1D vs 2D coordinate arrays
    if lon_z.ndim == 1:
        ix = int(np.argmin(np.abs(lon_z - tlon)))
        iy = int(np.argmin(np.abs(lat_z - target_lat)))
    else:
        # 2D: lon_z is (nx, ny), lat_z is (nx, ny)
        ix = int(np.argmin(np.abs(lon_z[:, 0] - tlon)))
        iy = int(np.argmin(np.abs(lat_z[0, :] - target_lat)))
    
    return ix, iy


def extract_constituents():
    """Extract amplitude and phase for all constituents at all sites."""
    results = {}
    
    for site_name, coords in SITES.items():
        results[site_name] = {
            "lat": coords["lat"],
            "lon": coords["lon"],
            "constituents": {}
        }
    
    for const in CONSTITUENTS:
        fname = TPXO_DIR / f"h_{const}_tpxo10_atlas_30_v2.nc"
        if not fname.exists():
            print(f"  WARNING: {fname.name} not found, skipping {const}")
            continue
        
        print(f"  Reading {const}...")
        ds = xr.open_dataset(fname)
        
        # Get coordinate arrays
        lon_z = ds["lon_z"].values  # shape (nx,) or (nx, ny)
        lat_z = ds["lat_z"].values  # shape (ny,) or (nx, ny)
        hRe = ds["hRe"].values      # shape (nx, ny), millimeters
        hIm = ds["hIm"].values      # shape (nx, ny), millimeters
        
        for site_name, coords in SITES.items():
            ix, iy = find_nearest_indices(lon_z, lat_z, coords["lon"], coords["lat"])
            
            # Extract real and imaginary parts (mm)
            re_mm = float(hRe[ix, iy])
            im_mm = float(hIm[ix, iy])
            
            # Convert to amplitude (meters) and phase (degrees)
            amplitude_m = np.sqrt(re_mm**2 + im_mm**2) / 1000.0
            phase_deg = np.degrees(np.arctan2(-im_mm, re_mm)) % 360
            
            results[site_name]["constituents"][const] = {
                "amplitude_m": round(amplitude_m, 6),
                "phase_deg": round(phase_deg, 4),
                "omega_deg_per_hr": OMEGA[const],
            }
        
        ds.close()
    
    return results


def save_results(results):
    """Save extracted constituents to JSON."""
    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved to {OUTPUT_JSON}")


def predict_tide(constituents_dict, times):
    """
    Predict tidal height from extracted constituents.
    
    Parameters
    ----------
    constituents_dict : dict
        The "constituents" sub-dict for one site from the JSON file.
    times : array-like of datetime objects (UTC)
        Times at which to predict.
    
    Returns
    -------
    heights : np.ndarray
        Predicted tidal height in meters relative to mean sea level.
    """
    # Reference epoch: 2000-01-01 00:00 UTC (standard for TPXO)
    t0 = datetime(2000, 1, 1, tzinfo=timezone.utc)
    
    # Convert times to hours since epoch
    hours = np.array([(t - t0).total_seconds() / 3600.0 for t in times])
    
    heights = np.zeros(len(hours))
    
    for const_name, params in constituents_dict.items():
        amp = params["amplitude_m"]
        phase = np.radians(params["phase_deg"])
        omega = np.radians(params["omega_deg_per_hr"])  # rad/hr
        
        heights += amp * np.cos(omega * hours - phase)
    
    return heights


# --- Main ---

if __name__ == "__main__":
    print("Extracting tidal constituents from TPXO10...")
    results = extract_constituents()
    save_results(results)
    
    # Quick sanity check: predict 24 hours at Oregon Offshore
    from datetime import timedelta
    t_start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    times = [t_start + timedelta(hours=h) for h in range(25)]
    h = predict_tide(results["Oregon Offshore"]["constituents"], times)
    print(f"\nSanity check — Oregon Offshore, May 1 2026:")
    print(f"  Range: {h.min():.3f} to {h.max():.3f} m")
    print(f"  Expected ~1-2 m total range for mixed semidiurnal regime")
