# OOI Observatory Reference

This document describes the Ocean Observatories Initiative (OOI) observatory structure,
the Regional Cabled Array sites, challenges working with OOINET, a project glossary,
and reference websites.


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


## OOINET challenges


- OOI can be daunting to learn
    - Dissolved oxygen example: Needs a write-up
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


- HITL, QA/QC, qartod: 'human in the loop', 'quality assurance / quality control', and
'QA/QC of Real Time Oceanographic Data`. This is an important aspect of ensuring data 
subjected to analysis are collected under nominal conditions. For example a salinity data 
dropout observed in 2025 is due to a clogged conductivity cell. This was observed by the 
RCA data team during their data review process and noted as an annotation.  A future goal 
of `argosy` is to scan the netcdf source / raw file from OOINET to check the `qartod` tests: 
`gross range` and `climatology`.  Significant dropouts such as this one -- when identified -- 
are flagged there to avoid treating bad data like it is valid. An alternative is to download 
annotations with the source / raw files; and scroll through these to see events of note for 
the data. *Note: See workflow Step 3 PostProcessing (in `FileSystemWorkflow.md`). This is where filters for bad data
can be instantiated.*


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
