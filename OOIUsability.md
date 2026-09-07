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
