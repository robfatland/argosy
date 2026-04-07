# AI Prompt


Contents


- Introduction for humans
- Python libraries
- Introduction for the CA
- OOI observatory
- Obstacles
- Glossary
- Websites
- Red zone goals
- Umbrella goals
- file system
- work flow
- raw data filenames
- profile metadata
- reference metadata
- sharding
- TMLD
- process the full timespan
- Sensor Table
- Visualization
- Midnight/Noon
- Tactics
- CA recommendations
- pending ideas
- next


## Introduction for humans


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
    - `Umbrella.md`: Expansion perspective (see glossary below)
    - `Cleaning.md`: Describes data filtering / cleaning
- logs development, tracks train of thought / next steps
- end of this file is a `tail` prompt
    - Heading is `## Next`
    - Usually read by the CA upon a prompt in the session box
    - Completed prompts are integrated into the log


### Publishing the Jupyter book version of `argosy`


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
- Install `xarray` and `h5netcdf` (or `netcdf4`)
- jupyter lab/book


## Introduction for the CA


This project concerns organizing and exploring oceanography data starting with 
data from the Ocean Observatories Initiative Regional Cabled Array shallow profilers. 
The idea is to transition from the archival data system to a more 
interpretable form of the data; and then to visualize, interpret and
further explore this data.


This work runs primarily on a Windows PC (assume this as default) in the WSL home file 
system, specifically `/home/username/argosy`. Within the `argosy` repo are Jupyter notebooks, 
markdown files, standalone Python modules file (`.py`) and other supporting files. 
The Python interpreter associated with execution of code is a `miniconda` installation 
with the default key `conda` environment being `argo-env2`.


When prompted for code: Write the code in a new `.py` file in `~/argosy` but do not run
it. The prompt will indicate whether the code is to run as a module or be copied to a
Jupyter notebook cell and run there. For example chart interaction will tend to run as
a module (see TMLD) whereas the bundle plot visualization will run in a Jupyter notebook.


The **Next** section at the end of this file is generally where prompts are composed.
The prompt line range is then referenced from the prompt window in the (`kiro`) VS Code IDE. 


Example: "Run on the prompt from lines 1118 - 1160 of `AIPrompt.md`."


## OOI observatory 


The Observatory consists of seven Arrays:


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


```
Site name           Latitude  Longitude   Depth (m)  D-offshore (km)
-----------------   --------  ---------   ---------  ---------------
Oregon Offshore     44.37     -124.96      577        67
Oregon Slope Base   44.53     -125.39     2910       101
Axial Base          45.83     -129.75     2620       453 
```


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


## Obstacles


- OOI can be daunting to learn
    - Dissolved oxygen example: There are three sensor streams for DO: Two in CTD files plus one in DO files.
    - What is the discovery path in the website documentation?


## Glossary


- shallow profiler, profile: A *shallow profiler* is a positively buoyant pod-shaped 
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


- Midnight profile: One of two extended profiles during any given day, running at local midnight


- Noon profile: One of two extended profiles during any given day, running at local noon


- profile chart: Sensor data from a profile is often represented as a 2D *profile chart*.
The x-axis is the sensor value and the y-axis is depth. For a shallow profiler the
depth range runs from 200 meters at the bottom to 0 meters at the top of the chart.


- bundle: A set of profiles considered collectively is often referred to as a *bundle*.
Most commonly the profiles in a bundle are consecutive in time. However a bundle may
be assembled using other criteria, for example profiles acquired at noon on consecutive
days.


- bundle chart: A profile chart containing multiple profiles, i.e. a bundle. In this 
Jupyter book bundle charts can be changed dynamically by means of two sliders: The
first corresponding to the first profile of the bundle and the second corresponding
to how many profiles are in the bundle. 


- curtain plot: A static chart of sensor data for many consecutive profiles as follows:
The horizontal axis is time, typically months to years. The vertical axis is depth as 
described for bundle charts. Sensor data is encoded using a colormap. This places 
consecutive profiles as adjacent vertical lines of color in the curtain plot. Curtain
plots are good for showing trends in sensor data with depth that develop over seasonal
time frames. 


- redux: Data from shallow profiles represent snapshots of the upper water column; placed
in the OOI data archive with the idea that they can be recovered or brought back for 
further analysis. `redux` meaning `brought back` is an identifying label used in folder
labels for shallow profiler (and other platform) data that has been brought back for
analysis. 


- shard: A *shard* is a NetCDF data file containing observational data from a single sensor 
(raster or vector) from a single profile. The name comes from the origin data files 
that typically cover multiple sensors over many days and hence many profiles.


- red zone: 'The challenge of the last 20 yards'; refers to the thematic objective 
of analyzing OOI data. The premise here being that there is an obstacle to analysis
where the sensor data is balled up with engineering data in large (500MB) complicated
NetCDF files which are in turn "hidden" within a sometimes opaque and confusing data
system.
    - *Red zone format* means 'data that is ready for scientific analysis'.
    - A synonym: 'Interpretable Data' (ID)
    - Another associated term `redux` refers to the act of bringing (data) back
    - Another associated term `shard` refers to data subsetting (see below)

- umbrella: Extending the data purview to many resources / sensors / projects
    - start: temperature profiles over several weeks
    - extend:
        - in time over the full duration of the OOI
        - to other scalar sensor types (PAR, pCO2, chlorophyll fluorescence, etc)
        - to vector sensor types (velocity, spectral irradiance, spectrophotometer sensors)
        - to specialized OOI sensors (sonar, ADCP)
        - other shallow profiler sites: Oregon Slope Base > Oregon Offshore, Axial Seamount
        - to data beyond OOI
            - circulation models such as ROMS
            - NOAA NDBC surface buoy data
            - ARGO biogeochemical drifters
            - satellite remote sensing: SST, surface chlorophyll, mean sea level anomaly
            - gliders
            - compilations: BCO DMO, GLODAP


- `SensorInformation.md` is a supporting document relating native datafile structure to red zone format.
- `ShallowProfiler.ipynb` is a supporting document in the same vein


## websites


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
    - Dataverse?
    - arXiv


## Red Zone Goals 


### Development Narrative


This is a simplified description of how this Jupyter Book is being built.


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
    

## Umbrella goals


The "umbrella" is an abstraction for "using other data resources beyond the shallow profiler
at Oregon Slope Base". This includes remote sensing data evoking the umbrella canopy above
the the umbrella pole corresponding to the profilers.


### Instruments/sensors/data streams beyond the shallow profiler 


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


## file system


- As noted `~/argosy` is the WSL location of this repository.
- We do not want the repo folder to include data files.
- The root folder for data is in the WSL filesystem at `~/ooi`
- The "high resolution" or "raw" data from OOINET resides in a subfolder `ooinet`
- The sub-folder of `ooinet` is `rca`
- This is further divided by sites: Axial Base, Oregon Offshore and Slope Base
- Our initial focus is the Slope Base shallow profiler
- Most shallow profiler instruments have one or more scalar sensors
    - This means the sensor records one measurement for each timestamp
    - These data go in the site name's `scalar` subfolder
- There are three exception instruments producing multiple values for each timestamp
    - These are velocity, spectral irradiance and a spectrophotometer
    - These data go in the `vector` subfolder
- The actual data files are in subfolders of `scalar` / `vector`
    - These subfolders are named by year and instrument type, as in `<yyyy>_<instrum>`
    - Example: Nitrate data for 2016 has folder name `~/ooi/ooinet/rca/SlopeBase/scalar/2016_nitrate`
    - The instrument abbreviations are standardized below in the **Sensor Table** section
- The NetCDF raw data files are sharded into the `redux` dataset
    - The redux data folders are also found within the `~/ooi` master data folder
- Several approaches to post-processing are possible, numbered 01, 02, ...
    - This operates on sharded (redux) data with results > `~/ooi/postproc/pp<NN>`
- Data analysis methods operate on `redux` or `postproc` versions of the data
    - Results are written to `~/ooi/analysis/<subfolder>`

```
~  -----  argosy is the respository for the Jupyter Book
                 home directory `~/argosy` is used for working scripts and markdown
                 ----- chapters subfolder: Jupyter Book chapters
 
~  -----  ooi is the root data folder
              ----- ooinet
                           ----- rca
                                     ----- AxialBase
                                                     ----- (follow pattern of SlopeBase)
                                     ----- OregonOffshore
                                                     ----- (follow pattern of SlopeBase)
                                     ----- SlopeBase
                                                     ----- scalar
                                                                  ----- <year>_<instrument>
                                                                  ----- ...etcetera: many of these
                                                     ----- vector
                                                                  ----- <year>_<instrument>
                                                                  ----- etcetera many of these
              ----- profileIndices (metadata timestamps for profile ascent/descent intervals)
              ----- redux 
                          ----- redux2014
                          ----- redux2015
                          ----- redux2016
                          ----- and so on through 2026
                          ----- redux2026 note redux<yyyy> holds many many (small) NetCDF data files
              ----- postproc
                             ----- pp01
                             ----- pp02
                             ----- pp03
                             ----- pp04
                             ----- and so on as methods develop
              ----- analysis 
                             ----- sga for spectral graph analysis 
                             ----- clustering
                             ----- and so on for other methods
              ----- visualizations
                                   ----- TBD; for static images and animations
              
```


Note: Under the "umbrella expansion" topic the only steps so far are looking into the National Data Buoy Center
data. Results are temporarily in `~/argosy/NDBC`.


Note: In `~/argosy` there are some residual files that need to be sorted. For example `tmld` is an acronym
for 'temperature mixed layer depth'. This was an experiment in human-generated data by means of interactively
clicking on profile charts. It is in Python because the interactive features were not working in the IPython
notebook. The files are moved to a temporary folder `~/argosy/TMLD`.


## workflow


Tasks:


- (0) Manual data order through browser interface
- (1) Automated: Data download (script)
    - Data comes from the OOINET server, 'ready' notification by email
    - URLs copied into download script: See `~/argosy/chapters/DataDownload.ipynb`
    - Data > localhost `~/ooi/ooinet/rca/Site/{scalar or vector}/<year_instrument>/fnm.nc`
    - Additional step: Scan for and delete superfluous (time-overlap) data files
- (2) Automated: Sharding from above source/raw files to `~/ooi/redux/redux2018/etcetera`
    - These NetCDF shard files are sorted by profile sequence and sensor (not instrument)
    - Hence the CTD instrument produces 4 shard sensor types:
        - Temperature, Salinity, Density, Dissolved Oxygen (with time and depth)
        - The naming system post-raw-files is tied to the **Sensor Table**
    - Other instruments produce one or more shard sensor datasets
        - Again see the **Sensor Table** for more elaboration
        - Most instruments produce 'single value per observation' data
            - These I refer to as *scalar* sensors
        - Exception: Four instruments produce multiple-value observations
            - For: velocity, spectral irradiance, optical absorption and beam attenuation
    - See `~/argosy/chapters/DataSharding.ipynb`
    - Some sensors are activated only during local-midnight and local-noon profiles
        - To identify when these happen there is a code block added to `DataSharding.ipynb`
        - This cell generates CSV files for midnight profiles and for noon profiles
- (3) Automated: Post-processing
    - Shard files are evaluated based on various criteria
        - Example: profile signal is kinked at the bottom or top of the profile
        - Example: various filtering strategies to try and reduce noise etc
        - A given post-processing strategy is assigned a two-digit number NN: 01, 02, ...
    - Post-processing results written to folders `~/ooi/postproc/pp<NN>`
- (4) Interactive: Visualizations
    - Bundle charts, Curtain charts, Animations etcetera
- (5) Interactive: Analysis
    - Spectral graph analysis
    - Clustering
    - And so on: Methods described in `~/argosy/Analysis.md`
- (6) Mirror data to S3
   

Some elaboration on these tasks follows.


### Task 1: Data Download


#### Order datasets from OOINET ('task 0, manual')


- Log in to OOI [access page](https://ooinet.oceanobservatories.org/data_access) with an established account
- LHS filters: Array, Cable, Platform, Instrument
- Data Catalog box (bottom center)
    - ***Do not try and use the time window interface***
    - ***+*** Action button: Download table appears top center
        - Also: Data availability plot, center center
    - Top center: Download button generates a data order
        - ***Select datasets with Stream type == `Science`***
        - > Pop up to finalize order
            - Calendars: Type in time range manually e.g. `2015-01-01 00:00:00.0`
            - Optional:
                - Un-check the box for **Download All Parameters**
                - Use ctrl-click to select parameters of interest
            - Submit the order
            - "Order ready" email sent to account usually < 2 hours


#### Download data order


Task 0 results in an email with URLs to the OOINET data server directory. 
The download retrieves NetCDF files from that OOINET staging area. 
Retrieval / management code is in notebook `DataDownload.ipynb`.


An OOINET filename example:


`deployment0004_RS01SBPS-SF01A-2A-CTDPFA102-streamed-ctdpf_sbe43_sample_20180208T000000.840174-20180226T115959.391002.nc`


Breakdown of this filename (partially understood):


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
control data. This example includes data from 157 cycles of the shallow profiler: ascent,
descent, rest. These source files are dense amalgams of information that can be overwhelming 
to work with.


Massive download jobs are subject to interruption so we want the code to be tolerant of
re-starting after only partial completion. Here is the code spec; should run in a single
Jupyter cell in the `DownloadData.ipynb` notebook.

    
- Open a file `~/argosy/download_link_list.txt`
    - Each line is a URL for a distinct data order
        - For each URL print a diagnostic of 
            - how many `.nc` files are present
            - how many have already been downloaded
            - how many remain to download
    - At that URL is a collection of files to download
- We want to download files that are not yet fully downloaded; otherwise skip
- Files are to be downloaded to the corresponging localhost destination folder
    - The base localhost folder location is `~/ooi/ooinet/rca/SlopeBase/scalar/<yyyy>_<instrument>`
    - If a destination folder does not exist: Print a message and halt
    - The destination folder name `yyyy` value is a year from 2014 to 2026
    - `<instrument>` is taken from the **Sensor Table**
- To determine the destination folder for a particular `.nc` file: 
    - Parse the `.nc` filename as:
    - `<first_part>_yyyyMMddTHHmmss.ssssss-yyyyMMddTHHmmss.ssssss.nc`
        - This maps to `<first_part>_datetime-datetime.nc`
        - The first datetime: year `yyyy` month `MM` day `dd` literal character `T`...
            - ...followed by hour `HH` minute `mm` second `ss.ssssss`
        - Second datetime follows the same format.
    - Destination folder `yyyy` is chosen as the same `yyyy` as the first datetime.
- Download the `.nc` NetCDF files and ignore the `.ncml` files
    - Some downloaded files will have a time dimension that crosses the year boundary


#### Degenerate source / raw data files


Cells 2 and 3 of `~/argosy/chapters/DataDownload.ipynb` address redundancy in source data files. 
Together they eliminate any source / raw data files with time ranges that are covered by other 
source / raw data files for the same instrument. The particular focus in on CTD files that are
delivered (by default) along with other instrument files. So if we download pH and pCO2 and 
nitrate files we may accidentally download multiple copies of the simultaneous CTD files. 


The process is simplified by the source / raw data files containing their time range in the
filename itself. 


The code in cell 2 of `DataDownloads.ipynb` looks for files with time range bounded by other
(single) files and creates a script to delete them . The code in cell 3 of `DataDownloads.ipynb` 
looks for files with time range bounded by multiple other files and creates a script to 
delete them. 


### Task 2: Data Sharding


It will prove convenient to 'shard' (break up) source files by sensor type and by 
individual profile; and then to compartmentalize shards by year (folder name `redux<YYYY>`).
Code for this and related operations is in `DataSharding.ipynb`.


One output file (a shard) corresponds to one profile and one sensor type, for example temperature 
data. Most profile data is acquired on ascent (as the sensor intrudes upward into undisturbed
water). There are a couple of exceptions, pCO2 and pH. Many profile files (shards) are written 
to `redux` folders labeled by year. Each single-sensor profile shard file is about 100kb in 
comparison with source files that are typically 500MB. Multiple sensor types are written to
the same 'by year' folder.


Shard folder name example: `~/ooi/redux/redux2018`


Shard filename example: `RCA_sb_sp_temperature_2018_296_6261_7_V1.nc`


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


The version number for sharding anticipates future improvements, for 
example using QA/QC metadata to evaluate usability of a particular profile.


#### midnight and noon profiles


The `DataSharding.ipynb` cell concerned with identifying midnight and noon profiles
produced this table on 06-APR-2026:


```
Year    Midnight      Noon   Active Days
  ----    --------      ----   -----------
  2015          66        78            97
  2016         327       330           342
  2017         155       159           161
  2018         204       211           218
  2019         233       235           243
  2020         141       143           146
  2021         330       331           336
  2022         262       264           265
  2023         154       159           161
  2024         255       256           263
  2025         314       313           326
 Total        2441      2479          2558
 ```


This indicates that the numbers of successful midnight and noon profile days are similar 
to one another in each year as we would expect. Also both are a little less than the 
number of days each year in which at least one of the other 7 profiles ran, also to be
expected.


The lists of midnight and noon profiles are kept in these two CSV files:


```
~/argosy/profiles_midnight.csv With columns index, start, peak, end
~/argosy/profiles_noon.csv     Ditto
```


The code also produces histograms of ascent, descent and total profile durations.



### Task 3: PostProcessing


This is pending work. Considerations include:


- Reducing the collection of analysis datasets based on additional criteria, e.g. QA/QC
- Noisy data at the top of a profile; proximity to the surface / wave action
- Low-pass filters applied along the depth axis
- Hi-pass filters that preserve transients ('hypothetical thin layers')
- Automated anomaly detection and search for coincidence
    - An excursion feature for a sensor persists over multiple profiles
    - An excursion feature for a sensor matches one for another sensor


A given postprocessing strategy is developed and applied to redux/shard data to produce
a new dataset in one of the `~/ooi/postproc` folders: `pp01`, `pp02` etcetera.


### Task 4: Visualizations


Working from sharded data build out both interactive visualizations and data 
animation generators. Code for this and related tasks is in `Visualizations.ipynb`.


A bundle plotter is an interactive visualization tool running in a Jupyter notebook 
cell that plots $N$ (slider 1) consecutive profiles together starting at profile $T$
(slider 2). Slider 2 can be dragged through time to scan the evolution of the epipelagic
through the lens of a given sensor.  anomalies, seasonal trends, mixed layer depth changes 
with season, possible sensor artifacts, and so on.
    

### Task 5: Analysis


No text for this yet.


### Task 6: Mirror localhost data folder to S3
    
    
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


    
## raw data filenames
    

Example: `deployment0004_RS01SBPS-SF01A-2A-CTDPFA102-streamed-ctdpf_sbe43_sample_20180208T000000.840174-20180226T115959.391002.nc`

    
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


The NetCDF file will have `data variables`, `coordinates`, `dimensions` and `attributes`.
The default Dimension is Observation `obs`. The Dimension we want to use is `time`.
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



## profile metadata


Profile metadata for both shallow and deep profilers is maintained in a public GitHub
repository as a set of CSV files delineated by platform and year. Each row of a
metadata file corresponds to a unique profile. This repository is cloned from 
GitHub to the location `~/ooi/profileIndices`.
    
    
The first column of the profile CSV file is a global index (a profile counter) specific 
to that profiler. The value in this column begins at 1 at the start of the profiler 
operation. Example: RCA OSB shallow profiler deployment in July 9 2015 begins with 
profile 1. This global index for this shallow profiler exceeds 20,000 in early 2026. 
    
    
In addition to the global index column, the metadata file has 3 additional columns. 
A profiler is in one of three phases and consequently divides its time between them:
Ascent, Descent, and Rest. The three additional profileIndices metadata columns are 
associated with the start time of ascent, the peak time of that ascent, and the time 
that the profiler completes its descent, returning to its support structure. 
The associated column names are `start`, `peak`, `end`. 


The GitHub repository **Organization** is 'OOI-CabledArray'. The repository of 
interest is 'profileIndices'. The repo can be cloned using:


```
cd ~/ooi
git clone https://github.com/OOI-CabledArray/profileIndices
```

Details: 


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


In the initial work we are concerned with `RS01SBPS`.


To select profile time-series data from a sensor/instrument on the Oregon Slope Base shallow 
profiler: Use time ranges in `~/ooi/profileIndices/RS01SBPS_profiles_2018.csv`. 


Note: Some sensors operate continuously (such as CTD temperature). Others operate
at a lower duty cycle, for example only during selected phases of a profile. Most
sensors operate (at least) during ascent with two notable exceptions: `pH` and `pCO2`.


For an instrument / sensor that operates on ascent the time range for a given 
profile would be given by columns 2 and 3: `start` and `peak`. For a descending
instrument the time range would be defined by `peak` and `end`.

    
Time format: `yyyy-MM-dd hh:mm:ss`.
    

Note: Noon and midnight profiles tend to have longer duration owing to a slower descent 
profile. Descent has built-in pauses allowing the sensors to equilibrate.


## reference metadata


This idea is described here for future implementation. No action at this time.
    

Goal: Produce a data availability/quality description for the sharded dataset.
This should be built when it helps achieve a specific goal.

    
Example design concept:
    

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


## sharding 


### translating source / raw input files to `~/ooi/redux/redux<YYYY>` folders / profile+sensor files


Instrument source / raw input folders are sorted as noted by year: `2018_ctd`, `2015_par` etcetera.


- Transcribe the bulk CTD file named above to a set of single-profile sensor data files
- These will be referred to as *redux files* or equivalently *shard files*.
- The output is XArray Datasets written as NetCDF files.
- The `dimension` of the output files will be `time` via `.swap_dims()`
- Using CTD temperature as an example: 
    - The data variable will be `sea_water_temperature` (input data variable) 
    - This will be written as data variable `temperature` in the output file
- The file will include coordinate `depth`
- The output folder will be `~/ooi/redux/redux2018` where the individual profile files will be written. 
- One file is written per profile


The output folders are `~/ooi/redux/redux<yyyy>`


The filename format for each redux profile `.nc` file:


- The filename format will be `AAA_SSS_TTT_BBB_YYYY_DDD_PPPPP_Q_VVVV.nc`
- These are to be filled in as follows for now:
    - AAA  = Array name: Using `RCA` for Regional Cabled Array
    - SSS  = Site: Using `sb` = Oregon Slope Base
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


```/tmp/ipykernel_206172/2169783661.py:91: Performance Warning: DataFrame is highly fragmented. (etcetera)```





## TMLD


### Estimated Temperature Mixed Layer Depth
    

This part of the project is on hold; no action. 


A human-driven TMLD picker program was written in Python. This is not Jupyter cell code because 
the Jupyter configuration does not support interactive chart location selection.
    

- Generate a CSV file with three columns, resides in `~/argosy/TMLD`.
    - First column = profile index as recorded in the profile filename in ~/ooi/redux/redux2018
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


## Process the full timespan


- List <instrum> files in a "to do" file
    - From the folders where the original <instrum> data file is located
- Create a new file listing all of the <instrum> files in that folder
    - Let us call this file `~/argosy/source_<instrum>_filelist.txt`
    - The first line will be the full path to the folder
    - The remaining lines are 1 line per <instrum> file
- Process these files to expand the time series for Oregon Slope Base shallow profiler <sensor> profiles
    - Example sensors: `dissolvedoxygen`, `density`, `salinity` 
    - Use those strings in the output filenames sensor field
- Input file location for year `<YYYY>` is `~/ooi/ooinet/rca/SlopeBase/scalar/<YYYY>_ctd`
- The original input file was:
    - `deployment0004_RS01SBPS-SF01A-2A-CTDPFA102-streamed-ctdpf_sbe43_sample_20180208T000000.840174-20180226T115959.391002.nc`
    - The string `CTDPF` indicates a CTD file. File extension must be `.nc`
    - Compile the source file list in `~/argosy/source_<instrum>_filelist.txt` as described above 


### Multi-year redux generator


This text may be somewhat redundant to what came above (to reconcile)
    
- Rewrite the redux code that runs in a Jupyter notebook cell
    - This scans multiple folders for (large) CTD source datafiles
        - If the folder is not found: Skip it
        - If a source folder is found that spans year breaks: Be sure to write outputs to the correct year-folder
        - We are still focused on just temperature data
        - The output files are called `redux` files
        - There follows some more detail on how this code will work
    - Source data folders have name format `~/ooi/ooinet/rca/SlopeBase/scalar/<yyyy>_<instrum>`
        - <yyyy> runs from 2014 through 2026
        - <instrum> designators are found in the **Sensor Table**
        - The program should prompt for y/n for each year (folder) for which there is data 
            - This prompt defaults to `y`
    - Output files as developed earlier with these changes:
        - remove data variables `lat` and `lon` and remove `obs` from the output `.nc` file. Retain time, depth and temperature.
        - when writing the output `redux` file: select destination folder based on this profile's year as follows:
            - a profile from 2018 will be written to `~/ooi/redux/redux2018`
            - a profile from 2019 will be written to `~/ooi/redux/redux2019`
            - and so forth: Possible year values are 2014 through 2026

    

### sensor compilation from many source <instrum> files
    

From a Jupyter cell Python script: Read the entries in the `~/argosy/source_<instrum>_filelist.txt` generated
above. The instrument name <instrum> is from the `key` column of the **Sensor Table**.
For each file listed we want to perform the following procedure: 

    
- Print the data file directory on a line
- Print the name of the current file on the next line
- Print `<start date> - <end date>` on the next line
- Print whether or not `sea_water_temperature` is present as a data variable in the file
    - If it is not present: 
        - State this
        - State the data variables that *are* present
        - prompt the User for instructions: `Continue [C] or Halt [H]?`
- For this input CTD file start a counter of how many profile files have been written to `~/ooi/redux/redux2018`
- Formulate the filename for the current profile
- Using the appropriate `start` and `peak` times from the appropriate `~/ooi/profileIndices` folder CSV file: 
    - Extract and write a temperature profile file to the folder `~/ooi/redux/redux2018` following the same format as before
    - In this process: Keep a running sum of how many data samples there are in each profile
    - Output files in ~/ooi/redux/redux2018 feature sea_water_temperature renamed `temperature` plus `depth` against dimension `time`
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


## Sensor table 
    

### Code to list datafile variables
    
    
```
import xarray as xr
ds = xr.open_dataset('<some_path>/<some_file>.nc')
ds
ds.data_vars.keys()
```
    
    
Source file structure: 
    
    
```
dimension
    obs(ervation) --> convert to time using swap_dims()

coordinates
    observation
    lat
    lon
    depth
    time

data variables
    sea_water_practical_salinity        Note use of prefix "sea_water_" for research analysis
    <many other types>

attributes
    <many; ignoring for now>
```


    
### Sensor table columns
    
    
The **sensor table** is a comprehensive list of sensor types for the shallow profiler. 
This will eventually be written to a standalone reference CSV file. 
    
    
Premise: Jupyter cell code in the `DataSharding.ipynb` notebook shards multiple types of 
source 'instrument' NetCDF datafiles to produce single-sensor shard files, one file
per profile. Shards are written into folders spanning single years; with folder names
`~/ooi/redux/redux<yyyy>` where `<yyyy>` is a four-digit year. The sensor table localizes the
metadata concerned with managing the sensor data.
    
    
Sensors correspond to rows of the sensor table. Not included in the sensor table are 
`time` and `depth` which are ancillary: `time` as dimension/coordinate and `depth` 
as data variable (XArray terminology). These define the two-dimensional framework for
for the sensor data. 
    
    
Here is the sensor table column information, columns going left to right.
Format of this table: column content, short column name, some elaboration


```
- sensor name,          sensor,  a descriptive "normal text" name
- source instrument,    instrum, OOI five-letter key from reference designator e.g. CTDPF, FLORT
- ooinet download key,  key,     short abbreviation of instrument name used in download folder name
- sensor data variable, datavar, the science data variable of interest for this sensor e.g. `sea_water_temperature`
- shard sensor name,    shard,   for `redux` sensor filename; e.g. RCA_sb_sp_dissolvedoxygen_2021_185_11876_3_V1.nc
- acquisition side:     side,    `ascent` or `descent` (mostly ascent; pCO2 and pH are the notable descending acquisitions)
- data extreme low,     xlow,    well below the expected data minimum
- data extreme high,    xhigh,   well above the expected data maximum
```
    
### Sensor table


For datavar == `vector` the actual data variable name is deferred; see not below.
    
```
sensor,         instrum,  key,  datavar,                      shard,           side,     xlow,  xhigh
temperature,      CTDPF,  ctd,  sea_water_temperature,        temperature,     ascent,    6.0,   20.0
salinity,         CTDPF,  ctd,  sea_water_practical_salinity, salinity,        ascent,   32.0,   36.0
density,          CTDPF,  ctd,  sea_water_density,            density,         ascent, 1024.0, 1028.0
dissolved oxygen, CTDPF,  ctd,  corrected_dissolved_oxygen,   dissolvedoxygen, ascent,   50.0,  300.0
nitrate,          NUTNR, nitr,  salinity_corrected_nitrate,   nitrate,         ascent,      0,     35
CDOM,             FLORT, flor,  fluorometric_cdom,            cdom,            ascent,    0.5,    4.5
Chlorophyll-A,    FLORT, flor,  fluorometric_chlorophyll_a,   chlora,          ascent,    0.0,    1.5
backscatter,      FLORT, flor,  optical_backscatter,          backscatter,     ascent,    0.0,    0.006
pCO2,             PCO2W, pco2,  pco2_seawater,                pco2,           descent,  200.0, 1200.0
pH,               PHSEN,   ph,  ph_seawater,                  ph,             descent,    7.6,    8.2
PAR,              PARAD,  par,  ?,                            par,             ascent,      0,    300
velocity,         VELPT,  vel,  (vector)x3,                   vel,             ascent,    -.4,     .4
spectralirrad,    SPKIR,  irr,  (vector)x7,                   irr,             ascent,      0,     15
opticalabsorb,    OPTAA,   oa,  (vector)x73,                  oa,              ascent,    .15,    .25
beamattenuation,  OPTAA,   ba,  (vector)x73,                  ba,              ascent,    0.0,    0.2
```


The table above needs a consistent convention for vector sensors. `vel` is `east/north/up` i.e. 3 values. 
`spectralirrad` is `si412-si443-si490-si510-si555-si620-si683` i.e. 7 values. `oa` and `ba` are not 
resolved yet but each has 73 values. 
    

Also need to look up the datavar for `PAR`.
    
    
#### Velocity

    
current
    
    
east                      'Current: East'          
north                     'Current: North'
up                        'Current: Vertical'
    

#### Spectral Irradiance
    

si412                     'Spectral Irradiance 412nm'
si443                     'Spectral Irradiance 443nm'
si490                     'Spectral Irradiance 490nm'
si510                     'Spectral Irradiance 510nm'
si555                     'Spectral Irradiance 555nm'
si620                     'Spectral Irradiance 620nm'
si683                     'Spectral Irradiance 683nm'

    
#### Spectrophotometer
    

Incomplete: Two sensors: Optical absorbance and beam attenuation; 73 channels 
for each but some of the edge channels are to be ignored.


c001
c002
...
c073


#### Dissolved Oxygen


**It seems that Dissolved Oxygen is identical to the DO found bundled in the 
CTD data files rendering the separate DO product redundant.**


Data variables:

    
```
sea_water_practical_salinity
sea_water_temperature
corrected_dissolved_oxygen
```


This is from working with the CA and should be verified with the OOI staff. First the CA claims that
DO files are distinct from dissolved oxygen found in CTD files. Quoting:
    

```
### Why OOI Created Separate DO Files

    
Instrument separation: The dedicated DO files come from the Aanderaa oxygen optode (a standalone sensor), 
while CTD files come from the SBE 52-MP CTD package. They're physically different instruments...
```


Comparison shows both CTD streams and the DO data identical. 
To Do: Confirm from the OOI site: `corrected_dissolved_oxygen` from the CTD file is science-ready data. 
    
    
#### Nitrate


For OOI RCA nitrate measurements using SUNA (Submersible Ultraviolet Nitrate Analyzer) 
sensors: Initial observation is a UV absorption spectrum measured with light passing 
through a sample. The nitrate dark sample data is taken with the light source *off*:
electronic noise, detector dark current and ambient light (no nitrate signal). 
Corrected Nitrate = Sample Data - Dark Sample Data. A subsequent salinity correction
arrives at `salinity_corrected_nitrate`.



    
    
## Visualization 

    
### Vis 1
    
    
Visualization sections are numbered in sequence with sub-topic to follow:
    

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
        - the code will need to translate from the index0 value to the corresponding filename from `~/ooi/redux/redux2018`
        - if the bundle specifications `nProfiles` and `index0` go over the end file (file 157) the code handles this gracefully
        - The bundle plot only refreshes when the User is done dragging the slider to a new value (left mouse button release)
- Each refresh of the bundle plot should indicate the profile range as `yyyy-doy-profile to yyyy-doy-profile`:
    - yyyy is year
    - doy is day of year or Julian day
    - profile is a day-relative profile number from 1 to 9

    
### Vis 2
    
    
#### Bundle animation
    

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

    
### Vis 3 
    
    
#### curtain plots
    
    
### Refreshing the two visualization cells: Bundle charts and bundle animation
    

This text is flagged 'reconciliation needed'
    

So far we have two visualizations: A bundle chart with two time sliders; and a bundle chart animation generator. 
As in the previous step we want both of these to be written to cope with redux files distributed through single-year
folders: redux2014, redux2015, ...and so on through..., redux2026. 
    
    
We now have working bundle chart code running in a Jupyter notebook cell. 
    
    
We also have a bundle animator; but it needs some modifications.

    
As with the bundle chart the animator features a pre-scan with User interaction, first to confirm using the various
populated `~/ooi/redux/redux<yyyy>` folders. This sets up the year range of the animation.
    
    
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
    
 
### Multi-sensor Bundle / Mean-std charts
    
    
This is the most recent specification for the sensor data bundle plotter. 
    
    
    
    
One of the recurring 
errors in recent revisions has been overlaying two horizontal axis ranges. This can be done in
matplotlib with careful attention to `axis`. What we want to *avoid* is plotting data from two 
different sensors using a single x-axis range. 


The sensor data bundle plotter runs in a Jupyter cell.
    

It first inputs from the User what years should be included in the profile time range,
corresponding to `~/ooi/redux/redux<yyyy>` folders.
    
    
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

    
The charts will have fixed range on the x-axis with defaults taken from
the **Sensor Table**.
    
    
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



### visualization questions, ideas
    
    
- Visualization revisit
    - Does the visualization code read the entire dataset into RAM at the outset? 
    - If so let's shift to reading only the data needed for a given chart...
        - ...each time the chart parameters change, for example due to moving a slider.

    
Rather than have the User choose 'bundle' or 'meanstd' as a permanent choice: Install a choice control
widget in the interface, one for each sensor being charted. The choices are 'bundle' and 'meanstd' so
the User can switch between views.
    
   

## Midnight/Noon
    

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

    
## Tactics

    
### Profile count calculation confusion (line ~1050):

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



## CA Recommendations

    
- Create a data dictionary section consolidating all variable names with their exact spellings
- Resolve the incomplete sensor table entries
- Add explicit DST handling (or use pytz/zoneinfo)
- Clarify the profile counting logic throughout
- Consider adding a troubleshooting section for common errors

    
## pending ideas

Concerning a diagnostic printout: 

During the User input phase of operation after selecting 2015 - 2016 a diagnostic
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
    

- redo backscatter shard: optical_backscatter, not total_volume_scattering_etcetera
- revamp animations
- add curtain plots: See e.g. ~/OceanRepos/notebooks/dev_notebooks/keenan/3d_DO.ipynb
- clear identification of which profiles are midnight, which are noon, which are neither
- fix PAR in the Sensor Table
- 2020 T vs S has some odd behaviors
    - seems like a Wide Aneurism appears in salinity but + / - buttons do not behave as expected
        - some kind of hysteresis where there should not be any
    - suggest making mean/std box width a slider
    
    
## Next
    
Before turning to PostProcessing and related topics: Let's get a start on curtain plots. These
plots encode data with color. As a first example let's use salinity data over the interval of
2024 through 2025. The color table used should correspond to about the central 80% of the
dynamic range of the data over this interval. The vertical axis is depth with 0 at the top of
the chart and 200 meters at the bottom. The horizontal axis is time, running from 01-JAN-2024
through 31-DEC-2025. While processing the data for the plot: There should be a "by 10%"
progress tracking printout. The chart should be pretty large. When no profile is available
do nothing; the background of the plot is white.
    
Write this code to run in a Jupyter cell (Visualizations.ipynb), saving it to ~/argosy/chapters
as `curtain_plot.py`.
    
