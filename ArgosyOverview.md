---
title: "Argosy"
author: ""
date: ""
---

\newpage


# Argosy Overview


**Argosy** is an ocean science research narrative in book form; and at the same time it is a working environment for analysis of data. The starting point of this analysis focuses on data from the OOI Regional Cabled Array shallow profilers and expands to other data sources. The main idea is that raw ocean observation data is transformed and subjected to comparative analysis. 


**Argosy** has a considerable number of 'moving parts', so the uninitiated reader is encouraged to persevere as the project framework takes shape. For example, just what and where are shallow profilers? A shallow profiler is a cluster of about fifteen sensors suspended in the water column at a depth of 200 meters, the limiting depth of sunlight penetration into the ocean. We consider three shallow profiler installations located off the coast of Oregon referred to (with abbreviations) as Oregon Slope Base (`sb`), Oregon Offshore (`oo`) and Axial Base (`ab`). Each of these sensor clusters ascends on a cable to within 5 meters of the surface and then retracts back down to its mooring at 200 meters, completing one profile of the upper part of the ocean water column at each respective site. This sensor profile is repeated nine times each day, generating raw source data to subsequently be processed and analysed. The processing work is consequently divided into two phases. 


- **Phase 1**: A pipeline from raw to 'analysis ready' data. 
- **Phase 2**: Interpretive data analysis: Concerning both *what the ocean is like* in an average sense; and *what anomalies* might be detected and interpreted.


This is an example reference: {cite}`nash2005`.


The Argosy repository is published as a **Jupyter Book** (readable narrative) and a
**working research repository** (scripts + planning notes). The GitHub landing page is
`README.md`; the book's ordered narrative is defined by `_toc.yml`.

## Who are you? (routing)

- **Arthur — science reader:** read on below, then follow the Jupyter Book chapters. Science narrative, not computing machinery.
- **Chuck — collaborator:** finish this, then head to **`DeveloperGuide.md`** (technical: filesystem layout, workflow tasks) and also `CodeManifest.md` (the file inventory).
- **Angus — an external researcher using the work:** Begin at **`SETUP.md`** (environment +
  public data access), then `DeveloperGuide.md`, then `Publishing.md` for citation/DOIs.
- **Maggie — OOI FB / DSC:** this overview plus the Jupyter Book give the purpose-and-scope picture; and you can follow the above user trajectories of course. For usability feedback on OOI data-access tools (concrete friction points for the DSC), see **`OOIUsability.md`** (a working doc in the repo, not part of the published book).

>Note: Operational commands (build/publish the book, per-file PDF export, standalone widgets) are
kept in the `operational-recipes` steering file, not here.

\newpage


## Quick Reference: Pointers to Key Actions


- **Building PDFs**: See the "Building the PDF" section below in this file. Per-file PDF and book publish commands are in the `operational-recipes` steering file.
- **Data file paths**: Always obtain via `ooipaths.py` (`import ooipaths as op`; `op.redux_dir(year, site)`, `op.postproc_dir(pp, year, site)`, etc.). Per-site layout `~/ooi/<site>/...`; never hardcode. See `PostProcessing.md` → "Recap of the data filesystem logic".
- **S3 backup (syncing ooinet)**: See `DataOps.md` → "S3 sync: data to AWS object storage"
- **Generating pp05 manifest**: `python postprocess_pp05.py` — see `PP05_QCAnalysis.md`
- **Adding sensor exclusions**: Edit `~/argosy/sensor_exclusions.csv` — see `PostProcessing.md` → "Sensor exclusions"
- **Localhost disk management**: WSL vhdx compaction, free space checks — see `DataOps.md` → "Localhost Data Management"
- **Running curtain plots**: Vis.ipynb curtain plot cell — see `Visualization.md`

\newpage

# Argosy Project Overview

This document is the primary entry point for `argosy` documentation. It describes the project, its purpose, and references the companion documentation files.


## Documentation Files

Documentation is split across focused markdown files. The book's reading order is defined by
`_toc.yml`; the complete file inventory (code, data, notebooks) is in `CodeManifest.md`.
Files are grouped below the same way the book is: Orientation, Phase 1, Phase 2, Reference,
and Working docs (repo-only, not in the published book).

**Orientation**
- `ArgosyOverview.md` — (this file) START HERE: what argosy is, persona routing, key-action pointers
- `OOIObservatory.md` — OOI observatory: sites, challenges, glossary, reference websites
- `RCAWritLarge.md` — Broader Regional Cabled Array context
- `OOIFAQandGeneralInfoSummary.md` — OOI FAQ / general info
- `SensorTable.md` — Sensor table, column descriptions, per-sensor notes (`sensortable.csv`)
- `SETUP.md` — Getting running: environment install, public S3 data access
- `DeveloperGuide.md` — Technical map: filesystem layout, workflow tasks 0–6, OOINET ordering, filename anatomy (absorbs the former Workflow.md)

**Phase 1 — Pipeline (raw → pp06)**
- `Sharding.md` — Sharding details, shard filenames, profile metadata, midnight/noon
- `PostProcessing.md` — redux → ppNN pipeline: pp01/pp02, pp05/pp06 filters, exclusions, QC
- `PP05_QCAnalysis.md` — pp05 methodology: three-tier exclusion, suspect ranges, manifest design
- `VectorData.md` — Vector sensor integration (velocity, spectral irradiance, spectrophotometer)
- `DataOps.md` — S3 layout/backup/sync/restore, localhost WSL vhdx disk management

**Phase 2 — Analysis**
- `Visualization.md` — Bundle plots, curtain plots, animations, midnight/noon annotation
- `Analysis.md` — Derived oceanographic parameters, exploration ideas, SGA methodology
- `SpectralGraphAnalysis.md` — Module-by-module guide for the SGA notebook
- `InternalWaves.md` — Internal wave analysis: terminology, physics, plan
- `TidalAnalysis.md` — Tidal prediction (TPXO10), start-depth correlation, blowdown events
- `ColumbiaPlumePlan.md` — Columbia River plume detection plan (+ satellite cross-comparison)
- `Umbrella.md` — Expansion beyond the shallow profiler: other data resources

**Reference**
- `CodeManifest.md` — Complete inventory of code, data, and documentation
- `OOINETSlopeBaseDataStatus.md` — OOINET data availability status for Slope Base

**Working docs (in the repo, NOT in the published book)**
- `DevelopmentLog.md` — Goals, narrative, open topics, pending, Next
- `SessionState.md` — Machine-readable session state for AI continuity
- `DeveloperGuide.md` recipes live in the `operational-recipes` steering file
- `Publishing.md` — Open-science / DOI archiving plan (Zenodo, Figshare, OSF)
- `VisQC.md` — Visual QC workflow (cline review) design
- `Testing.md` — Test definitions (SGA synthetic validation, IW incompressibility)
- `CoincidencePlans.md` — Anomaly detection: auto/hetero coincidence plans
- `pp06ErraticFilterPrompt.md` — Design notes for the pp06 erratic filter
- `OOIUsability.md` — Usability notes on OOI data-access tools (OOINET etc.); DSC feedback
- `poster/AGUPoster.html` — AGU poster (standalone artifact)
- `DevelopmentLog.md` — Red zone goals, umbrella goals, development narrative, open topics, pending ideas, Next prompt section


## Introduction


This `argosy` repository is a Jupyter book on the analysis of oceanographic data.


This markdown file is project documentation; also used to develop prompts for a Coding Assistant.
I sometimes refer to this as 'CA'. $CA_0$ was Q Developer (AWS) with Claude Sonnet. 
$CA_1$ is the more current agentic `kiro` also from AWS integrated with a customized version of
the VS Code IDE. 


This document's features include:


- description of the `argosy` project
- summary of particular Ocean Observatories Initiative (OOI) data resources
- description of data acquisition, cleaning and visualization workflow
- reference to additional markdown files in this repo
    - `Analysis.md`: Data exploration ideas
    - `Umbrella.md`: Expansion perspective (see glossary in `OOIObservatory.md`)
    - `VectorData.md`: Discussion of vector sensor integration (velocity, spectral irradiance, spectrophotometer)
- logs development, tracks train of thought / next steps (see `DevelopmentLog.md`)
- end of `DevelopmentLog.md` is a `tail` prompt
    - Heading is `## Next`
    - Usually read by the CA upon a prompt in the session box
    - Completed prompts are integrated into the log


### Publishing the `argosy` Jupyter book


The `argosy` repo is a Jupyter book. It is amenable to **build** commands: 
`jupyter-book` and `ghp-import`. Typical build:


```
cd ~/argosy
jupyter-book build .
ghp-import -n -p -f _build/html
git pull
git add .
git commit -m 'commit comment'
git push
```


The published [Argosy Jupyter Book link](https://robfatland.github.io/argosy/intro.html)


## Python libraries


- Using `miniconda`
- Install `matplotlib`, `pandas`
- Install `xarray` and `netcdf4`
- jupyter lab/book
- Need: libraries for tidal data


## AI Guidelines


This project concerns organizing and exploring oceanography data starting with 
data from the Ocean Observatories Initiative Regional Cabled Array shallow profilers. 
The idea is to translate source data to an interpretable format; and then to 
visualize, analyze, and interpret this data.


This `argosy` repo exists in the WSL home directory on a Windows PC. Within 
`argosy` we have a Jupyter Book structure with additional files superimposed. 
The order of the day is to build the analysis machinery; writing a Jupyter Book
proper will follow later. 


The Python interpreter associated with execution of code is a `miniconda` 
installation. (Some tidying of environments is called for.)


There are two interactive environments in play here: First a Jupyter lab via
browser; and second the VS Code IDE variant `kiro` with the built-in AWS AI
coding assistant built in. 


A code module, say `dosomething.py`, is often intended for translation to a Jupyter
notebook cell.


As a general principle: Updates and advances should be reflected in this markdown
file or in related files that are pointed to here.


The **Next** section at the end of `DevelopmentLog.md` is used to stage prompts for `kiro`.
An example prompt in the IDE might then read: 'Follow the Next prompt in `~/argosy/DevelopmentLog.md`.'


## Building the PDF

To generate a single PDF from all documentation markdown files:

```bash
cd ~/argosy
pandoc \
  ArgosyOverview.md \
  OOIObservatory.md \
  SensorTable.md \
  DeveloperGuide.md \
  Sharding.md \
  Visualization.md \
  PostProcessing.md \
  DataOps.md \
  PP05_QCAnalysis.md \
  SpectralGraphAnalysis.md \
  TidalAnalysis.md \
  InternalWaves.md \
  CoincidencePlans.md \
  VectorData.md \
  Analysis.md \
  Umbrella.md \
  OOINETSlopeBaseDataStatus.md \
  Testing.md \
  CodeManifest.md \
  DevelopmentLog.md \
  -o argosy.pdf \
  --pdf-engine=xelatex \
  -V geometry:margin=1in \
  -V fontsize=11pt \
  --toc \
  --toc-depth=2 \
  -H _header.tex
```

To build a single-file PDF (e.g. `X.md`):

```bash
cd ~/argosy
pandoc X.md -o X.pdf --pdf-engine=xelatex -V geometry:margin=1in -V fontsize=11pt -H _header.tex
```

Prerequisites: `pandoc`, `texlive-xetex`, `fonts-dejavu`.
