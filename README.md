# argosy

A cloud-forward workflow and analysis environment for the **OOI Regional Cabled Array
shallow profilers** — taking raw ocean-observatory data through a sharded,
quality-controlled, analysis-ready form and into oceanographic analysis.

Argosy is **dual-purpose**: it is both a published **Jupyter Book** (a readable narrative
of the science and the machinery) and a **working research repository** (scripts, data
pipeline, and planning notes). This README is the 30-second front door.

## Start here

- **New to the project?** Read **`ArgosyOverview.md`** — it explains what argosy is and
  routes you based on who you are.
- **Jupyter Book:** https://robfatland.github.io/argosy/intro.html
  — *note: the published book was last built a while ago and is currently stale; it is being
  refreshed.* In the meantime the markdown docs in this repo are the current source of truth.
- **Kindred example** (the model we admire): Ryan Abernathey's *Physical Oceanography*
  Jupyter Book — https://earth-env-data-science.github.io/ (and https://ocean-transport.github.io/).

## Who is this for?

- **Arthur Casual** — a science reader: what is this and why does it matter → the Jupyter Book / `ArgosyOverview.md`.
- **Maggie Glass** — OOI Facilities Board / Data Systems Committee: oversight & credibility → the Jupyter Book + `ArgosyOverview.md`.
- **Angus Neversee** — an external researcher who found this repo and wants to *use* it → `SETUP.md` (get running, public data access) then `DeveloperGuide.md`.
- **Chuck Boom** — a collaborator working on the machinery → `DeveloperGuide.md` (technical map) + `CodeManifest.md` (file inventory).

## What argosy does

Argosy begins with the **Oregon Slope Base** shallow profiler and is built to expand to
**Oregon Offshore** and **Axial Base**. Work is organized in two phases:

- **Phase 1 — Pipeline:** raw OOINET data → sharded profiles (`redux`) → quality-controlled
  analysis-ready datasets (`pp06`).
- **Phase 2 — Analysis:** anomaly coincidence, residual climatology, spectral graph analysis,
  internal waves, Columbia River plume detection, and cross-comparison with satellite data
  (NASA PO.DAAC SST/SSS/ocean color).

## Data

Data lives outside this repo (`~/ooi`, mirrored to a public S3 bucket `s3ooi`); the repo holds
code, documentation, and the Jupyter Book. See `SETUP.md` for public data access and
`Publishing.md` for open-science archiving / DOI plans.
