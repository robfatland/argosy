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
- **Data:** publish the **pp06 tier** (the analysis-ready postproc product), not raw and not
  redux. Rationale: raw `ooinet` is ~204 GB (S3 archive, legacy keys) and redux is intentionally
  NOT published (more flawed than pp06). pp06 is compact — **all three sites are now complete and
  in S3** (sb, oo, ab; ~46 GB total). Deposit/reference pp06 as the citable dataset.
- **OSF:** deferred (Open Topic).

## Relationship to the S3 public bucket (Sep 2026)

pp06 is ALREADY publicly downloadable from S3 (`{sb,oo,ab}/postproc/pp06/*`, unauthenticated
read; see `DataOps.md` and the "Public data sharing (S3)" steering rule). But **S3 public-read is
not durable citability** — it lasts only as long as the bills are paid, and egress is owner-billed
(a cost/abuse exposure, guarded by a budget alarm + kill switch). Zenodo is the persistence + DOI
hedge and the likely long-term home for the durable public pp06 release, offloading hosting and
egress to an open-data service. So the two are complementary: **S3 = live/working access; Zenodo =
durable, citable, cost-offloaded release.** This is `BR.md` open-question 8 ("which data products
should be free, and how bundled?") — reconcile the final bundling decision there.

## Steps when ready (to be verified & recorded here on first run)

1. Tag a GitHub release of `argosy`.
2. Enable Zenodo GitHub integration for the repo → confirm the release DOI is minted.
3. Upload the poster PDF to Zenodo → get its DOI → encode that DOI URL in the poster QR.
4. Prepare the pp06 dataset for deposit. All three sites (sb/oo/ab) now exist in S3 (~46 GB total,
   within Zenodo's ~50 GB record limit) — decide whether to deposit one bundled 3-site record or
   per-site records. Source is `s3://s3ooi/<site>/postproc/pp06/`.
5. (Optional) Mirror poster to Figshare; (optional) enable Software Heritage.
6. Once a durable Zenodo pp06 release exists, revisit whether to keep the live S3 public-read
   policy or point reusers at the Zenodo DOI instead (reduces owner-billed egress). See BR open-Q 8.
