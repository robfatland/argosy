## Intellectual support: do published products ship code and documentation?


Path curation: Does a published record also carry the code and documentation? Here from six of the 24 Zenodo records are AI-pulled summaries:


**1. High support — code + documentation together.**
*Parsing NMEA Data from a Nortek Signature 500 (Voulgaris).* This record is drawn
from a shallow-profiler-adjacent instrument, and it is the most complete: the archive bundles
MATLAB code (`.m`), raw and parsed data (`.dat`, `.asv`, `.mat`), **and** a `.pdf` describing
the parsing procedure. A downstream user gets the data, the tool that produced it, and prose
explaining both. Gold star.


*External link:* none — no GitHub or other repository link in the record (it is itself a software-type record, self-contained).


**2. High support — executable notebooks alongside data.**
*10 Years of QC Surface Weather Measurements, Coastal Endurance (Wingard).* A 572 MB dataset
that ships `.ipynb` Jupyter notebooks and a MATLAB Live Script (`.mlx`) next to the `.nc`
data files. The QC and gridding logic is not just described, it is runnable. This is the
pattern argosy itself should follow: publish the curated NetCDF **and** the sharding /
post-processing notebooks that generated it.


*External link:* yes — the description links out to GitHub (`github.com/cwingard/...`), and the record is flagged `isPartOf` a companion Zenodo record. There is more stuff behind the data.


**3. Moderate support — processing code, config-driven.**
*NSF-OOI Native Resolution Conductivity & Temperature (Black).* The archive pairs the data
`.zip` with `.yaml` configuration files, and the record is one of a family of Black/OSU
products whose descriptions point to a shared processing codebase. The configuration travels
with the data, which makes the product reproducible *if* the reader can obtain the referenced
code — shy of bundling it directly.


*External link:* yes (partial) — no GitHub link, but the description cites two companion Zenodo DOI records (`doi.org/10.5281/zenodo...`), so there is more stuff in the same family, just not the code itself.

**4. Moderate support — domain code in a second language.**
*Direct Covariance Surface Stress and Heat Fluxes (Edson).* Ships MATLAB `.m` code and an
`.rtf` note with the flux data. The flux computation is genuinely non-trivial, and shipping
the `.m` files means the method is inspectable. It falls short of full support mainly in
documentation depth (an `.rtf` note rather than a methods document).


*External link:* none — no GitHub or other repository link; the `.m` code is bundled in the archive rather than pointed to elsewhere.


**5. Documentation-only — guidance without data.**
*OOI BGC Sensor Best Practices Guide (Palevsky).* A pure `.pdf` publication-type record: no
data at all, only documentation. This is the inverse failure mode — maximal intellectual
context, nothing to apply it to directly — but it is valuable precisely because it is the
written knowledge that most data records omit. Path curation needs both halves; this record
is one half done well.


*External link:* none — no GitHub or other repository link in the record.


**6. Low support — bare data, minimal context.**
*A 7-year Validated Nitrate Dataset, Global Irminger Sea (Reed).* Two `.nc` files, a short
(~1,400-character) description, and no code or documentation files in the archive. It is a
clean, citable dataset, but a reader cannot reconstruct how it was built or re-run the QC
without contacting the author. Several Reed/WHOI nitrate and ADCP records share this profile
(data-only `.nc`, terse metadata), as do the two Ragland ambient-sound records (a single
`.nc` or `.zip` with ~220-character descriptions).


*External link:* none — no GitHub, repository, or companion-record link at all. The data stands alone.


---

## CF-compliance of the pp06 NetCDF files: how much work to publish-ready?

Context for path curation: before pp06 goes up as a Zenodo product, the NetCDF files should
pass a CF (Climate and Forecast) conventions check. This is an assessment of the gap, based on
inspecting live pp06 files across the `ab` site (temperature, salinity, density, backscatter,
par, nitrate, dissolvedoxygen) with `xarray` (`decode_cf=False`).

**Bottom line:** the files are already most of the way to CF-1.x compliance — they inherit
solid variable-level metadata from OOI's original NetCDF. Closing the gap is modest and almost
entirely mechanical attribute surgery, not data surgery.

### What's already there (the hard part, done)

Each variable already carries the attributes CF cares about most:

- `standard_name` from the CF standard-name table (`sea_water_temperature`,
  `sea_water_practical_salinity`, `sea_water_density`,
  `volume_backwards_scattering_coefficient_of_radiative_flux_in_sea_water`,
  `downwelling_photosynthetic_photon_flux_in_sea_water`, etc.)
- `units` in udunits form (`degrees_Celsius`, `kg m-3`, `m-1`, `umol L-1`, `1` for salinity)
- `long_name`, `_FillValue`, `comment`
- `time` done correctly: `standard_name=time`, `units=seconds since 1900-01-01`,
  `calendar=gregorian`, `axis=T`
- `depth` with `units=m`, `axis=Z`
- `ancillary_variables` pointing at the QARTOD results

### The gaps (the work)

1. **No global `Conventions` attribute.** CF requires `Conventions = "CF-1.8"` (or similar). One
   line. This alone is why a checker would flag the file as "not CF" even though the content is
   largely compliant.
2. **Broken `coordinates` attribute.** Every data variable says `coordinates: lat depth lon time`,
   but there are **no `lat` or `lon` variables in the file** (only `time` and `depth` exist). A CF
   checker fails on this: a `coordinates` attribute must reference variables that exist. Two fixes:
   (a) add scalar `lat`/`lon` coordinate variables (the profiler is at a fixed mooring, so a single
   lat/lon pair is correct and improves the file), or (b) rewrite `coordinates` to `"depth time"`.
   Option (a) is better and still cheap.
3. **`depth` is positive-down but lacks `positive`.** CF needs `positive = "down"` on a Z coordinate
   measured as depth. One attribute.
4. **Inconsistent `_FillValue` across files.** `depth` is `-9999999.0` in some files and `nan` in
   others; `par` uses `-100000000.0`. Not strictly a CF violation, but worth normalizing while in
   there.
5. **Minor global metadata** CF *recommends* (not requires): `title`, `institution`, `source`,
   `history`, `references`, `featureType`. Since each file is a single profile along time, declaring
   `featureType = "trajectoryProfile"` (or `"profile"`) would make it a proper CF Discrete Sampling
   Geometry — optional but valuable for a published product.
6. **No CF checker is installed** (`compliance-checker` is absent from the `argosy` env), so there is
   currently no automated verification. Installing it is part of doing this properly.

### Effort estimate

The transformation is per-file, deterministic, and vectorizable — the same shape as
`postprocess_pp06_filter3.py` (open, tweak attrs, write temp, replace). Attribute surgery, not
data surgery.

- **Core script (items 1–3): ~half a day.** A `postprocess_pp06_cfify.py` that walks the pp06 tree,
  adds `Conventions`, adds scalar `lat`/`lon` (from site metadata in `ooipaths`/`sensortable`), sets
  `depth:positive="down"`, and fixes the `coordinates` string. Most of the time goes into getting
  lat/lon per site right and a `--dry-run`.
- **Global metadata + DSG `featureType` (items 4–5): ~another half day** if the goal is a clean
  publishable product rather than just checker-passing.
- **Verification:** install `compliance-checker`, run `compliance-checker --test=cf` over a sample
  from each site/year/sensor. A few hours including fixing whatever it flags.

**Total: roughly 1–1.5 days** to get from "CF-ish" to "passes `compliance-checker --test=cf`
cleanly," most of it in writing and validating one batch script rather than in any conceptual
difficulty. Runtime cost is trivial — metadata rewriting, similar to Filter 3's pass.

**Scope caveat:** this touches every pp06 file across all four sites and all years
(`ab`/`oo`/`sb`/`synthetic`, 2014–2026). The script should be idempotent and `--dry-run`-first, and
because it rewrites in place, the S3 mirror is the backstop before a full run.

*(Tracked in `DevelopmentLog.md` → Open Topics as "Address CF-compatibility".)*
