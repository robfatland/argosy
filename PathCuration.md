# Path Curation


## Community-driven publication of OOI data, code and documentation


**Summary:** This memo concerns the *transition problem* of making OOI data more readily usable. The transition is *from* OOI engineering (data organized and available as L1/L2 products) *to* community-driven expansion of available scientific data (L1/L2 and higher level L3+) and tools and documentation under the FAIR paradigm; recognizing the need for a lower barrier to entry. Two suggestions:


- From progress so far (particularly Zenodo): Build out and promote *path curation* guidance
- Implement AI Assistant support (2 possible modes) for researchers 


## Notes on current status


* The "*transition solution*" is already in progress; within the OOI website and on Zenodo (+ Github)
    * Example: I want current data from ADCPs at particular sites. The data products page is organized by physical products; not by science themes or by instrument. To find *current* or *ADCP* data requires hunting around on the website; where eventually I would discover `VELPROF` and related data types. The Data Product Specification is 41 pages (half of this MATLAB code) that seems to produce L1 data... do I need to use this? Furthermore: Several Zenodo records are relevant... does the website refer me to them? 
* The [DSC 2026 Action Item](https://docs.google.com/document/d/11QpakTqgdPrwWmic2K7j2v6IEM_umnRBkBRHmjZShdo/edit?tab=t.0) document reads: "The DSC will [...] reorganize the OOI data products page and make it a more useful, easy to navigate resource. The page will include what qualifies as a community data set, which is likely connected to a published research paper or data paper with DOI. Two categories of data sets will be created/linked: published data sets (PI provides DOI) and research data products without a DOI."
    - "reorganize" is addressed below in terms of an AI assistant
    - "categories of data sets": Suggest revisit this with FAIR principles in mind
* The [data products page](https://oceanobservatories.org/data-products/data-products-complete-list/) is a list of physical products
* As of 24-OCT-2026 there are 24 records (equivalent to *projects*) uploaded to the [Zenodo "NSF-OOI" community](https://zenodo.org/communities/nsf-ooi/)
    * Repos relevant to the current/ADCP/VEL* example above:
        - ooi-data-explorations (Chris Wingard)
        - Parsing NMEA raw Nortek 500 Signature Data (George Voulgaris)
        - Additional repos by Andrew Reed, Craig Risien, Carolina Camargo


## Suggestions


- FB + DSC + PMO: Take on *path curation*: Publishing curated data plus software tools plus documentation
    - Underway at Zenodo (24 publications; see table below)
    - Collect/assess hard, soft pub requirements e.g. CF-compatible NetCDF
    - Assess the Zenodo catalog: How is it going so far?
    - Build community awareness of the path curation plan and pattern
    - Work with scientists to expand out the Zenodo catalog
- Set up an AI assistant associated with oceanobservatories (already in progress?)
    - Define the OOI documentation corpus
        - Include Zenodo
        - Include Interactive Oceans and other affiliate sites
    - RAG-based AI Assistant: Accesses the entire corpus
        - Version 1: Install a dedicated Assistant on the site
            - Benefit is the Assistant can be refined to be very effective
            - Downside is it takes effort to build and has some cost to operate
        - Version 2: Publish the corpus in an AI-consumable form
            - Burden on the User to give their own AI the URL of the corpus
            - Prompt: "Use https://oceanobservatories.org/llms.txt to answer my OOI questions: etcetera"
            - Benefit: Simpler / cheaper than building an Assistant
            - Maybe try this first, add the Assistant later
    - The AI assistant dissolves barriers { instrument, dataset, science theme } 



As an example of L3+ data production, the figure below illustrates a dataset generator built with AI coding assistance. The operator identifies mixed layer depth based on temperature, salinity and dissolved oxygen data. (In review for Zenodo publication 25-OCT-2026.) 


\begin{center}
\includegraphics[width=0.8\textwidth]{images/MLDSelector.png}
\end{center}


*An interactive Mixed Layer Depth (MLD) selection tool (`argosy` project, Rob Fatland): User selects mixed-layer depths per profile and per profiling sensor from RCA shallow profiler data. Initial haul: 2% of 3 sites x 11 years x 9 profiles per day x 3 sensors.*



## Some details


- Where products live: Zenodo NSF-OOI community; durability, discoverability, attribution
- How light should path curation guidelines be? (too heavy is too onerous; versus trust and reproducibility) 
- Acceptance criteria
- Credit assignment
- Versioning
- Compatibility/usability (for example NetCDF CF Compliance)
- Facilitating scientist using their own AI assistant 
    - Including guidelines on human participation and accountability

<br><br><br>


## Current NSF-OOI contributions on Zenodo


A survey of the **NSF-OOI community on Zenodo** (`zenodo.org/communities/nsf-ooi`, 24 records as of
2026-10-13): Community-curated, DOI-published OOI products. 


\scriptsize
\setlength{\extrarowheight}{4pt}
\renewcommand{\arraystretch}{1.4}

+-------------------------------------------------+---------------------+-----------+-------------+
| Title                                           | Contributor         | Size      | Published   |
+=================================================+=====================+===========+=============+
| NSF-OOI Native Resolution Conductivity and      | Black (OSU)         | 29.6 GB   | 2026-09-22  |
| Temperature, 2014–2026                          |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| NSF-OOI Binned Fluorometric Chlorophyll-a,      | Black (OSU)         | 1.4 GB    | 2026-09-21  |
| FDOM, and Backscatter, 2014–2026                |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| OOI Global ADCP Data Regridded and              | Reed (WHOI)         | 6.6 GB    | 2026-09-10  |
| Quality-Controlled                              |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| Ocean-Data-Lab/ooipy: v1.3.0 (LF data access    | Ragland (WHOI)      | 1.8 MB    | 2026-09-03  |
| restore)                                        |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| Gridded OOI Washington Offshore Profiler Mooring| Risien (OSU)        | 3.3 GB    | 2026-08-26  |
| (CE09OSPM) CTD + DO, 2014–2025                  |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| NSF-OOI Spectral Absorption and Attenuation –   | Black (OSU)         | ?         | 2026-08-05  |
| Baseline Drift Corrected – Relative, 2014–2026  |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| A 7-year Validated Nitrate Dataset — OOI Global | Reed (WHOI)         | 38.9 MB   | 2026-07-27  |
| Irminger Sea Array                              |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| A 5-year Validated Nitrate Dataset — OOI Pioneer| Reed (WHOI)         | 43.8 MB   | 2026-07-27  |
| New England Shelf Array                         |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| NSF-OOI Binned Spectral Absorption and          | Black (OSU)         | 44.8 GB   | 2026-07-17  |
| Attenuation, 2014–2026                          |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| bitbucket.org/ooicgsn/cgsn-parsers              | Wingard (OSU)       | 4.7 MB    | 2026-07-06  |
+-------------------------------------------------+---------------------+-----------+-------------+
| Direct Covariance Surface Stress and Heat Fluxes| Edson (WHOI)        | 28.6 MB   | 2026-03-10  |
| — OOI Surface Moorings                          |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| github.com/oceanobservatories/                  | Wingard (OSU)       | 30.9 MB   | 2026-03-05  |
| ooi-data-explorations                           |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| 10 Years of QC Surface Weather Measurements —   | Wingard (OSU)       | 572.0 MB  | 2026-03-02  |
| OOI Coastal Endurance Array                     |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| 10 Years of QC Carbonate Measurements — OOI     | Wingard (OSU)       | 87.2 MB   | 2025-12-16  |
| Coastal Endurance Array                         |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| bitbucket.org/ooicgsn/cgsn-processing           | Wingard (OSU)       | 3.2 MB    | 2025-09-05  |
+-------------------------------------------------+---------------------+-----------+-------------+
| Gap-Filled Dissolved Oxygen Data — OOI Endurance| Cervantes           | 671.4 MB  | 2025-06-26  |
| Array Inshore Moorings                          |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| Parsing NMEA raw Nortek 500 Signature Data —    | Voulgaris (USC)     | 468.5 MB  | 2024-12-19  |
| OOI RCA Sites  *(shallow profiler)*             |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| A model for community-driven development of best| Palevsky            | 2.0 MB    | 2024-04-03  |
| practices: OOI BGC Sensor Data Best Practices   |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| Bottle-calibrated dissolved oxygen profiles —   | Fogaren             | 233.9 KB  | 2023-07-19  |
| OOI Irminger Sea Array 2014–2022                |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| OOI Biogeochemical Sensor Data Best Practices   | Palevsky            | 7.4 MB    | 2023-07-12  |
| and User Guide                                  |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| Ambient sound spectrograms 2015–2021 — OOI      | Ragland             | 1.4 GB    | 2024-11-06  |
| low-frequency hydrophones                       |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| Shelfbreak Jet Transport from OOI Pioneer       | Camargo             | 2.9 MB    | 2024-03-13  |
+-------------------------------------------------+---------------------+-----------+-------------+
| Ambient sound cross-correlations between OOI    | Ragland (UW)        | 6.3 GB    | 2024-02-19  |
| hydrophones — Central/Eastern Caldera 2015–2022 |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| A Stitch in Time: 20+ Years of Mooring Data from| Risien (OSU)        | 1010.5 MB | 2023-01-30  |
| the Central Oregon Shelf                        |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+

\normalsize
\setlength{\extrarowheight}{0pt}
\renewcommand{\arraystretch}{1.0}

*Source: Zenodo `nsf-ooi` community API. Size = sum of record file sizes. "Contributor" = last name of the first listed creator, with first affiliation in parentheses (blank where Zenodo supplied none).

