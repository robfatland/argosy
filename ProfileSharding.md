# Profile Metadata and Sharding

This document covers profile metadata from the OOI profileIndices repository,
reference metadata design, the sharding process that translates raw data into
per-profile per-sensor files, and the TMLD (Temperature Mixed Layer Depth) tool.


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


Note: Derived information concerning profiles, for example like the indices of the
noon profiles, are not to be written into the repo directory `profileIndices`. It
should be treated as read-only so that it can be updated from GitHub without 
erasing important metadata. Such metadata goes into the parallel `metadata` folder, 
**not** `profileIndices`. 


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
    - PPPPP = global profile index drawn from the `profileIndices` tables
    - Q     = this profile's index relative to the data acquisition day: a number from 1 to 9
    - VVV   = version number: Use `V1` at this time


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


## midnight and noon profiles


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


## TMLD


### Estimated Temperature Mixed Layer Depth
    

This part of the project is on hold; no action. 


A human-driven TMLD picker program was written in Python. This is not Jupyter cell code because 
the Jupyter configuration does not support interactive chart location selection.
    

- Generate a CSV file with three columns, resides in `~/argosy/TMLD`.
    - First column = global profile index as recorded in the profile filename in ~/ooi/redux/redux2018
    - Second column is `Estimated TMLD`
        - 'Estimated Temperature Mixed Layer Depth' (meters, positive downward)
    - Third column = temperature at that depth for that profile
- Estimated TMLD value `N`
    - The upper `N` meters of the water column is well-mixed due to wave action etcetera
    - At the bottom of this layer temperature begins to steadily decrease with depth (pycnocline)
    - With increasing depth the temperature gradient decreases
    - The mixed layer / pycnocline boundary often appears as a pronounced kink in the temperature curve
    - Equivalent boundaries exist: Salinity, density, other sensible attributes of the water column
- The TMLD data can be included in bundle plots as distinct markers (see `VisualizationNotes.md`)
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
        - <instrum> designators are found in the **Sensor Table** (see `SensorReference.md`)
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
above. The instrument name <instrum> is from the `key` column of the **Sensor Table** (see `SensorReference.md`).
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
