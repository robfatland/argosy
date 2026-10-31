# OOI Usability Notes

## Introduction

This document collects usability observations about OOI data-access tools and interfaces:
what works well, what causes friction, and where improvements would help scientific users.
It is written from the standpoint of hands-on use of the OOI systems in the course of the
argosy project (building the shallow-profiler data pipeline).

The intended audience includes the argosy team and, in particular, feeds the OOI Facilities
Board / Data Systems Committee (DSC) role (persona: **Maggie Glass**). The DSC evaluates and
recommends improvements to OOI data services that lead to more efficient and effective
scientific use of OOI data, so concrete, reproducible friction points recorded here are
meant to be actionable input to that process.

Each interface gets its own section. Within a section: observed issues are logged as prose,
and follow-up work is tracked under **Open Topics**.

See also `OOIFAQandGeneralInfoSummary.md` for OOIFB/DSC background and the OOINET vs. Data
Explorer distinction, and `DeveloperGuide.md` → "ordering and downloading from OOINET" for
the current ordering workflow.


## OOINET

OOINET is the legacy OOI user interface for browsing and ordering data. (Data Explorer is the
newer interface intended to replace it.) The argosy pipeline currently orders raw source
NetCDF through OOINET's Data Navigation table.

### Issue: parameter-selection in the order dialog is opaque

The Download button on the Data Navigation table raises a temporary order-generation window
that offers the option to download only certain parameters rather than all of them. This is
potentially valuable: restricting the parameter set makes the order volume much smaller, and
therefore the order faster to stage and download. However, it is not clear which parameters
are actually necessary for a given downstream use. The result is guesswork — a user cannot
easily tell which parameters can be safely dropped without risking loss of something needed
later, so the pragmatic (but wasteful) default is to download everything.

### Open Topics

1. **Winnow the parameter list to what argosy actually uses.** Review the per-instrument
   parameter options in the OOINET order dialog (starting with CTD) and determine the minimal
   set the pipeline actually consumes, so future orders can select only those. Goal: a
   documented, per-instrument "required parameters" list that shrinks order volume without
   losing needed data. (Sharding currently keys on specific science variables — e.g. CTD
   yields temperature, salinity, density, dissolved oxygen — so those, plus whatever
   coordinate/time/depth fields the pipeline needs, are the starting point.)

2. **Provenance: how to make use of it (define it first).** Orders can optionally "Include
   Provenance." Before deciding whether/how to use it, we need a working definition of what
   OOI provenance records contain and what questions it can answer. Then: is it worth
   including in argosy orders, and if so, how would the pipeline surface or store it?

3. **Annotations: how to make use of them (define it first).** Orders can optionally "Include
   Annotations." Similarly, define what OOI annotations are (human/QC notes attached to data —
   e.g. the RCA data team's flag of a clogged conductivity cell), then decide how argosy
   should consume them. Candidate: fold relevant annotations into the QC/exclusion workflow
   (`sensor_exclusions.csv`, pp05) rather than treating them purely as read-only metadata.


## Data Products page (oceanobservatories.org/data-products)

The public Data Products page (`https://oceanobservatories.org/data-products/`, with its
expanded companion `.../data-products-complete-list/`) catalogs the ~200 science data products
OOI measures or derives. It is organized by **sampling regime** — Air-Sea Interface,
Seafloor/Crust, Water Column — and lists each product as a human-readable name plus a 7-letter
product code (e.g. `TEMPWAT`, `PRACSAL`, `VELPROF`).

### Issue: products are undiscoverable by instrument or by scientific topic

Worked example — the question "How would I find ocean current data from this page?" A user
thinking in terms of **instruments** ("ADCP") or **topics** ("currents") finds nothing: the
page contains no "ADCP" link and the word "current" never appears. The data is present but only
under physics-based product names in the Water Column group:

- Velocity Profile — `VELPROF` (the ADCP profile product)
- Turbulent Velocity Profile — `VELTURB`
- Mean Point Water Velocity — `VELPTMN` (single-point current meter)
- Turbulent Point Water Velocity — `VELPTTU`
- Vertically Averaged Horizontal Water Velocity — `IESAHWV` (inverted echo sounder)
- Echo Intensity — `ECHOINT` (ADCP-derived companion)

The page provides no bridge from the user's vocabulary (currents, ADCP) to its own vocabulary
(velocity). Three distinct friction points:

1. **No synonym / instrument bridge.** No search box, no "see also," no instrument column. The
   user must already know that currents → "velocity" and that the ADCP is the instrument behind
   `VELPROF`. Confirming the instrument requires leaving for the Instruments page
   (`/instruments/`, where ADCP lives as the VEL/ADCPS/ADCPT instrument classes).
2. **Catalog vs. availability conflation.** The page reads like it should answer "what data are
   available," but it only enumerates what OOI *can* produce somewhere — not what any given site
   actually carries or over what time range. The real availability question is answerable only
   in a *different* tool, Data Explorer (`https://dataexplorer.oceanobservatories.org/`), via
   catalog search filtered by parameter and location.
3. **Grouping by sampling regime, not discipline.** "Water Column" lumps velocity together with
   temperature, nitrate, pH, and ~30 others, so currents do not stand out even once the user is
   on the correct page.

Net effect: a scientist cannot answer "what current data exist, and at which OOI sites?" from
this page. The realistic human path is (a) translate currents/ADCP → "velocity" and scan for
`VEL*`/`IES*` codes; (b) cross to the Instruments page to confirm the instrument; (c) go to Data
Explorer (or the site list, `/site-list/`) to find actual coverage by site and time.

### Open Topics

1. **Discoverability by instrument and topic (DSC-relevant recommendation).** Recommend that the
   Data Products page support the vocabulary users actually bring: add a search/filter box, an
   instrument-class column (or cross-links to the Instruments page per product), and
   topic/discipline tags (e.g. "currents," "carbonate system," "optics") alongside the
   sampling-regime grouping. Minimum viable fix: a visible note that the page is a *capability*
   catalog and that per-site availability lives in Data Explorer, with a direct link. Logged from
   the "find ocean currents" worked example.
