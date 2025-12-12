# shallowprofiler.py module contents
#   - imports / configuration
#   - shallow profiler metadata
#   - shallow profiler data access
#   - shallow profiler sensor data dictionaries
#   - shallow profiler specific sensor bespoke functions

#############################
#############################
####
#### Imports / Configuration
####
#############################
#############################

import os, sys, time, glob, warnings
from os.path import join as joindir
from IPython.display import clear_output
from matplotlib import pyplot as plt
from matplotlib import colors as mplcolors
import numpy as np, pandas as pd, xarray as xr
from numpy import datetime64 as dt64, timedelta64 as td64

warnings.filterwarnings('ignore')

def doy(theDatetime): return 1 + int((theDatetime - dt64(str(theDatetime)[0:4] + '-01-01')) / td64(1, 'D'))
def dt64_from_doy(year, doy): return dt64(str(year) + '-01-01') + td64(doy-1, 'D')
def day_of_month_to_string(d): return str(d) if d > 9 else '0' + str(d)


print('\nJupyter Notebook running Python {}'.format(sys.version_info[0]))


#############################
#############################
####
#### Shallow Profiler Metadata
####
#############################
#############################

def ReadProfileMetadata(fnm = './data/rca/profiles/osb/january2022.csv'):
    """
    Profiles are saved in a CSV file as six events per row: Rest start, Rest end, Ascent start,
    Ascent end, Descent start, Descent end. Each event includes a time and depth. There is event
    degeneracy in that for a given row the Rest end is the same event as Ascent start. Likewise
    Ascent end is also Descent start. Descent end is Rest start *in the subsequent row*. The 
    exception is of course in the final row. Event depth is measured as a negative value below
    the zero which is the sea surface.
    
    The profile source file path uses a default tied to Oregon Slope Base (OSB), January 2022.
    """
    df = pd.read_csv(fnm, usecols=["1","2","4","5","7","8","10","11","13","14","16","17"])
    df.columns=['r0t','r0z','r1t','r1z','a0t','a0z','a1t','a1z','d0t','d0z','d1t','d1z']
    df['r0t'] = pd.to_datetime(df['r0t'])
    df['r1t'] = pd.to_datetime(df['r1t'])
    df['a0t'] = pd.to_datetime(df['a0t'])
    df['a1t'] = pd.to_datetime(df['a1t'])
    df['d0t'] = pd.to_datetime(df['d0t'])
    df['d1t'] = pd.to_datetime(df['d1t'])
    return df



def GenerateTimeWindowIndices(profiles, date0, date1, time0, time1):
    '''
    In UTC: Define a time box from two bounding days and -- within a day -- 
    a bounding time interval. This function then produces a list of profile 
    indices for profiles that begin ascent within the time box. These indices
    refer to the rows in the profiles DataFrame

    'profiles' is a profile metadata DataFrame

    date0       define the time box in the [date0, date1] sense
    date1
    time0       likewise inclusive [time0, time1] sense
    time1
    '''
    pidcs = []
    for i in range(len(profiles)):
        a0 = profiles["a0t"][i]
        if a0 >= date0 and a0 <= date1 + td64(1, 'D'):
            delta_t = a0 - dt64(a0.date())
            if delta_t >= time0 and delta_t <= time1: pidcs.append(i)
    return pidcs


#############################
#############################
####
#### Shallow Profiler Data Access
####
#############################
#############################
#
# - to do: deprecate this: For example hi/lo/color > data dictionaries

def AssembleShallowProfilerDataFilename(data_file_root_path, site, sensor, month, year): 
    return data_file_root_path + '/' + site + '/' + sensor + '_' + month + '_' + year + '.nc'

def GetSensorTuple(s, f):
    '''
    Based on a sensor key and a filename: 
      Return a 5-tuple: Two DataArrays (sensor, depth) plus range-lo, range-hi, default color string
    Argument s is the sensor identifier string like 'temp'
    Argument f is the source filename like './../data/osb_ctd_jan22_temperature.nc' 
    '''
    DA_sensor    = xr.open_dataset(f)[s]                # DataArray
    DA_depth     = xr.open_dataset(f)['depth']          # DataArray
    range_lo     = ranges[s][0]                         # expected numerical range of this sensor data
    range_hi     = ranges[s][1]                         #   lo and high
    sensor_color = colors[s]                            #   default chart color for this sensor
    return (DA_sensor, DA_depth, range_lo, range_hi, sensor_color)




# A data dictionary called dd
# dd = {}


# A list of keys for sp sensors (excepting spectrophotometer)
sp_sensorkeys = ['time',
                 'conductivity', 'density', 'pressure', 'salinity', 'temoperature', 
                 'chlora', 'backscatter', 'fdom', 
                 'si412', 'si443', 'si490', 'si510', 'si555', 'si620', 'si683', 
                 'nitrate', 'nitratedark', 
                 'pco2', 'dissolvedoxygen', 'par', 'ph', 'east', 'north', 'up']

# A dictionary of expected numerical data range tuples using sp_sensorkeys
sp_data_ranges = {'time':(0., 1.),
                  'conductivity':(3.2,3.7),
                  'density':(1024, 1028),
                  'pressure':(0.,200.),
                  'salinity':(32, 34),
                  'temperature':(7, 11),
                  'chlora':(0.,1.5),
                  'backscatter':(0.00,0.006),
                  'fdom':(0.5,4.5),
                  'si412':(0.0, 15.0),
                  'si443':(0.0, 15.0),
                  'si490':(0.0, 15.0),
                  'si510':(0.0, 15.0),
                  'si555':(0.0, 15.0),
                  'si620':(0.0, 15.0),
                  'si683':(0.0, 15.0),
                  'nitrate':(0., 35.),
                  'nitratedark':(0., 35.),
                  'pco2':(200.0, 1200.0),
                  'dissolvedoxygen':(50.0, 300.),
                  'par':(0.0, 300.),
                  'ph':(7.6, 8.2),
                  'east':(-0.4, 0.4),
                  'north':(-0.4, 0.4),
                  'up':(-0.4, 0.4) }

# sp_modes = {'conductivity':(('a','d','r'), (0,1,2,3,4,5,6,7,8))}
# sp_standard_deviations = {'conductivity':(0.1, 0.6), etcetera
# sp_colors = {conductivity':('xkcd:maroon','xkcd:light orange'),
# sp_sensornames = {'conductivity':'Conductivity',

# Notes on reformatting spectral irradiance (spkir) data by channel
# From an un-differentiated spkir.nc source file we have Dataset ds.
# This will be written as 7 sensor files where sensor name is spkir412nm etc.
# Already using non-duplicated 'time'. Sensor names will have spkir pre-pended.
# 
# relative_path = 'rca/sensors/data/'
# site          = 'osb'
# instrument    = 'spkir'
# sensor        = 'spkir'
# spkir_months  = ['apr21', 'jul21', 'jan22']
# for month in spkir_months:
#     input_fnm       = relative_path + site + '_' + instrument + '_' + month + '_' + sensor + '.nc'
#     output_fnm_base = relative_path + site + '_spkir_' + month + '_'
#     ds = xr.open_dataset(input_fnm)
#     ReformatSpkirData(ds, output_fnm_base)
#
# ds = xr.open_dataset('rca/sensors/data/osb_spkir_jan22_spkir412nm.nc')
# ds.spkir412nm.plot()
#






#############################
####
#### Shallow Profiler Sensor Data Dictionaries
####
#############################


# Old version: A list of sub-lists: Each sublist has [0] sensor name string [1] instrument name string.
# Deprecate this in favor of mapping sensors to instruments some less labored way.
# Also this is not verified 1:1 with sp_sensorkeys
# sensors = [
# ['conductivity', 'ctd'], ['density', 'ctd'], ['pressure', 'ctd'], ['salinity', 'ctd'], 
#   ['temperature', 'ctd'],
# ['chlora', 'fluor'], ['backscatter', 'fluor'], ['fdom', 'fluor'],
# ['spkir412nm', 'spkir'], ['spkir443nm', 'spkir'], ['spkir490nm', 'spkir'], 
#   ['spkir510nm', 'spkir'], ['spkir555nm', 'spkir'], ['spkir620nm', 'spkir'], ['spkir683nm', 'spkir'],
# ['nitrate', 'nitrate'],
# ['nitratedark', 'nitrate'],
# ['pco2', 'pco2'],
# ['do', 'do'],
# ['par', 'par'],
# ['ph', 'ph'],
# ['up', 'vel'], ['east', 'vel'], ['north', 'vel']]



# Not verified against sp_sensorkeys
ranges = {
'conductivity':(3.2,3.7),'density':(1024, 1028),'pressure':(0.,200.),'salinity':(32, 34),'temp':(7, 11),
'chlora':(0.,1.5),'backscatter':(0.00,0.006),'fdom':(0.5,4.5),
'spkir412nm':(0.0, 15.0), 'spkir443nm':(0.0, 15.0), 'spkir490nm':(0.0, 15.0), 'spkir510nm':(0.0, 15.0), 'spkir555nm':(0.0, 15.0), 'spkir620nm':(0.0, 15.0), 'spkir683nm':(0.0, 15.0),
'nitrate':(0., 35.),
'pco2':(200.0, 1200.0),
'do':(50.0, 300.),
'par':(0.0, 300.),
'ph':(7.6, 8.2),
'up':(-0.4, 0.4),'east':(-0.4, 0.4),'north':(-0.4, 0.4)
}



# Not verified against sp_sensorkeys
standard_deviations = {
'conductivity':(0.1, 0.6),'density':(0., .3),'pressure':(0.,10.),'salinity':(.0, .4),'temp':(.0, .7),
'chlora':(0.0, 0.5),'backscatter':(0.0,0.003),'fdom':(0.0,0.7),
'spkir412nm':(0.0, .5), 'spkir443nm':(0.0, .5), 'spkir490nm':(0.0, .5), 'spkir510nm':(0.0, .5), 'spkir555nm':(0.0, .5), 'spkir620nm':(0.0, .5), 'spkir683nm':(0.0, .5),
'nitrate':(0., 4.),
'pco2':(0.0, 10.0),
'do':(0.0, 40.),
'par':(0.0, 30.),
'ph':(0., 0.2),
'up':(0., 0.1),'east':(0, 0.1),'north':(0., 0.1)
}


# Move this into sp_colors
# Match to sp_sensorkeys
colors = {
'conductivity':'xkcd:maroon','density':'xkcd:brick red','pressure':'xkcd:eggplant','salinity':'cyan','temp':'red',
'chlora':'green','backscatter':'xkcd:blood orange','fdom':'xkcd:olive drab',
'spkir412nm':'black', 'spkir443nm':'black', 'spkir490nm':'black', 'spkir510nm':'black', 
'spkir555nm':'black', 'spkir620nm':'black', 'spkir683nm':'black',
'nitrate':'black',
'pco2':'black',
'do':'blue',
'par':'red',
'ph':'yellow',
'up':'red','east':'green','north':'blue'
}

# Realign
# Match to sp_sensorkeys
sensor_names = {
'conductivity':'Conductivity','density':'Density (kg m-3)','pressure':'Pressure',
'salinity':'Salinity','temp':'Temperature (deg C)',
'chlora':'Chlorophyll-A','backscatter':'Particulate Backscatter','fdom':'Fluorescent DOM',
'spkir412nm':'Spectral Irradiance 412nm',
'spkir443nm':'Spectral Irradiance 443nm',
'spkir490nm':'Spectral Irradiance 490nm',
'spkir510nm':'Spectral Irradiance 510nm',
'spkir555nm':'Spectral Irradiance 555nm',
'spkir620nm':'Spectral Irradiance 620nm',
'spkir683nm':'Spectral Irradiance 683nm',
'nitrate':'Nitrate Concentration',
'pco2':'CO2 Concentration',
'do':'Dissolved Oxygen',
'par':'Photosynthetically Available Radiation',
'ph':'pH',
'up':'Current: Vertical','east':'Current: East','north':'Current: North'
}


#############################
#############################
####
#### Shallow Profiler Specific Sensor Bespoke Functions
####
#############################
#############################


def ReformatSpkirData(ds, output_fnm_base):
    """
    From an un-differentiated spkir.nc source file we have Dataset ds.
    This will be written as 7 sensor files where sensor name is spkir412nm etc.
    Already using non-duplicated 'time'. Sensor names will have spkir pre-pended.
    """
    ds_data_vars = [i for i in ds.data_vars]
    ds_attrs     = [i for i in ds.attrs]
    dvars = [['412nm', 'spkir412nm'],      # [0] becomes [1]
             ['443nm', 'spkir443nm'], ['490nm', 'spkir490nm'], ['510nm', 'spkir510nm'],
             ['555nm', 'spkir555nm'], ['620nm', 'spkir620nm'], ['683nm', 'spkir683nm']]

    for dv in dvars:                 # loops over data variables to modify 
        local_ds = ds.copy()         #   the local_ds copy of the passed full dataset
        for ds_dv in ds_data_vars:
            if not ds_dv == dv[0] and not ds_dv == 'z':
                local_ds = local_ds.drop(ds_dv)
            elif ds_dv == dv[0]:
                local_ds = local_ds.rename({ds_dv:dv[1]})
        for key in ds_attrs: 
            if not key == 'units': local_ds.attrs.pop(key)

        # double check: eliminate duplicated time entries
        _, keeper_index = np.unique(local_ds['time'], return_index=True)
        local_ds = local_ds.isel(time=keeper_index)
        
        write_fnm = output_fnm_base + dv[1] + '.nc'
        local_ds.to_netcdf(write_fnm)
    return



##############
# 
# This code adjusts spkir data files by breaking them out into wavelength channels.
#   It is confusing because an input file e.g. osb_spkir_jan22_spkir.nc has already
#   been generated by ReformatDataFile() found in data.py. 
#
# This code is disabled with the idea of building it into the Jupyter Book properly
#   in a soon-ish time frame.
#
##############
#
# relative_path = 'rca/sensors/data/'
# site          = 'osb'
# instrument    = 'spkir'
# sensor        = 'spkir'
# spkir_months  = ['apr21', 'jul21', 'jan22']
# if False: 
#     for month in spkir_months:
#         input_fnm       = relative_path + site + '_' + instrument + '_' + month + '_' + sensor + '.nc'
#         output_fnm_base = relative_path + site + '_spkir_' + month + '_'
#         ds = xr.open_dataset(input_fnm)
#         ReformatSpkirData(ds, output_fnm_base)
#
# run this to verify
# ds = xr.open_dataset('rca/sensors/data/osb_spkir_jan22_spkir412nm.nc')
# ds.spkir412nm.plot()
#
###############



if __name__ == '__main__':
    '''
    The shallowprofiler module is code specific to the three shallow profilers associated with CEA + RCA.
    This code tests the intrinsic functions etcetera.
    '''
    print(sp_sensorkeys[0])
