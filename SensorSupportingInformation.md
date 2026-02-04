The present focus:


- Obtain source data from the OOINET data product servers
    - Oregon Slope Base shallow profiler
    - Span from 2015 through 31-DEC-2025
    - List sensors including instruments and scalar or vector type
    - Master directory will be in an S3 bucket called `epipelargosy` in a folder called `ooidata`
        - The sub-structure of the `ooidata` folder is as follows:
            - `ooidata/rca` is data from the Regional Cabled Array
            - Three `rca` subdirectories: `oo`, `sb`, `ab`...
                - ...respectively for Oregon Offshore, Slope Base, Axial Base shallow profilers
            - Subdirs of `sb` are `scalar` and `vector` as categories of instrument/sensor
                - `vector` is nominally reserved for 3 instruments
                    - current
                    - spectral irradiance
                    - spectrophotometers
                - `scalar` is nominally reserved for instrument datasets:
                    - CTD
                    - Fluorometer
                    - Nitrate
                    - PAR
                    - pCO2
                    - pH
              - `ooidata` also contains tracking files: `discovery_summary.txt` and `ooi_data_inventory.json`  
    - The S3 bucket can be mounted on localhost i.e. a development machine using this command:


```cd ~; mount-s3 epipelargosy s3 --allow-delete```


- WSL access and Windows home access notes
    - Note that this lands in the home directory of the WSL Ubuntu filesystem
        - I will refer to this as `~` 
        - `~` is accessible by the Coding Assistant (CA (Q Developer))
            - This is on the first Dev Machine referred to as "the Dell"
            - It uses the `wsl` command in PowerShell to do this
                - This has not been verified on the second Dev Machine "the Surface"
        - `/mnt/c/Users/<uname>` is accessible by the CA if needed
- Mirroring S3 bucket versions of the data
    - It may be necessary to create mirror versions of `ooidata` in `~`
    - These two development machines are laptops with 1TB drives
- The following section is metadata for the shallow profiler system
    - This includes a list of instruments and associated sensors
        - These should match up with data files provided by OOINET
        - Some sensor types may be qualified; and may be synthetic or derived
        - A single NetCDF data file will correspond to an Instrument
            - Examples NetCDF data files have been imported to ~/argosy/tmpdata
            - Filename format: <instrument name>example.nc


```
Keys for shallow profile sensor data
These key names avoid spaces and underscores. Inside a given NetCDF file (Instrument)
there will be several data types listed corresponding to sensors. These data type / sensor names
in the data files are different than what I am defining and using. The official (from data file)
versions of the sensor names are given in quotes to the right of the sensor names.

Format:
- No indent: Category: One of 'dimension', 'coordinate', 'scalar', 'vector'
- Single indent: Dimension/coordinate type (for those categories), otherwise: instrument
- Double indent: Sensor associated with the above instrument

dimension
    observation

coordinate
    observation
    lat
    lon
    depth
    time

scalar
    CTD
        pressure                  'Pressure'
        conductivity              'Conductivity'
        temperature               'Temperature (deg C)'
        salinity                  'Salinity'
        density                   'Density (kg m-3)'
    dissolvedoxygen
        dissolvedoxygen           'Dissolved Oxygen' 
    nitrate
        nitrate                   'Nitrate Concentration'
    nitratedark
        nitratedark               ?
    fluorometer
        chlora                    'Chlorophyll-A'
        fdom                      'Fluorescent DOM'
        backscatter               'Particulate Backscatter'
    pco2
        pco2                      'CO2 Concentration'
    ph
        ph                        'pH'
    par
        par                       'Photosynthetically Available Radiation'

vector instruments
    current
        east                      'Current: East'          
        north                     'Current: North'
        up                        'Current: Vertical'
    spectralirradiance
        si412                     'Spectral Irradiance 412nm'
        si443                     'Spectral Irradiance 443nm'
        si490                     'Spectral Irradiance 490nm'
        si510                     'Spectral Irradiance 510nm'
        si555                     'Spectral Irradiance 555nm'
        si620                     'Spectral Irradiance 620nm'
        si683                     'Spectral Irradiance 683nm'
    spectrophotometer
        c001                      ?
        c002
        ...
        c073

Other data types listed by instrument file type:
    CTD
    dissolvedoxygen
    nitrate
    fluorometer
    pco2
    ph
    par
    current
    spectralirradiance
    spectrophotometer

(First draft) Expected numerical data ranges by sensor

conductivity:(3.2,3.7)
density:(1024, 1028)
pressure:(0.,200.)
salinity:(32, 34)
temperature:(7, 11)
chlora:(0.,1.5)
backscatter:(0.00,0.006)
fdom:(0.5,4.5)
si412:(0.0, 15.0)
si443:(0.0, 15.0)
si490:(0.0, 15.0)
si510:(0.0, 15.0)
si555:(0.0, 15.0)
si620:(0.0, 15.0)
si683:(0.0, 15.0)
nitrate:(0., 35.)
nitratedark:(0., 35.)
pco2:(200.0, 1200.0)
dissolvedoxygen:(50.0, 300.)
par:(0.0, 300.)
ph:(7.6, 8.2),
east:(-0.4, 0.4),
north:(-0.4, 0.4),
up:(-0.4, 0.4) }
spectrophotometer: ?
```

Here is 'simplest' code to elaborate details of a particular Instrument:


```
import xarray as xr
ds = xr.open_dataset('~/argosy/tmpdata/ctdexample.nc')
ds
```

Default dimension will be observation index `obs`.
Five standard Coordinates: observation, time, lat, lon, depth
Data variables
Attributes: Text fields describing the dataset


Constraints...
- ...ascent only, except as noted for descending sensors such as nitrate
    - measurements of undisturbed water as the pod ascends
- ...dual dimension strategy: time dimension for profiles, depth dimension for an individual profile 






### Python library installations


- Using `miniconda`
- Install `matplotlib`, `pandas`
- Install `xarray` and `h5netcdf` (or if that fails: can install `netcdf4`)


### ordering data

- Log in to OOI using an established User account
- Navigate to the [access page](https://ooinet.oceanobservatories.org/data_access)
- Use the LHS filters to narrow results appearing in the Data Catalog box (bottom center)
    - ***Do not try and use the time window interface***
- For a dataset of interest: Click the ***+*** Action button
    - This mysteriously features the word **Plot** in hover text
    - The result of this click: A new table appears top center
        - Also appearing: A data availability plot, center center
    - The new table features an Action column with a Download button
    - Use the Download button to generate a data order
        - ***Be sure to select a dataset with Stream type == Science***
        - This should bring up a pop up for finalizing the data order
- For the pop-up data order
    - Use the calendars to specify a time range
    - Un-check the box for **Download All Parameters**
    - Use ctrl-click to select parameters of interest
    - Submit the order; turnaround time will be on the order of hours
    

### Data Variable names of interest listed by instrument/file


Using Python + xarray here are data types by Instrument file:


*Unresolved*: Each instrument includes int_ctd_pressure. I suggest verifying this can be
ignored in lieu of depth.


#### CTD

    corrected_dissolved_oxygen
    do_fast_sample-corrected_dissolved_oxygen
    sea_water_practical_salinity
    sea_water_electrical_conductivity
    sea_water_density
    sea_water_temperature


#### Dissolved Oxygen


**Unresolved**: *It would seem that Dissolved Oxygen is bundled in the CTD data
rendering a separate product redundant.*


Variables:
  sea_water_practical_salinity
  sea_water_temperature
  corrected_dissolved_oxygen


#### nitrate

  nutnr_nitrogen_in_nitrate
  nitrate_concentration
  sea_water_practical_salinity
  salinity_corrected_nitrate


#### nitratedark


  nutnr_nitrogen_in_nitrate
  nitrate_concentration


#### fluorometer


Variables:
  fluorometric_cdom
  seawater_scattering_coefficient
  sea_water_practical_salinity
  total_volume_scattering_coefficient
  fluorometric_chlorophyll_a
  optical_backscatter
  sea_water_temperature
  int_ctd_pressure


  
#### pco2


Variables:
  int_ctd_pressure
  pco2_seawater


  
#### ph



Variables:
  sea_water_practical_salinity
  ph_seawater
  int_ctd_pressure



#### par


These data are on order.



### Verify that the CSV profile table selects ascent data properly


This code generates a plot of temperature against depth for four consecutive profiles.
The profiles are in a color sequence: red, orange, green, blue. Time ranges are pulled 
from the appropriate CSV file. The data are then pulled from the `ctdexample.nc` data 
file. The plot y-axis is depth (from 0 to 200 m) and temperature as the x-axis (from
6 deg C to 16 deg C). Here is the code that runs in a Jupyter notebook cell: 


```
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt

# Load profile times and text > datetimes for columns 2, 3, 4
profiles = pd.read_csv('~/profileIndices/RS01SBPS_profiles_2018.csv')
profiles['start'] = pd.to_datetime(profiles['start'])
profiles['peak'] = pd.to_datetime(profiles['peak'])
profiles['end'] = pd.to_datetime(profiles['end'])

# Load CTD data
ds = xr.open_dataset('/home/rob/argosy/tmpdata/ctdexample.nc')

# Find profiles that overlap with CTD data
ctd_start = pd.to_datetime(ds.time.min().values)
ctd_end = pd.to_datetime(ds.time.max().values)
matching = profiles[(profiles['start'] >= ctd_start) & (profiles['peak'] <= ctd_end)]

# Select 4 consecutive profiles
colors = ['red', 'orange', 'green', 'blue']
fig, ax = plt.subplots(figsize=(4, 5))

for i in range(4):
    profile = matching.iloc[i]
    start_time = profile['start']
    peak_time = profile['peak']
    
    # Select data for this profile (ascent: start to peak)
    mask = (ds.time >= start_time) & (ds.time <= peak_time)
    profile_data = ds.where(mask, drop=True)
    
    # Ensure depth is positive
    depth = profile_data['depth']
    if depth.mean() < 0:
        depth = -depth
        print("procedure was obliged to reverse sign of depth data")
    
    # Plot temperature vs depth
    ax.plot(profile_data['sea_water_temperature'], depth, color=colors[i])

ax.set_ylim(200, 0)
ax.set_xlim(6, 16)
ax.set_xlabel('Temperature (°C)')
ax.set_ylabel('Depth (m)')
ax.set_title('CTD Temperature Profiles - Slope Base, 2018')
ax.grid(True, alpha=0.3)
plt.tight_layout()
# plt.savefig('/home/rob/argosy/temperature_profiles.png', dpi=150)
plt.show()
```


Next we want a Python program that will downloaded all the files from a successful data
order. Once the data are on order (see procedure above) an email is sent to the User
account email address carrying two links: A THREDDS server link and a direct download
link. 


Here is an example, the direct 
[download link for sb PAR 2015 -- 2025](https://downloads.oceanobservatories.org/async_results/kilroy1618@gmail.com/20260103T003554734Z-RS01SBPS-SF01A-3C-PARADA101-streamed-parad_sa_sample).


In the DataDownload.ipynb notebook we now have a Python cell that copies data files from an order
on the OOINET server to localhost. In detail what this code does:

- input download link and target folder (instrument + time range)
    - example `~/s3/ooidata/rca/sb/scalar/2015_2025_par`
- create the folder if it does not yet exist (the User may create this in advance)
- discover the names and sizes of all files at the download link
    - Creates an initial Download Manifest that may be modified below
- print the total data volume and the mean size of all files with a `.nc` file extension
- modify the Download Manifest as follows:
    - input from the User a response to 'Skip CTD files?' > response string `userskip`
        - if userskip == "n": No change to Download Manifest
        - else:               Remove `.nc` files containing `ctdpf` or `CTDPF`
- For Download Manifest again print total data volume
- ask for a `y` confirmation to proceed > download the files to the target directory


We are now moving to a new Python program that will initially run in a notebook cell:

- input a NetCDF file folder on localhost
- make a list of all NetCDF files in that folder
- 