# Synthetic MLD Dataset — Design Note (first cut)

Working doc (not in the Jupyter Book). Companion to `MLDObservations.md`,
`MLDAnnotationPlan.md`, and the `mld/` 1-D CNN pipeline (`Analysis.md`).

## Purpose

A **shadow dataset** of artificial profiles with *predetermined* MLD ground truth. Train the
1-D CNN on the real human-labeled pp06 data, then run it against the synthetic set to probe how
it generalizes across the MLD operating envelope. A failure localizes to a parameter region
(e.g. "fails when MLD > 70 m" or "fails below SNR X"), which a random same-size real draw cannot
reveal.

**Caveat on interpretation.** This is a clean generalization test ONLY to the extent the
synthetic inputs sit in the same distribution the model trained on (physical-unit magnitudes,
depth coverage, mixed-layer roughness). Where synthetic profiles are out-of-distribution, a
failure means "OOD," not "model wrong." We keep realism knobs explicit so a failure is
interpretable.

## DENSITY DECISION (2026-10-10) — read first

Density is derived from T, S, depth (TEOS-10), so as a model input it adds no information and as
a prediction head it asks the model to re-learn a known function. **Decision: drop density as
both input channel and output head.** Model on **T, S, DO** (3 inputs, 3 heads). A density MLD,
if ever wanted, is **computed** from predicted T/S, not learned. See `WorkingWithAgenticAI.md`
Lesson 3.

Consequences:
- This is a MODEL CHANGE from the trained `mldnet_20260925` (4 heads / 8 input ch). Touches
  `mld_config.SENSORS`, `model.py` (`in_ch`), `dataset.py`. Requires a retrain.
- **Synthetic shards: still WRITE a density shard** (derive via gsw — "might as well," keeps the
  parallel pp06 tree complete and faithful), **but emit NO density label row** in the metadata
  CSV. So the density shard exists on disk; the model neither consumes nor is scored on it.

Sensor-expansion stance (not for this cut): other sensors (chlorophyll-a first, then backscatter,
then ADCP as Phase-2 corroboration) are to be read AGAINST the T/S/DO-derived MLD — "given the
physical MLD, what structure appears in the chlorophyll column?" — NOT fused into the estimator.
MLD is a means, not an end.

## Model facts this must honor (from `mld/`)

- Model (POST-density-drop target) = shared 1-D CNN backbone + **3** heatmap heads: temperature,
  salinity, dissolvedoxygen. (The 2026-09-25 trained model was 4-head incl. density; it will be
  retrained to 3-head.)
- Input per sensor = **2 channels** on a 0–200 m / 1 m / 200-bin grid:
  - ch0 = filtered value (adaptive Savitzky-Golay), **in raw physical units — NO standardization**.
  - ch1 = local roughness ("scratchiness": rolling MAD of raw−light-smooth).
  - a presence mask rides alongside (1 where a real sample fell in the bin).
- Target = Gaussian heatmap (sigma 4 m) centered on the MLD; **no-MLD = flat all-zero target**.
- Peak extraction: argmax; confidence < 0.30 => reported as no-MLD.

Implications:
1. Synthetic absolute values MUST sit in the real per-sensor range (ch0 is unnormalized).
2. Synthetic depth coverage MUST mimic real (profiles often don't sample the top ~15–30 m).
3. Mixed-layer "stem" MUST carry realistic roughness, or ch1 is ~0 everywhere (OOD).
4. We generate on realistic irregular sampling and push through the SAME `_bin_profile`/filter
   path the trainer/infer use — never hand-place values on the grid.

## Composition

- **80% MLD-present** ("textbook"), **20% no-MLD**.
- Count: initial cut ~1580 (≈ real labeled count) OR a structured sweep — see Sweep. Decision:
  **sweep** (characterize envelope), not count-matched.
- **GPI namespace:** synthetic profiles get reserved GPIs in a high band (>= 900000) that cannot
  collide with real pp06 GPIs, and are tagged synthetic so inference never confuses them.

## Output: real pp06 shards in a parallel universe

Decision: write genuine pp06-format NetCDF shards (not model-ready arrays), so synthetic data
flows through the EXACT same `_bin_profile`/filter path as real data and could hypothetically be
trained on.

- **Parallel root** `~/ooi/synthetic/` — NOT inside any real site tree (`sb|oo|ab`), so globbing a
  real site never sees synthetic shards. Two layers of collision protection: separate root AND
  reserved GPI band (>= 900000) + a `synthetic` site/filename token.
- Layout mirrors the real per-site tree:
  ```
  ~/ooi/synthetic/postproc/pp06/<yyyy>/RCA_synthetic_sp_<sensor>_<yyyy>_<ddd>_<gpi>_<daily>_V1.nc
  ~/ooi/synthetic/metadata/annotations/mld_labels_synthetic_block00_synthetic.csv
  ~/ooi/synthetic/metadata/annotations/mld_candidates_synthetic_block00.csv
  ```
- `synthetic` kept as a BARE directory the synthetic tooling knows about for now (not registered
  as an ooipaths pseudo-site). Promote to a registered pseudo-site only if/when we actually train
  on it.
- **Shards written per sensor INCLUDING density** (density derived via gsw). The label CSV,
  however, carries rows only for **T, S, DO** — no density label (see Density Decision).

## Metadata table = generator IS the annotator

The generator writes the label/metadata table in the SAME pass it writes the shards — it has
perfect ground truth at write time, so there is NO `MLD.py` hand-labeling step for synthetic data.
Schema mirrors what `MLD.py` emits (so `dataset.py` consumes it unchanged): one row per
(gpi, sensor, who) with `who = "synthetic"`, the known `mld_depth`, `no_mld_recorded`, and the
filter columns (adaptive_savgol_mad / window / adaptivity matching the labeling convention).
Rows for T/S/DO only; density omitted.

## Per-profile structure

### Shared geometry
- **Shallowest sampled depth** `d_min`: random per profile, range **5–40 m, mode ~20 m**
  (right-skewed; triangular(5, 20, 40) or clipped lognormal). Grounded in real pp06: measured
  archetype d_min = {7, 14, 15, 15, 17, 17, 18, 19, 19, 33} — cluster ~14–19 m, one at 33, two at 7.
  triangular(5, 20, 40) matches well; mode could nudge to ~17.
- Deepest depth ~195–199 m. Irregular sample spacing like real ascent profiles.

### Temperature = BASELINE
- MLD elbow at **z0** (sweep axis). Mixed layer: ~constant from `d_min` to z0.
- Cline: **decreasing**, sharp gradient at the elbow, rolling over to zero-gradient (vertical) in
  the deepest ~20 m toward a deep asymptote.
- Real envelope (oo archetypes, measured 2026-10-10): surface **11.1–12.9 °C**, deep **8.0–8.4 °C**,
  cline magnitude **2.8–4.9 °C** (median ~3).

### Salinity, DO = derived from the T baseline
- Each sensor's elbow depth ~ **Gaussian(z0_T, sigma = 4 m)** (co-located, not identical —
  corroborated by oo GPI 2561: T 61.1 m vs S 61.8 m).
- **Salinity**: cline **increasing**. Envelope: surface **32.46–32.63**, deep **33.82–33.97**,
  cline **~1.35 PSU** (strikingly stable across all 4 archetypes — narrow sweep OK).
- **DO**: cline **decreasing**. Envelope: surface **260–267**, deep **116–125**, cline
  **~138–146 umol kg-1** (large dynamic range). Units confirmed from data: **umol kg-1**.
- Same sharp-then-rollover cline shape as T.

Real-value table (oo pp06 archetypes, shallowest-10 m surface / deepest-20 m asymptote):

| sensor | surface | deep | cline \|Δ\| | n |
|---|---|---|---|---|
| temperature | 11.1–12.9 °C | 8.0–8.4 °C | 2.8–4.9 | 4 |
| salinity | 32.46–32.63 | 33.82–33.97 | ~1.35 PSU | 4 |
| dissolvedoxygen | 260–267 | 116–125 | ~138–146 umol kg-1 | 3 |

### Density = DERIVED, not synthesized
- Compute from synthetic T, S, depth via TEOS-10 (`gsw`): pressure from depth+latitude, then
  **in-situ density** (pp06 uses in-situ, not sigma0). The density head's "label" MLD follows from
  the derived profile's elbow (co-located with T/S by construction).

### No-MLD profiles (20%)
- All sensors begin at `d_min` already in a gradient — NO constant mixed-layer section.
  Monotone-ish from top to deep asymptote. Target heatmap = flat zeros for all heads.

## Noise model (realism knob)
- When an MLD is present: the mixed-layer **stem** (d_min -> z0) carries a **smoothly-varying**
  noise signal (not white; low-frequency wander) so ch1 roughness is nonzero where the annotator
  saw scratchiness. Magnitude per sensor TBD as a fraction of that sensor's cline magnitude.
- From the cline down: noise **negligible for now** — but implemented as a tunable knob defaulting
  ~0, so below-cline roughness can be enabled later without a rewrite.
- No-MLD profiles: minimal/!! TBD — likely light smooth noise throughout.

## Sweep axes (first cut)
- **z0** (T baseline MLD depth): ~24–72 m band from archetypes; sweep e.g. 15–90 m.
- **cline magnitude**: per-sensor, around the real envelopes above.
- **cline sharpness**: how abrupt the elbow is / how fast it rolls to vertical.
- (noise level: fixed for first cut; promote to a sweep axis later.)
- Resolution per axis: TBD (small, e.g. 5–7 steps each) to keep the first cut tractable.

## Open items before coding
- Noise magnitudes per sensor (fraction of cline mag?).
- Sweep step counts per axis + total profile count.
- Latitude(s) for `gsw` pressure/density (per-site, from ooipaths).
- Where synthetic shards/arrays live: `~/ooi/mld/synthetic/` (mirror the example schema the
  trainer consumes, or emit model-ready arrays directly?).

## Resolved parameters (2026-10-10)

- **Sequencing**: (a) refactor `mld/` to 3-sensor (T/S/DO) + retrain on real data FIRST, then build
  the synthetic harness against the 3-head model.
- **Noise (stem)**: smooth low-frequency wander ~3% of each sensor's cline magnitude
  (T ~±0.1 °C, S ~±0.04 PSU, DO ~±4 umol kg-1). Below cline ~0 (tunable knob).
- **Sweep**: z0 {20,35,50,65,80} m x cline-mag {low,mid,high} x sharpness {sharp,med,gradual}
  = 45 MLD-present combos, replicated ~28x -> ~1575 total; 80/20 MLD-present/no-MLD.
- **Sites**: ALL (sb, oo, ab) — don't strain at gnats; fine-tune/rerun later if needed. Per-site
  latitude from ooipaths for gsw.
- **Synthetic time frame**: years begin at **9000** (sentinel; signals "not real"), spanning ~11
  years like the real SP record without rolling to a 5th digit. Shards stamped under 9000+.

## Zeroth-order acceptance test

Before anything subtle: can the retrained T/S/DO model score ~**100% on easy/textbook synthetic
cases**? Correct = predicted MLD within tolerance of ground truth (start at **±5 m**, matching the
~5 m real-data MAE; tighten later) AND no-MLD cases correctly abstaining. If it can't nail the
clean cases, the hard cases are moot. This is the gate.

## As-built (2026-10-10) — generator state

The generator (`mld/synthetic.py`) diverged from the original spec during visual validation.
Current state:

- **3-sensor model** (T/S/DO; density dropped) retrained: `mldnet_20261010T233510.pt`, test MAE 4.65 m.
- **MLD-present sweep (1350 profiles)**: z0 {20,35,50,65,80} x magnitude {low,mid,high} x cline
  sharpness {sharp10,med18,gradual28 m} x **elbow radius {tight1,round3,broad6 m}** x 10 replicates.
  - Flat mixed-layer STEM >= 10 m, genuinely flat to z0 (one-sided tanh below z0; `_tanh_cline`).
  - **Rounded elbow** via softplus knee shifted 4*elbow_r below z0 so the stem stays flat and the
    corner rounds just below the MLD (independent of cline slope).
  - **NOISE OFF**: raw == clean signal (stem-noise code retained, disabled).
- **No-MLD block (300 profiles)**: contiguous GPI block AFTER the MLD-present ones. No flat stem;
  initial slope > 1/6 in normalized chart space; gradual flat asymptote at 200 m; half plain-concave,
  half with a mid-profile inflection (`_gradient_only`). Noise off.
- **Output**: real pp06 shards in `~/ooi/synthetic/`, GPIs >= 900000, synthetic years 9000+ (stored
  NetCDF time clamped to 2200 to dodge the ns-datetime overflow; filename year is the real sentinel).
  Label CSV T/S/DO only (no density label); density shard written for completeness.
- **Validation tooling**: `SyntheticViewer.py` — `--dump` (10 MLD gpis x 4 sensors = 40 PNGs, blue
  dot at MLD), `--dumpNoMLD` (6 x 4 = 24 PNGs), interactive temperature viewer (one Next button).
  `ArchetypeValuePuller.py` grounded the value envelopes.

Visual check PASSED for both MLD-present and No-MLD across all 4 sensors (2026-10-10).

## Status
Synthetic dataset built and visually validated. OPEN / NEXT:
- The zeroth-order acceptance test earlier scored ~0.5% — but that was BEFORE the flat-stem fix,
  the gentler clines, noise-off, and the orientation we confirmed by eye. **Re-run the acceptance
  test (`mld/score_synthetic.py`) against the current dataset** now that the profiles are known-good.
  The earlier failure was traced to synthetic profiles being too flat/too sharp (OOD vs training) —
  the current gentler, archetype-grounded profiles are the fair test.
- Then: decide whether to tune toward realism (reintroduce noise; match real roughness) or treat
  the clean-case score as the baseline before adding noise back.
