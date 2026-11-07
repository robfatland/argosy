# Path Curation


## Community-driven publication of OOI data, code and documentation


**Summary:** This (working document) memo considers the challenge of making OOI data more readily usable. The OOI data system provides engineering and science data as L1/L2 products. (Additional characterization needed.) We envision progress as community-driven expansion of available scientific data types and production methods (L3+). I suggest the DSC assess data publication progress including Zenodo, and provide guidance on data publication as a process that includes tools and scientist-oriented documentation.


- Expand the Zenodo nsf-ooi community by facilitating publication standards that incorporate data, code and documentation. Together this defines a path so I use the term *path curation*.
- Implement an AI Assistant for researchers that spans the OOI program sensors, the operational parameters, the arrays, Zenodo nsf-ooi publications, and so on: Everything that makes OOI a viable contributor to oceanographic research. A prototype is currently operating on the cloud.


## Notes on current status


* The [DSC 2026 Action Item](https://docs.google.com/document/d/11QpakTqgdPrwWmic2K7j2v6IEM_umnRBkBRHmjZShdo/edit?tab=t.0) document reads: "The DSC will [...] reorganize the OOI data products page and make it a more useful, easy to navigate resource. The page will include what qualifies as a community data set, which is likely connected to a published research paper or data paper with DOI. Two categories of data sets will be created/linked: published data sets (PI provides DOI) and research data products without a DOI."
    - "reorganize" is addressed below in terms of an AI assistant
    - "categories of data sets": Suggest revisit this with FAIR principles in mind
    - An example of how OOI data access can be challenging. 
        - Suppose I want current data from ADCPs at particular sites. The data products page is organized by physical products; not by science themes or by instrument. To find *current* or *ADCP* data requires hunting around on the website; where eventually I would discover `VELPROF` and related data types. The Data Product Specification is 41 pages (half of this MATLAB code) that seems to produce L1 data... do I need to use this if L1 is my starting point product? Several Zenodo records seem ADCP-relevant... but I do not believe the OOI website points me to them.
* The [data products page](https://oceanobservatories.org/data-products/data-products-complete-list/) is a list of physical products
* From 06-NOV-2026: 28 records (*projects*) in [Zenodo "NSF-OOI" community](https://zenodo.org/communities/nsf-ooi/)
    * Repos relevant to the current/ADCP/VEL* example above:
        - ooi-data-explorations (Chris Wingard)
        - Parsing NMEA raw Nortek 500 Signature Data (George Voulgaris)
        - Additional repos by Andrew Reed, Craig Risien, Carolina Camargo
    * Machine learning training: MLD (Rob Fatland)
* Open question: Is NSF PAR the "analysis-ready data" publication root site over Zenodo?
* Open question: What standards are in place? For example **Croissant** for metadata mentioned in relation to Zenodo.


## Some elaboration


- FB + DSC + PMO: Take on *path curation*: Publishing curated data plus software tools plus documentation
    - Underway at Zenodo (28 publications; see table below)
    - Collect/assess hard, soft pub requirements
        - CF-compatible NetCDF, Croissant, 
    - Assess the Zenodo catalog: How is it going so far?
    - Build community awareness of the *path curation* plan and pattern
    - Coordinate with scientists to expand the Zenodo catalog
- Set up an AI assistant associated with oceanobservatories (already in progress?)
    - Define the OOI documentation corpus
        - Include Zenodo
        - Include Interactive Oceans and other affiliate sites
        - This is already done (prototype) in a GitHub repo (corpus via gh-pages)
    - RAG-based AI Assistant: Accesses the entire corpus
        - Server version: Install a dedicated Assistant at a URL (browser version)
            - The Assistant can be refined via corpus additions
            - Downside: Effort to build, cost to operate
        - Localhost: Simple Python-on-laptop version
            - Same dynamic: Coordinate LLM calls with corpus referral
            - Down side: User must have their own LLM credentials
            - An example Python program is published in the repo
            - Simpler / cheaper than building an Assistant
    - The AI assistant dissolves barriers { instrument, dataset, science theme } 



As an example of L3+ data production, the figure below illustrates a dataset generator built with AI coding assistance. The operator identifies mixed layer depth based on temperature, salinity and dissolved oxygen data. (Training data (output) published on Zenodo NOV-2026.) 


\begin{center}
\includegraphics[width=0.8\textwidth]{images/MLDSelector.png}
\end{center}


*An interactive Mixed Layer Depth (MLD) selection tool (`argosy` project, Rob Fatland): User selects mixed-layer depths per profile and per profiling sensor from RCA shallow profiler data. Initial haul: 2% of 3 sites x 11 years x 9 profiles per day x 3 sensors.*


<br><br><br>


## Current NSF-OOI contributions on Zenodo


A survey of the **NSF-OOI community on Zenodo** (`zenodo.org/communities/nsf-ooi`, 28 records as of
2026-11-06): Community-curated, DOI-published OOI products. 


\scriptsize
\setlength{\extrarowheight}{4pt}
\renewcommand{\arraystretch}{1.4}

+-------------------------------------------------+---------------------+-----------+-------------+
| Title                                           | Contributor         | Size      | Published   |
+=================================================+=====================+===========+=============+
| Fauna Annotations, ROPOS Dive R2226,            | Jensen (Smith)      | no files  | 2026-10-30  |
| Southern Hydrate Ridge (VISIONS'22)             |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| Fauna Annotations, ROPOS Dive R1463,            | Jensen (Smith)      | no files  | 2026-10-30  |
| Southern Hydrate Ridge (VISIONS'11)             |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| Human-labeled Mixed Layer Depth (MLD)           | Fatland (UW)        | 1.1 MB    | 2026-10-25  |
| training set — OOI RCA shallow profilers        |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
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
| CAMDSB103 August 2022 to August 2023            | Bigham (UW)         | 8.0 GB    | 2026-08-28  |
| Fauna Annotations                               |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| Gridded OOI Washington Offshore Profiler Mooring| Risien (OSU)        | 3.3 GB    | 2026-08-26  |
| (CE09OSPM) CTD + DO, 2014–2025                  |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| NSF-OOI Spectral Absorption and Attenuation –   | Black (OSU)         | no files  | 2026-08-05  |
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
| Ambient sound spectrograms 2015–2021 — OOI      | Ragland             | 1.4 GB    | 2024-11-06  |
| low-frequency hydrophones                       |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| A model for community-driven development of best| Palevsky            | 2.0 MB    | 2024-04-03  |
| practices: OOI BGC Sensor Data Best Practices   |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| Shelfbreak Jet Transport from OOI Pioneer       | Camargo             | 2.9 MB    | 2024-03-13  |
+-------------------------------------------------+---------------------+-----------+-------------+
| Ambient sound cross-correlations between OOI    | Ragland (UW)        | 6.3 GB    | 2024-02-19  |
| hydrophones — Central/Eastern Caldera 2015–2022 |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| Bottle-calibrated dissolved oxygen profiles —   | Fogaren             | 233.9 KB  | 2023-07-19  |
| OOI Irminger Sea Array 2014–2022                |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| OOI Biogeochemical Sensor Data Best Practices   | Palevsky            | 7.4 MB    | 2023-07-12  |
| and User Guide                                  |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+
| A Stitch in Time: 20+ Years of Mooring Data from| Risien (OSU)        | 1010.5 MB | 2023-01-30  |
| the Central Oregon Shelf                        |                     |           |             |
+-------------------------------------------------+---------------------+-----------+-------------+

\normalsize
\setlength{\extrarowheight}{0pt}
\renewcommand{\arraystretch}{1.0}

*Source: Zenodo `nsf-ooi` community API. Size = sum of record file sizes. "Contributor" = last name of the first listed creator, with first affiliation in parentheses (blank where Zenodo supplied none). "no files" = the record lists no files (metadata only).

