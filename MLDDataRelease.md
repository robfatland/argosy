# MLD Training Set — Zenodo Release & Versioning

Record of the Zenodo publication of the human-labeled MLD training set, and the repeatable
procedure for cutting future versions. This is a working doc in the repo (not part of the
Jupyter Book).

## DOIs

- **v1 DOI (this release):** `10.5281/zenodo.23650419`
- **Concept DOI (all versions, cite this for the living dataset):** `10.5281/zenodo.23650418`
  *(confirmed on the Zenodo record page — "Cite all versions". Becomes a resolvable link once
  v1 is published.)*

Record page: https://zenodo.org/records/23650419

## What was published (v1)

Single-annotator (Rob Fatland, `who = R`) human MLD labels on OOI RCA shallow-profiler pp06
profiles, as **training data** for a 1-D CNN. No model, no model output, no synthetic data.

Bundle (8 files):

- `mld_labels_{sb,oo,ab}.csv` — the labels. `sb` 2,212 / `oo` 1,824 / `ab` 2,284 rows
  (6,320 total; 4,362 with an MLD value, 1,958 no-MLD/no-data). Columns include folded-in
  `ascent_start`/`ascent_end` (UTC).
- `profile_index_{sb,oo,ab}.csv` — the labeled-profile slice of the OOI-CabledArray profile
  index (`gpi` → UTC `start`/`peak`/`end`).
- `README.md` — data dictionary, sampling summary, UTC/Zulu note, versioning.
- `METHODS.md` — premise, stratified 5-day-block sampling rationale, annotator caveat,
  gpi/profileIndices provenance, code pointers, version change log.

Metadata used: Resource type = Dataset; License = CC-BY-4.0; Version = `v1`; Community =
`nsf-ooi`; keywords (mixed layer depth, MLD, shallow profiler, OOI, RCA, training data, ...);
related identifiers linking the argosy repo and the OOI-CabledArray/profileIndices repo.

## Source material locations

- **Staging bundle (canonical, this laptop):** `~/mld_zenodo_release/v1/`
- **Drag-upload copy:** `~/D/mld_zenodo_v1/` (= Windows `Downloads\mld_zenodo_v1\`)
- Deliberately kept out of both `~/argosy` and `~/ooi` to avoid cluttering the repo and the
  data tree. Regenerable from the label CSVs in `~/ooi/<site>/metadata/annotations/` plus the
  profile indices in `~/ooi/<site>/profileIndices/`.
- Label-generation code (not shipped in the record, linked from it): `MLD.py`,
  `PreSelectProfiles.py`, `MLDAnnotationPlan.md` in https://github.com/robfatland/argosy
- gpi / profile-index source: https://github.com/OOI-CabledArray/profileIndices

## How to cut the next version (vN+1)

The dataset grows as more profiles are labeled. Each expansion is a **new version of the same
Zenodo record**, preserving the concept DOI and minting a fresh version DOI.

1. Re-stage into a new folder, e.g. `~/mld_zenodo_release/v2/`:
   - Copy the current label CSVs from `~/ooi/<site>/metadata/annotations/`.
   - Rebuild `profile_index_<site>.csv` for the (now larger) labeled gpi set, and re-fold
     `ascent_start`/`ascent_end` onto the label rows (same scripts/process as v1).
2. Update `METHODS.md` → "Version change log" with the new date, what was added, and new
   totals. Update the counts in `README.md`.
3. Copy the bundle to `~/D/mld_zenodo_v<N>/` for dragging.
4. On the Zenodo record page click **"New version"** → upload the new files → set Version =
   `vN` → Publish. The concept DOI is unchanged; a new version DOI is issued.
5. Update the DOIs/counts in this file.

## Status / follow-ups

- [x] Reserve + save draft (DOIs above).
- [x] **Submitted for review to the `nsf-ooi` community** (publishes on curator acceptance).
      Awaiting curator action — may show "in review" for a while; the DOI goes live on accept.
- [x] Add a pointer in `ArgosyOverview.md` → "Pointers to Key Actions".
- [x] Log the release in `DevelopmentLog.md`.
- [ ] Confirm the record shows "published" once the curator accepts; concept DOI becomes a
      resolvable link at that point.
- [x] profileIndices attribution confirmed: **Joe Duprey** and **Wendi Ruef** (UW / OOI RCA).
      Named in METHODS.md provenance; also added as contributors in the Zenodo wizard.
