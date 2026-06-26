# Testing

This document concerns setting up tests to show that project software works as
intended. Failed tests should be flagged to the Open Issues list.


## Spectral Graph Analysis

Plan: Generate a synthetic dataset that mimics the structure of pp06 shard data
but with clearly defined, known properties. Run SGA modules 1–7 on this synthetic
data and verify that the clustering output matches expectations.

Synthetic dataset design:
- Location: `~/ooi/postproc/pp06synthetic/redux<yyyy>/`
- Format: identical shard filenames and NetCDF structure to pp06
- Content: two distinct water column "states" (e.g. summer-stratified vs winter-mixed)
  constructed analytically with known temperature/salinity/density profiles
- Each state should be clearly separable in feature space
- Include ~100 profiles per state, assigned to consecutive global indices
- Optionally: add a third "transition" state with intermediate properties

Expected SGA result:
- Module 6 should identify the correct number of clusters (2 or 3)
- Cluster assignments should match the known state labels exactly (or nearly so)
- The Fiedler vector should show a clean sign change between the two primary states
- Silhouette score should be high (>0.7) for the correct k

Implementation steps:
1. Write a script to generate synthetic shard files with prescribed sensor profiles
2. Point `sga_config.py` at `pp06synthetic` (change `data_base`)
3. Run modules 1–7
4. Compare cluster labels against known ground truth
5. Report pass/fail


## Internal Waves

Define three cells from the `internal_wave.py` visualization grid. Track their area
(which should remain fairly constant due to incompressibility) over the time series
where one wavelength of the internal wave passes by.

Implementation:
- Select three sets of four adjacent grid particles forming rectangular cells
  (one near interface, one in upper layer, one in lower layer)
- For each frame: compute the quadrilateral area from the four displaced particle positions
  using the shoelace formula
- Plot area vs time for each cell
- Verify area variation is small (consistent with divergence-free velocity field)
- If area varies significantly: the displacement field violates incompressibility
  and needs correction

Pass criterion: area variation < 3% of initial area (accepts linear-theory residual).


### Development history

1. **Initial attempt**: Arbitrary ASPECT_RATIO = 3.0 (horizontal/vertical orbit ratio).
   Incompressibility test showed 70–150% area variation. Completely wrong.

2. **First fix**: Derived ASPECT_RATIO from the continuity equation:
   `ASPECT_RATIO = WAVELENGTH / (2π × DECAY_SCALE)`. Still failed (40–70%) because
   the derivation assumed small displacements but the sign-flip across the interface
   and the derivative of |z| introduced errors.

3. **Stream function formulation (current)**: Rewrote displacement using:
   - η(x,z,t) = B(z) × sin(kx - ωt) [vertical]
   - ξ(x,z,t) = B'(z)/k_m × cos(kx - ωt) [horizontal]
   
   where B(z) = A × exp(-|z - z_iface|/D). This guarantees ∂ξ/∂x + ∂η/∂z = 0
   analytically (linear theory). Test results: <1% deep, ~2% near interface.

4. **Remaining ~2% error**: Arises because the divergence-free condition is satisfied
   in Eulerian (fixed-point) coordinates, but we're tracking Lagrangian (material)
   parcels that undergo finite displacement. When displacement ~ decay scale (20m
   amplitude, 40m e-folding), second-order terms matter.

5. **Future improvement**: Fully Lagrangian formulation where the divergence-free
   condition is enforced on the deformed coordinate system. Significantly more complex
   (requires iterative or symplectic integration). Deferred.
