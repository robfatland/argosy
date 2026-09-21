# PP06: Filtered Physical Dataset

pp06 is the **physical, filtered** shard dataset built from the pp05-qualified redux shards
(contrast pp05, which is a QC *manifest* only — see `PP05_QCAnalysis.md`). It exists because the
shallow-profiler data are at times erratic: sensor artifacts appear as large, physically
implausible excursions that must be removed before analysis.

pp06 is produced by a numbered sequence of filters. **Filter 0 builds pp06 from redux** (a copy
of the qualifying shards); **Filters 1–3 then refine those pp06 shards in place**. All output
lives under `~/ooi/<site>/postproc/pp06/<yyyy>/` (per-site layout via `ooipaths`).

Restricted to the 8 HSD scalar sensors: temperature, salinity, density, DO, CDOM, chlorA,
backscatter, PAR.

| Filter | Purpose | Sensors | Script |
|--------|---------|---------|--------|
| 0 | Baseline copy from the pp05 manifest | all 8 HSD | `postprocess_pp06.py` |
| 1 | Suppress conductivity erratics (MRA walk) | salinity, density | `postprocess_pp06.py` |
| 2 | Savitzky-Golay smoothing (quantization noise) | cdom, chlorA | `postprocess_pp06_filter2.py` |
| 3 | Rolling-minimum despike (Briggs et al. 2011) | backscatter | `postprocess_pp06_filter3.py` |


## Filter 0: Baseline (manifest → pp06)

Copy each redux shard listed in the pp05 manifest into `~/ooi/<site>/postproc/pp06/<yyyy>/`,
same format as redux. This is the starting dataset the later filters refine.


## Filter 1: Suppress conductivity erratics (salinity + density)

The conductivity sensor produces salinity and (with temperature) density. This filter drops
salinity/density samples that fail either of two criteria. Because density depends on salinity,
**every discarded salinity sample discards the matching density sample too.** Discards are logged
to `~/ooi/<site>/postproc/pp06/pp06_filter1.csv` (sensor, global profile index, sample index,
value, depth).

Criteria (applied in an ascending walk through the profile):

- **PPC — physically-possible criterion:** value must lie in `[sp_lo, sp_hi]`.
- **SSC — sample-to-sample criterion** (e.g. 0.5 PSU): let `D = |value − MRA|`; if `D > SSC` the
  value is discarded, else it becomes the new MRA.

**MRA (Most Recent Acceptable)** is the most recent good sample in the walk. The first sample
inside the PPC range starts the profile and seeds the MRA; everything before it is discarded.
Each accepted sample updates the MRA. (More elaborate Markov-style filters are possible; deferred.)


## Filter 2: Savitzky-Golay smoothing (CDOM, chlorA)

The ECO fluorometer channels show quantization-step noise. A Savitzky-Golay filter
(`window=11`, `polyorder=2`) smooths the steps while preserving real features: at ~0.3 m/s ascent
and ~1 Hz sampling, 11 points span ~3–4 m, wider than the 1–3-point quantization steps but
narrower than genuine CDOM/chlorophyll layers (>10 points). Operates in place on pp06 shards.


## Filter 3: Backscatter despike (rolling-minimum baseline)

Optical backscatter carries transient spikes from individual large particles crossing the beam.
Following Briggs et al. (2011), a rolling minimum over an 11-sample depth window extracts the
spike-free baseline (the window minimum is unlikely to be spike-contaminated) and replaces the
signal with it. Same ~3–4 m span as Filter 2. Operates in place on pp06 backscatter shards.


## Filter 1 erratic examples

- **2016-328-2, GI 3278, ~37 m:** negative salinity excursion. Note a second candidate near ~57 m
  in the same profile is *real* data (the same signal appears in the +1 profile) — an argument for
  not setting SSC too tight.
- **GI 2075, ~81 m:** salinity erratic.
- **GI 9043, ~124 m → 61 m:** a large salinity excursion. Ideally removed whole by holding the MRA,
  but that also cuts the upper profile even though the sensor appears to recover.

Term note: **GI/GPI** = global profile index (integer P). The prior/subsequent profiles P−1 / P+1
are used for corroboration; if a neighbor index is missing, the nearest earlier/later profile in
time serves. Quoted depths are approximate.


## See also

- `PP05_QCAnalysis.md` — the upstream pp05 QC manifest (tiered exclusions, suspect/fail ranges).
- `PostProcessing.md` — the full redux → ppNN pipeline overview.
