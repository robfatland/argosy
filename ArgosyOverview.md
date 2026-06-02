---
title: "Argosy"
author: ""
date: ""
---

\newpage

## Pointers to Key Actions

Operational procedures are documented in their respective files. This section
provides a quick-reference index.

- **Building the PDF**: See [Building the PDF](#building-the-pdf) section below in this file.
- **S3 backup (syncing ooinet)**: See `PostProcessing.md` → "S3 Backup: Syncing ooinet to AWS"
- **Generating pp05 manifest**: `python postprocess_pp05.py` — see `PP05_QCAnalysis.md`
- **Generating pp01/pp02**: `python postprocess_special_profiles.py noon|midnight` — see `PostProcessing.md`
- **Adding sensor exclusions**: Edit `~/argosy/sensor_exclusions.csv` — see `PostProcessing.md` → "Sensor exclusions"
- **Localhost disk management**: WSL vhdx compaction, free space checks — see `PostProcessing.md` → "Localhost Data Management"
- **Running curtain plots**: Vis.ipynb curtain plot cell — see `Visualization.md`

\newpage

# Argosy Project Overview

This document is the primary entry point for the `argosy` project documentation.
It describes the project, its purpose, and references the companion documentation files.


## Documentation Files

This project's documentation is split across the following focused files:

- `ArgosyOverview.md` — (this file) Project introduction, AI guidelines, Python libraries, publishing instructions
- `OOIObservatory.md` — OOI observatory description, sites, challenges, glossary, and reference websites
- `SensorTable.md` — Sensor table with column descriptions, per-sensor notes, and reference to `sensortable.csv`
- `Workflow.md` — File system layout, workflow tasks 0–6, data download details, raw data filenames, degenerate source files
- `Sharding.md` — Profile metadata, reference metadata, sharding details, shard filenames, midnight/noon profiles, TMLD
- `Visualization.md` — Visualization tools: bundle plots, curtain plots, animations, midnight/noon annotation
- `VisNotebookRebuild.md` — Rebuild plan for Visualizations.ipynb bundle/curtain/animation cells (reverted; changes to re-apply)
- `DevelopmentLog.md` — Red zone goals, umbrella goals, development narrative, tactics, CA recommendations, pending ideas, and the Next prompt section


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
    - `Cleaning.md`: Describes data filtering / cleaning
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
  Workflow.md \
  Sharding.md \
  Visualization.md \
  PostProcessing.md \
  PP05_QCAnalysis.md \
  VectorData.md \
  Analysis.md \
  Umbrella.md \
  CodeManifest.md \
  OOINETSlopeBaseDataStatus.md \
  DevelopmentLog.md \
  -o argosy.pdf \
  --pdf-engine=xelatex \
  -V geometry:margin=1in \
  -V fontsize=11pt \
  --toc \
  --toc-depth=2 \
  -H _header.tex
```

Prerequisites: `pandoc`, `texlive-xetex`, `fonts-dejavu`.
