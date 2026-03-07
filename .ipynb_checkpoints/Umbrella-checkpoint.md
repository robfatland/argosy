# Umbrella

This file describes the 'umbrella' askpect of this OOI project. For a definition
of umbrella in this context: See `~/argosy/AIPrompt.md`. This markdown file 
primarily concerns non-OOI data resources aspect of the umbrella concept. The
scientific objective is to use this profusion of data to better characterize 
the upper water column (photic zone) in the northeast Pacific, particularly in 
the vicinity of the Regional Cabled Array.


## List of data resources outside of the OOI program


- National Data Buoy Center (NDBC)
- PO-DAAC


## National Data Buoy Center (NDBC)


Oregon Slope Base (informal abbreviation in this book "sb") is located at 42.754°N, 124.839°W.
The "Port Orford" NDBC station 46015 is at the same location. 


[46015 dedicated web page](https://www.ndbc.noaa.gov/station_page.php?station=46015)


```
NDBC buoy 46015 "Port Orford" 42.754 N 124.839 W`
```


Compare 


```
Oregon Slope Base 44.529 N 125.390 W
Oregon Offshore   44.374 N 124.956 W 
```


[46015 historic data dedicated page](https://www.ndbc.noaa.gov/station_history.php?station=46015)


[Descriptions of data fields in NDBC historical data files](https://www.ndbc.noaa.gov/faq/measdes.shtml)


I downloaded and placed an example text table file: 
Standard Meteorological Data, NDBC Buoy 46015, hourly for 2016. 
This is placed for scrutiny in ~/argosy with filename `NDBC46015h2016.txt`. 
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


- NDBC Verify the latitude and longitude of SB matches 46015 from a source file

