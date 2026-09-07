# VisQC: Visual Quality Control for Profile Metadata


## Purpose

This `VisQC` work is related to internal wave (abbreviated `iw`) detection. It is a quality control and annotation process. The QC: From postproc level 06 data we move to level 07. The annotation: VisQC is a two-stage workflow for validating and correcting the derived cline metadata: Pycno, thermo, halo and oxy. Estimates of these clines are first produced by `~/argosy/iw/cline_extract.py`; then corrected manually.


Automatic cline identification often fails due to noise and signal ambiguity. Actual ocean water does not conform to a simple description. VisQC provides for human-in-the-loop correction.


## Step 1: VisQCInspector.py


Run this interactive tool to step through profiles one at a time for a selected year.


- **Left panel**: T, S, DO, density traces vs depth (surface at top), independent
  auto-scaled x-axes; two adjustable cline boundary lines (upper/lower) for the selected
  sensor's cline (nudge buttons or click-to-set).
- **Right panel**: potential density σ₀ (TEOS-10 via `gsw`) vs depth for the same profile,
  derived from the salinity + temperature shards. Shows a note if `gsw` isn't installed.
- Widget buttons: **Accept**, **Correct** (save adjusted boundaries), **Discard**.
- Writes one row per (gpi, sensor) to the visitation CSV at
  `metadata/annotations/visqc_visitation_<site>.csv` (re-deciding overwrites that pair's
  row). Columns: `timestamp, gpi, sensor, decision, upper_depth, lower_depth, cline_depth,
  cline_thickness, reviewed_at`. Accept/Discard auto-advance to the next profile.
- Site via `ARGOSY_SITE`; start date via `VISQC_START_DATE` (default 2024-01-01).

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
