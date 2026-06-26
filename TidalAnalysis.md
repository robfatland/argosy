# Tidal Analysis


## Section 1: Tidal Prediction from TPXO10

### What is TPXO10?

TPXO10-atlas-v2 is a global ocean tidal model produced by Oregon State University
(Egbert & Erofeeva, 2002). It provides harmonic tidal constituents on a global grid.
Each constituent is characterized by amplitude (meters), phase (degrees), and angular
frequency (degrees per hour). Given these constituents for a specific location, tidal
height can be predicted at any past or future time without the original 30 GB dataset.

Reference: Egbert, G.D. and S.Y. Erofeeva, "Efficient inverse modeling of barotropic
ocean tides," Journal of Atmospheric and Oceanic Technology, 19, 183-204, 2002.
[TPXO home page](http://www.tpxo.net/)

### Extraction process

The script `tidal_extract.py` (now retired; output preserved in `tidal_constituents.json`)
performed the following:

1. Read TPXO10 atlas NetCDF files (amplitude and phase grids for each constituent)
2. For each of the three RCA shallow profiler sites (Oregon Offshore, Oregon Slope Base,
   Axial Base), extracted the nearest grid point values for 14 constituents:
   m2, s2, n2, k2, k1, o1, p1, q1, 2n2, m4, ms4, mn4, mm, mf
3. Saved amplitude (meters), phase (degrees), and angular frequency (degrees/hour) for
   each constituent at each site to `tidal_constituents.json`

### Predicting tidal height

Given the JSON file, tidal height at any time t is computed by summing sinusoids:

    h(t) = sum over constituents: amplitude × cos(omega × hours_since_epoch - phase)

where `hours_since_epoch` is hours since 2000-01-01 UTC. This is implemented as
`predict_tide()` in `TimeSeriesProfileCorrelation.py`. The prediction is purely
deterministic — no external data needed beyond the JSON file.

The dominant constituents are M2 (principal lunar, period 12.42 hours) and K1
(luni-solar diurnal, period 23.93 hours). The predicted signal has amplitude of
approximately ±1.5 meters at Oregon Slope Base.


## Section 2: Does Start Depth Track the Tidal Signal?

### Motivation

The shallow profiler at Oregon Slope Base rests on a platform at ~200m depth.
When it begins an ascent profile, the starting depth should be at (or near) the
platform depth. However, the platform is anchored to the seafloor via a two-legged
mooring. Tidal variation changes the water column height above the platform,
effectively raising or lowering it relative to the pressure-derived depth coordinate.
Additionally, horizontal currents can depress the platform ("blowdown").

If the tidal signal is the dominant driver of start-depth variation, the two time
series should correlate strongly.

### Observations (January 1-11, 2024)

Examining 10 days of pp06 temperature profiles:

- **Start depth** oscillates with amplitude ~1.5-2.0 m around its mean (~185 m),
  with a clear semi-diurnal period matching the M2 tide.
- **Predicted tidal height** from TPXO10 constituents shows similar amplitude and period.
- **Phase relationship**: The two signals are visibly similar in period but appear
  out of phase. A naive subtraction (start depth - tidal height) produces a residual
  with amplitude comparable to the original signals, indicating the phase mismatch
  is significant.

### Cross-correlation to determine time lag

We computed the normalized cross-correlation between start depth and tidal height
over the full 10-day window, searching for the lag (±9 hours) that maximizes
correlation:

- Two positive correlation peaks were found (one at positive lag, one at negative lag)
- Neither peak produced a dramatically better alignment than the other
- The result was inconclusive: the tidal prediction and the start depth share the
  same dominant frequency but their phase relationship is not a simple constant offset

### Interpretation

The phase mismatch likely arises because:
1. The barotropic tide (surface tide, what TPXO10 predicts) propagates differently
   than the baroclinic response (internal tide) at depth
2. The profiler platform's depth response is mediated by the mooring dynamics, which
   introduces its own transfer function
3. Other forcings (currents, internal waves) contribute to start-depth variability
   on similar timescales

The tidal signal is present in start depth, but a simple time-shifted comparison
does not fully explain the observed variability.


## Section 3: Files

| File | Location | Purpose |
|------|----------|---------|
| `TidalSignal.ipynb` | `~/argosy/chapters/` | Notebook: runs the analysis module |
| `TimeSeriesProfileCorrelation.py` | `~/argosy/` | Module: 5-panel chart, cross-correlation analysis |
| `tidal_constituents.json` | `~/argosy/` | 14 tidal constituents for 3 RCA sites (self-contained) |
| `TidalSignal.png` | `~/ooi/visualizations/` | Output figure (5 panels) |


## Section 4: Further Work

### Other shallow profiler sites

Repeat this analysis at Oregon Offshore and Axial Base using the same
`tidal_constituents.json` (which already contains their constituents). Compare:
- Does the phase relationship differ by site?
- Is the correlation stronger at sites with less current exposure?

### End depth variability and blowdown events

The end depth (shallowest point of each profile) shows:
- Typical values: 5-15 m below the surface (platform ascends to near-surface)
- Episodic "blowdowns": profiles terminate at ~50 m, far short of normal ascent height

These blowdowns likely correspond to strong horizontal currents that depress the
mooring platform and prevent full ascent. The RCA shallow profiler mooring is a
custom two-legged design (tethered to the seafloor by one electro-optical cable
and one mechanical anchor leg) with a platform at ~200 m depth. Strong currents
can tilt the mooring, reducing the vertical range available for profiling.

Investigation:
- Correlate blowdown events with VELPT current measurements (when available)
- Examine seasonal patterns (winter storms drive stronger currents)
- Determine if blowdown-truncated profiles should be excluded from depth-sensitive
  analyses or treated with adjusted depth ranges

### Descent data for improved temporal resolution

The profiler's descent (after each ascent) provides an additional time sample of
the water column. Incorporating descent T/S data would give ~4 observations per
3-hour profile cycle instead of 1, significantly improving the ability to resolve
tidal-period signals. This requires sharding the descent data from the source
NetCDF files (currently stored on S3 at `s3://s3ooi/ooinet/`). See discussion in
`DevelopmentLog.md` and `Analysis.md`.
