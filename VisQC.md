# VisQC: Visual Quality Control for Profile Metadata


## Purpose

VisQC is a two-stage workflow for validating and correcting the derived cline metadata
(pycnocline depth, thermocline depth, etc.) produced by `iw/cline_extract.py`.

The premise: automated peak-finding sometimes fails. It may latch onto noise, pick a
secondary feature instead of the primary, or produce a depth estimate that is clearly
wrong when you look at the actual profile. VisQC provides a human-in-the-loop step
to catch and correct these errors before the metadata feeds into internal wave analysis.


## Stage 1: VisQCInspector.py

An interactive tool that steps through profiles one at a time:
- Displays T (bottom x-axis) and S (top x-axis) vs depth (y-axis, surface at top)
- Overlays the derived metadata (cline depth markers, strength annotations)
- Widget buttons to: accept, correct (adjust depth), or discard the profile
- Outputs a visitation metadata CSV tracking decisions made

## Stage 2: VisQCCorrector.py

Reads the visitation CSV and produces a corrected version of `cline_extract_site.csv`
incorporating the human-verified adjustments.

Open question: Should this also produce a corrected post-processing redux (pp07)?
Deferred for now.


## Current metadata columns (from cline_extract)

Per profile we have:
- **Cline depth** (meters): pycnocline, thermocline, halocline, oxycline, secondary pycnocline
- **Cline strength** (gradient magnitude at the peak): all four primary + secondary

We do NOT currently have:
- **Cline thickness** (vertical extent of the transition zone)


## Cline thickness estimation

Standard approaches:

1. **Gradient threshold method**: Define the cline as the depth range where |dρ/dz|
   exceeds some fraction of the peak gradient (e.g. 50% of max). The top and bottom
   of that zone give the cline thickness. Uses linear interpolation at the threshold
   crossings for sub-grid-cell resolution (avoids quantization artifacts from the
   discrete depth grid). Simple, reproducible, but threshold-dependent.

2. **Tangent-line method** (Chu & Fan, 2011): Fit a tangent line at the point of maximum
   gradient. Where it intersects the upper and lower "shelf" values (above and below the
   cline) defines the thickness. More geometrically motivated but sensitive to noise in
   the shelf values.

3. **Sigmoid fit**: Fit an error function (erf) or hyperbolic tangent to the density
   profile through the cline region. The width parameter of the sigmoid IS the cline
   thickness. Most robust for clean data; fails if the cline isn't well-approximated
   by a monotonic transition.

4. **N² half-width**: The depth range over which N² exceeds half its maximum value
   (full width at half maximum of the buoyancy frequency peak). Analogous to spectral
   linewidth. Physically meaningful — directly relates to internal wave trapping.

Recommendation: Start with method 1 (gradient threshold at 50% of peak). It's fast,
works on all four cline types identically, and produces a single "thickness" number per
cline per profile. If that proves too noisy, upgrade to method 4 (N² FWHM) for the
pycnocline specifically.

Adding thickness to `cline_extract.py` output: a future enhancement. For VisQC purposes,
the depth + strength are sufficient for visual validation.
