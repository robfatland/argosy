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
| `internal_wave.py` | `~/argosy/iw/` | Generates the internal wave animation (particles, pycnocline boundary, orbit ellipses). Output: `~/ooi/sb/visualizations/internal_wave.mp4`. |
| `TestInternalWaveIncompressibility.py` | `~/argosy/iw/` | Validates incompressibility: tracks area of 3 rectangular cells over one period. Pass criterion: <3% variation. Currently passes at <2%. |
| *(pending)* | `~/argosy/iw/` | Module for internal wave detection from real T/S profile data. |
| `cline_extract.py` | `~/argosy/iw/` | Extracts pycnocline, thermocline, halocline, oxycline depth/strength per profile. Output: `~/ooi/sb/metadata/cline_extract_slopebase.csv`. |

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


## Cline Extraction: Detecting stratification boundaries


### Introduction for the non-specialist

The ocean is layered. Warm, fresh, oxygen-rich water sits near the surface; cold,
salty, oxygen-depleted water lies below. The boundary between these layers — where
properties change most rapidly with depth — is called a "cline." There are several:

- The **thermocline** is where temperature drops fastest.
- The **halocline** is where salinity changes fastest.
- The **pycnocline** is where density changes fastest (a combined effect of T and S).
- The **oxycline** is where dissolved oxygen drops fastest.

These boundaries matter because internal waves — slow, large-amplitude waves
invisible at the surface — propagate along the pycnocline. Their speed and
wavelength depend on how sharp the density transition is. By tracking the
pycnocline depth over time (profile by profile, 9 times per day for a decade),
we can detect internal wave oscillations: the pycnocline heaves up and down with
tidal and other periodicities.

The thermocline and halocline don't always coincide with the pycnocline. When
fresh river water (Columbia plume) arrives, it creates a shallow halocline above
the thermocline. When they separate, that's a diagnostic of water mass intrusion.


### Algorithm

For each ascent profile in pp06:

1. Load temperature, salinity, and dissolved oxygen from shards at the same GPI.
2. Compute potential density (sigma-0) from T and S using the TEOS-10 equation of
   state (`gsw` library). This removes the pressure artifact from in-situ density.
3. Smooth all profiles lightly (Savitzky-Golay, window ~11 points ≈ 3 m).
4. Compute vertical gradients: dT/dz, dS/dz, dsigma0/dz, dO2/dz.
5. Find peaks (local maxima of absolute gradient) above a minimum threshold.
6. Record the depth and magnitude of the strongest peak for each variable.
7. If a secondary peak exists for sigma-0 (e.g. seasonal thermocline above permanent
   pycnocline), record that separately.
8. Compute N2 = -(g/rho) * dsigma0/dz at the pycnocline depth.
9. Compute mixed layer depth (MLD): mean sigma-0 within the shallowest 3 meters
   of available data serves as the reference (~6 points at 0.5 m grid spacing).
   MLD = first depth below that reference band where sigma-0 exceeds
   reference + 0.03 kg/m3. Using a 3 m band avoids contaminating the reference
   with stratified water even when the mixed layer is shallow (summer, plume events).


### Profile skip conditions

A profile is excluded from the output CSV (counted as "skipped") if any of:

1. **Missing T or S shard** — potential density requires both temperature and salinity.
2. **Fewer than 50 valid points** — too few non-NaN depth/value pairs after cleaning
   (likely a truncated or heavily contaminated profile).
3. **Sensor exclusion** — temperature or salinity timestamp falls within a manual QC
   exclusion window from `sensor_exclusions.csv`.
4. **Depth overlap < 50 m** — after loading T and S independently, if their valid depth
   ranges don't overlap by at least 50 m, there isn't enough common grid to compute
   a meaningful gradient.

Typically a few hundred profiles out of ~20,000 are skipped, mostly due to conditions
2 and 4 (short or truncated profiles that would produce unreliable cline estimates).


### Output CSV columns

```
site, gpi, timestamp,
pycnocline_depth, pycnocline_strength,
thermocline_depth, thermocline_strength,
halocline_depth, halocline_strength,
oxycline_depth, oxycline_strength,
N2_max, N2_max_depth,
secondary_pycnocline_depth, secondary_pycnocline_strength,
mld
```

One row per profile. Output: `~/ooi/sb/metadata/cline_extract_slopebase.csv`.

Units:
- Depths in meters (positive downward from surface)
- Strength: dT/dz in C/m, dS/dz in PSU/m, dsigma0/dz in kg/m3/m, dO2/dz in umol/kg/m
- N2 in rad2/s2 (typically 1e-4 to 1e-3 in the pycnocline)
- MLD in meters


### Connection to internal wave analysis

The time series of `pycnocline_depth` IS the internal wave signal. Its temporal
oscillation encodes:
- Period → comparison with tidal prediction (M2 = 12.42 hr)
- Amplitude → vertical displacement of the pycnocline (meters)
- N2 at the pycnocline → internal wave phase speed: c = N*H/pi (for mode-1)
- Wavelength → from dispersion relation given omega and N

Multiple profiles per day (up to 9) resolve the semi-diurnal tidal cycle.
The decade-long record enables seasonal and interannual variability analysis.


### Dependencies

- `gsw` (TEOS-10 Gibbs SeaWater library) for potential density
- `scipy.signal.savgol_filter` for smoothing
- `scipy.signal.find_peaks` for cline detection
