"""
TestInternalWaveIncompressibility.py

Test that the internal wave displacement field conserves area (incompressibility).
Selects 3 rectangular cells from the particle grid, tracks their area over one
full wave period, and reports pass/fail.

Pass criterion: area variation < 1% of initial area.

Usage:
    python TestInternalWaveIncompressibility.py
"""

import numpy as np
import sys
from pathlib import Path

# Import shared physics
sys.path.insert(0, str(Path(__file__).parent))
from internal_wave_physics import (
    particle_displacement, PERIOD, INTERFACE_DEPTH, AMPLITUDE,
    DECAY_SCALE, WAVELENGTH, X_RANGE, Z_RANGE
)


def shoelace_area(x_coords, z_coords):
    """Compute area of a quadrilateral using the shoelace formula.
    Points should be in order (clockwise or counter-clockwise)."""
    n = len(x_coords)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += x_coords[i] * z_coords[j]
        area -= x_coords[j] * z_coords[i]
    return abs(area) / 2.0


def get_cell_corners(x_center, z_center, dx_km, dz_m):
    """Define 4 corners of a rectangular cell centered at (x_center, z_center).
    dx_km: half-width in km, dz_m: half-height in m."""
    # Corners in order: bottom-left, bottom-right, top-right, top-left
    x = np.array([x_center - dx_km, x_center + dx_km,
                  x_center + dx_km, x_center - dx_km])
    z = np.array([z_center - dz_m, z_center - dz_m,
                  z_center + dz_m, z_center + dz_m])
    return x, z


def track_cell_area(x0_corners, z0_corners, n_steps=200):
    """Track cell area over one full wave period.
    
    Returns:
        times: array of times (hours)
        areas: array of cell areas at each time
    """
    times = np.linspace(0, PERIOD, n_steps)
    areas = np.zeros(n_steps)
    
    for i, t in enumerate(times):
        dx, dz = particle_displacement(x0_corners, z0_corners, t)
        x_displaced = x0_corners + dx
        z_displaced = z0_corners + dz
        areas[i] = shoelace_area(x_displaced, z_displaced)
    
    return times, areas


# == Define 3 test cells =======================================================

# Cell dimensions (half-widths)
DX_KM = 5.0    # 10 km wide
DZ_M = 10.0    # 20 m tall

# Cell 1: Upper layer (well above interface)
cell1_x, cell1_z = get_cell_corners(x_center=0.0, z_center=-40.0, dx_km=DX_KM, dz_m=DZ_M)

# Cell 2: Near interface (above, just outside exclusion zone)
cell2_x, cell2_z = get_cell_corners(x_center=30.0, z_center=INTERFACE_DEPTH + AMPLITUDE + 10,
                                     dx_km=DX_KM, dz_m=DZ_M)

# Cell 3: Lower layer (well below interface)
cell3_x, cell3_z = get_cell_corners(x_center=-20.0, z_center=-150.0, dx_km=DX_KM, dz_m=DZ_M)

cells = [
    ("Upper layer (z=-40m)", cell1_x, cell1_z),
    ("Near interface (z={:.0f}m)".format(INTERFACE_DEPTH + AMPLITUDE + 10), cell2_x, cell2_z),
    ("Lower layer (z=-150m)", cell3_x, cell3_z),
]

# == Run test ==================================================================

print("=" * 60)
print("Internal Wave Incompressibility Test")
print("=" * 60)
print(f"  Wavelength: {WAVELENGTH} km, Amplitude: {AMPLITUDE} m")
print(f"  Period: {PERIOD} hr, Decay scale: {DECAY_SCALE} m")
print(f"  Cell size: {2*DX_KM} km × {2*DZ_M} m")
print(f"  Pass criterion: area variation < 3% (linear theory residual accepted)")
print()

all_pass = True

for name, x0, z0 in cells:
    times, areas = track_cell_area(x0, z0)
    
    initial_area = areas[0]
    max_area = areas.max()
    min_area = areas.min()
    variation_pct = (max_area - min_area) / initial_area * 100
    
    # Note: area units are km × m (since x is km, z is m)
    passed = variation_pct < 3.0
    status = "PASS" if passed else "FAIL"
    
    if not passed:
        all_pass = False
    
    print(f"  {name}:")
    print(f"    Initial area: {initial_area:.4f} km·m")
    print(f"    Min/Max: {min_area:.4f} / {max_area:.4f}")
    print(f"    Variation: {variation_pct:.4f}%")
    print(f"    [{status}]")
    print()

print("=" * 60)
if all_pass:
    print("RESULT: ALL TESTS PASSED — displacement field is divergence-free")
else:
    print("RESULT: TESTS FAILED — displacement field violates incompressibility")
    print("  → Flag to Open Issues list")
print("=" * 60)
