# Vector Data

Discussion and planning for the four vector sensors on the shallow profiler.


## Velocity: VELPT (Nortek Aquadopp)


### Instrument description

The VELPT on the shallow profiler is a Nortek Aquadopp — a single-point acoustic Doppler
current meter. It measures mean water velocity in two horizontal dimensions (U, V) plus
vertical (W) as the profiler ascends through the water column. The result is a 3-component
velocity vector (east, north, up) at each observation timestamp during the profile.

Data product: VELPTMN (Mean Point Water Velocity)
Channels: 3 (east, north, up)
Source: [RCA Current Meters page](https://interactiveoceans.washington.edu/instruments/current-meter/)


### Comparison with ADCP

The RCA also has ADCPs (Teledyne RDI 5-beam 600 kHz VADCPs) mounted on the Platform
Interface Assembly at 200m depth — the same platform where the shallow profiler rests.
These are upward-looking and profile the *entire* water column simultaneously from a
fixed position, producing a velocity profile with depth bins (typically 2–4m resolution).

Key differences:

| | VELPT (on profiler) | ADCP (on platform) |
|---|---|---|
| Measurement type | Single point, co-located with profiler | Full water column profile from fixed position |
| Spatial coverage | One depth at a time (as profiler moves) | Entire 200m column simultaneously |
| Temporal resolution | Continuous during ascent (~45 min) | Continuous (24/7, not just during profiles) |
| Motion contamination | Profiler motion adds noise | Stationary mount, cleaner signal |
| Depth resolution | Determined by profiler speed + sample rate | Fixed bin size (2–4m) |
| Scientific value | Current at the exact location of other sensors | Background current field independent of profiler |

### Scientific merit of VELPT for this project

The VELPT gives you the current *at the same point and time* as all other profiler sensors.
This is valuable for:
- Correlating current shear with stratification features (e.g. do thin layers coincide with velocity gradients?)
- Understanding advective transport of the water masses being sampled
- Identifying internal waves (oscillating velocity + isopycnal displacement)

However, the measurement is contaminated by the profiler's own motion through the water.
The profiler ascends at roughly 0.1 m/s, and the Aquadopp must separate ambient current
from platform velocity. This makes the vertical (W) component particularly noisy.

The ADCP on the platform provides a cleaner, more complete velocity picture but is a
*separate data stream* not currently in scope for this project (it's not a profiler sensor).


### Decision status

**Not currently planned for inclusion in the profile feature vector.** The 3-component
velocity adds only 3 values per depth bin (273 total features for 91 bins) — modest
compared to the scalar sensors. The concern is motion contamination reducing signal quality.
Revisit after the scalar + spectral sensors are integrated.


## Optical Absorption and Beam Attenuation: OPTAA (oa, ba)


### Instrument description

The OPTAA is a WET Labs AC-S spectrophotometer measuring two quantities across ~83 spectral
channels (approximately 400–730nm, 4nm resolution):
- **Optical absorption (a)**: Rate at which light energy is absorbed by seawater constituents
- **Beam attenuation (c)**: Rate at which light is removed by both absorption and scattering

The instrument operates only during noon and midnight profiles (the extended-descent profiles)
due to its equilibration requirements. Sampling rate is ~4 Hz.

Of the 83 channels delivered, the first few and last few should be discarded due to
low lamp intensity at the spectral edges (particularly short wavelengths) and detector
noise at the long-wavelength end. A working subset of approximately 65–70 channels is typical.

Data products:
- OPTABSN: Optical Absorption Coefficient (a)
- OPTATTN: Optical Beam Attenuation Coefficient (c)

Channels: 73 per sensor (after OOI processing; some edge channels already excluded)


### The derived third parameter: particulate scattering (b)

The fundamental relationship in ocean optics:

**b(λ) = c(λ) − a(λ)**

Scattering equals attenuation minus absorption, at each wavelength. This gives a full
spectral scattering coefficient — 73 channels of scattering derived directly from the
attenuation and absorption measurements. This derived quantity encodes information about
particle concentration, size distribution, and composition.

Note: This is *total* scattering, not backscattering. The FLORT sensor measures backscatter
at a single wavelength (~700nm); the OPTAA-derived scattering gives the full spectral
picture across 400–730nm. They are related but distinct measurements.


### Reduction of 73 channels to characteristic parameters

Five approaches for reducing the high-dimensional spectral data:

**1. Spectral slope (γ) of particulate scattering**

Fit a power law: b_p(λ) ∝ λ^(−γ). The exponent γ is inversely related to particle size —
steep slopes (large γ) indicate small particles; flat slopes indicate large particles.
One number summarizes the entire spectrum's shape.

*This would be a good entry step. The derived spectral slope could be sidebar-correlated
with the FLORT single-wavelength backscatter as a first null hypothesis test: Does the
power-law extrapolation to 700nm agree with the FLORT measurement?*

**2. Spectral slope ratio (S_R)**

Ratio of absorption slopes in two wavelength bands. The canonical formulation uses
275–295nm vs 350–400nm bands as indicators of dissolved organic matter molecular weight
and source. However, the AC-S range is 400–730nm — entirely outside the UV bands cited
in the literature. The question is whether meaningful slope ratios can be defined within
the 400–730nm range. This needs investigation; it may not transfer directly from the
UV-based methodology.

**3. Absorption at specific wavelengths as biogeochemical proxies**

- a(440): Proxy for CDOM concentration
- a(676): Correlates with chlorophyll-a (the red absorption peak)

*These immediately suggest null hypothesis correlations with the FLORT FDOM sensor
(compare a(440) vs fluorometric CDOM) and the FLORT chlorophyll-a sensor (compare
a(676) vs fluorometric chlorophyll-a). Agreement would validate both instruments;
disagreement would be scientifically interesting.*

**4. Three-point chlorophyll-a estimate from absorption**

The absorption peak near 676nm minus a baseline (interpolated from flanking wavelengths)
gives a chlorophyll estimate independent of fluorescence. This can be compared directly
to the FLORT fluorometric chlorophyll-a measurement. Discrepancies may indicate
non-photochemical quenching (fluorescence suppression in high light) or changes in
phytoplankton community composition.

**5. PCA/EOF on the spectra**

Run PCA on the ~65 usable channels of absorption (and separately on attenuation) across
all profiles. Typically 3–5 principal components capture >95% of variance. The PC scores
become the reduced feature set — each one corresponds to a distinct spectral shape
(e.g. PC1 ≈ total particle load, PC2 ≈ phytoplankton vs detritus ratio,
PC3 ≈ size distribution shift).

*This would take some work to justify but looks interesting as a dimensionality reduction
strategy for the SGA feature vector. Note: past experience indicates the first few and
last few of the 73 channels should be discarded before running PCA, as edge-channel noise
would otherwise dominate the variance and corrupt the principal components.*


### Decision status

Not yet integrated. The OPTAA data is only available for noon/midnight profiles (pp01/pp02),
which limits its use in the full SGA feature vector (most profiles lack OPTAA data).
Best suited for a specialized analysis of the noon/midnight subset.


## Spectral Irradiance: SPKIR


### Instrument description

The SPKIR is a Satlantic OCR-507 multispectral radiometer measuring downwelling spectral
irradiance — the amount of solar radiation (light energy) per unit area reaching the sensor
as it ascends through the water column. It measures at seven discrete wavelength bands:

| Channel | Wavelength | Bandwidth |
|---------|-----------|-----------|
| si412   | 412 nm    | ~10 nm    |
| si443   | 443 nm    | ~10 nm    |
| si490   | 490 nm    | ~10 nm    |
| si510   | 510 nm    | ~10 nm    |
| si555   | 555 nm    | ~10 nm    |
| si620   | 620 nm    | ~20 nm    |
| si683   | 683 nm    | ~20 nm    |

These wavelengths are chosen to match standard ocean color satellite bands (MODIS, SeaWiFS).
The sensor measures *apparent* optical properties — they depend on the ambient light field
(sun angle, cloud cover, time of day) unlike the *inherent* optical properties measured
by the OPTAA.

Data product: SPECTIR (Downwelling Spectral Irradiance)
Source: [RCA Spectral Irradiance page](https://interactiveoceans.washington.edu/instruments/spectral-irradiance-sensor/)


### Scientific applications

**Light attenuation with depth (Kd):**
The diffuse attenuation coefficient Kd(λ) is derived from the slope of ln(Ed) vs depth
at each wavelength. Kd characterizes how quickly light is removed from the water column
and is a key input to primary productivity models. Each wavelength gives a separate Kd,
so you get a 7-element Kd vector per profile.

More precisely: Light in the ocean decays approximately exponentially with depth:

    Ed(λ, z) = Ed(λ, 0) × exp(−Kd(λ) × z)

Where Ed(λ, z) is downwelling irradiance at wavelength λ and depth z, Ed(λ, 0) is
irradiance just below the surface, and Kd(λ) is the attenuation rate in units of m⁻¹.

To compute Kd from a profile: Plot ln(Ed) vs depth. In the region where the relationship
is linear (typically upper 50–100m, below immediate surface effects), the slope of that
line is −Kd. A steeper slope means light is removed faster (murkier water).

Physical interpretation of Kd at different wavelengths:
- Kd(412) large → CDOM and/or particles absorbing blue light
- Kd(683) large → chlorophyll absorbing red light (phytoplankton bloom)
- Kd uniform across wavelengths → particle scattering dominates (turbid water)
- Kd small everywhere → clear oligotrophic water

Why Kd rather than raw Ed: Two profiles at the same location on the same day — one at
10am, one at 2pm — will have very different Ed values (sun angle changes how much light
enters). But Kd will be nearly identical because the *rate of decay* depends on what's
in the water, not how much light entered at the surface. Kd is a property of the water
column itself rather than of the illumination conditions.

Practical computation from SPKIR data: For each of the 7 wavelengths in a single profile
ascent, Ed is measured at many depths. Take ln(Ed) at each depth, fit a line through the
linear portion (avoiding the top few meters where surface effects and wave focusing cause
noise), and the slope gives Kd for that wavelength. Result: 7 Kd values per profile.

**Euphotic zone depth:**
The depth where irradiance falls to 1% of its surface value (the "1% light level") defines
the euphotic zone. This can be computed per wavelength or as a PAR-weighted average.
Compare with the scalar PAR sensor for validation.

**Water clarity and particle characterization:**
The spectral shape of Kd encodes information about what's attenuating light — pure water
absorption dominates at red wavelengths, while particles and CDOM dominate at blue
wavelengths. The ratio Kd(490)/Kd(555) is a standard water clarity index.

**Satellite validation:**
The 7 wavelengths match satellite ocean color bands. In-situ Kd profiles can validate
satellite-derived diffuse attenuation products for this region.

**Quenching correction for chlorophyll fluorescence:**
Chlorophyll fluorescence (from FLORT) is suppressed in high-light conditions near the
surface ("non-photochemical quenching"). The SPKIR irradiance profile provides the light
field needed to model and correct this artifact.


### Reduction to characteristic parameters

The 7 channels are already a compact representation (unlike the 73-channel OPTAA).
Useful derived quantities:

1. **Kd(λ) vector** (7 values per profile): Fit ln(Ed) vs depth in the upper water column.
   This is the most scientifically useful reduction — it removes the dependence on surface
   illumination conditions and gives an inherent property of the water column.

2. **Euphotic depth** (1 value): Depth where Ed falls to 1% of surface. Scalar summary
   of light penetration.

3. **Kd spectral slope**: Fit a power law or exponential to Kd(λ) across the 7 bands.
   Indicates whether attenuation is dominated by particles (flat) or dissolved matter (steep).

4. **Band ratios**: e.g. Ed(490)/Ed(555) at a reference depth — standard ocean color index.


### Considerations for the SGA feature vector

Unlike OPTAA, the SPKIR operates on *all* profiles (not just noon/midnight). However,
irradiance is an apparent property — it depends on time of day, cloud cover, and season.
Profiles at different times of day will have very different irradiance values even if the
water column is identical.

**Recommendation:** Use Kd(λ) rather than raw Ed(λ) in the feature vector. Kd removes
the surface illumination dependence and characterizes the water column itself. This adds
7 features per depth bin (or 7 features per profile if computed as a single depth-averaged
Kd). For SGA, a single Kd vector per profile (7 values total, not per depth bin) may be
most appropriate since Kd is relatively constant with depth in the upper mixed layer.

**Caveat:** Nighttime profiles have no meaningful irradiance data. SPKIR features would
need to be masked or excluded for nighttime profiles, or the analysis restricted to
daytime profiles only.


### Decision status

Not yet integrated. The time-of-day dependence and nighttime data absence make this
sensor more complex to incorporate than the scalar sensors. Best approached after the
scalar + OPTAA integration is complete.
