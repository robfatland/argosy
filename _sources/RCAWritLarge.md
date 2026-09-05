# RCA Writ Large


An inventory of Regional Cabled Array data streams: Organized in terms of sensors, instruments, sites and science disciplines. 


## Water Column: Oceanography + Biogeochemistry


Three instrumented mooring sites span the continental margin to open ocean: Oregon Slope Base (~2900 m depth, ~100 km offshore), Oregon Offshore / Endurance (~600 m, ~65 km offshore), and Axial Base (~2600 m, ~350 km offshore).

Each site hosts a shallow profiler (science pod plus platform at 200 meters) and a complementary deep profiler.


### Shallow profiler science pods


Winched instrument clusters that profile 0–200 m depth, 9 profiles/day.


**15 sensors per profiler**


| Category | Sensors |
|----------|---------|
| Physical (CTD) | Temperature, Salinity, Density (derived), Pressure |
| Dissolved gases | Dissolved Oxygen |
| Bio-optical | Chlorophyll-A fluorescence, CDOM fluorescence, Optical backscatter |
| Light | PAR, Spectral irradiance (7 wavelengths) |
| Biogeochemical | Nitrate, pCO2, pH |
| Current | 3-component point current meter: east, north, up) |
| Spectrophotometer | Optical absorption, Beam attenuation (2 x 83 channels) |


### Shallow profiler platforms (× 3 sites)


Fixed platform at ~200 m where the profiler science pod rests between ascents.


| Instrument | Description |
|------------|-------------|
| Upward-looking ADCP | Profiles entire water column from 200 m to surface. Continuous (24/7). |
| CTD | Continuous T/S/P at platform depth |
| Dissolved Oxygen | Continuous O2 at platform depth |
| HPIES | Horizontal Electric Field, Pressure, and Inverted Echo Sounder |
| 150 kHz ADCP | Current profiles |
| Optical attenuation | Beam-c at platform depth |


### Deep profilers (× 3 sites)


Wire-following profilers span sea floor to 150 m depth.


| Instrument | Description |
|------------|-------------|
| CTD | Temperature, Salinity, Pressure |
| Dissolved Oxygen | |
| current | 3-D single point current meter |
| Fluorometers | CDOM, Chlorophyll-A, Optical backscatter |


Together the deep + shallow profilers span the entire water column at Oregon Offshore, Slope Base, and Axial Base sites.


### Research topics


- Water mass emplacement: Detection, causation
- Current analysis including upwelling signatures
- Climatology and stratified anomalies
- Terrigenous influence


## Seafloor Instrumentation


### Mooring sites


| Instrument | Sites | Description |
|------------|-------|-------------|
| Broadband seismometer (OBS) | Slope Base, Axial Base | Broadband ocean-bottom seismometer |
| Low-frequency hydrophone | Slope Base, Axial Base | Acoustic monitoring |
| CTD | All sites | Seafloor T/S/P |
| ADCP (150 kHz) | All sites | Near-bottom current profiles |
| Dissolved Oxygen | All sites | Near-bottom O2 |


Note: The APL team supporting RCA has built supporting compute infrastructure that may be of value in parsing hydrophone data.


### Research topics

- Seismic event detection and characterization (earthquake catalogs, tremor)
- Acoustic ecology: Marine mammal vocalizations, anthropogenic noise, biological sound
- Near-bottom current variability and benthic boundary layer dynamics
- Correlation of seismic activity with bottom pressure changes (precursor signals)
- Long-term seafloor temperature trends at depth


## Axial Seamount Volcanology and Hydrothermal

Active submarine volcano on the Juan de Fuca ridge. Erupted 1998, 2011, 2015. Focus: volcanic activity monitoring, hydrothermal vents, magma dynamics.

### Caldera Sites (Eastern Caldera, Central Caldera, International District, ASHES)

| Instrument | Description |
|------------|-------------|
| BOTPT (× 4) | Bottom Pressure and Tilt — nano-resolution pressure recorder + tiltmeters (LILY, IRIS, HEAT). Tracks seafloor inflation/deflation from magma migration. |
| Broadband seismometers (× 4+) | Short-period and broadband OBS distributed around caldera. Seismic event detection. |
| Short-period seismometers | Triangular arrays for event location |
| Hydrophones | Low-frequency and broadband acoustic monitoring |
| HD video camera | Pan/tilt/zoom at ASHES vent field. Streams live video of active vents. |
| Digital still camera | High-definition stills at 1-second intervals. Monitoring vent activity and fauna. |
| 3-D temperature array (TMPSF) | Multi-probe array in vent field measuring diffuse flow temperatures |
| Resistivity sensor | Monitors fluid flow at vents |
| Osmotic fluid sampler (RASFL) | Autonomous time-series fluid sampling at vents |
| CTD (cabled) | Continuous T/S/P in hydrothermal plume |
| Mass spectrometer (MASSP) | In-situ dissolved gas chemistry at vents |
| Diffuse vent fluid sampler | Pore fluid chemistry |


### Research topics

- Eruption forecasting: Can inflation rate, seismicity trends, and tilt predict the next event?
- Magma supply rate estimation from continuous pressure/tilt time series
- Hydrothermal flux variability: Do vent temperatures and chemistry respond to tidal forcing?
- Vent ecosystem dynamics: Colonization, succession, and response to thermal/chemical perturbation (from camera time series)
- Hydrothermal plume dispersion: How far and in what direction do plume signatures propagate? (Integration with water column profiler data at Axial Base)
- Post-eruption recovery: Timescale for re-establishment of steady-state inflation after 2015 eruption
- Seismo-volcanic coupling: Relationship between regional tectonic seismicity and local volcanic response
- Diffuse vs. focused flow partitioning: What fraction of heat/chemical flux exits through diffuse flow vs. black smokers?
- Long-term chemical evolution of vent fluids: Are there secular trends in dissolved gases, metals, or pH?


## Southern Hydrate Ridge (Methane Seeps + Geohazards)

Located at ~780 m depth on the Cascadia accretionary prism. Focus: methane hydrate
dynamics, seep characterization, fluid flux, seismic activity.

| Instrument | Description |
|------------|-------------|
| Digital still camera | Monitors bubble plume activity at seep sites |
| Broadband seismometer | Regional seismicity |
| Short-period seismometers (array) | Triangular array for methane release / seismic event correlation |
| Broadband hydrophone | Acoustic monitoring of bubble plumes |
| CTD | Seafloor T/S/P at seep sites |
| ADCP | Current profiles near seep |
| Osmotic fluid sampler (RASFL) | Time-series pore fluid sampling |
| BOTPT | Bottom pressure / tilt |


### Research topics

- Methane flux quantification: Can bubble plume imaging + acoustic data yield volumetric emission rates over time?
- Seismic triggering of methane release: Do earthquakes (local or regional) correlate with increased seep activity?
- Hydrate stability and climate sensitivity: Does bottom water temperature change (from CTD) correlate with seep intensity?
- Pore fluid chemistry evolution: Long-term trends in methane concentration, sulfate reduction
- Biological community response: How do chemosynthetic communities at seeps respond to changes in flux?
- Tidal modulation of seep activity: Is methane release correlated with pressure (tidal) cycles?
- Cascadia subduction zone monitoring: Slow slip events, episodic tremor detected by the seismometer array


## Experimental and PI-Added Instruments

| Category | Description |
|----------|-------------|
| PI instruments (various) | Researcher-funded instruments added to OOI infrastructure. Data served via piweb.ooirsn.uw.edu. Includes specialized sensors not part of core OOI. |
| DAS (Distributed Acoustic Sensing) | Experimental campaigns using the fiber-optic cable itself as a sensor. Converts the cable into a continuous array of acoustic/seismic sensors spanning the full cable length. |
| Cabled Endurance (Oregon Offshore) | Shared infrastructure with the Coastal Endurance Array. Shallow + deep profilers and seafloor instruments at the midshelf/offshore line. |


### Research topics

- DAS as a seismic/acoustic array: Can the cable resolve ocean surface gravity waves, internal waves, whale calls, ship traffic?
- Continuous strain monitoring along the cable path (plate boundary deformation)
- Novel PI sensor validation: How do new instruments compare with collocated core OOI sensors?
- Cross-platform data fusion: Combining PI and OOI streams to answer questions neither addresses alone


## Data Stream Summary

| Domain | Sites | Key measurements |
|--------|-------|-----------------|
| Physical oceanography | All 3 mooring sites | T, S, density, currents, pressure (full water column) |
| Biogeochemistry | All 3 mooring sites (shallow profilers) | O2, nutrients, pH, pCO2, fluorescence |
| Bio-optics | All 3 mooring sites (shallow profilers) | Chl-A, CDOM, backscatter, spectral irradiance, absorption |
| Volcanology | Axial caldera (4+ sites) | Inflation/deflation, seismicity, tilt, vent temperatures |
| Hydrothermal chemistry | Axial ASHES, International District | Dissolved gases, fluid chemistry, vent imaging |
| Methane/hydrate dynamics | Southern Hydrate Ridge | Bubble plumes, pore fluids, seep imaging |
| Geophysics | All seafloor sites | Seismicity, bottom pressure, acoustic |


## References


- [RCA Interactive Oceans](https://interactiveoceans.washington.edu/) maintained by the University of Washington
- [OOI Instruments](https://oceanobservatories.org/instruments/) maintained by the OOI program
    - [OOI Cabled Array](https://oceanobservatories.org/array/cabled-axial-seamount-array/)
- [PMEL Axial BOTPT data](https://www.pmel.noaa.gov/eoi/rsn/index2.html)

