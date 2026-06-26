"""
internal_wave.py — Animate an internal wave propagating westward.

Shows:
- Particles in two layers (warm above, cold below) tracing elliptical orbits
- Particles at the interface moving with the boundary
- A moving pycnocline boundary curve
- Time axis at top with advancing marker
- Seamless loop (one full period, last frame = first frame shifted)

Usage:
    source ~/miniconda3/etc/profile.d/conda.sh && conda activate argosy
    python internal_wave.py

Output:
    ~/ooi/visualizations/internal_wave.mp4
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.cm import ScalarMappable
from matplotlib.colors import hsv_to_rgb
from pathlib import Path
import sys

# Import shared physics
sys.path.insert(0, str(Path(__file__).parent))
from internal_wave_physics import (
    particle_displacement, interface_curve,
    WAVELENGTH, AMPLITUDE, PERIOD, PHASE_SPEED,
    X_RANGE, Z_RANGE, INTERFACE_DEPTH, DECAY_SCALE, omega, k
)

# == Animation-specific parameters =============================================

# Particle grid
N_PARTICLES_X = 30
N_PARTICLES_Z_UPPER = 8
N_PARTICLES_Z_LOWER = 10
N_INTERFACE_PARTICLES = 100

# Animation: two full periods for seamless loop (~24.84 hours)
N_FRAMES = 400
DT = (2 * PERIOD) / N_FRAMES
FPS = 30

# == Particle initial positions ================================================

x_vals = np.linspace(X_RANGE[0] * 0.85, X_RANGE[1] * 0.85, N_PARTICLES_X)

# Upper layer: starts AMPLITUDE + 5m above interface, up to near surface
z_upper = np.linspace(INTERFACE_DEPTH + AMPLITUDE + 5, 0, N_PARTICLES_Z_UPPER)
X_up, Z_up = np.meshgrid(x_vals, z_upper)
X_up, Z_up = X_up.flatten(), Z_up.flatten()

# Lower layer: starts AMPLITUDE + 5m below interface, down to near bottom
z_lower = np.linspace(Z_RANGE[0] + 5, INTERFACE_DEPTH - AMPLITUDE - 5, N_PARTICLES_Z_LOWER)
X_lo, Z_lo = np.meshgrid(x_vals, z_lower)
X_lo, Z_lo = X_lo.flatten(), Z_lo.flatten()

# Interface particles: start exactly at interface
x_interface_particles = np.linspace(X_RANGE[0] * 0.9, X_RANGE[1] * 0.9, N_INTERFACE_PARTICLES)
Z_iface = np.full(N_INTERFACE_PARTICLES, INTERFACE_DEPTH)

# Near-interface particles: +6m (orange) and -6m (cyan)
x_near_particles = np.linspace(X_RANGE[0] * 0.9, X_RANGE[1] * 0.9, N_INTERFACE_PARTICLES)
Z_above = np.full(N_INTERFACE_PARTICLES, INTERFACE_DEPTH + 6.0)
Z_below = np.full(N_INTERFACE_PARTICLES, INTERFACE_DEPTH - 6.0)


# == Figure setup ==============================================================

fig = plt.figure(figsize=(14, 6))

# Main axes for the wave
ax = fig.add_axes([0.06, 0.12, 0.88, 0.72])
ax.set_xlim(*X_RANGE)
ax.set_ylim(*Z_RANGE)
ax.set_xlabel('Distance (km)')
ax.set_ylabel('Depth (m)')
ax.set_title('Internal Wave (M2 tidal period, propagating eastward →)', pad=35)
ax.axhline(0, color='lightblue', linewidth=2)
ax.grid(True, alpha=0.15)

# Time axis at top
ax_time = fig.add_axes([0.06, 0.85, 0.88, 0.04])
ax_time.set_xlim(0, 2 * PERIOD)
ax_time.set_ylim(-0.5, 0.5)
ax_time.xaxis.tick_bottom()
ax_time.set_xlabel('')
ax_time.set_yticks([])
ax_time.set_facecolor('#f8f8f8')
time_marker, = ax_time.plot([], [], 'rv', markersize=10, clip_on=False)

# Interface line
x_iface_plot = np.linspace(*X_RANGE, 500)
interface_line, = ax.plot([], [], 'k-', linewidth=2.5)

# Upper particles: random colors broadly warm (reds, oranges, yellows, magentas)
rng = np.random.default_rng(42)
hues_upper = rng.uniform(0.85, 1.15, len(X_up)) % 1.0  # wraps around red (0.85-0.15 via mod)
sats_upper = rng.uniform(0.4, 1.0, len(X_up))
vals_upper = rng.uniform(0.5, 1.0, len(X_up))
from matplotlib.colors import hsv_to_rgb
colors_upper = np.array([hsv_to_rgb([h, s, v]) for h, s, v in zip(hues_upper, sats_upper, vals_upper)])
pos_up_init = np.column_stack([X_up, Z_up])
scat_upper = ax.scatter(pos_up_init[:, 0], pos_up_init[:, 1], s=12, c=colors_upper,
                        alpha=0.7, edgecolors='none')

# Lower particles: random colors broadly cool (blues, teals, purples)
hues_lower = rng.uniform(0.45, 0.80, len(X_lo))  # wide blue-purple range
sats_lower = rng.uniform(0.3, 1.0, len(X_lo))
vals_lower = rng.uniform(0.4, 1.0, len(X_lo))
colors_lower = np.array([hsv_to_rgb([h, s, v]) for h, s, v in zip(hues_lower, sats_lower, vals_lower)])
pos_lo_init = np.column_stack([X_lo, Z_lo])
scat_lower = ax.scatter(pos_lo_init[:, 0], pos_lo_init[:, 1], s=12, c=colors_lower,
                        alpha=0.7, edgecolors='none')

# Interface particles (dark green, slightly larger)
scat_iface = ax.scatter(x_interface_particles, Z_iface, s=20, c='darkgreen',
                        alpha=0.9, edgecolors='none', label='Interface particles', zorder=5)

# Near-interface: +4m orange, -4m cyan
scat_above_near = ax.scatter(x_near_particles, Z_above, s=14, c='orange',
                             alpha=0.8, edgecolors='none', label='+4m above interface', zorder=4)
scat_below_near = ax.scatter(x_near_particles, Z_below, s=14, c='cyan',
                             alpha=0.8, edgecolors='none', label='-4m below interface', zorder=4)

# Tracker particles: 1/3 from left edge (index ~67 of 200)
TRACKER_IDX = 67
tracker_above, = ax.plot([], [], 'o', color='red', markersize=8, zorder=10)
tracker_below, = ax.plot([], [], 'o', color='magenta', markersize=8, zorder=10)
tracker_iface, = ax.plot([], [], 'o', color='lime', markersize=8, zorder=10)

ax.legend(loc='lower right', fontsize=8)

# Orbit ellipses for a few representative particles
orbit_lines = []
# Pick a few from upper, lower, and interface
demo_indices_upper = np.linspace(0, len(X_up)-1, 4, dtype=int)
demo_indices_lower = np.linspace(0, len(X_lo)-1, 4, dtype=int)
demo_indices_iface = np.linspace(0, N_INTERFACE_PARTICLES-1, 3, dtype=int)

for _ in range(4 + 4 + 3):
    line, = ax.plot([], [], '-', color='gray', linewidth=0.3, alpha=0.4)
    orbit_lines.append(line)


def draw_orbit(x0, z0, line_obj):
    """Draw full orbit ellipse for one particle."""
    t_orbit = np.linspace(0, PERIOD, 80)
    dx, dz = particle_displacement(np.full(80, x0), np.full(80, z0), t_orbit)
    line_obj.set_data(x0 + dx, z0 + dz)


def init():
    interface_line.set_data([], [])
    time_marker.set_data([], [])
    tracker_above.set_data([], [])
    tracker_below.set_data([], [])
    tracker_iface.set_data([], [])
    for line in orbit_lines:
        line.set_data([], [])
    return [interface_line, scat_upper, scat_lower, scat_iface,
            scat_above_near, scat_below_near,
            tracker_above, tracker_below, tracker_iface,
            time_marker] + orbit_lines


def animate(frame):
    t = frame * DT

    # Interface line: draw through the interface particle positions
    # (the particles ARE the material surface)
    dx_if, dz_if = particle_displacement(x_interface_particles, Z_iface, t)
    x_if_sorted = x_interface_particles + dx_if
    z_if_sorted = Z_iface + dz_if
    # Sort by x for clean line drawing
    sort_idx = np.argsort(x_if_sorted)
    interface_line.set_data(x_if_sorted[sort_idx], z_if_sorted[sort_idx])

    # Upper particles
    dx_up, dz_up = particle_displacement(X_up, Z_up, t)
    pos_up = np.column_stack([X_up + dx_up, Z_up + dz_up])
    scat_upper.set_offsets(pos_up)

    # Lower particles
    dx_lo, dz_lo = particle_displacement(X_lo, Z_lo, t)
    pos_lo = np.column_stack([X_lo + dx_lo, Z_lo + dz_lo])
    scat_lower.set_offsets(pos_lo)

    # Interface particles: use physics module displacement (at interface, full amplitude)
    dx_if, dz_if = particle_displacement(x_interface_particles, Z_iface, t)
    pos_if = np.column_stack([x_interface_particles + dx_if, Z_iface + dz_if])
    scat_iface.set_offsets(pos_if)

    # Near-interface particles: +4m (orange) and -4m (cyan)
    dx_above, dz_above = particle_displacement(x_near_particles, Z_above, t)
    pos_above = np.column_stack([x_near_particles + dx_above, Z_above + dz_above])
    scat_above_near.set_offsets(pos_above)

    dx_below, dz_below = particle_displacement(x_near_particles, Z_below, t)
    pos_below = np.column_stack([x_near_particles + dx_below, Z_below + dz_below])
    scat_below_near.set_offsets(pos_below)

    # Tracker particles
    tracker_above.set_data([pos_above[TRACKER_IDX, 0]], [pos_above[TRACKER_IDX, 1]])
    tracker_below.set_data([pos_below[TRACKER_IDX, 0]], [pos_below[TRACKER_IDX, 1]])
    tracker_iface.set_data([pos_if[TRACKER_IDX, 0]], [pos_if[TRACKER_IDX, 1]])

    # Time marker
    time_marker.set_data([t % (2 * PERIOD)], [0])

    # Orbit ellipses
    idx = 0
    for i in demo_indices_upper:
        draw_orbit(X_up[i], Z_up[i], orbit_lines[idx])
        idx += 1
    for i in demo_indices_lower:
        draw_orbit(X_lo[i], Z_lo[i], orbit_lines[idx])
        idx += 1
    for i in demo_indices_iface:
        draw_orbit(x_interface_particles[i], INTERFACE_DEPTH, orbit_lines[idx])
        idx += 1

    return [interface_line, scat_upper, scat_lower, scat_iface,
            scat_above_near, scat_below_near,
            tracker_above, tracker_below, tracker_iface,
            time_marker] + orbit_lines


# == Run and save ==============================================================

print("Generating internal wave animation...")
print(f"  Wavelength: {WAVELENGTH} km, Amplitude: {AMPLITUDE} m")
print(f"  Period: {PERIOD} hr, Phase speed: {PHASE_SPEED:.1f} km/hr (westward)")
print(f"  Particles: upper={len(X_up)}, lower={len(X_lo)}, interface={N_INTERFACE_PARTICLES}")
print(f"  Frames: {N_FRAMES} (one full period), FPS: {FPS}")
print(f"  Loop-clean: last frame is one DT before repeating first frame")

anim = FuncAnimation(fig, animate, init_func=init,
                     frames=N_FRAMES, interval=1000//FPS, blit=True)

out_path = Path("~/ooi/visualizations/internal_wave.mp4").expanduser()
out_path.parent.mkdir(parents=True, exist_ok=True)
anim.save(str(out_path), writer='ffmpeg', fps=FPS, dpi=150)
plt.close()

print(f"\nSaved: {out_path}")
print(f"Duration: {N_FRAMES/FPS:.1f} seconds ({2*PERIOD:.2f} hr of simulated time)")
