"""
internal_wave_physics.py — Shared physics for internal wave visualization and tests.

Uses a stream function formulation to guarantee divergence-free (incompressible)
velocity and displacement fields.

Stream function: ψ(x, z, t) = A(z) * cos(kx - ωt)
  where A(z) decays exponentially from the interface.

Displacement (from integrating velocity):
  dx = ∂ψ/∂z * (1/ω) * sin(kx - ωt)  ... wait, let's be more careful.

For a linear internal wave, the displacement field (ξ, η) satisfies:
  ∂ξ/∂x + ∂η/∂z = 0  (incompressibility)

Using: η(x,z,t) = B(z) * sin(kx - ωt)  [vertical displacement]
Then:  ξ(x,z,t) = -(1/k) * dB/dz * cos(kx - ωt)  [horizontal displacement]

This automatically satisfies ∂ξ/∂x + ∂η/∂z = 0:
  ∂ξ/∂x = (dB/dz) * sin(kx - ωt)
  ∂η/∂z = (dB/dz) * sin(kx - ωt)
Wait — that gives 2*(dB/dz)*sin ≠ 0. Let me redo this.

∂ξ/∂x + ∂η/∂z = 0 means:
  ∂ξ/∂x = -(∂η/∂z)
  
η = B(z) * sin(kx - ωt)
∂η/∂z = B'(z) * sin(kx - ωt)

So ∂ξ/∂x = -B'(z) * sin(kx - ωt)
Integrating in x: ξ = (B'(z)/k) * cos(kx - ωt)

Check: ∂ξ/∂x = -B'(z)/k * k * sin(kx - ωt) = -B'(z)*sin(kx - ωt)  ✓
And:   ∂η/∂z = B'(z)*sin(kx - ωt)
Sum = 0. ✓

With B(z) = AMPLITUDE * exp(-|z - z_iface| / DECAY_SCALE):
  Above interface (z > z_iface): B'(z) = -AMPLITUDE/DECAY_SCALE * exp(-(z-z_iface)/DECAY_SCALE)
  Below interface (z < z_iface): B'(z) = +AMPLITUDE/DECAY_SCALE * exp(-(z_iface-z)/DECAY_SCALE)

So: ξ = (B'(z)/k) * cos(kx - ωt)
     = (±1) * (AMPLITUDE / (k * DECAY_SCALE)) * exp(-dist/DECAY_SCALE) * cos(kx - ωt)
     
Sign: above interface B' < 0, so ξ has negative cos; below B' > 0, so ξ has positive cos.
"""

import numpy as np

# == Wave parameters ===========================================================

# Config1 (mildly nonlinear — visible steepening asymmetry):
#   WAVELENGTH = 100.0 km, AMPLITUDE = 20.0 m, DECAY_SCALE = 40.0 m
#   AMPLITUDE/DECAY_SCALE = 0.5, horizontal displacement ~8 km at interface

# Config2 (symmetric/linear limit — reduce amplitude relative to decay scale):
WAVELENGTH = 100.0       # km
AMPLITUDE = 5.0          # m (reduced from 20 for linear regime)
PERIOD = 12.42           # hours (M2 tidal)
PHASE_SPEED = WAVELENGTH / PERIOD  # km/hr westward

# Domain
X_RANGE = (-150, 150)    # km
Z_RANGE = (-100, 10)     # m
INTERFACE_DEPTH = -50.0  # m (mean pycnocline)

# Decay scale
DECAY_SCALE = 40.0       # m (e-folding from interface)
# AMPLITUDE/DECAY_SCALE = 0.125 — well within linear regime

# Derived
omega = 2 * np.pi / PERIOD          # rad/hr
k = 2 * np.pi / WAVELENGTH          # rad/km

# Horizontal amplitude scale at interface:
# |ξ_max| = AMPLITUDE / (k_m * DECAY_SCALE) where k_m is in rad/m
# But k is in rad/km, so: AMPLITUDE / (k * 1000 * DECAY_SCALE) in km
# Or equivalently: AMPLITUDE * WAVELENGTH / (2*pi*DECAY_SCALE*1000) in km
# Let's keep it in mixed units: horiz is km, vert is m.
# The factor converting B'(z) [m/m] to ξ [km]:  1/(k [rad/km]) * (1/1000 [km/m])
# Actually k is in rad/km, B' is in m/m = dimensionless-ish (amplitude_m / decay_m)
# ξ = B'(z)/k has units: (m / m) / (rad/km) = km/rad ≈ km
# Hmm, let's just be explicit with units:

# B(z) in meters, z in meters
# B'(z) = dB/dz in m/m (dimensionless)
# k in rad/km → k_m = k / 1000 in rad/m
# ξ = B'(z) / k_m in meters
# To get ξ in km: ξ_km = B'(z) / k_m / 1000 = B'(z) / (k / 1000) / 1000 = B'(z) / k
# Wait: k is rad/km = 0.0628 rad/km
# B'(z) at interface = AMPLITUDE / DECAY_SCALE = 20/40 = 0.5 (m/m, but really 1/m... )
# 
# Let me use consistent units. Everything in meters and hours:

k_m = k / 1000.0  # convert rad/km to rad/m


# == Displacement functions ====================================================

def particle_displacement(x0, z0, t):
    """
    Compute particle displacement at time t.
    Guaranteed divergence-free by construction from stream function.
    
    Args:
        x0: initial x positions (km)
        z0: initial z positions (m)
        t: time (hours)
    
    Returns:
        dx: horizontal displacement (km)
        dz: vertical displacement (m)
    """
    x0 = np.asarray(x0, dtype=float)
    z0 = np.asarray(z0, dtype=float)
    
    dist = np.abs(z0 - INTERFACE_DEPTH)
    
    # Vertical displacement: η = B(z) * sin(kx - ωt)
    B = AMPLITUDE * np.exp(-dist / DECAY_SCALE)
    phase = k * x0 - omega * t
    dz = B * np.sin(phase)  # meters
    
    # Horizontal displacement: ξ = B'(z)/k_m * cos(kx - ωt)
    # B'(z) = -B/DECAY_SCALE for z > interface, +B/DECAY_SCALE for z < interface
    # Sign of B': negative above, positive below
    Bprime = np.where(z0 >= INTERFACE_DEPTH,
                      -B / DECAY_SCALE,
                      +B / DECAY_SCALE)
    
    dx_m = (Bprime / k_m) * np.cos(phase)  # meters
    dx = dx_m / 1000.0  # convert to km
    
    return dx, dz


def interface_curve(x_array, t):
    """
    Compute interface vertical position at time t.
    
    Args:
        x_array: x positions (km)
        t: time (hours)
    
    Returns:
        z positions of interface (m)
    """
    x_array = np.asarray(x_array, dtype=float)
    return INTERFACE_DEPTH + AMPLITUDE * np.sin(k * x_array - omega * t)
