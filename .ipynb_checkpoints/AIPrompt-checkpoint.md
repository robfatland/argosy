# AI Prompt


## Introduction for humans


This document is a project summary together with prompts for a Coding Assistant (CA). 
$CA_0$ is Q Developer from AWS, powered by Claude Sonnet. The Q Dev successor Kiro 
(also from AWS) is "agentic" and the intent is to substitute that in at some point. 


In addition to summarizing and providing prompts at the bottom of the file, this
document states some goals and records progress. New CA sessions can get up to speed
by scanning this context.


## Introduction for a coding agent (aka coding assistant (CA))


This effort concerns organizing oceanography data starting with the
Ocean Observatories Initiative Regional Cabled Array shallow profilers. 
The idea is to transition from the archival data system to a more 
interpretable form of the data; and then to visualize, interpret and
further explore this data. 


This markdown file is intended as context for a Coding Assistant (CA). 


A CA is likely to be running as a VSCode IDE extension. At the start of a chat session it 
has no context.


To see the file structure: This work exists on a Windows PC in the WSL2 home file system.
Folders of interest at this time include `reduxYYYY` and `argosy`. Within `argosy` there
are Jupyter notebooks, markdown files (including this `AIPrompt.md` file, and standalone
Python programs. When asking for code I will indicate whether it is to be run as a 
standalone or in an IPython notebook cell. 


The CA is directed to scan this document in its entirety. 


The penultimate heading is **Pending**. This section is not a CA prompt; it is
notes for later propmts.


The final prompt in this file is found at the bottom of the file under 
the heading **Next**.


The line range of this prompt will often be provided to the CA in the IDE chat window as a 
meta-prompt, for example:


"Get the next prompt from lines 1118 - 1160 of `AIPrompt.md`."


As a **Next** prompt is resolved (often with some iteration) the prompt text is
typically integrated into the body of the document; with a new **Next** prompt to follow.


## Glossary


shallow profiler, profile: A *shallow profiler* is a positively buoyant pod-shaped 
structure roughly two meters in diameter moored in the ocean at 200m depth to a holding 
platform by means of a cable wrapped about a spool. Under normal operating conditions
a winch unwinds the cable over the course of about 45 minutes. As the cable 
spools out the shallow profiler floats upward, typically to 20 meters of the surface.
Once it reaches the apex of this ascent the process is reversed and the pod returns to 
its resting location on the holding platform at a depth of 200 meters. During this 
ascent/descent profiling process several attached sensors record data. Each ascent/descent 
cycle is a *profile*. There are nine planned profiles per day, two of which at local
noon and local midnight feature a slower descent to permit certain sensors to better 
equilibrate (notably pH and pCO2).


Midnight profile: One of two extended profiles during any given day, running at local midnight


Noon profile: One of two extended profiles during any given day, running at local noon


profile chart: Sensor data from a profile is often represented as a 2D *profile chart*.
The x-axis is the sensor value and the y-axis is depth. For a shallow profiler the
depth range runs from 200 meters at the bottom to 0 meters at the top of the chart.


bundle: A set of profiles considered collectively is often referred to as a *bundle*.
Most commonly the profiles in a bundle are consecutive in time. However a bundle may
be assembled using other criteria, for example profiles acquired at noon on consecutive
days.


bundle chart: A profile chart containing multiple profiles, i.e. a bundle. In this 
Jupyter book bundle charts can be changed dynamically by means of two sliders: The
first corresponding to the first profile of the bundle and the second corresponding
to how many profiles are in the bundle. 


curtain plot: A static chart of sensor data for many consecutive profiles as follows:
The horizontal axis is time, typically months to years. The vertical axis is depth as 
described for bundle charts. Sensor data is encoded using a colormap. This places 
consecutive profiles as adjacent vertical lines of color in the curtain plot. Curtain
plots are good for showing trends in sensor data with depth that develop over seasonal
time frames. 


redux: Data from shallow profiles represent snapshots of the upper water column; placed
in the OOI data archive with the idea that they can be recovered or brought back for 
further analysis. `redux` meaning `brought back` is an identifying label used in folder
labels for shallow profiler (and other platform) data that has been brought back for
analysis. 


shard: A *shard* is a NetCDF data file containing observational data from a single sensor 
(raster or vector) from a single profile. The name comes from the origin data files 
that typically cover multiple sensors over many days and hence many profiles.


red zone ('the challenge of the last 20 yards'): A sub-project with the objective being
to aggregate and organize OOI data for scientific analysis.
- In particular I may use *red zone format* to mean 'data ready for scientific analysis'.
- As a synonymous term I introduce the term 'Interpretable Data' abbreviated ID
- A second synonymous term: `redux` data
    - These are sensor profiles written as individual NetCDF files.
    - The term `redux` is intended to evoke *revived* from the compound OOINET files to a form of ID


umbrella: A sub-project of this work with the objective being to extend the interpretable data from
the initial simple case (temperature profiles as a function of depth over several weeks)...
    - extending in time over the full duration of the OOI
    - extending to other scalar sensor types (PAR, pCO2, chlorophyll fluorescence, etc)
    - extending to vector sensor types (velocity, spectral irradiance, spectrophotometer sensors)
    - extending to specialized OOI sensors (sonar, ADCP)
    - extending to additional shallow profiler sites: From Oregon Slope Base to Oregon Offshore and Axial Seamount
    - extending to data beyond OOI
        - circulation models such as ROMS
        - NOAA NDBC surface buoy data
        - ARGO biogeochemical drifters
        - satellite remote sensing: sea surface temperature, surface chlorophyll, mean sea level anomaly
        - in situ gliders
        - referential data compilations: BCO DMO, GLODAP



- `SensorInformation.md` is a supporting document relating native datafile structure to red zone format.
- `ShallowProfiler.ipynb` is a supporting document in the same vein


## A sketch of the initial workflow


Three tasks:


### Task 1: Data Download


Retrieve NetCDF files from the OOINET staging area populated via a manual data order. 
The file retrieval / management code resides in the notebook `DataDownload.ipynb`.


OOINET filename example:


`deployment0004_RS01SBPS-SF01A-2A-CTDPFA102-streamed-ctdpf_sbe43_sample_20180208T000000.840174-20180226T115959.391002.nc`


Breakdown of this filename:


- `deploymentNNNN` refers to the fourth operational phases; each deployment typically months to a year in duration
- `RS` identifies the Regional Cabled Array
- `01` TBD
- `SB` refers to the (Oregon) Slope Base site
- `PS` is "Profiler (Shallow)" i.e. the Shallow Profiler at the Oregon Slope Base site
- `SF` TBD
- `01A` TBD
- `2A` TBD
- `CTDPF` is a CTD instrument (multiple sensors)
- `A102` TBD
- `streamed` TBD
- `ctdpf` is a second (lower case) reference to the CTD
- `sbe43` TBD
- `sample` TBD
- `20180208T000000.840174-20180226T115959.391002` is a UTC time range for the sensor data in this file
- `.nc` indicates file format is NetCDF


This data file combines together multiple sensors plus associated engineering and quality 
control data. This example includes data from 157 ascents of the shallow profiler profile in 
addition to data from descents and rest intervals. In short the file is a dense amalgam of
information that can be overwhelming to work with. Note this file covers a period of time 
in 2018. It will prove convenient to break up these files by sensor and by individual
profile (herein 'sharding') and to compartmentalize sharded data by year.


### Task 2: Data Sharding


Break downloaded data into individual files in an organizing directory structure. Code for this
and related operations is in `DataSharding.ipynb`.


One output file (a shard) corresponds to one ascent profile and one sensor type, for
example temperature data. Many such files profiles (shards) are written to a directory labeled by
year. Each single-sensor ascent shard file is about 100kb in comparison with source files that
are typically 500MB. 


Shard folder name example: `~/redux2018`


Shard ascent filename example: `RCA_sb_sp_temperature_2018_296_6261_7_V1.nc`


Breakdown of this filename:


- `RCA` = Regional Cabled Array
- `sb` = (Oregon) Slope Base
- `sp` = Shallow Profiler
- `temperature` = sensor type
- `2018` = year of this profile
- `296` = Julian day of this profile
- `6261` = global index of this profile (see `profileIndices` below)
- `7` = daily index of this profile, a number from 1 to 9
- `V1` = version number of this shard operation
- `.nc` = file type NetCDF



### Task 3: Bundle plotter and other visualizations


Working from sharded data build out both interactive visualizations and data animation generators.
Code for this and related tasks is in `Visualizations.ipynb`.


A bundle plotter is a double-slider visualization tool running in a Jupyter notebook 
cell that plots $N$ consecutive profiles together (slider 1) starting at profile T 
(slider 2). Slider 2 can be dragged through time so as to scan this sensor's view of 
the epipelagic zone: We can notice anomalies, seasonal trends, mixed layer depth changes 
with season, possible sensor artifacts, and so on.


<Place a screenshot here.>
    

## Special terminology


    

## Reference websites


- [The OOI official website](https://oceanobservatories.org/)
    - [The OOINET data resource](https://ooinet.oceanobservatories.org/data_access)
    - [OOI Glossary](https://oceanobservatories.org/glossary/)
    - [Deciphering OOI Reference Designators](https://oceanobservatories.org/knowledgebase/how-to-decipher-a-reference-designator/)
    - [Related: OOI Sites and Platforms](https://oceanobservatories.org/site-list/)
- [The Regional Cabled Array website](https://interactiveoceans.washington.edu/)
    - [Shallow Profilers](https://interactiveoceans.washington.edu/technology/shallow-profiler-moorings/)
    - [Horizontal Echosounders (HPIES) page](https://interactiveoceans.washington.edu/instruments/hpies/)
    - [RCA QA/QC](https://qaqc.ooi-rca.net/)
- Publication of data, workflow, visualizations
    - Zenodo


## Red Zone Goals


- Begin: Isolate a spatiotemporal dataset as a *first run* at the redzone workflow
    - From the OOI observatory (many arrays) narrow the focus to the Regional Cabled Array (RCA)
    - From the RCA distribution across many hundreds of kilometers: narrow to a single site and platform
        - Specifically the Oregon Slope Base shallow profiler
    - From fifteen sensor streams to one: Temperature
    - A note on native data format: NetCDF, Deployment-related time boxes, continuous, many sensors in one file e.g. for CTD
    - From continuous data to profile ascents only: Using ascent metadata, up to nine ascents per day
    - From the OOINET server obtain CTD datasets spanning the majority of the program timeline
        - Specifically from 2015 through the end of 2025; folder separation by year
    - From nominal nine profiles per day: Set up a data structure of actual profiles that produced usable data
    - Produce a `redux` temperature profile dataset (low data volume in comparison with the CTD file volume)
        - Place this data in AWS S3 object storage
        - Data are aggregated as profiles with dimension `time` (not `obs`)
        - For latency reasons data may be duplicated on localhost
    - Produce a running average (mean and standard deviation) dataset
        - Characterization by site, time of day, time of year
    - Stub: How would this lead to a climatology dataset?
    - Create visualization tools based on `matplotlib` residing in a notebook in this Argosy Jupyter Book
        - Plots tend to set up with temperature (etcetera) variation on the x-axis and depth on the y-axis
        - Plots can be single profile or bundled (an overlay of many related profiles)
            - Interactive bundle plots select time window width and starting point via two sliders
            - This uses the interactive widget
    - Create time-series animations of this data
    - From this start to formulate how to build a persistent anomaly dataset
- Add six additional data/sensor types that follow the above guidelines
    - Dissolved Oxygen, Salinity, Density, Backscatter, FDOM, Chlorophyll A
    - Following the same process as the temperature data
    - The visualization has to expand to permit intercomparison
- Add additional data/sensor types
    - Point current measurement (3-element vector)
    - PAR
    - pH
    - Nitrate 
    - pCO2
    - Spectral Irradiance (7-element vector)
- Add spectrophotometer data (approximately 70-element vector)
    - Details TBD
- Publish a Client
    - Prototype as Jupyter Notebooks in the Argosy Jupyter Book
    - Probably set up to read from a downloadable tar file
    

## Umbrella goals: Instruments/sensors/data streams beyond the shallow profiler 


This is at much lower task resolution.


- Extend the Oregon Slope Base workflow to the other two shallow profilers in the RCA
- Incorporate NOAA sea surface state buoy data
- Apply the methodology to the shallow profiler platform moored at 200 meters
- Extend focus within RCA to other sensors
    - Horizontal Electrometer Pressure Inverted Echosounders (HPIES; 2 sites)
    - Broadband Hydrophone and other acoustic sensors as directed (see WL, SA)
    - Axial tilt meters, seismometers etcetera
- Glider data from Coastal Endurance
- NANOOS installations
- ARGO
- Global ocean dataset formerly known as GLODAP
- PO-DAAC data including 
- Inferred ocean surface chlorophyll (LANDSAT, MODIS etcetera) 
- Publish the pipeline and output results to be openly available
    - Includes appraisal of working on the OOI-hosted Jupyter Hub
    - Includes containerization as appropriate


## CA behavior


- The acronym CA refers by default to a Coding Assistant aka Coding Agent
- The CA should not modify this file unless invited to do so
- The CA is encouraged to create focused markdown documentation files
    - Cover narrow topics
    - Name format: `CA_<Topic>.md`.
- The CA will be directed in the **Next** prompt on the context of the code
    - Typically it will be code that runs in a Jupyter notebook cell
    - Less typically it will be a standalone Python program
- The CA should always place a comment at or near the top of code
    - Comment is between one and four lines in length
    - Comment briefly tells what this code does
    - Comment briefly indicates where this execution occurs in the workflow


## Code locations in relation to workflow tasks


Most of the work is done by IPython notebooks, in development. Eventually code 
should migrate to straight up `.py` Python files.


- No code: Data order, done by a human on the OOINET website
- `DataDownload.ipynb`
    - Manual: Data order already generated on the OOINET system (full time resolution)
    - Manual: URLs copied sequentially from email notice(s) to `~/argosy/download_link_list.txt`
    - Manual: Make sure localhost receive folders exist: `ooinetdata/RCA/sb/scalar/2015_flor` etcetera
    - Jupyter cell: `DataDownload.ipynb` uses the above `.txt` file to 
        - Deprecated: Build a `bash` script that downloads NetCDF files from the OOINET server
        - Actually: Downloads 
- `ShardProfiles.ipynb`
    - Extract sensor data cut into profile bins; write these as NetCDF files
    - Output folders are `~/redux<yyyy>`
- No code: Copy shard folders to an S3 bucket
- Deprecated: `ShallowProfiler.ipynb`
    - To be deleted but currently contains notes to transcribe
- No code: `SensorInformation.md` 
    - Metadata, notes; to be combined with `ShallowProfiler.ipynb`
    - Visualizations on redux data
    - "TemperatureChart" checks temperature (sensor) data match to ascent timing metadata
- `tmld_selector.py` is a human-manual location picker for temperature-based mixed layer depth
    - This was not coming together in a Python notebook cell.
    - It works great in straight-up Python
    - Results are written to `tmld_estimates.csv`
    - These can be opted in to a bundle plot
- `Visualizations.ipynb`
    - Bundle plot interactive visualization
    - Bundle animation: Bundle mode, mean-sd mode
    

## Technical Notes


The OOI "observatory" consists of seven Arrays:


- Regional Cabled Array
- Coastal Endurance Array
- Global Station Papa Array
- Global Irminger Sea Array
- Coastal Pioneer Array
- Global Argentine Basin Array (no longer operational)
- Global Southern Ocean Array (no longer operational)


Each array is a sub-program. Array deployment dates back to 2013-2015. The components
of the active arrays are continuously subject to maintenance.


The initial focus as noted is the Regional Cabled Array (RCA) off the coast of Oregon. 
The RCA is distributed along two electro-optic cables emanating from a shore station 
in Pacific City on the Oregon coast.


The first cable is named for its endpoint: 'Axial Seamount', about 450 km west of Pacific City. 
The second cable is named 'Continental Margin': The cable crosses the continental shelf and
then curves south and east along the continental shelf margin. This cable hosts the 
Oregon Slope Base site, the initial focus of this work.


This study begins with a characterization of the upper 200 meters of the water column, 
known variously as the photic or epipelagic zone. There are three sites in the RCA where 
a sensor assembly called a shallow profiler is used to profile the upper water column 
nine times per day: Oregon Slope Base, Oregon Offshore and Axial Slope Base. 


In this work the term *Instrument* indicates an aggregation of one or more *Sensors*.
For example a fluorescence *instrument* consists of three sensors: One for 
fluorescent dissolved organic matter, one for chlorophyll, and one that measures 
particulate backscatter. These three sensors would be considered *scalar* sensors 
as they generate single-valued observational data. There are also *vector* sensors,
specifically a spectrophotometer, a spectral irradiance sensor and a 3-axis current 
sensor. 'Vector' means the sensor generates multiple values per observation.


The profiler pod makes 9 ascents and 9 descents each day from where it rests on
a platform moored 200 meters below the surface. Mooring is by means 
of two cables that extend down to the sea floor.


## Gripes


- Why does OOI have two streams for DO (that appear to be identical) in CTD files plus a third (also apparently identical) stream in the DO file?
    - What is the discovery path in the website documentation?
    
    
## Sensor list and associated file label


This partial list can stay here for the moment. The definitive information is 
in the file `SensorInformation.md` in the `argosy` root directory. 

    
- CTD NetCDF files include...
    - Dissolved oxygen 
    - Density
    - Temperature
    - Salinity
- PARAD NetCDF files include...
    - PAR data
    
    
## Source data file system and file structure


- RCA source datafiles are resident on localhost in `~/ooidata/rca/`
- subfolder `/sb` abbreviating Oregon **S**lope **B**ase. 
- subfolder `/scalar` for scalar instruments
- subfolder `<year0>_<year1>_<instrument>` for example `2015_2025_ctd`
- Datafile name in this folder, example: 
    - `deployment0004_RS01SBPS-SF01A-2A-CTDPFA102-streamed-ctdpf_sbe43_sample_20180208T000000.840174-20180226T115959.391002.nc`
        - `Deployments` last months or as much as a year between maintenance events
        - `RS01SBPS` is a reference designator
            - `RS` is Regional Cabled Array
            - `01` ?
            - `SB` is Slope Base
            - `PS` is (reversed) shallow profiler
        - `SF01A` is the profiler (not the fixed platform)
        - `2A` ?
        - `CTDPFA102` is CTD data
        - ?
        - `20180208T000000.840174` is the data start time
        - `20180226T115959.391002` is the data end time (Zulu)
        - .nc is NetCDF


The NetCDF file will have `variables`, `coordinates`, `dimensions` and `attributes`.
The default Dimension is Observation 'obs'. The Dimension we want to use is `time`.
This is done using an `xarray`: `swap_dims()` method on the `xarray` `Dataset`:


```
ds = ds.swap_dims({'obs':'time'})
```


- `data variables` include sensor data of interest and QA/QC/Engineering metadata
- `coordinates` are a special type of data variable
    - natively the important coordinates are `obs`, `depth` and `time`
    - there is also `lat` and `lon` but these do not vary much for a shallow profiler
- `dimensions` are tied to `coordinates`: They are the data series reference
- `attributes` are metadata; can be useful; ignore for now



## Using profile metadata


Profile metadata for both shallow and deep profilers is retained in a public GitHub
repo as a set of CSV files delineated by platform and year. The first column of a
profile CSV file is an index (a profile counter) that begins at 1 at the start of the 
(example:) RCA OSB shallow profiler deployment in July 9 2015. Today the index exceeds 
20,000. In addition to the index column this file has 3 additional columns. 
    

A shallow profiler divides its time between three phases: Ascent, Descent, and Rest.
The metadata CSV file therefore continues with three additional columns associated 
with the start time of an ascent, the peak time of that ascent, and the time that the 
profiler returns to the support platform at 200m depth. The associated column names 
are `start`, `peak`, `end`. 


The GitHub repository organization is 'OOI-CabledArray'. The repository of interest is 
'profileIndices'. The RCA Data Manager who built this is Wendi Ruef. 
    

The repository has been cloned to localhost ~ as `profileIndices`. 



- Wendi Ruef (RCA): `https://github.com/OOI-CabledArray/profileIndices`
- Clone to localhost WSL ~/profileIndices
- Profiles are broken down by array and site identifier, then by year
    - Array CE = Coastal Endurance, associated with the Oregon Offshore site ('OS')
    - Array RS = Regional Cabled Array, associated with Slope Base ('SB') and Axial Base ('AB') sites
- Here are the six resulting codes: 3 Deep Profilers, 3 Shallow Profilers 
    - CE04OSPD Offshore (Sub-folder 'os') deep profiler
        - years 2015, 18, 19, 21, 22, 23, 24, 25
    - CE04OSPS ~ Oregon Offshore ('os') shallow profiler (CE = Coastal Endurance array)
        - 2014 -- 2026
    - RS01SBPD ~ Slope base ('sb') **deep profiler**
        - years 2015, 2018, 2019, 2020, 2021, 2022, 2023, 2024
    - RS01SBPS ~ Slope Base ('sb') shallow profiler
        - 2014 -- 2026
    - RS03AXPD ~ Axial Base ('ab') **deep profiler**
        - years 2014, 2017 -- 2025
    - RS03AXPS ~ Axial Base ('ab') shallow profiler
        - years 2014 -- 2026


To select data from the Slope Base shallow profiler CTD during 2018: Use the time
ranges present in the file `~/profileIndices/RS01SBPS_profiles_2018.csv`. 


Note: Some sensors operate continuously (such as CTD temperature). Other operate
at a lower duty cycle / during selected phases.
    
    
For an instrument / sensor that operates on ascent the time range for a given 
profile would be given by columns 2 and 3: start and peak. Other cases will be
elaborated as they come up.

    
Times are given in format 'yyyy-MM-dd hh:mm:ss'.
    

Note: Noon and midnight profiles tend to have longer duration owing to a slower descent profile.



## Further development of shallow profile metadata


This is an idea but not implemented yet.
    

In this phase the goal is to produce the extensive `redux` dataset. 
It will be of further red zone use to build out additional metadata.

    
Here is one design concept
    

- CSV file
    - The first called `RCA_sb_sp_ctd_temperature_profile_status.csv`
    - This will span the full range of available time (2014 - 2026)
    - Each row corresponds to a year + day
        - The majority of years will have 365 rows, leap years 366
        - The first row will be column headers
        - Subsequent rows in chronological order
    - Columns
        - year
        - Julian day
        - date (dd-MON-year format e.g. 01-FEB-2026)
        - 1
        - 2
        - 3
        - 4
        - 5
        - 6
        - 7
        - 8
        - 9
        - Total
        - Noon
        - Midnight
    - Column values
        - The first 3 columns are straightforward
        - Each number column 1 ... 9 has value 1 or 0 based on the profile indices (present / absent)
        - Total is the sum of columns 1 ... 9
        - Noon is an index for the profile number that happened at noon local time
        - Midnight likewise


A second metadata file will describe active profiling intervals and gaps. 



## Single Input File to `redux`


- Transcribe the bulk CTD file named above to a set of single-profile files for temperature data.
- These will be referred to as *redux files*.
- Do not modify the `profile_status.csv` file from the previous step.
- Do not create a `timeline.csv` file.
- Rather: Just focus on the transcription task
- The output files will be NetCDF
    - Advise: Use XArray Datasets or DataFrames?
- The `dimension` of the output files will be `time` via `.swap_dims()`
- The data variable will be `sea_water_temperature` (input data variable) written as `temperature` (output)
- The file will include coordinate `depth`
- The output folder will be `~/redux2018` where the individual profile files will be written. 
- One file is written per profile

The output folders are `~/redux<yyyy>`.

The filename format for each redux profile `.nc` file is slightly different than before, as follows:
    
- The filename format will be `AAA_SSS_TTT_BBB_YYYY_DDD_PPPPP_Q_VVVV.nc`
    - These are to be filled in as follows for now:
        - AAA  = Array name: Using `RCA` for Regional Cabled Array
        - SSS  = Site: Using `sb` for Oregon Slope Base
        - TTT  = Platform: Use `sp` for shallow profiler
        - BBB  = Observation type, one of:
            - `temperature` for temperature
            - `salinity` for salinity
            - `density` for density
            - `dissolvedoxygen` for dissolved oxygen
        - YYYY  = four digit year
        - DDD   = three digit Julian day as in 027 for January 27
        - PPPPP = Profile index drawn from the `profileIndices` tables
        - Q     = This profile's index relative to the data acquisition day: a number from 1 to 9
        - VVV   = Version number: Use `V1` at this time
    
An output filename example: `RCA_sb_sp_temperature_2018_003_3752_4_V1.nc`.

A single year could produce as many as (365*9) redux files.

When the program runs: First determine the time range of the source NetCDF file. Print this
out and include the estimated number of available profiles by multiplying the time range in days
by nine. 

For each profile: Data are extracted using time limits from the profileIndices CSV files. Specifically
the profile start time is given in the `start` column. The profile end time is given in the `peak` 
column: When the profiler reached peak depth closest to the ocean surface.

This program should tally up how many profiles it attempted to extract and write; and 
it should tally up how many were extracted successfully. Print these values at the end as 
a diagnostic remark. 

Warning: A prior version of the code program produced this error: 

```/tmp/ipykernel_206172/2169783661.py:91: PerformanceWarning: DataFrame is highly fragmented. (etcetera)```


## Visualization 1
    
    
Visualization sections are numbered in sequence with sub-topic to follow:
    

### Jupyter notebook cell code: Bundle plots for temperature profiles


Create a code block to run in a Jupyter notebook cell that will generate bundle plots as follows:


- Use matplotlib
- marker size typically 1 (small)
- `temperature` is on the x-axis with range wide enough to accommodate all the temperature data
- `depth` is on the y-axis with a range of 0 meters to 200 meters: From top to bottom
- The bundle plot means that several-to-many consecutive profiles are plotted on a single chart
- The bundle is chose via two widget sliders called `nProfiles` and `index0`:
    - `nProfiles` is a number of time-consecutive profiles to plot on a single chart (a bundle of profile plots)
        - The minimum value is 0, the default starts at 1, the maximum value is 100
    - `index0` is the index of the first profile (chronologically) in the bundle plot
        - this is an integer from 1 to 157 (the number of profiles produced in the redux step)
        - the code will need to translate from the index0 value to the corresponding filename from `~/redux2018`
        - if the bundle specifications `nProfiles` and `index0` go over the end file (file 157) the code handles this gracefully
        - The bundle plot only refreshes when the User is done dragging the slider to a new value (left mouse button release)
- Each refresh of the bundle plot should indicate the profile range as `yyyy-doy-profile to yyyy-doy-profile`:
    - yyyy is year
    - doy is day of year or Julian day
    - profile is a day-relative profile number from 1 to 9


## Experiment: Can the Q Developer CA identify mixed layer depth from a text description? 


A naive attempt produced a non-result. However the AI2 "AstaLabs" release of AutoDiscovery made significant
progress; which I will not attempt to capture here. A human-driven ETMLD picker program was written in Python.
This is not Jupyter cell code because my set-up is not supporting interactive mouse clicks. Here is the 
specification for the program:


- Generate a CSV file with three columns, resides in `~argosy`.
    - First column = profile index as recorded in the profile filename in ~/redux2018
    - Second column is `Estimated TMLD`
        - 'Estimated Temperature Mixed Layer Depth' (meters, positive downward)
    - Third column = temperature at that depth for that profile
- Estimated TMLD value `N`
    - The upper `N` meters of the water column is well-mixed due to wave action etcetera
    - At the bottom of this layer temperature begins to steadily decrease with depth (pycnocline)
    - With increasing depth the temperature gradient decreases
    - The mixed layer / pycnocline boundary often appears as a pronounced kink in the temperature curve
    - Equivalent boundaries exist: Salinity, density, other sensible attributes of the water column
- The TMLD data can be included in bundle plots as distinct markers
    - 1:1 correspondence to individual profile curves
    - Marker should be larger, different color


### TMLD generator program

    
- Establish a range of profiles to annotate
- Display each in sequence
- Left mouse click identifies the TMLD depth 
- standalone Python program as noted (not Jupyter cell) 
- confirm a choice by hitting Enter
- program should also support a "no data" choice if the User wants to skip
- cursor location is printed in/near the chart so User can see both depth and temperature.


## Processing the full timespan dataset


- CTD is the initial emphasis
- List the CTD files in a "to do" file
- From the folders where the original CTD data file is located
- Create a new file listing all of the CTD files in that folder
    - Let us call this file `source_ctd_filelist.txt`
    - The first line will be the full path to the folder
    - The remaining lines are 1 line per CTD file
- Process these files to expand the time series for Oregon Slope Base shallow profiler `temperature` profiles
- Expand to `dissolvedoxygen`, `density`, `salinity` 
    - Use those strings in the output filenames sensor field
- Input file location for year `<YYYY>` is `~/ooidata/rca/sb/scalar/<YYYY>_ctd`
- The original input file was:
    - `deployment0004_RS01SBPS-SF01A-2A-CTDPFA102-streamed-ctdpf_sbe43_sample_20180208T000000.840174-20180226T115959.391002.nc`
    - The string `CTDPF` indicates a CTD file. File extension must be `.nc`
    - Compile the source file list in `source_ctd_filelist.txt` as described above 


## Temperature compilation from many source CTD files
    

Write a Python script that will run in a Jupyter cell. It will work from the file `source_ctd_filelist.txt` generated
in the previous stage of this effort. For each file listed we want to perform the following procedure: 

    
- Print the data file directory on a line
- Print the name of the current file on the next line
- Print `<start date> - <end date>` on the next line
- Print whether or not `sea_water_temperature` is present as a data variable in the file
    - If it is not present: 
        - State this
        - State the data variables that *are* present
        - prompt the User for instructions: `Continue [C] or Halt [H]?`
- For this input CTD file start a counter of how many profile files have been written to `~/redux2018`
- Formulate the filename for the current profile
- Using the appropriate `start` and `peak` times from the appropriate `~/profileIndeces` folder CSV file: 
    - Extract and write a temperature profile file to the folder `~/redux2018` following the same format as before
    - In this process: Keep a running sum of how many data samples there are in each profile
    - Output files in ~/redux2018 feature sea_water_temperature renamed `temperature` plus `depth` against dimension `time`
    - Do not retain other data variables or other coordinates, particularly `lat` and `lon`
- Repeat this procedure of writing temperature profile files, incrementing the 'writes' counter
- After every 90 profile writes: Print the number of profiles written for this input file so far
- Upon completing a file: Print diagnostics:
    - How many profile files were written
    - What is the average number of data values per profile
- If the number of profile files written for a given input file is zero:
    - State this and prompt the User for instructions: `Continue [C] or Halt [H]?`
    - If the User choses Continue: Proceed to the next input CTD file
- Continue to the next input CTD file until all have been processed in this manner 


## Visualization 2
    
    
### Bundle animation
    

- Write a version of the bundle plot visualization that creates an animation: As an output .mp4 file.
- This code will run in a Jupyter cell
- The input questions take on the default value if the User just hits Enter.
    - Start by asking "Include TMLD estimate in the visualization? Default is no. [y/n]" 
    - Then ask "How many profiles in the bundle? Default is 18 (two days)" refer to this as N
    - Then ask "How many seconds delay between frames? (0.1 sec):" refer to this as d
    - Then ask "Start date (default 01-JAN-2018):" refer to this as T0
    - Then ask "End date (default 31-DEC-2018):" refer to this as T1
- Start at T0 and continue to T1: To create an animated chart sequence
    - The output file should be called 'temp_bundle_animation.mp4' followed by the appropriate file extension
    - Each frame of the animation consists of N profiles bundled in one chart
    - The horizontal axis is fixed at 7 deg C to 19 deg C, does not change from one frame to another
    - The vertical axis is fixed as before from 200 meters to 0 meters
    - Show N profiles per frame of the animation
    - For a given profile: If the TMLD option is selected but there is no value for the TMLD in the CSV file: Omit adding that marker.
    - If possible: Add in a 'hold time' per frame of d seconds
    - If a time gap > 48 hours exists between any two consecutive profiles in a given bundle/frame: 
        - This chart frame includes in large black letters at the lower right 'Time Gap'
        - The Time Gap message persists until all N consecutive profiles do not have a time gap
- Check that the output file exists and report its status


## Ordering data from the Data Access page once logged into OOI
    
    
- This is the `OOINET` data resource (not Data Explorer)
- For the moment: Order one year at a time (CTD)
- Left sidebar: Begin by setting filters
    - Do not set the time range filters
    - Array = Cabled Array
    - Platform = Shallow Profiler
    - Do not select a Node
    - Instruments = CTD
- Data Catalog (center-low panel)
    - Shows 2 results: Shallow profiler and Platform; select the former
- Data Navigation (center-top window below title bar)
    - Shows 4 Engineering and 1 Science result; select the download button for Science
- Download time range pop-up wizard
    - Set start to Jan 1 2019 00:00:00 (for example)
    - Set end to Dec 31 2019 23:59:59 (for example)
    - Clicked on download (email to be sent in a few minutes notifying completion)


## Prepare for expansion: Temperature 2015 through 2025


- Created folders `redux2014` through `redux2026` (implicitly Oregon Slope Base only to this point)
- Order and download proper CTD data from years beyond 2018

    
## Multi-year redux generator

    
- Rewrite the redux code that runs in a Jupyter notebook cell
    - This scans multiple folders for (large) CTD source datafiles
        - If the folder is not found: Skip it
        - If a source folder is found that spans year breaks: Be sure to write outputs to the correct year-folder
        - We are still focused on just temperature data
        - The output files are called `redux` files
        - There follows some more detail on how this code will work
    - Source data folders have name format `~/ooidata/rca/sb/scalar/<yyyy>_ctd` where <yyyy> runs from 2015 through 2025
        - The program should prompt for y/n for each year (folder) for which there is data 
            - This prompt defaults to `y`
    - Output files as developed earlier with these changes:
        - remove data variables `lat` and `lon` and remove `obs` from the output `.nc` file. Retain time, depth and temperature.
        - when writing the output `redux` file: select destination folder based on this profile's year as follows:
            - a profile from 2018 will be written to `~/redux2018`
            - a profile from 2019 will be written to `~/redux2019`
            - and so forth: Possible year values are 2014 through 2026

    
## Refreshing the two visualization cells: Bundle charts and bundle animation
    
    
So far we have two visualizations: A bundle chart with two time sliders; and a bundle chart animation generator. 
As in the previous step we want both of these to be written to cope with redux files distributed through single-year
folders: redux2014, redux2015, ...and so on through..., redux2026. 
    
    
We now have a working bundle chart code running in a Jupyter notebook cell. 
    
    
We also have a bundle animator; but it needs some modifications.

    
As with the bundle chart the animator features a pre-scan with User interaction, first to confirm using the various
populated `~/redux<yyyy>` folders. This sets up the year range of the animation.
    
    
We want to give the User a new display mode as an option: Display the bundle (the default, as currently set up)
or display a mean profile defined as follows: 
    - The profiles in a given bundle are averaged to produce a 'mean profile'.
        - This is displayed as a medium-heavy line
    - The standard deviation is also calculated as a function of depth
        - This is displayed as two + and - profiles relative to the mean profile using a thin line
    
    
The last User input is animation start and end date. Revisit how the default values for these prompts are calculated. 
The default start date should be the earliest date in the chosen folders/years; and the default end date should be 
the latest date in the chosen folders/years.
    
    
The bundle chart includes the Time Gap alert. This is also present in the animation so that is good. 

    
The bundle chart viewer gives the option to fix the x-axis for all bundle charts. For the animation: This is not an 
option: The temperature range will be fixed at 7 deg C to 20 deg C. (19 deg C was too low for some of the data.)
    
    
The animation output mp4 file should be written in the ~ folder.
    
    
The code handles zero / nan mean cases gracefully.   
    
    
## SECTION NEEDS A TITLE
    

This task is to upgrade the Jupyter cell code to perform a bulk download of NetCDF source files
from one or more URLs. Each URL corresponds roughly to a calendar year where for now we are working
with CTD files.
    
    
Massive download jobs are subject to interruption so we want the code to be tolerant of
re-starting after only partial completion. Here is the functionality description:

    
- Open a file `~/argosy/download_link_list.txt`
    - Each line is a URL for a distinct data order
        - For each URL print a diagnostic of 
            - how many `.nc` files are present
            - how many have already been downloaded
            - how many remain to download
    - At that URL is a collection of files to download
- We want to download files that are not yet fully downloaded; otherwise skip
- Files are to be downloaded to the corresponging localhost destination folder `yyyy_ctd`
    - The base localhost folder location is `~/ooidata/rca/sb/scalar/`
    - If a destination folder does not exist: Print a message and halt
    - The destination folder name `yyyy` value is a year from 2014 to 2026
- To determine the destination folder for a particular `.nc` file: 
    - Parse the `.nc` filename as:
    - `<first_part>_yyyyMMddTHHmmss.ssssss-yyyyMMddTHHmmss.ssssss.nc`
        - This maps to `<first_part>_datetime-datetime.nc`
        - The first datetime: year `yyyy` month `MM` day `dd` literal character `T`...
            - ...followed by hour `HH` minute `mm` second `ss.ssssss`
        - Second datetime follows the same format.
    - Destination folder `yyyy` is chosen as the same `yyyy` as the first datetime.
- Download the `.nc` NetCDF files and ignore the `.ncml` files



## The Sensor Table
    
    
We now define the sensor table as a comprehensive list of sensor types for the shallow 
profiler. For the moment this resides in this file; but will eventually be written as
a standalone CSV file. 
    
    
Premise: Jupyter cell code in the `DataSharding.ipynb` notebook shards multiple types of 
source 'instrument' NetCDF datafiles to produce single-sensor shard files, one file
per profile. Shards are written into folders spanning single years; with folder names
`~/redux<yyyy>` where `<yyyy>` is a four-digit year. In the course of going from 
complicated instrument file to much simpler/smaller shard files to visualizations to
analysis we need consistent metadata; so the sensor table localizes that metadata
to a single resource.
    
    
Sensors correspond to rows of the sensor table, eventually to be written as a CSV file.
Not included in the sensor table are `time` and `depth`: These are ancillary data: 
`time` as dimension/coordinate and `depth` as data variable (XArray terminology).
    
    
Here is the sensor table column information, columns going left to right.
Format: column content, short column name, some elaboration


- sensor name,          sensor,  a descriptive "normal text" name
- source instrument,    instrum, OOI five-letter key from reference designator e.g. CTDPF FLORT
- ooinet download key,  key,     short abbreviation of sensor name used in download folder names
- sensor data variable, datavar, for the science data variable e.g. `sea_water_temperature`
- shard data variable,  shard,   the sensor shard name is used in `redux` shard files e.g. `RCA_sb_sp_dissolvedoxygen_2021_185_11876_3_V1.nc`
- acquisition side:     side,    `ascent` or `descent` (mostly ascent; pCO2 and pH are the notable descending acquisitions)
- data extreme low,     xlow,    well below the expected data minimum
- data extreme high,    xhigh,   well above the expected data maximum

    
Sensor table:
    
```
sensor,         instrum,  key,  datavar,                             shard,           side,     xlow,  xhigh
temperature,      CTDPF,  ctd,  sea_water_temperature,               temperature,     ascent,    6.0,   20.0
salinity,         CTDPF,  ctd,  sea_water_practical_salinity,        salinity,        ascent,   32.0,   36.0
density,          CTDPF,  ctd,  sea_water_density,                   density,         ascent, 1024.0, 1028.0
dissolved oxygen, CTDPF,  ctd,  corrected_dissolved_oxygen,          dissolvedoxygen, ascent,   50.0,  300.0
nitrate,          NITNR, nitr,                     ,                 nitrate,         ascent,    ???,    ???
CDOM,             FLORT, flor,  fluorometric_cdom,                   cdom,            ascent,    0.5,    4.5
Chlorophyll-A,    FLORT, flor,  fluorometric_chlorophyll_a,          chlora,          ascent,    0.0,    1.5
backscatter,      FLORT, flor,  optical_backscatter,                 backscatter,     ascent,    0.0,    0.006
pCO2,             PCO2W, pco2,    ?,                                 pco2,           descent,  200.0, 1200.0
pH,               PHSEN,   ph,    ?,                                 ph,             descent,    7.6,    8.2
PAR,              PARAD,  par,    ?,                                 par,             ascent,    ???,    ???
velocity,         VELPT,  vel,    ?,                                 vel,             ascent,    ???,    ???
spectralirrad,    SPKIR,  irr,    ?,                                 irr,             ascent,    ???,    ???
opticalabsorb,    OPTAA,   oa,
beamattenuation,  OPTAA,   ba,
```
    
Unless noted each sensor is *scalar* (single numerical value per sample). The four exceptions
are `velocity`, `spectral irradiance`, `optical absorption` and `beam attenuation`. The latter
two sensors are both produced by a spectrophotometer (OPTAA).


## Sharding and shard files
    
    
The shard code inventory output files to avoid reproducing effort. As noted shard folders are `~/redux<YYYY>`.

    
The filename format for each shard (profile) `.nc` file:
    
    
- Nine name fields: `AAA_SSS_TTT_BBB_YYYY_DDD_PPPPP_Q_VVVV.nc`
    - AAA  = Array name: Using `RCA` for Regional Cabled Array
    - SSS  = Site: `sb` for (Oregon) Slope Base
    - TTT  = Platform: `sp` for shallow profiler
    - BBB  = Sensor type; the shard name taken from the sensor table:
        - `dissolvedoxygen` for dissolved oxygen
    - YYYY  = four digit year of this profile
    - DDD   = three digit Julian day of this profile
    - PPPPP = Global profile index from the `profileIndices` resource
    - Q     = Day-relative profile: a number from 1 to 9
    - VVV   = Version label: Initially `V1`
    
    
Instrument input folders by year: `2014_ctd`, `2015_ctd` etcetera through `2026_ctd`.
These are in the base location `~/ooidata/rca/sb/scalar/`. These files are downloaded
from OOI using code in the `DataDownload.ipynb` notebook. 


    
## Multi-sensor Bundle / Mean-std charts
    
    
This is the most recent specification for the sensor data bundle plotter. One of the recurring 
errors in recent revisions has been overlaying two horizontal axis ranges. This can be done in
matplotlib with careful attention to `axis`. What we want to *avoid* is plotting data from two 
different sensors using a single x-axis range. 


The sensor data bundle plotter runs in a Jupyter cell.
    

It first inputs from the User what years should be included in the profile time range,
corresponding to `~/redux<yyyy>` folders.
    
    
The code will accommodate one or two sensor types out of these four sensor types: 
 
    
{ temperature, salinity, density, dissolved oxygen } 

    
The User is given a choice of 
1 or 2 sensors (default is 2)
Key for sensor 1 (1, 2, 3 or 4)
Low range for sensor 1 (defaults given below)
High range for sensor 1
Choice of bundle plot or mean-std plot for sensor 1 (default is bundle)
If 2 sensors are chosen the corresponding: 
Key, Low, High, choice of bundle or mean-std for sensor 2

    
The charts will have fixed range on the x-axis with defaults as follows:
    
    
temperature         low    7.0     high   20.0
salinity            low   32.0     high   34.0
density             low 1024.0     high 1028.0
dissolved oxygen    low   50.0     high  300.0
    
    
These are presented as default-on-Enter so the User can type in alternative values.


There will be two control sliders to make this plot interactive. The first is the 
number of profiles to include in the bundle (or mean-std calculation as the case may be).
This is called the nProfiles slider. It ranges from 0 to 180 and is initialized to have
a value of 1. 
    
The second slider chooses the first profile index of the current bundle. This is the 
index0 slider.


Changing slider values only creates a new chart when the left mouse button is 
released.
    
If the index0 slider plus the nProfiles values exceeds the available profiles then
the chart simply plots the profiles that are available. 

    
There are to be four additional buttons in the control area laid out horizontally with
labels "--", "-", "+", "++". These affect the current value of the index0 slider. 
The "-" and "+" buttons will decrement / increment the index0 slider value by 1 profile.
The "--" and "++" buttons will decrement / increment the index0 slider by half of the
current nProfiles value. Tapping any of these four buttons updates the chart.
    
    
In the case of a bundle chart with 1 sensor: The plot width is fairly wide. 
    
    
In the case of a bundle chart with 2 sensors: The plot is wider still. That is: The
x-axis is extended to give more horizontal extent and the two sensor ranges will 
be offset from one another so that the resulting sensor bundle traces will not (ideally) 
overlap. This is done by having two respective axes, one for each sensor, where the
range of the axes is determined as follows: 
    
    
Suppose the x-axis range for sensor 1 is from `a` to `b`. For sensor 2 it is from `c` to `d`.
Then the bundle chart range will accommodate both sets of sensor profiles by having a sensor 1 
axis running from `a` to `(2b - a)`; and a sensor 2 axis running from `(2c - d)` to `d`.
In this way sensor 2 data will be displaced to the right and sensor 1 to the left so that 
the profiles do not overlap.
    
    
As a concrete example: temperature in range 7 to 20 deg C means that the x-axis for the
temperature sensor should run from 7 to 33 deg C. Then suppose sensor 2 is salinity with 
range 32 to 34: Then the chart should have a second horizontal axis with a data range 
from 30 to 34.
    
    
Include a diagnostic print statement along these lines: 
    
    
sensor 1 has range 7 to 20; chart first x-axis has range 7 to 33 to left-justify.
sensor 2 has range 32 to 34; chart second x-axis has range 30 to 34 to right-justify.
    
    
Both sensor x-axis labels are to be printed below the chart, one above the other, labeled.
This will include two tick mark bars, labeled for the respective sensors in the same 
color ink. 


## Progress made
    
Fix some issues with the latest version of the bundle chart explorer. The main description
is lines 838 to 938 of this file.
    
- The label for the second axis should go above the chart
    - It was mistakenly below the chart where it conflicts with labes for the first axis
- Use blue rather than green for the second data type
- An initial density profile was displayed but no salinity
- Changing the two sliders resulted in no change in the display
- Prompts for the sensor keys should spell out the sensor names as:
    - temperature, salinity, density, dissolved oxygen
    
## More progress
    
While the bundle plot seems to be working: With two plots both set to meanstd there is an
error as soon as I move the nProfiles slider as follows:

```
---------------------------------------------------------------------------
ValueError                                Traceback (most recent call last)
Cell In[21], line 108, in update_plot(change)
    105     if depths is None: depths = ds.depth.values
    107 if all_data:
--> 108     data_array = np.array(all_data)
    109     mean = np.nanmean(data_array, axis=0)
    110     std = np.nanstd(data_array, axis=0)

ValueError: setting an array element with a sequence. The requested array has an inhomogeneous shape after 1 dimensions. The detected shape was (24,) + inhomogeneous part.
```
    
In addition to fixing this error let's make the default response to the "which years?" question be 2023,2024.

The default number of sensors in the plot should be 2.
The default first sensor should be temperature.
The default second sensor should be salinity.
The default response to 'bundle or meanstd?' should be `meanstd`.
    
The four colors for sensors { temp, salinity, density, do } should be { red, blue, black, cyan }.

    
## Intermezzo: AstaLabs

    
I uploaded the first 81 x 4 profile files to AstaLab at AI2 to run 20 experiments. These were
{ density, dissolved oxygen, salinity, temperature } files for 2016, January 1 -- 9, 9 profiles
per day. I borrowed text from this `AIPrompt.md` file to write up context for the data exploration.
Of the 324 upload files a number (40+) had to be reloaded; an annoyance.


URL: `https://autodiscovery.allen.ai/runs/3d1b04de-de13-4a16-b6e4-43b6f874fb28`
    

    
    
    
## Synchronize localhost with S3
    
    
Python standalone `redux_s3_synch.py` in `~/argosy` rewrite:


- Re-format that time in human-readable format. 
- Order of operations:
    - Fast index: List of sensors sorted alphabetically
        - To date: 'density', 'dissolvedoxygen', 'salinity', 'temperature'
    - Medium index: Profile sequence for a given day: 1, 2, ..., 9
    - Slow index: Julian day for a given year
    - Slowest index: Year

Example 8-file sequence per the above (where `<ix>` is the appropriate profileIndices global index):
    
```
RCA_sb_sp_density_2024_217_<ix>_9_V1.nc
RCA_sb_sp_dissolvedoxygen_2024_217_<ix>_9_V1.nc
RCA_sb_sp_salinity_2024_217_<ix>_9_V1.nc
RCA_sb_sp_temperature_2024_217_<ix>_9_V1.nc
RCA_sb_sp_density_2024_218_<ix>_1_V1.nc
RCA_sb_sp_dissolvedoxygen_2024_218_<ix>_1_V1.nc
RCA_sb_sp_salinity_2024_218_<ix>_1_V1.nc
RCA_sb_sp_temperature_2024_218_<ix>_1_V1.nc
```


## Pending ideas
    
    
- Visualization revisit
    - Does the visualization code read the entire dataset into RAM at the outset? If so let's shift to reading 
only the data needed for a given chart each time the chart parameters change, for example due to moving a slider.

    
Rather than have the User choose 'bundle' or 'meanstd' as a permanent choice: Install a choice control
widget in the interface, one for each sensor being charted. The choices are 'bundle' and 'meanstd' so
the User can switch between views.
    
    
The std render is not correct.
    

## Shard rewrite
    
    
The `DataSharding.ipynb` primary sharding cell was rewritten. It generalizes instruments to include both
CTDPF and FLORT instruments (source files). The SENSOR_MAP is also expanded with key information: 


```
data variable in source file              shard name for this sensor          low extreme      high extreme
fluorometric_cdom                         cdom                                0.5              4.5
fluorometric_chlorophyll_a                chlora                              0.0              1.5
optical_backscatter                       backscatter                         0.0              0.006
```
    
    
## Work in progress on Visualization
    
    
This former prompt needs to go into the visualization bundle chart specification.
    

It is time to revisit Visualization, specifically bundle charts. We now have seven sensor types with
nitrate pending. 
    



## Visualization: Bundle chart

- User input to configure
    - Select one or two sensors from 7 available
    - Range of years, inclusive, default is 2015-2016
- Use the data range from the above table as start values
- For each sensor: Option of draw individual profiles or mean+-stdev for the current bundle
- Four advance buttons: <--> <-> <+> <++> will change the bundle range
    - <--> is earlier by half the current number of profiles rounded up
    - <->  is earlier by one profile
    - <+> and <++> are forward in time by the same amounts



### Adding MIDNIGHT/NOON and annotation file

The local time at the Oregon Slope Base site is UTC-8 during standard time and UTC-7 during
daylight savings time. Create a data structure tied to Oregon Slope Base that contains this
information. Then add the following feature:
    
When a profile bundle size is nProfiles = 1: When that profile start-end interval spans 
local midnight place the word MIDNIGHT in large font on the chart at the lower right. Likewise
when the profile start-end interval spans local noon place the word NOON in large font on the
chart at the lower right.
    
The next feature to add will be annotation per profile from a source CSV file: In the
form of either text or markers. The name of the annotation file will arbitrary so there 
will be (at the bottom of the user interface) a blank field where the user will type a 
filename such as `~/argosy/annotation.csv`. 
    
Next to the filename field place a button labeled `Annotation Load`. When this is clicked
the code will attempt to render annotations from the given CSV file. This button will toggle
on/off.
    
The CSV file must have the following column labels present in row 1: 
    
```
shard, profile, depth, value, color, markersize, opacity, text
```

`shard` will be the sensor designation as found in shard filenames.
`profile` will be the global profile Index as found in `profileIndices`.
`depth` is depth in meters, positive downward
`value` is a data value for this sensor type
`color` is a marker color
`markersize` is a marker size
`opacity` is a marker opacity
`text` is some annotation text
    
If one of the CSV fields is not present in row 1: Print a message to this effect 
and do nothing further.

For each subsequent row present: Fields can be blank by having no text, i.e. two commas `,,`
or one comma at the end `,`. The`shard` and `profile` fields can not be empty. If they
are: Print an error message and do nothing further.
    
If the text field is not empty: Print the text on the chart when the corresponding
shard is active and the single bundle profile matches the profile value. Otherwise
render a marker of the given location, size, color and opacity.

The code should in general try to print a "no can do" diagnostic message if it is 
unable to draw a given annotation, again only when nProfiles = 1. 

For marker rendering: 

    
- If no markersize is given: The marker size is 9.
- If no opacity is given: The default is fully opaque.
- If no color is given: Use the color of the `shard` sensor
- If no depth is given: Use depth = 180.
- If no value is given: Use value = center of x-axis range for this sensor
    
### Refine MIDNIGHT / NOON single profile annotation
    
In the previous step the MIDNIGHT / NOON annotations are not working well. To debug 
this revisit the logic with these two modifications to build: 
    
- The condition for a profile to be considered at local noon is: Local noon falls in 
a time window defined by [(local) `start` time - 30 minutes, (local) `end` time + 30 minutes]. 
That is: Both times defining this time window are in local time for a meaningful comparison 
to local noon. The same logic applies to local midnight.
    
- As a temporary validation measure: When printing 'NOON' or 'MIDNIGHT': Underneath that
print the profile `peak` time shifted to local time. Again this time shift is -8 hours
during standard time and -7 hours during daylight savings.
    
## More pending ideas

Concerning a diagnostic printout: 

During the User input phase of operation after selectiong 2015 - 2016 a diagnostic
print statement produces this incorrect content:
    
```
Scanning redux folders from 2015 to 2016...
  redux2015: 4394 profiles
  redux2016: 20671 profiles
```
    
This appears to be counting shard files in redux folders. Replace this with the number
of profiles for each year as found in `profileIndices`. Include the maximum possible value
after the actual value: In parentheses, as in for example: 

```
Scanning profileIndices metadata...
  2015: 578 profiles (3285 possible)
  2016: 2975 profiles (3366 possible)
```
    
Concerning NOON / MIDNIGHT determination:
    
Both NOON and MIDNIGHT profiles are distinct from the other seven possible profiles
in that the descent stage (between time `peak` and time `end` in profileIndices) takes
longer in order to allow for sensor equilibration, specifically for the pCO2 and pH 
sensors that operate on descent only. 

## Profile count calculation confusion (line ~1050):

- The diagnostic shows "4394 profiles" for 2015 but then says it should show "578 profiles (3285 possible)"
- The document correctly identifies this as counting shard files (4 sensors × ~1100 profiles ≈ 4400)
- But the logic needs clarification: Are you counting unique profiles or total shard files?

Time zone handling ambiguity:

- Mentions UTC-8/UTC-7 for standard/daylight time
- Doesn't specify when DST transitions occur (important for the NOON/MIDNIGHT logic)
- Consider adding explicit DST transition dates or using a timezone library
    
Gripes section (line ~180):

- Mentions "two streams for DO" plus a third - this unresolved question could affect the dissolved oxygen processing
- Should be investigated before finalizing the sensor variable names
    
Animation frame timing (line ~450):

- Says "If possible: Add in a 'hold time' per frame of d seconds"
- This uncertainty should be resolved - matplotlib animations support frame duration

Axis offset calculation (lines ~900-920):

- The formula for offsetting two sensor ranges is clever but could use a worked example
- The concrete example helps but doesn't match the formula exactly (should verify the math)

Profile index terminology:

- Sometimes "profile index" means global index from profileIndices
- Sometimes it means day-relative (1-9)
- Consider using distinct terms like "global_index" and "daily_profile_number"

Missing "Next" section:

- Document ends with "There is no immediate 'next' task" but earlier sections reference pending work
- Consider a prioritized task list

Recommendations:

- Create a data dictionary section consolidating all variable names with their exact spellings
- Resolve the incomplete sensor table entries
- Add explicit DST handling (or use pytz/zoneinfo)
- Clarify the profile counting logic throughout
- Consider adding a troubleshooting section for common errors

    
## To Do

- revamp animations
- curtain plots: See e.g. ~/OceanRepos/notebooks/dev_notebooks/keenan/3d_DO.ipynb
- 