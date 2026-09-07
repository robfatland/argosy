# Publishing & DOIs (open-science archiving)

Working doc (not in the Jupyter Book TOC). Captures how to publish argosy for open
science with durable, citable identifiers.

## Why (motivation)

- OOI Facilities Board oversight has expressed interest in publishing this work openly.
- Putting data on an S3 bucket is not durable citability: **the S3 copy lasts only as
  long as the bills are paid.** A DOI-issuing archive is the persistence hedge.
- Pushing the repo to GitHub gives visibility but a GitHub URL is not a stable citation.
- Two complementary mechanisms (both worth using):
  - **By reference** — mint a DOI that points at a snapshot of the GitHub repo (code).
  - **By upload** — deposit the actual artifacts (poster PDF, an analysis-ready data subset).

## Options

### Primary: Zenodo (recommended)
- CERN-operated, free, the de facto standard for software + data DOIs. Covers BOTH axes.
- **By reference (code):** enable the Zenodo↔GitHub integration; each GitHub *release*
  is auto-archived and gets a versioned DOI plus a "concept DOI" spanning all versions.
- **By upload (artifacts):** deposit the AGU poster PDF and a data subset directly; each
  gets its own DOI. Records up to ~50 GB.

### Secondary: Figshare (redundant, extra visibility)
- Similar to Zenodo for figures/posters/datasets; strong discoverability. Redundant to
  Zenodo but a good low-cost visibility action, especially for the poster.

### Parked (do-or-don't — see Open Topics): OSF (Open Science Framework)
- Project hub tying repo + data + poster + wiki together with DOIs. Decide later whether
  the project-hub model is worth the added surface.

### Also worth knowing
- **Software Heritage** — archives the *entire* git history (not just releases), issues
  SWHIDs. Free complement to Zenodo for long-term code provenance.
- **Dryad** — curated data repository (curation fee); more formality than needed now.

## Plan of record

- **Code:** Zenodo by-reference via GitHub releases (concept + versioned DOIs).
- **Poster:** deposit the AGU poster PDF to Zenodo (by upload) so its QR code / citation
  resolves to a durable DOI landing page; optionally mirror to Figshare for visibility.
- **Data:** publish the **postproc subset**, not raw. Rationale: raw `ooinet` is ~204 GB
  (S3 archive, legacy keys); postproc is compact — sb is ~15 GB now, with Oregon Offshore
  (`oo`) and Axial Base (`ab`) still to come (so plan for ~3× that). Deposit/reference the
  postproc tier as the analysis-ready, citable dataset.
- **OSF:** deferred (Open Topic).

## Steps when ready (to be verified & recorded here on first run)

1. Tag a GitHub release of `argosy`.
2. Enable Zenodo GitHub integration for the repo → confirm the release DOI is minted.
3. Upload the poster PDF to Zenodo → get its DOI → encode that DOI URL in the poster QR.
4. Prepare the postproc data subset for deposit (decide sb-only first vs. all sites).
5. (Optional) Mirror poster to Figshare; (optional) enable Software Heritage.
