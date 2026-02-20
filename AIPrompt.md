# AI Prompt


## Introduction for humans


For humans: This document is project background and prompts for a Coding Assistant (CA). 
Initial work used CA = Q Developer from AWS powered by Claude Sonnet. Q Dev is not Agentic;
however its successor Kiro (also from AWS) will be; this is circa early 2026. This file
lays out project goals and acts a progress journal in relation to those goals. New CA 
sessions can scan this to quickly boot up the context.


## Introduction for coding agent (aka coding assistant)


For CA: This effort concerns organizing oceanography data starting with data produced by the
Ocean Observatories Initiative; in fact specifically focusing on the Regional Cabled Array
shallow profilers. The underlying idea is to transition from a somewhat daunting archival data 
system to data and visualizations amenable to physical interpretation. This markdown file
is intended as context for a Coding Assistant. 


The CA with no context at the start of a chat session is directed to read this document
in its entirety. With that done an immediate prompt is found at the bottom
of this file under the heading **Next**. The line range of this prompt 
is provided to the CA in the IDE chat window as a meta-prompt, for example:


"Get the next prompt from lines 300 - 342 of `AIPrompt.md`."


As a **Next** prompt is addressed: It is either accepted or undergoes some iterative refinement.
For this reason it is ideal if the **Next** prompt is written to convey a complete specification.
Once any iteration is done: The prompt text is migrated upward (and rewritten as necessary) into 
the descriptive context body of the document.


## An quick sketch of the initial workflow


In three stages:


(1) Begin with a NetCDF file retrieved from the OOINET staging area (a data order delivery). Filename example: 


`deployment0004_RS01SBPS-SF01A-2A-CTDPFA102-streamed-ctdpf_sbe43_sample_20180208T000000.840174-20180226T115959.391002.nc`


This includes 157 ascent profiles, with many sensor types built into a CTD; in a 400MB `.nc` file. The data
are *not* pre-assigned as ascent profiles. Rather the data file is a continuous time series containing
ascents, descents and rest intervals from the shallow profiler.


Note this file covers a period of time in 2018. It will prove convenient to compartmentalize data by year.


(2) One output file corresponds to one ascent profile with temperature data. Many such files written to 
a dedicated directory. Each file is 100kb. Filename example: 


`RCA_sb_sp_temperature_2018_296_6261_7_V1.nc`


This captures array, site, platform, sensor type, year, day of year, profile number (metadata version), profile number (day of), extractor version.


(3) Bundle plotter and other visualizations. A bundle plotter is a double-slider visualization tool running in a Jupyter notebook 
cell that plots N consecutive profiles together (slider 1) starting at profile T (slider 2). Slider 2 can be dragged through time 
so as to scan this sensor's view of the epipelagic: We see anomalies, seasonal trends, mixed layer depth changes with season, 
possible sensor artifacts, etcetera.


<Place a screenshot here.>
    

## Special terminology


- Red Zone (the challenge of the last 20 yards): Aggregate and organize OOI data for scientific analysis.
    - In particular I may use *red zone format* to mean 'data ready for scientific analysis'.
    - This is related in meaning to `redux` data: Profiles stripped out of source datasets and written as individual NetCDF files.
- Umbrella: Extend the analysis space to include specialized instruments in OOI (sonar, spectrophotometer) and from other programs.
- Bundle plot: Multiple profiles from a sensor displayed together, potentially with a stride, potentially with a color coding scheme
- Midnight: One of two extended profiles during any given day, running at local midnight
- Noon: One of two extended profiles during any given day, running at local noon
- `SensorInformation.md` is a supporting document relating native datafile structure to red zone format.
    

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
- The CA should always place a comment at or near the top of code as the title
    - Comment is between one and four lines in length
    - Comment briefly tells what this code does
    - Comment briefly indicates where this execution occurs in the workflow


## Code locations


These are IPython notebooks in development. Eventually this code can be migrated 
to a workflow as straight up .py Python files. 

- No code: Data order, done by a human on the OOINET website
- `DataDownload.ipynb`
    - A data order is generated on the OOINET system (full time resolution)
    - It appears usually between minutes to hours: email notification
    - DataDownloader uses the delivery URL to build a `bash` script
    - The script downloads (multiple NetCDF) datafiles from the OOINET server
    - These files are input to DataStreamline
- No code: Copy the source NetCDF files to an S3 bucket
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
of the active arrays are continuously subjected to maintenance.


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


## Jupyter notebook cell code: Bundle plots for temperature profiles


Create a code block to run in a Jupyter notebook cell that will generate bundle plots as follows:


- Code uses matplotlib
- marker size is 1
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


## Experiment: Can the CA identify mixed layer depth from a text description? 


No: The code primarily just selected the top of the profile. We do not have time to teach the AI how 
to do this better without some examples so (after this description) we request a picker program.


- Generate a CSV file with three columns to reside in this directory.
    - First column is profile index as recorded in the profile filenames in ~/redux2018
    - Second column is `Estimated TMLD` 
        - This stands for 'Estimated Temperature Mixed Layer Depth'
        - It is a depth in meters measured positive-downward
        - It is described below
        - We want to test if you the AI CA are able to make these estimates from a text description
    - Third column is the temperature at that depth for that profile
    - As there are 157 profiles in ~/redux2018 this file (with header) will be 158 lines
- Estimated Temperature Mixed Layer Depth description
    - The upper N meters of the water column is well-mixed due to wave action etcetera
    - At the bottom of this layer at a depth of N meters the temperature begins to decrease with depth
    - The temperature continues to drop with depth with the gradient becoming less sharp
    - The TMLD is this value N; it often appears as a distinct kink in the profile chart
- Modify the Jupyter cell bundle plotter from the previous prompt as follows:
    - Read the TMLD CSV file generated above
    - Make the bundle plots exactly as before
    - For each profile add a marker at the TMLD depth and temperature for that profile
        - This marker should be larger to make it obvious but not enormous


## TMLD generator


We will now generate a TMLD file by recording left-mouse-clicks on each profile chart. 
This is User driven; and as the interactive mouse clicks were not working the Jupyter 
notebook we will run this as a standalone Python program. 


To be tolerant of User error we log the most recent click (selected TMLD point) only after
the User hits Enter. 


Whereupon the click location (depth and temperature) is transcribed as a next row in the TMLD file. 


The program displays N/P where N is the number of profiles completed 
so far and P is the total number of profiles, equal to the number of files in 
the ~/redux2018 folder for temperature data.


Cursor location is printed near the chart as depth and temperature.


## List the CTD files in a "to do" file
    

- Return to the folder where the original CTD data file is located
- Create a new file listing all of the CTD files in that folder
    - Let us call this file `source_ctd_filelist.txt`
    - The first line will be the full path to the folder
    - The remaining lines are 1 line per CTD file
- This list of files will be processed sequentially to expand the time series for Oregon Slope Base shallow profiler temperature profiles
    - The output will be additional NetCDF temperature profile files in ~/redux2018
- As a reminder the input file location is `~/ooidata/rca/sb/scalar/2015_2025_ctd`
- As a reminder the original input file is called:
    - `deployment0004_RS01SBPS-SF01A-2A-CTDPFA102-streamed-ctdpf_sbe43_sample_20180208T000000.840174-20180226T115959.391002.nc`
    - Notice that in this file name we see the string `CTDPF` which indicates a CTD file
    - Notice the file extension is `.nc` which indicates a NetCDF file
    - Both of these conditions must be met for the filename to be placed into `source_ctd_filelist.txt` 


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


## Bundle animation
    

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



## Expand sensor list to 4: temperature, salinity, density, dissolved oxygen
    
    
It is time to start diversifying sensor types from one (temperature) to four. This means
a rewrite of the Jupyter cell code to shard source datafiles to `redux<yyyy>` folders. 
    
    
Since we are adding three types of sensor: We begin by showing input data variable 
names and corresponding redux data variable names for all four:
    
    
sea_water_temperature                      -->    temperature
sea_water_practical_salinity               -->    salinity                    
sea_water_density                          -->    density           
do_fast_sample-corrected_dissolved_oxygen  -->    dissolvedoxygen
    
    
The code should attempt to do all four types by checking for the existence of an
output file first. If the output file already exists: Do not attempt to write the 
profile. 

    
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
        - VVV   = Version number: Use `V1`
    
    
For input: The code checks all source folders, named by year `2014_ctd`, `2015_ctd` etcetera through `2026_ctd`.
These are in the base location `~/ooidata/rca/sb/scalar/`. 


    
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
    

    
## Next
    
Does the code read the entire dataset into RAM at the outset? If so let's shift to reading only the data
needed for a given chart each time the chart parameters change, for example due to moving a slider.

Rather than have the User choose 'bundle' or 'meanstd' as a permanent choice: Install a choice control
widget in the interface, one for each sensor being charted. The choices are 'bundle' and 'meanstd' so
the User can switch between views. 