import os, sys, time, glob, warnings
from os.path import join as joindir
from IPython.display import clear_output
from matplotlib import pyplot as plt
from matplotlib import colors as mplcolors
import numpy as np, pandas as pd, xarray as xr
from numpy import datetime64 as dt64, timedelta64 as td64
from ipywidgets import interact, widgets
from traitlets import dlink

from shallowprofiler import *

warnings.filterwarnings('ignore')

def doy(theDatetime): return 1 + int((theDatetime - dt64(str(theDatetime)[0:4] + '-01-01')) / td64(1, 'D'))
def dt64_from_doy(year, doy): return dt64(str(year) + '-01-01') + td64(doy-1, 'D')
def day_of_month_to_string(d): return str(d) if d > 9 else '0' + str(d)


def RenderShallowProfilerTwoDayDepthChart():
    '''
    This is a very hardcoded function that generates a two-day span of profiles with some
    annotations indicating what is going on, particularly with midnight / noon profiles.
    '''
    t0, t1, fnm = '2022-01-01', '2022-01-03', './data/rca/sensors/osb/conductivity_jan_2022.nc'
    ds          = xr.open_dataset(fnm).sel(time=slice(dt64(t0), dt64(t1)))
    fig, axs    = plt.subplots(figsize=(12,4), tight_layout=True)
    axs.plot(ds.time, -ds.depth, marker=',', ms=36., color='k', mfc='r', linewidth='.001')
    axs.set(ylim = (-210., 0.), title='Shallow profiler depth over two days', ylabel='depth (m)', xlabel='Hours (UTM)')
    axs.text(dt64('2021-12-31 22:15'), -184, 'AT')
    axs.text(dt64('2021-12-31 22:05'), -193, 'REST')
    axs.text(dt64('2022-01-01 07:40'), -205, 'midnight')
    axs.text(dt64('2022-01-01 21:30'), -205, 'noon')
    axs.text(dt64('2022-01-01 09:05'), -20, 'slow')
    axs.text(dt64('2022-01-01 09:05'), -30, 'descent')
    axs.text(dt64('2022-01-01 22:30'), -20, 'slow')
    axs.text(dt64('2022-01-01 22:30'), -30, 'descent')
    return True
    

def VisualizeProfiles(date_id, n_days, year_id, month_id, month_name, site_name, site_abbrev, datafnm):
    '''
    Plot profiles similar to ProfilerDepthChart: One day per row, supports many days, 
    wider and simpler layout. This is a backup diagnostic tool for looking at longer 
    time intervals. 
    '''
    ds = xr.open_dataset('./data/rca/sensors/' + site_abbrev + '/' + datafnm)
    fig, axs = plt.subplots(n_days, 1, figsize=(15,n_days), tight_layout=True)
    for i in range(n_days):
        daystring = str(i+1) if i > 8 else '0' + str(i+1)
        time0 = dt64(year_id + '-' + month_id + '-' + daystring + 'T00:00:00')
        time1 = dt64(year_id + '-' + month_id + '-' + daystring + 'T23:59:59')
        dsDay = ds.sel(time=slice(time0, time1))
        axs[i].plot(dsDay.time, dsDay.z, marker='.', markersize=3., color='k')
        axs[i].set(ylim = (-200., 0.))
    print('...' + month_name + ' ' + str(year_id) + ' ' + site_name + ' daily profiles...')
    return True



def ChartSensor(p, xrng, pidcs, A, Az, Albl, Acolor, Aleg, wid, hgt, z0=-200., z1=0.):
    """
    Make a stack of charts with one horizontal axis versus y-depth.
    The data are in DataArrays A and Az. 
    pIdcs are row indices of the profile Dataframe: A choice of which profiles to plot 
      by index. The dataframe gives bounding times for the profile/mode selected. 
    
    p        pandas Dataframe of indexed profile timestamps
    xrng     2-list: low, high values for the sensor
    pIdcs    list of indices within p to use in generating a sequence of paired charts
    A        xarray Dataset: source data of type A
    Az       xarray Dataset: depth data for sensor A
    Albl     string: label for sensor A
    Acolor   string: color for sensor A
    Aleg     'rest', 'ascent' or 'descent'
    wid      width for two charts
    hgt      height for one chart (scaled by number of charts)
    z0, z1   depth range
    """
    
    # empirical values for the day's two longer-duration profiles
    midn0 = td64( 7*60 + 10, 'm')        # 7 hours 10 minutes
    midn1 = td64( 7*60 + 34, 'm')        # 7 hours 34 minutes
    noon0 = td64(20*60 + 30, 'm')        # 20 hours 30 minutes
    noon1 = td64(20*60 + 54, 'm')        # 20 hours 54 minutes 
        
    # limit the number of charts to 100
    ncharts = len(pidcs)
    if ncharts > 100: ncharts = 100
    do_one = True if ncharts == 1 else False
    print("Attempting", ncharts, "charts\n")

    # ncharts x 1: charts in a vertical column
    fig, axs = plt.subplots(ncharts, 1, figsize=(wid, hgt*ncharts), tight_layout=True)

    # profile table p has column headers 'a0z', 'a0t' and so on for r and d
    #   We are interested in the time columns to constrain data selection.
    #   These correspond to which "leg" is stipulated: rest, ascent or descent.
    #   Given these are versus-depth charts: the rest option doesn't make much sense.
    if   Aleg == 'rest':   keyA = ('r0t', 'r1t')
    elif Aleg == 'ascent': keyA = ('a0t', 'a1t')
    else:                  keyA = ('d0t', 'd1t')

  
    # The subsequent code is 'loop over charts: plot each chart: A'
    # For this we need both a profile index into the profile dataframe p (from the
    #   pidcs[] list *and* a chart index 0, 1, 2, ... These are respectively 
    #   pidx and i.
    for i in range(ncharts):
        
        pidx = pidcs[i]

        tA0, tA1 = p[keyA[0]][pidx], p[keyA[1]][pidx]
        Ax, Ay = A.sel(time=slice(tA0,  tA1)), Az.sel(time=slice(tA0, tA1))
        
        if do_one: axs.plot(    Ax, Ay, ms = 4., color=Acolor, mfc=Acolor)
        else:      axs[i].plot( Ax, Ay, ms = 4., color=Acolor, mfc=Acolor)
        
        # set the chart title
        if i == 0: 
            if do_one: axs.set(title = Albl + ' (' + Acolor + ')')
            else:      axs[i].set(title = Albl + ' (' + Acolor + ')')

        # Set axis ranges from passed list of pairs xrng[][]
        if do_one: axs.set(    xlim = (xrng[0], xrng[1]), ylim = (z0, z1))
        else:      axs[i].set( xlim = (xrng[0], xrng[1]), ylim = (z0, z1))

        # chart time label
        profile_start_time = 'Start UTC: ' + str(tA0)
        delta_t = tA0-dt64(tA0.date())
        if delta_t > midn0 and delta_t < midn1: profile_start_time += " MIDNIGHT local"
        if delta_t > noon0 and delta_t < noon1: profile_start_time += " NOON local"
        xlabel = xrng[0] + 0.2*(xrng[1] - xrng[0])
        ylabel = -10
        if do_one: axs.text(xlabel, ylabel, profile_start_time)
        else: axs[i].text(xlabel, ylabel, profile_start_time)
        
    return fig, axs

def ChartOneSensor(p, xrng, pidcs, A, Az, Albl, Acolor, Aleg, wid, hgt, z0=-200., z1=0.):
    return ChartSensor(p, xrng, pidcs, A, Az, Albl, Acolor, Aleg, wid, hgt, z0=-200., z1=0.)

    

def ChartTwoSensors(p, xrng, pidcs, A, Az, Albl, Acolor, Aleg, \
                                    B, Bz, Blbl, Bcolor, Bleg, \
                                    wid, hgt, z0=-200., z1=0.):
    """
    Make a stack of charts with two horizontal axes to compare two sensors A and B.
    The data are in DataArrays: A, Az, B, Bz. pidcs are row indices for the profile
    Dataframe, i.e. a choice of which profiles to plot by index. 
    
    p        pandas Dataframe of indexed profile timestamps
    xrng     list of 2-lists: low-to-high values for the two sensors
    pIdcs    indices within p to use in generating a sequence of paired charts
    A        xarray Dataset: source data of type A (B)
    Az       xarray Dataset: depth data for sensor A (B)
    Albl     string: label for sensor A (B)
    Acolor   string: color for sensor A (B)
    Aleg     'rest', 'ascent' or 'descent'
    wid      width for two charts
    hgt      height for one chart (scaled by number of charts)
    z0, z1   depth range
    """
    
    # empirical values for the day's two longer-duration profiles
    midn0 = td64( 7*60 + 10, 'm')        # 7 hours 10 minutes
    midn1 = td64( 7*60 + 34, 'm')        # 7 hours 34 minutes
    noon0 = td64(20*60 + 30, 'm')        # 20 hours 30 minutes
    noon1 = td64(20*60 + 54, 'm')        # 20 hours 54 minutes 
        
    # limit the number of charts to 100
    ncharts = len(pidcs)
    if ncharts > 100: ncharts = 100
    do_one = True if ncharts == 1 else False
    chart_case = 'chart' if do_one else 'charts'
    print("Attempting", ncharts, chart_case, "\n")

    # ncharts x 1: charts in a vertical column
    fig, axs = plt.subplots(ncharts, 1, figsize=(wid, hgt*ncharts), tight_layout=True)
    
    # list of twin axes for sensor B (one for each chart)
    axstwin = axs.twiny() if do_one else [axs[i].twiny() for i in range(ncharts)]

    # profile table p has column headers 'a0z', 'a0t' and so on for r and d
    #   We are interested in the time columns to constrain data selection
    if   Aleg == 'rest':   keyA = ('r0t', 'r1t')
    elif Aleg == 'ascent': keyA = ('a0t', 'a1t')
    else:                  keyA = ('d0t', 'd1t')
    if   Bleg == 'rest':   keyB = ('r0t', 'r1t')
    elif Bleg == 'ascent': keyB = ('a0t', 'a1t')
    else:                  keyB = ('d0t', 'd1t')
  
    # The subsequent code is 'loop over charts: plot each chart, A and B'
    # For this we need both a profile index into the profile dataframe p (from the
    #   passed list pidcs[] *and* a chart index 0, 1, 2, ... These are respectively 
    #   pidx and i.
    for i in range(ncharts):
        
        pidx = pidcs[i]

        tA0, tA1 = p[keyA[0]][pidx], p[keyA[1]][pidx]
        tB0, tB1 = p[keyB[0]][pidx], p[keyB[1]][pidx]
        
        Ax, Ay = A.sel(time=slice(tA0,  tA1)), Az.sel(time=slice(tA0, tA1))
        Bx, By = B.sel(time=slice(tB0,  tB1)), Bz.sel(time=slice(tB0, tB1))
        
        if do_one:
            axs.plot(    Ax, Ay, ms = 4., color=Acolor, mfc=Acolor)
            axstwin.plot(Bx, By, ms = 4., color=Bcolor, mfc=Bcolor)
        else:
            axs[i].plot(    Ax, Ay, ms = 4., color=Acolor, mfc=Acolor)
            axstwin[i].plot(Bx, By, ms = 4., color=Bcolor, mfc=Bcolor)
        
        # axis ranges
        if i == 0: 
            if do_one:
                axs.set(title = Albl + ' (' + Acolor + ', lower x-axis) and ' \
                              + Blbl + ' (' + Bcolor + ', upper x-axis)')
            else:
                axs[i].set(title = Albl + ' (' + Acolor + ', lower x-axis) and ' \
                                 + Blbl + ' (' + Bcolor + ', upper x-axis)')

        # Set axis ranges from passed list of pairs xrng[][]
        if do_one:
            axs.set(    xlim = (xrng[0][0], xrng[0][1]), ylim = (z0, z1))
            axstwin.set(xlim = (xrng[1][0], xrng[1][1]), ylim = (z0, z1))
        else:
            axs[i].set(    xlim = (xrng[0][0], xrng[0][1]), ylim = (z0, z1))
            axstwin[i].set(xlim = (xrng[1][0], xrng[1][1]), ylim = (z0, z1))

        # chart time label
        ascent_start_time = 'Start UTC: ' + str(tA0)
        delta_t = tA0-dt64(tA0.date())
        if delta_t > midn0 and delta_t < midn1: ascent_start_time += " MIDNIGHT local"
        if delta_t > noon0 and delta_t < noon1: ascent_start_time += " NOON local"
        xlabel = xrng[0][0] + 0.2*(xrng[0][1] - xrng[0][0])
        ylabel = -10
        if do_one: axs.text(xlabel, ylabel, ascent_start_time)
        else: axs[i].text(xlabel, ylabel, ascent_start_time)
        
    return fig, axs



def BundleChart(profiles, date0, date1, time0, time1, wid, hgt, data, title):
    '''
    Create a bundle chart: Multiple profiles showing sensor/depth in ensemble.
        date0   start / end of time range: date only, range is inclusive [date0, date1]
        date1
        time0   start / end time range for each day
        time1       (this scheme permits selecting midnight or noon)
        wid     figure size
        hgt
        data    a value from the data dictionary (5-tuple: includes range and color)
        title   chart title
        
    profiles is a global DataFrame
    '''
    pidcs = GenerateTimeWindowIndices(profiles, date0, date1, time0, time1) # each index contributes a thread to the bundle
    fig, ax = plt.subplots(figsize=(wid, hgt), tight_layout=True)
    for i in range(len(pidcs)):
        ta0, ta1 = profiles["a0t"][pidcs[i]], profiles["a1t"][pidcs[i]]          # [ta0, ta1] is this thread's time range (ascent)
        ax.plot(data[0].sel(time=slice(ta0,  ta1)), data[1].sel(time=slice(ta0, ta1)), ms = 4., color=data[4], mfc=data[4])
    ax.set(title = title)
    ax.set(xlim = (data[2], data[3]), ylim = (-200, 0))
    return ax


def ShowStaticBundles(d, profiles):
    '''creates bundle charts for Jan 2022, Oregon Slope Base'''
    BundleChart(profiles, dt64('2022-01-01'), dt64('2022-02-01'), td64(0, 'h'), td64(24, 'h'), 8, 6, d['do'], 'Dissolved Oxygen')
    BundleChart(profiles, dt64('2022-01-01'), dt64('2022-02-01'), td64(0, 'h'), td64(24, 'h'), 8, 6, d['temp'], 'Temperature')
    BundleChart(profiles, dt64('2022-01-01'), dt64('2022-02-01'), td64(0, 'h'), td64(24, 'h'), 8, 6, d['density'], 'Density')
    BundleChart(profiles, dt64('2022-01-01'), dt64('2022-02-01'), td64(0, 'h'), td64(24, 'h'), 8, 6, d['salinity'], 'Salinity')
    BundleChart(profiles, dt64('2022-01-01'), dt64('2022-02-01'), td64(0, 'h'), td64(24, 'h'), 8, 6, d['chlora'], 'Chlorophyll A Fluorescence')
    # These last two are not terribly illuminating
    # BundleChart(profiles, dt64('2022-01-01'), dt64('2022-02-01'), td64(0, 'h'), td64(24, 'h'), 8, 6, d['fdom'], 'FDOM')
    # BundleChart(profiles, dt64('2022-01-01'), dt64('2022-02-01'), td64(0, 'h'), td64(24, 'h'), 8, 6, d['bb'], 'Particulate Backscatter')
    
    return



def BundleInteract(d, profiles, sensor_key, time_index, bundle_size):
    '''
    Consider a time range that includes many (e.g. 279) consecutive profiles. This function plots sensor data
    within the time range. Choose the sensor using a dropdown. Choose the first profile using the start slider.
    Choose the number of consecutive profiles to chart using the bundle slider. 
    Details
      - There is no support at this time for selecting midnight or noon profiles exclusively
          - nitrate, ph and pco2 bundle charts will be correspondingly sparse
      - There is a little bit of intelligence built in to the selection of ascent or descent
          - most sensors measure on ascent or ascent + descent. pco2 and ph are descent only
          - ph and pco2 still have a charting bug "last-to-first line" clutter: For some reason
            the first profile value is the last value from the prior profile. There is a hack in
            place ("i0") to deal with this.
    '''
    

    (phase0, phase1, i0) = ('a0t', 'a1t', 0) if not (sensor_key == 'ph' or sensor_key == 'pco2') else ('d0t', 'd1t', 1)
    
    # print('  type(data):', type(data))
    # print('  data[0]:', data[0])
    # print('  len(data[0]):', len(data[0]))
    # print('  len(data):', len(data))
    print('BundleInteract() running...\n\n\n')
    
    # print('  type(data[0]):', type(data[0]))
    # print('\n\n\n')
    
    # d = dict(data[0])
    
    # print('type(d):', type(d))
    # print('\n\n\n')
    
    x      = d[sensor_key][0]
    z      = d[sensor_key][1]
    xlo    = d[sensor_key][2]
    xhi    = d[sensor_key][3]
    xtitle = sensor_names[sensor_key]
    xcolor = d[sensor_key][4]

    # This configuration code block is hardcoded to work with March 2021
    date0, date1   = dt64('2022-01-01'), dt64('2022-02-01')
    time0, time1   = td64(0, 'h'), td64(24, 'h')
    wid, hgt       = 9, 6
    x0, x1, z0, z1 = xlo, xhi, -200, 0
    title          = xtitle
    color          = xcolor
    pidcs          = GenerateTimeWindowIndices(profiles, date0, date1, time0, time1)    # !!!!! either midn or noon, not both
    nProfiles      = len(pidcs)
    
    fig, ax = plt.subplots(figsize=(wid, hgt), tight_layout=True)
    iProf0 = time_index if time_index < nProfiles else nProfiles
    iProf1 = iProf0 + bundle_size if iProf0 + bundle_size < nProfiles else nProfiles
    for i in range(iProf0, iProf1):
        pIdx = pidcs[i]
        ta0, ta1 = profiles[phase0][pIdx], profiles[phase1][pIdx]
        xi, zi = x.sel(time=slice(ta0,  ta1)), z.sel(time=slice(ta0, ta1))
        ax.plot(xi[i0:], zi[i0:], ms = 4., color=color, mfc=color)
    ax.set(title = title)
    ax.set(xlim = (x0, x1), ylim = (z0, z1))

    # Add text indicating the current time range of the profile bundle
    # tString = str(p["ascent_start"][pIdcs[iProf0]])
    # if iProf1 - iProf0 > 1: tString += '\n ...through... \n' + str(p["ascent_start"][pIdcs[iProf1-1]])
    # ax.text(px, py, tString)
    
    plt.show()
    return


def BundleInteractor(d, profiles, continuous_update = False):
    '''Set up three bundle-interactive charts, vertically. Independent sliders for choice of 
    sensor, starting profile by index, and number of profiles in bundle. (90 profiles is about
    ten days.) A fast machine can have cu = True to give a slider-responsive animation. Make
    it False to avoid jerky 'takes forever' animation on less powerful machines.
    '''
    style = {'description_width': 'initial'}
    
    # data dictionary d{} keys:
    optionsList = ['temperature', 'salinity', 'density', 'conductivity', 'do', 'chlora', 'fdom', 'bb', 'pco2', 'ph', 'par', 'nitrate']
    
    print('type(d):', type(d))
    print('len(d):', len(d))
    print('d["conductivity"]: is ok')
    print()
    print()
    print()

    interact(BundleInteract, d = [d],             \
                             profiles = profiles, \
                             sensor_key = widgets.Dropdown(options=optionsList,  value=optionsList[0], description='sensor'), \
                             time_index = widgets.IntSlider(min=0, max=270, step=1, value=160,                    \
                                                            layout=widgets.Layout(width='35%'),                   \
                                                            continuous_update=False, description='bundle start',  \
                                                            style=style),
                             bundle_size = widgets.IntSlider(min=1, max=90, step=1, value=20,                     \
                                                            layout=widgets.Layout(width='35%'),                   \
                                                            continuous_update=False, description='bundle width',  \
                                                            style=style))

    return
