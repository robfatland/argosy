# Workflow


## File system


This section describes both the repository (code + markdown) file system
at `~/argosy` and the associated data file system at `~/ooi`.


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
    - The instrument abbreviations are standardized in `SensorTable.md`
- The NetCDF raw data files are sharded into the `redux` dataset
    - The redux data folders are also found within the `~/ooi` master data folder
- Several approaches to post-processing are possible, numbered 01, 02, ...
    - This operates on sharded (redux) data with results > `~/ooi/postproc/pp<NN>`
- Data analysis methods operate on `redux` or `postproc` versions of the data
    - Results are written to `~/ooi/analysis/<subfolder>`
    - So far there are two: `analysis/clustering` and `analysis/sga`
        - `sga` refers to spectral graph analysis
- Profile Indices provided by the RCA data team reside in `~/ooi/profileIndices`
- Visualizations (typically pngs produced from charts) reside in `~/ooi/visualizations/`
    - The intent here is to set up category subfolders


```
~  -----  argosy is the repository for the Jupyter Book
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
                                                                  ----- <year>_<instrument> (vel, irr, oa, ba)
                                                                  ----- etcetera many of these
              ----- profileIndices (metadata timestamps for profile ascent/descent intervals)
              ----- metadata (other (derived) metadata; do not collide with the profileIndices repo)
                          ----- README.md
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
                             ----- depth histograms, profile duration histograms, etcetera
```


Note: Under the "umbrella expansion" topic the only steps so far are looking into the National Data Buoy Center
data. Results are temporarily in `~/argosy/NDBC`. Pursue this further: Expand the folder structure in `~/ooi`.


Note: In `~/argosy` there are some residual files that need to be sorted. For example `tmld` is an acronym
for 'temperature mixed layer depth'. This was an experiment in human-generated data by means of interactively
clicking on profile charts. It is in Python because the interactive features were not working in the IPython
notebook. The files are moved to a temporary folder `~/argosy/TMLD`.


## Pipeline tasks


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
        - Again see `SensorTable.md` for more elaboration
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
    - Bundle charts, Curtain plots, Animations etcetera
- (5) Interactive: Analysis
    - Spectral graph analysis
    - Clustering
    - And so on: Methods described in `~/argosy/Analysis.md`
- (6) Mirror data to S3


## Task 1: Data Download


### Order datasets from OOINET ('task 0, manual')


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


### Download data order


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
- Files are to be downloaded to the corresponding localhost destination folder
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


### Degenerate source / raw data files


Cells 2 and 3 of `~/argosy/chapters/DataDownload.ipynb` address redundancy in source data files.
Together they eliminate any source / raw data files with time ranges that are covered by other
source / raw data files for the same instrument. The particular focus is on CTD files that are
delivered (by default) along with other instrument files. So if we download pH and pCO2 and
nitrate files we may accidentally download multiple copies of the simultaneous CTD files.


The process is simplified by the source / raw data files containing their time range in the
filename itself.


The code in cell 2 of `DataDownloads.ipynb` looks for files with time range bounded by other
(single) files and creates a script to delete them. The code in cell 3 of `DataDownloads.ipynb`
looks for files with time range bounded by multiple other files and creates a script to
delete them.


## Task 2: Data Sharding


See `Sharding.md` for full details on the sharding process, filename conventions,
and multi-year processing.


## Task 3: PostProcessing


See `PostProcessing.md` for details on pp01, pp02, and future strategies.


## Task 4: Visualizations


See `Visualization.md` for bundle plots, curtain plots, and animations.


## Task 5: Analysis


See `Analysis.md` for spectral graph analysis, clustering, and other methods.


## Task 6: Mirror localhost data folder to S3


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


## Raw data filenames


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


## Profile metadata


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


Note: Derived information concerning profiles, for example like the indices of the
noon profiles, are not to be written into the repo directory `profileIndices`. It
should be treated as read-only so that it can be updated from GitHub without
erasing important metadata. Such metadata goes into the parallel `metadata` folder,
**not** `profileIndices`.


## Reference metadata


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
        - 1, 2, 3, 4, 5, 6, 7, 8, 9
        - Total
        - Noon
        - Midnight
    - Column values
        - The first 3 columns are straightforward
        - Each number column 1 ... 9 has value 1 or 0 based on the profile indices (present / absent)
        - Total is the sum of columns 1 ... 9
        - Noon is an index for the profile number that happened at noon local time
        - Midnight likewise
