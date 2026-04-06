# Umbrella

This file describes the 'umbrella' askpect of this OOI project. For a definition
of umbrella in this context: See `~/argosy/AIPrompt.md`. This markdown file 
primarily concerns non-OOI data resources, the most important aspect of the umbrella 
concept. The scientific objective is to use this profusion of data to better characterize 
the upper water column (photic zone) in the northeast Pacific, particularly in 
the vicinity of the Regional Cabled Array.


## List of umbrella data resources outside of the OOI program


- National Data Buoy Center (NDBC)
- PO-DAAC


## National Data Buoy Center (NDBC)


Oregon Slope Base (informal abbreviation in this book "sb") is located at 42.754°N, 124.839°W.
The "Port Orford" NDBC station 46015 is 200 km away (not adjacent). This topic is relegated
to `~/argosy/NDBC` for the time being.


[46015 dedicated web page](https://www.ndbc.noaa.gov/station_page.php?station=46015)


The following quote seems to be in error: 


```
NDBC buoy 46015 "Port Orford" 42.754 N 124.839 W
```


Shallow profiler coordinates:


```
Site name             Abbreviation     Latitude          Longitude
------------------    ------------     --------          ---------
Oregon Offshore         OOF            44.37415          -124.95648
Oregon Slope Base       OSB            44.52897          -125.38966 
Axial Base              AXB            45.83049          -129.75326
```   


#### Distance calculation


```
from math import pi, cos, sqrt
def distance_approximate(lat_a_dd, lon_a_dd, lat_b_dd = 44.6, lon_b_dd = -124.)
    '''
    A very coarse distance local distance estimation in km.
    The default lat/lon is Newport Oregon.
    '''
    conversion = pi/180
    lat_a_rad = lat_a_dd * conversion
    lon_a_rad = lon_a_dd * conversion
    lat_b_rad = lat_b_dd * conversion
    lon_b_rad = lon_b_dd * conversion
    re        = 6378.                        # earth radius, km
    mean_lat  = (lat_a_rad - lat_b_rad)*0.5
    dx_km     = (lon_a_rad - lon_b_rad)*cos(mean_lat)*re
    dy_km     = (lat_a_rad - lat_b_rad)*re
    return sqrt(dx_km**2 + dy_km**2)
```


[46015 historic data dedicated page](https://www.ndbc.noaa.gov/station_history.php?station=46015)


[Descriptions of data fields in NDBC historical data files](https://www.ndbc.noaa.gov/faq/measdes.shtml)


I downloaded and placed an example text table file: 
Standard Meteorological Data, NDBC Buoy 46015, hourly for 2016. 
This is placed for scrutiny in` ~/argosy/NDBC` with filename `NDBC46015h2016.txt`. 
The first two rows act as type/units doubled column headers:


```
#YY  MM DD hh mm WDIR WSPD GST  WVHT   DPD   APD MWD   PRES  ATMP  WTMP  DEWP  VIS  TIDE
#yr  mo dy hr mn degT m/s  m/s     m   sec   sec degT   hPa  degC  degC  degC   mi    ft
```


These 18 columns are interpreted in order from left to right:


- Year (Note: Date is UTC)
- Month
- Day
- Hour
- Minute
- Wind Direction (degrees true north)
- Wind speed (meters per second)
- Wind gust (meters per second)
- Wave height (meters)
- DPD = Dominant Wave Period in seconds
- APD = Average Wave Period in seconds
- MWD = Mean Wave Direction (degrees true north)
- Pressure (hectoPascal, equivalent to millibars)
- Air Temperature (deg C)
- Water Temperature (deg C)
- Dewpoint (deg C) NODATA = 999
- Visibility (miles) NODATA = 99
- Tide (feet) NODATA = 99


There are 8307 rows of actual data starting December 31 2015 at 23:50 UTC.
The possible number of rows is 366 x 24 = 8784 so we expect about 480
missing entries corresponding to 20 days.


### Comparing NDBC buoy data with Slope Base shallow profiler data



data that are comparable to shallow profiler data include...


- Wave height + Wind + Wave Periods: compare to mixed layer depth
- Wave Direction compare to velocity at profile apex
- Water temperature compare to temperature at profile apex



Other data types beyond standard meteorological are: 


- Continuous winds data
- Five types of wave data
- Supplemental measurement data (certain years only)


## Task list



