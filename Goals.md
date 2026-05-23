# Goals


## Red Zone Goals


This is a partial description of how this Jupyter Book is constructed.


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
- Add the last four additional scalar sensors
    - PAR
    - pH
    - Nitrate
    - pCO2
- Add four vector sensors
    - Point current measurement: east, north, up
    - spectral irradiance: 7 wavelengths, downwelling
    - instrument: spectrophotometer
        - sensor: optical absorbance
        - sensor: beam attenuation
        - 73 elements (wavelengths)
- Set up a file system structure (see `Workflow.md`)
    - source data
    - metadata including profile time boundaries
    - separated sensor+profile data files ("sharding" (`redux`))
    - post-processing versions of the sharded data
- Build out analysis machinery
    - Simple straightforward methods
    - Spectral graph methods


## Umbrella goals


"Umbrella" is an abstraction for "using other data resources beyond the shallow profiler
at Oregon Slope Base". This includes remote sensing data evoking the umbrella canopy above
the umbrella pole corresponding to the profilers.


### Instruments/sensors/data streams beyond the shallow profiler


This is at much lower task resolution.


- Use current sensors (ADCP etcetera) on the profiler platform for current
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


See also `Umbrella.md` for details on specific non-OOI data resources (NDBC, etc.).
