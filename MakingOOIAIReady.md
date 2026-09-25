# Making OOI AI-Ready (MOAR)

> Working discussion document. Purpose: seed a conversation with OOI RCA technical staff
> toward an NSF proposal on configuring OOI — starting with RCA — for AI-assisted research.
> Written primarily to sharpen the author's own thinking; a deliberate nod to the OOI
> Facilities Board / Data Systems Committee (DSC) governance audience is included, since
> "interpretable, trustworthy data" is squarely a DSC concern. 


`This material is operational (if philosophical) and is not included as part of the Argosy repo Jupyter Book.`

## The leading question, answered first

**Is OOI's data system, as it stands, "AI-ready"? And if not, how much running room is there?**

Short answer: **OOI is AI-*accessible* but not AI-*ready*, and the running room is the opportunity.** OOI was architected (2000s–2010s, pre-genAI, pre-"foundation model") around a human-centric premise: acquire data reliably, expose
it through interfaces a scientist can browse and download, and let domain experts do the
interpretation. That premise produced an impressive delivery system (Data Explorer, THREDDS/OPeNDAP, M2M, JupyterHub, the Raw Data Archive, Gold Copy S3, QARTOD flags). But "a human can get the data" is a very different bar from "a machine-learning pipeline or an LLM-driven agent can consume, trust, and reason over the data at scale." On this second bar OOI
scores low because the system *aspires* to that but uses up all of its calories before it gets there.


Premise: **After 14 years, the holy grail of OOI —
interpretable, trustworthy, analysis-ready data that a newcomer can pick up and believe — is not attained.** The last mile (from
bytes to trusted, labeled, ML-consumable, provenance-carrying products) is left to each user to reinvent, in isolation, without shared scaffolding. AI-readiness is a discipline that closes the last mile and solves the trustworthiness
problem in the process; so "**AI-readiness and trustworthiness are the same investment.**"

## The grand picture (briefly, once)

The end state worth imagining: a researcher (or an autonomous agent acting for one) asks a
question in natural language — *"show me candidate water-mass intrusion events at Slope Base in
2019 and corroborate them across the shallow profiler, the deep profiler, and satellite SST" —
and the system retrieves analysis-ready data with attached uncertainty and provenance, runs or
composes the right analysis, cites the methods and prior literature, flags what it is unsure of,
and returns a result a human can audit line-by-line. Multi-modal fusion across OOI's concentric
sensor rings — shallow profiler (SP), deep profiler (DP), fixed platforms, and the geophysical
suite (seismic, hydrophone, **DAS**, ADCP, tilt, bottom-pressure, vent temperature) — becomes a
first-class capability rather than a heroic one-off.

That is the destination. **This document is deliberately not about the destination.** It is about
the first few phases of road that a funded RCA team could start building *tomorrow*, each of which
delivers standalone value even if the grand vision never fully arrives. Multi-modal fusion is
acknowledged as the ultimate goal and then set aside; the near-term story is single-modality,
tractable, and cumulative.

## The cost of status quo

Every OOI science user today independently:

- **rediscovers data quality** QARTOD flags exist, but "which profiles are actually usable for
  my purpose" is re-derived by every user from scratch. There is no shared, versioned,
  machine-readable "good data" layer. 
  - Example: Argosy has a data manifest: built by hand, one instrument class, three sites
- **rebuilds the same preprocessing workflow**
  - Reshaping the native `obs`-indexed, multi-sensor,
  multi-month NetCDF files into per-profile, analysis-ready units: Repeat per User.
  - Argosy's sharding covers this for SPs: Shareable (bird in the hand) because Rob built the scaffolding.
- **cannot easily train models,** because there are no curated labeled datasets, no benchmarks,
  no train/test splits, and no standard way to attach human judgment to observations.
- **cannot let an LLM help,** because the documentation, methods, and provenance are scattered
  across PDFs, wikis, portals, and tribal knowledge — not in a retrievable, grounded corpus.

The compounding cost is **non-reproducibility and eroded trust**: results are hard to audit,
harder to reproduce, and the barrier to entry stays high. Doing nothing is not free; it is a recurring, distributed, invisible tax on every project and a ceiling on what the facility's data can contribute.


The positive inversion: **AI-ready infrastructure yields interpretable, trustworthy data as a
byproduct.** The same metadata, provenance, uncertainty, and labeled-example layers that let a
model train are what let a human (or a reviewer, or a DSC member) *trust* a result. You do not
choose between "AI" and "good science data practice" — they are the same roadmap.

## Building blocks

Rather than a monolithic "AI platform," think in composable building blocks. Each is independently
fundable, independently useful, and ordered so that later blocks depend on earlier ones.

**Block 1 — Analysis-Ready, Cloud-Optimized (ARCO) data.**
Standardized, per-feature data products (not raw dumps) in cloud-native formats (Zarr/NetCDF on
S3), addressable without bulk download, with consistent dimensions/coordinates and rich,
machine-readable metadata (CF conventions + explicit units, QC, provenance). This is the
foundation; nothing to follow works without it.

**Block 2 — A trust layer: QC, provenance, and uncertainty as first-class data.**
Machine-readable quality state per observation (beyond a flag), the processing lineage that
produced each product, and quantified uncertainty. This is the block that turns "delivered" into
"trustworthy," and it is the DSC's natural home.

**Block 3 — Labeled datasets and benchmarks.**
Curated, versioned, human-labeled reference sets (e.g. mixed-layer depth, cline depths, event
catalogs) with documented train/test splits and evaluation metrics — the raw material for ML and
the yardstick for claims. Without shared benchmarks, every ML result is anecdote.

**Block 4 — A retrievable knowledge corpus.**
OOI documentation, method descriptions, sensor characteristics, calibration history, and prior
publications assembled into a grounded, citable corpus an LLM can retrieve over (RAG). This is
what lets AI *assist* rather than hallucinate, and it is cheap relative to its leverage.

**Block 5 — Agentic / tool-using research assistants.**
Only after 1–4: agents that compose retrieval + analysis + citation over the trusted products and
corpus, always producing auditable, human-checkable output. This is the visible payoff, but it is
the *last* block, and it is worthless built on untrustworthy foundations.

**Multi-modal fusion** (learning jointly across SP/DP/platform/geophysical rings, including DAS)
sits above Block 5 as the ultimate goal — explicitly deferred here.

## Phased roadmap (where a funded RCA team puts its effort first)

The discipline: **each phase ships a standalone deliverable and de-risks the next.** Start narrow
(RCA shallow profiler scalar data — the best-characterized, most tractable slice), prove the
pattern, then generalize across instruments and arrays.

**Phase 0 — Pick the proving ground and set conventions (months 0–3).**
RCA shallow profiler, scalar sensors, three sites, the ~10-year record. Define the ARCO product
spec, the metadata/provenance schema, and the labeled-dataset format. Deliverable: a written
standard other instruments can adopt. (argosy has de-facto answers to most of this already — see
below — which is why it is a credible starting point rather than a blank page.)

**Phase 1 — ARCO products + trust layer for the proving ground (months 3–12).**
Produce cloud-optimized, per-profile analysis-ready products for RCA SP scalars, with QC,
provenance, and uncertainty attached, published openly with DOIs. Deliverable: the first OOI data
product a stranger can pick up and *trust* without re-deriving quality. This alone is a
publishable, DSC-relevant contribution independent of any "AI."

**Phase 2 — First labeled dataset + benchmark + a trained model (months 9–18).**
Mixed-layer depth is the ideal first target: physically meaningful, human-labelable, with an
established algorithmic baseline (Holte & Talley 2009) to benchmark against. Produce a
human-labeled MLD reference set, train a model, and publish the *comparison* to the dual
threshold/gradient method as the evaluation. Deliverable: a reusable labeled dataset + benchmark +
model card — the template for cline detection, event catalogs, and beyond. **This is the phase
where "AI" first appears, and it appears as rigorous, benchmarked, trustworthy science.**

**Phase 3 — Knowledge corpus + retrieval-grounded assistant (months 12–24).**
Assemble the OOI/RCA documentation-and-methods corpus and stand up a RAG assistant that answers
questions grounded in it with citations. Deliverable: a lower barrier to entry for every new
user, and the substrate for later agents. Cheap, high-leverage, low-risk.

**Phase 4 and beyond — agentic composition, then multi-modal.**
Only once 1–3 are trusted: tool-using agents that compose the products + corpus into auditable
analyses; then, as the reach goal, cross-modal learning across the concentric sensor rings.

Generalization to the rest of OOI is a *repeat of the pattern*, not new invention: the Phase-0
standard and the Phase-1/2 templates were designed to port to Coastal Endurance, Pioneer, and
Global with the site/instrument specifics swapped in.

## Is argosy a building block? An honest assessment

You asked me not to hold back. argosy is **on track to be a credible Block-1/2/3 prototype for
the RCA shallow profiler slice**, and it is a genuine existence proof that the pattern is
buildable by a small team. But it misses the AI-ready mark in specific, nameable ways, and naming
them is more useful than cheerleading.

**Where argosy hits the mark (and why it matters):**
- **It already produces analysis-ready products, not raw dumps** (redux shards → pp05 → pp06),
  with a per-site, path-centralized layout and a single source of truth for paths (`ooipaths.py`).
  That is Block 1 in miniature.
- **It has a nascent trust layer**: the pp05 manifest is a machine-readable "good data" list;
  `sensor_exclusions.csv` is versioned QC; the sign-off tooling (SignoffQC) is a mechanism for
  attaching *human judgment* to observations — the seed of Block 3's labeled data.
- **It is being built cloud-native-ish**: S3-backed data, an ephemeral-EC2 pipeline, a public
  pp06 tier, an explicit "compute goes to the data" tenet. That instinct is the right one.
- **It takes reproducibility and documentation seriously**: the bicameral Book/processing split,
  the "where do components go?" discipline, DOIs via Zenodo, a documented pipeline. This is the
  cultural half of AI-readiness, and it is often the half that is missing.
- **It is already doing Phase 2 in embryo**: the MLD labeled-dataset-plus-Holte&Talley-benchmark
  plan is exactly the Phase-2 template above.

**Where argosy misses (the honest gaps):**
- **Format is not yet cloud-optimized.** Per-profile NetCDF shards are analysis-ready but not
  ARCO in the Zarr/lazy-access sense; an agent still can't slice across the record without
  fetching many files. The Local/S3 source switch is a step, not the destination.
- **The trust layer is partial and implicit.** pp05 encodes *inclusion* but not *uncertainty*;
  provenance lives in filenames and docs, not in a queryable, per-observation lineage. QARTOD
  flags aren't yet first-class in the products.
- **Metadata is not yet standardized/interoperable.** It's coherent *within* argosy (a real
  achievement) but not expressed in community conventions (CF, ACDD, STAC) that would let *other*
  tools and agents consume it without bespoke glue. This is the single biggest gap between
  "excellent private practice" and "AI-ready infrastructure."
- **No knowledge corpus / retrieval layer yet** (Block 4). The docs are unusually good and
  well-organized — which means argosy is well-positioned to *become* such a corpus — but it isn't
  one yet.
- **Human labels are ad hoc.** SignoffQC and the MLD labeling are the right idea, but there's no
  standardized label schema, inter-annotator provenance, or benchmark protocol yet.
- **Single-instrument, single-array, single-team.** By design — but AI-readiness is partly a
  *governance and standards* problem, and a one-team project can't confer facility-wide
  interoperability by itself. That's exactly why this needs to become a *proposal*, not a repo.

**Verdict:** argosy is a strong, honest **prototype and pattern**, not yet an AI-ready building
block — and that distinction is the proposal's point. It demonstrates that a small team can build
the analysis-ready + trust + labeled-data layers for one slice; the proposal's job is to turn that
demonstrated pattern into *standardized, interoperable, facility-scale* infrastructure. argosy
earns its place as the worked example precisely because its gaps are the general gaps in miniature.

## A candidate science hook (to make the argument concrete)

Proposals need a compelling question that *requires* the infrastructure to answer. A strong
candidate, drawn from this project's trajectory:

**"Does the multi-year shallow-profiler record, made analysis-ready and coupled with the deep
profiler and satellite context, reveal a coherent, corroborated story of water-mass intrusion
along the Oregon margin — and can that story be detected, attributed, and trusted by an
AI-assisted pipeline rather than assembled by hand?"**

This question is well-chosen for the proposal because it is *only tractable with the building
blocks*: it needs analysis-ready multi-year products (Block 1), trustable QC so events aren't
artifacts (Block 2), labeled event examples and a benchmark (Block 3), grounded method/literature
retrieval to attribute mechanisms (Block 4), and eventually cross-instrument corroboration (the
multi-modal reach goal). Water-mass intrusion is physically meaningful, observable in T/S/density
+ BGC signatures, corroborable across SP/DP/satellite, and connects to live questions about
margin ventilation, hypoxia, and the OMZ. It is a question whose *answer* matters and whose
*method* demonstrates the whole roadmap. It also degrades gracefully: even Phase 1–2 alone yield a
publishable intrusion-detection-and-validation result, independent of the full agentic vision.

## Notes, caveats, open questions for RCA

- **Two empirical claims here are this project's observations, not verified facts**: **SSS** is not so good but **SST** validates peak SP data well in many instances.
- **Is the profileIndices metadata (Wendi & Joe) published for deep profilers too, or only shallow?** This affects how quickly DP joins the proving ground.
- **Governance angle for the DSC (Maggie):** the trust layer (Block 2) is where facility
  governance and AI-readiness meet. A DSC that champions machine-readable QC/provenance/uncertainty
  standards would be advancing both trustworthiness and AI-readiness with one policy.
- **Relationship to existing OOI access (Data Explorer, THREDDS, M2M, JupyterHub, Gold Copy S3):**
  AI-readiness is not a replacement for these — it is a *product and metadata layer on top of the
  Gold Copy / raw archive*. The proposal should position it as additive, leveraging the cloud-native
  Gold Copy buckets rather than duplicating delivery.
- **The "start tomorrow" claim rests on argosy** being a running pattern for Phase 0–2. If the
  proposal wants to lead, it should show, not assert — argosy is the show.

---
- **profileIndices covers deep profilers too** (confirmed Sep 2026 against
  `github.com/OOI-CabledArray/profileIndices`): the repo publishes `*PD` deep-profiler
  start/peak/end files (`CE04OSPD`, `RS01SBPD`, `RS03AXPD`) alongside the `*PS` shallow-profiler
  ones, same schema — though DP coverage is sparser (fewer years, gaps) and the repo README still
  describes itself as "Shallow Profilers" only. Implication: the proving ground can extend from SP
  to DP without waiting on new delimiter metadata — DP joins the roadmap sooner than assumed.LD
work (the Phase-2 labeled-dataset-plus-benchmark template).*
