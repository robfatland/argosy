# Internal Waves


## Terminology


- **isopycnal**: A surface of constant density analogous to an isotherm. Internal waves cause isopycnals to oscillate vertically.
- **pycnocline**: A depth range of maximum dρ/dz, most rapid change of density with depth. In the pycnocline the isopycnals are closely packed together. This is where internal waves have their largest vertical displacement amplitude. This is the starting point of the physics. To go further: look at buoyancy in relation to density.


## File inventory

| File | Location | Description |
|------|----------|-------------|
| `InternalWaves.md` | `~/argosy/` | This file. Reference documentation for the internal wave analysis. |
| `InternalWaves.ipynb` | `~/argosy/chapters/` | Notebook for the internal wave inventory analysis. Uses `%run` to launch modules. |
| `internal_wave_physics.py` | `~/argosy/iw/` | Shared physics module. Stream function formulation guaranteeing divergence-free displacement fields. |
| `internal_wave.py` | `~/argosy/iw/` | Generates the internal wave animation (particles, pycnocline boundary, orbit ellipses). Output: `~/ooi/visualizations/internal_wave.mp4`. |
| `TestInternalWaveIncompressibility.py` | `~/argosy/iw/` | Validates incompressibility: tracks area of 3 rectangular cells over one period. Pass criterion: <3% variation. Currently passes at <2%. |
| *(pending)* | `~/argosy/iw/` | Module for internal wave detection from real T/S profile data. |

Test specification (how to run, pass/fail criteria): see `Testing.md` → "Internal Waves".


## Plan


- Set up markdown (this file), IPython notebook (`chapters/InternalWaves.ipynb`), Python module(s)
- On AWS set up a small VM
- On AWS run a descent profile shard operation from Level 1 { Temperature, Salinity, Density }
- Calculate pycnocline changes in depth with time (profile/anti-profile)
- Reconcile salinity and temperature results
- Determine if the profiler velocity sensor (VELPT) is useful
- Expand this project to incorporate platform ADCP data to derive direction, validate amplitude, etc.
- Scope: Full time, 3 shallow profilers
- Publish the result


## Stream function physics


### Formulation

The displacement field uses a stream function that guarantees incompressibility
(∂ξ/∂x + ∂η/∂z = 0) analytically.

Vertical displacement:

    η(x, z, t) = B(z) × sin(kx − ωt)

where B(z) = A × exp(−|z − z_interface| / D).

From incompressibility (∂ξ/∂x = −∂η/∂z), integrating in x:

    ξ(x, z, t) = B'(z) / k_m × cos(kx − ωt)

where B'(z) = dB/dz:
- Above interface: B'(z) = −B/D (negative → horizontal displacement opposes phase)
- Below interface: B'(z) = +B/D (positive → horizontal displacement follows phase)

Check: ∂ξ/∂x + ∂η/∂z = −B'(z)sin(kx−ωt) + B'(z)sin(kx−ωt) = 0. ✓


### Parameters (pedagogical visualization)

- Wavelength: 100 km
- Amplitude: 5 m
- Period: 12.42 hr (M2 tidal)
- Interface depth: −50 m
- Decay scale: 40 m (e-folding from interface)
- AMPLITUDE/DECAY_SCALE = 0.125 — well within linear regime


### Development history

1. **Initial attempt**: Arbitrary ASPECT_RATIO = 3.0 (horizontal/vertical orbit ratio).
   Incompressibility test showed 70–150% area variation. Completely wrong.

2. **First fix**: Derived ASPECT_RATIO from the continuity equation:
   `ASPECT_RATIO = WAVELENGTH / (2π × DECAY_SCALE)`. Still failed (40–70%) because
   the derivation assumed small displacements but the sign-flip across the interface
   and the derivative of |z| introduced errors.

3. **Stream function formulation (current)**: Rewrote displacement using the
   η/ξ pair above. This guarantees ∂ξ/∂x + ∂η/∂z = 0 analytically (linear theory).
   Test results: <1% deep, ~2% near interface.

4. **Remaining ~2% error**: Arises because the divergence-free condition is satisfied
   in Eulerian (fixed-point) coordinates, but we're tracking Lagrangian (material)
   parcels that undergo finite displacement. When displacement ~ decay scale,
   second-order terms matter.

5. **Future improvement**: Fully Lagrangian formulation where the divergence-free
   condition is enforced on the deformed coordinate system. Significantly more complex
   (requires iterative or symplectic integration). Deferred.
