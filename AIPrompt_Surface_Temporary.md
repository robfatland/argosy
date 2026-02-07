# AI Prompt


For humans: This document is project background and prompts for a Coding Assistant (CA). 
Initial work used CA = Q Developer from AWS powered by Claude Sonnet. Q Dev is not Agentic;
however its successor Kiro (also from AWS) will be; this is circa early 2026. This file
lays out project goals and acts a progress journal in relation to those goals. New CA 
sessions can scan this to quickly boot up the context.


For CA: This effort concerns organizing oceanography data starting with data produced by the
Ocean Observatories Initiative; in fact specifically focusing on the Regional Cabled Array
shallow profilers. The underlying idea is to transition from a somewhat daunting archival data 
system to data and visualizations amenable to physical interpretation. This markdown file
is intended as context for a Coding Assistant. 


The CA with no context at the start of a chat session is directed to read this document
in its entirety. With that done an immediate prompt is found at the bottom
of this file under the heading **Next**. The precise line range (e.g. "lines 300 - 342") 
will be provided in the CA chat window. 

As each **Next** prompt is addressed: That prompt text migrates up into the context section.


## Special terminology


- Red Zone ('the last 20 yards challenge'): Translate OOI data for scientific analysis.
- Umbrella: Extend the OOI analysis to other sensor data
    - specialized instruments in OOI (sonar, spectrophotometer)
    - ocean circulation models
    - satellite remote sensing
    - 


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


- Isolate a spatiotemporal dataset as a *first model* of the redzone workflow
    - From the OOI observatory (many arrays) narrow the focus to the Regional Cabled Array (RCA)
    - From the RCA distribution across many hundreds of kilometers: narrow to a single site and platform
        - Specifically the Oregon Slope Base shallow profiler
    - From fifteen sensor streams to one: Temperature
    - A note on native data format: NetCDF, Deployment-related time boxes, continuous, many sensors in one file e.g. for CTD
    - From continuous data to profile ascents only: Using ascent metadata
    - From the OOINET server obtain CTD datasets spanning the majority of the program timeline
        - Specifically from 2015 through the end of 2025
    - From nominal nine profiles per day: Set up a data structure of actual profiles that produced usable data
    - Produce a temperature profile dataset (low data volume in comparison with the CTD file volume)
        - Place this data in AWS S3 object storage
        - Data are aggregated as profiles with dimension `time` (not `obs`)
    - Produce a running average (mean and standard deviation) dataset
        - Characterization by site, time of day, time of year
    - Document how this would lead to a climatology dataset
    - Create a set of visualization tools based on `matplotlib` residing in a notebook in this Argosy Jupyter Book
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
    

## Umbrella goals: Instruments/sensors/data streams beyond the shallow profiler 


This is at much lower task resolution.


- Extend the Oregon Slope Base workflow to the other two shallow profilers in the RCA
- Apply the methodology to the shallow profiler platform moored at 200 meters
- Extend focus within RCA to other sensors
    - Horizontal Electrometer Pressure Inverted Echosounders (HPIES; 2 sites)
    - Broadband Hydrophone and other acoustic sensors as directed (see WL, SA)
    - Axial tilt meters, seismometers etcetera
- Glider data from Coastal Endurance
- NANOOS installations
- NOAA sea state buoys
- ARGO
- Global ocean dataset formerly known as GLODAP
- PO-DAAC data including 
- Inferred ocean surface chlorophyll (LANDSAT, MODIS etcetera) 
- Publish the pipeline and output results to be openly available
    - Includes appraisal of working on the OOI-hosted Jupyter Hub
    - Includes containerization as appropriate


## CA behavior


- The acronym CA refers by default to a Coding Assistant
- The CA should not modify this file but is invited to create focused markdown files
    - As appropriate: Markdown files that cover narrow topics
    - These files to be named `CA_Topic.md`.


## Completed code



These are IPython notebooks in preparation. Eventually this code can be migrated 
to a workflow as straight up .py Python files. 


- DataDownload.ipynb
    - A data order is generated on the OOINET system (full time resolution)
    - It appears usually between hours to a day with an email notification
    - DataDownloader uses the delivery URL to build a `bash` script
    - The script downloads (multiple NetCDF) datafiles from the OOINET server
    - These files are input to DataStreamline
- DataStreamline.ipynb
    - Extract sensor data cut into profile bins; write these as NetCDF files
    - Location in folder structure and filename convention TBD
- ShallowProfiler.ipynb
    - "TemperatureChart" checks temperature (sensor) data match to ascent timing metadata


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


## Sensor list and associated file label


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
This is done using an `xarray` `swap_dims()` method on the `xarray` `Dataset`:


```
ds = ds.swap_dims({'obs':'time'})
```


- `data variables` include sensor data of interest and QA/QC/Engineering metadata
- `coordinates` are a special type of data variable
    - natively the important coordinates are `obs`, `depth` and `time`
    - there is also `lat` and `lon` but these do not vary much for a shallow profiler
- `dimensions` are tied to `coordinates`: They are the data series reference
- `attributes` are metadata; can be useful; ignore for now



## Aggregating data files for processing


## Using profile metadata


A shallow profiler divides its time between three phases: Ascent, Descent, Rest.


The time stamps for these phases are found in a GitHub repository. The organization
at GitHub is 'OOI-CabledArray'. The repository of interest is 'profileIndices'.
The RCA Data Manager who built this is Wendi Ruef. The repository has been 
cloned 



Ascent and descent interval metadata is available from GitHub.
    - Wendi Ruef (RCA): `https://github.com/OOI-CabledArray/profileIndices`
    - This repo is cloned to localhost WSL ~/profileIndices
    - Profiles are broken down by array and site identifier, then by year
        - Array CE = Coastal Endurance, associated with the Oregon Offshore site ('OS')
        - Array RS = Regional Cabled Array, associated with Slope Base ('SB') and Axial Base ('AB') sites
    - Here are the six resulting codes: 3 Deep Profilers, 3 Shallow Profilers 
        - CE04OSPD Offshore (Sub-folder 'os') deep profiler
            - years 2015, 18, 19, 21, 22, 23, 24, 25
        - CE04OSPS ~ Oregon Offshore ('os') shallow profiler (CE = Coastal Endurance array)
            - 2014 -- 2026
        - RS01SBPD ~ Slope base ('sb') deep profiler
            - years 2015, 2018, 2019, 2020, 2021, 2022, 2023, 2024
        - RS01SBPS ~ Slope Base ('sb') shallow profiler
            - 2014 -- 2026
        - RS03AXPD ~ Axial Base ('ab') deep profiler
            - years 2014, 2017 -- 2025
        - RS03AXPS ~ Axial Base ('ab') shallow profiler
            - years 2014 -- 2026


To select data from the Slope Base shallow profiler CTD during 2018: Use the time
ranges present in the file `~/profileIndices/RS01SBPS_profiles_2018.csv`. This file has four
columns: profile, start, peak, end. For an instrument / sensor that operates on ascent
the time range for a given profile would be given by columns 2 and 3: start and peak. 
The times are given in format 'yyyy-MM-dd hh:mm:ss'.


See the ShallowProfiler notebook code on relating profile metadata to data recorded in the NetCDF file.





## Previously

- Select a candidate CTD file:
    - `~/ooidata/rca/sb/scalar/2015_2025_ctd/deployment0004_ ... .391002.nc`
- Generate a CSV file writer 
    - The first CSV file will be called `rca_sb_ctd_temp_profile_status.csv`
    - This will span the full range of available time (2014 - 2025)
    - It will be populated as data files are processed
    - Each row corresponds to a year + day
        - The majority of years will have 365 rows, leap years 366
        - The first row will be column headers
        - Subsequent rows will be in chronological order
    - Columns
        - year
        - Julian day
        - date in dd-MON-year format e.g. 01-FEB-2026
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

This program will be the starting point for a program that extracts and writes temperature profiles.
It should provide diagnostics such as the mean number of profiles per day over the interval the source file covers.

## In the on-deck circle


As progress is made: Update the profile status file from the previous step: `rca_sb_ctd_temp_profile_status.csv`.

Also create a new text file describing what time ranges have been transcribed, as follows: 

- This will be a CSV file
- The two columns will be `date` and `start/stop`.
- The date will be that of the first available valid data value
    - it could be 01-JAN-2018T00:00:00
    - Round all times to the nearest second
    - This will have a value in the second column of `start`
- A second date following the one above will be that of the last available data value
- However if there are any days in between where no profiles exist: This will insert two additional entries: A stop and a start.
- Processing additional source data will introduce more stop and start markers.


## TITLE NEEDED HERE!!!!!!!!!!!!!!!!


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
- The output folder will be `~/redux` where the individual profile files will be written. 
- One file is written per profile
- The filename format will be `AAA_SSS_TTT_BBB_YYYY_DDD_PPPP_Q_VVVV.nc`
    - These are to be filled in as follows for now:
        - AAA  = Array name: Using `RCA` for Regional Cabled Array
        - SSS  = Site: Using `OSB` for Oregon Slope Base
        - TTT  = Platform: Using `Profiler` (in contrast to `Platform`)
        - BBB  = Observation type: Using `Temp` for temperature
        - YYYY = four digit year
        - DDD  = three digit Julian day as in 027 for January 27
        - PPPP = Profile index drawn from the `profileIndices` tables
        - Q    = This profile's index relative to the data acquisition day: a number from 1 to 9
        - VVV  = Version number: Using `V1`
        
An output filename example: `RCA_OSB_Profiler_Temp_2018_003_3752_4_V1.nc`.

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
        - the code will need to translate from the index0 value to the corresponding filename from `~/redux`
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
    - First column is profile index as recorded in the profile filenames in ~/redux
    - Second column is `Estimated TMLD` 
        - This stands for 'Estimated Temperature Mixed Layer Depth'
        - It is a depth in meters measured positive-downward
        - It is described below
        - We want to test if you the AI CA are able to make these estimates from a text description
    - Third column is the temperature at that depth for that profile
    - As there are 157 profiles in ~/redux this file (with header) will be 158 lines
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
the ~/redux folder for temperature data.


Cursor location is printed near the chart as depth and temperature.


## List the CTD files in a "to do" file

- Return to the folder where the original CTD data file is located
- Create a new file listing all of the CTD files in that folder
    - Let us call this file `source_ctd_filelist.txt`
    - The first line will be the full path to the folder
    - The remaining lines are 1 line per CTD file
- This list of files will be processed sequentially to expand the time series for Oregon Slope Base shallow profiler temperature profiles
    - The output will be additional NetCDF temperature profile files in ~/redux
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
- For this input CTD file start a counter of how many profile files have been written to `~/redux`
- Formulate the filename for the current profile
- Using the appropriate `start` and `peak` times from the appropriate `~/profileIndeces` folder CSV file: 
    - Extract and write a temperature profile file to the folder `~/redux` following the same format as before
    - In this process: Keep a running sum of how many data samples there are in each profile
    - Output files in ~/redux feature sea_water_temperature renamed `temperature` plus `depth` against dimension `time`
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


## Bundle plot visualization code: .mp4 time series animation


- This code runs in a Jupyter cell
- The input questions take on the default value if the User just hits Enter.
    - Start by asking "Include TMLD estimate in the visualization? Default is no. \[y/n\]" 
    - "How many profiles in the bundle? Default is 18 (two days)" refer to this as N
    - "How many seconds delay between frames? (0.1 sec):" refer to this as d
    - "Start date (default 01-JAN-2018):" refer to this as T0
    - "End date (default 31-DEC-2018):" refer to this as T1
- Start at T0 and continue to T1: Create an animated chart sequence
    - The output file should be called 'temp_bundle_animation.mp4'
    - Each frame consists of N profiles bundled in one chart
    - The horizontal axis is fixed at 7 deg C to 19 deg C, does not change from one frame to another
    - The vertical axis is fixed from 200 meters to 0 meters at the top
    - For a given profile: If the TMLD option is selected but there is no value for the TMLD in the CSV file: Omit adding that marker.
    - Add in a 'hold time' per frame of d seconds
    - If a time gap exists between two profiles exceding 48 hours: 
        - The chart frame should include in large black letters at the lower right 'Time Gap'
        - This Time Gap message persists until all N consecutive profiles do not have such a time gap between them
- Check that the output file exists and report its status


## Recover proper CTD data for OSB beyond 2018


- The data downloaded prior did not include temperature (and salinity and so on)
- Revisiting the data access page
    - Left filters
        - Array = Cabled Array
        - Platform = Shallow Profiler
        - Instruments = CTD
    - Data Catalog (center, lowest panel)
        - Shows 2 results: Shallow profiler and Platform; select the former
    - Data Navigation (center, upper window below title bar)
        - Shows 4 Engineering and 1 Science result; select the download button for the latter
    - Download time range pop-up wizard
        - Set start to Jan 1 2019 00:00:00
        - Set end to Dec 31 2019 23:59:59
        - Clicked on download (email to be sent in a few minutes notifying completion)
- Go online and try to order CTD data from 2022 or 2023 for OSB
    - Revisiting the data download .ipynb file
        - If the target folder does not exist: Create it
        - Unpack ~ rather than switching between /home/rob and /home/kilroy 
- Line up on what else CTD gives us and define the identifier strings

    
    





