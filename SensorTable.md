# Sensor Reference

> Note: The heading structure in this file has `### Why OOI Created Separate DO Files` at the same level as other `###` headings but `#### Nitrate` nested under it. This should be reorganized (Nitrate belongs at the same level as other instruments).

This document contains the comprehensive sensor table for the shallow profiler,
column descriptions, per-sensor notes, and references to the standalone CSV files.
See also `sensortable.csv` for the machine-readable version.


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
This is written to a standalone reference CSV file: `~/argosy/sensortable.csv`.
Vector sensor details are in companion files: `vcurrent.csv`, `vspectralirr.csv`, `vspectrophot.csv`.
    
    
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


For datavar == `vector` the actual data variable name is deferred; see notes below.
    
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
PAR,              PARAD,  par,  par_counts_output,            par,             ascent,      0,    300
velocity,         VELPT,  vel,  (vector)x3,                   vel,             ascent,    -.4,     .4
spectralirrad,    SPKIR,  irr,  (vector)x7,                   irr,             ascent,      0,     15
opticalabsorb,    OPTAA,   oa,  (vector)x73,                  oa,              ascent,    .15,    .25
beamattenuation,  OPTAA,   ba,  (vector)x73,                  ba,              ascent,    0.0,    0.2
```


The table above needs a consistent convention for vector sensors. `vel` is `east/north/up` i.e. 3 values. 
`spectralirrad` is `si412-si443-si490-si510-si555-si620-si683` i.e. 7 values. `oa` and `ba` are not 
resolved yet but each has 73 values. 
    

PAR datavar is `par_counts_output` (calibrated L1 product, units: µmol photons m⁻² s⁻¹).
    
    
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
