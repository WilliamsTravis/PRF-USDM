from sys import platform
import os

if platform == 'win32':
    homepath = "C:/users/user/github/PRF-USDM/"
    os.chdir(homepath)
    from flask_cache import Cache # I have this one working on Windows but not Linux
    import gdal
    import rasterio
    import boto3
    import urllib
    import botocore
    def PrintException():
        exc_type, exc_obj, tb = sys.exc_info()
        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, f.f_globals)
        print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))

    gdal.UseExceptions()
    print("GDAL version:" + str(int(gdal.VersionInfo('VERSION_NUM'))))
else:
    homepath = "/prf-app/"
    os.chdir(homepath)
    from flask_caching import Cache # I have this one working on Linux but not Windows :)
    
import copy
import dash
from dash.dependencies import Input, Output, State, Event
import dash_table_experiments as dt
import dash_core_components as dcc
import dash_html_components as html
from flask import Flask
import json
import numpy as np
import pandas as pd
import plotly
from tqdm import *
#from flask_cors import CORS
#from flask_cache import Cache
#from flask_caching import Cache
import xarray as xr


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))

###########################################################################
##################### Quick Mode Function #################################
###########################################################################
# Now, how do we choose monthly values. Mode, Median, Mean? Mean would be strange. Mode
    # Is turning out to be incredibly slow...
def arrayMode(array):
    def mode(lst):
        lst = list(lst)
        uniques = np.unique(lst)
        frequencies = [lst.count(i) for i in uniques]
        mx = max(frequencies)
        indx = frequencies.index(mx)
        return uniques[indx]
    return np.apply_along_axis(mode, axis = 0, arr = array)

###########################################################################
##################### Basis Risk Check ####################################
###########################################################################
def basisCheck(usdm,noaa,strike,dm):

    # Is it a named array list or just arrays?
    if len(usdm) == 2:
        date = usdm[0][-6:]
        usdm = usdm[1]
    if len(noaa) == 2:
        noaa = noaa[1]

    # Get cells at or above dm level drought
    drought = np.copy(usdm)
    drought[drought >= dm] = 9999
    drought[drought < 6] = 1

    # get cell at or below strike level rain
    rainless = np.copy(noaa)
    rainless[rainless <= strike] = 9999
    rainless[rainless < 9999] = 2 # No payouts. I had to set the triggered payouts to a high number to escape the index value range.
    rainless[rainless == 9999] = 1 # Payouts

    # Now, where are the 1's in drought that aren't in rainless?
    basis = rainless*drought
    basis[basis < 19998] = 0 # 19998 is where no payouts and drought intersect (9999*2)
    basis[basis == 19998] = 1

    return basis

###########################################################################
############## Finding Average Cellwise Coefficients of Variance ##########
###########################################################################
def covCellwise(arraylist):
    # Standardize to avoid negative values?
    arrays = [arraylist[i][1] for i in range(len(arraylist))]
    arraylist = standardize(arraylist)
    # First get standard deviation for each cell
    sds = np.nanstd([a[1] for a in arraylist],axis = 0)
   # Now get mean values for each cell
    avs = np.nanmean([a[1] for a in arraylist],axis = 0)
    # Third, simply divide
    covs = sds/avs
    # Average SD
    average = np.nanmean(covs)
    return(average)

###########################################################################
##################### USDM Drought Check ##################################
###########################################################################
def droughtCheck(usdm,dm):
    # Get just the array
    if len(usdm) == 2:
        date = usdm[0][-6:]
        usdm = usdm[1]

    # Get cells at or above dm level drought
    drought = np.copy(usdm)
    drought[drought >= dm] = 6
    drought[drought < 6] = 0
    drought[drought == 6] = 1

    return drought

def droughtCheck2(rain,strike):
    # Get just the array
    if len(rain) == 2:
        date = rain[0][-6:]
        rain = rain[1]

    # Get cells at or above dm level drought
    drought = np.copy(rain)
    drought[drought <= strike] = -9999
    drought[drought > -9999] = 0
    drought[drought == -9999] = 1

    return drought

###########################################################################
##################### Quick Histograms ####################################
###########################################################################
def indexHist(array,guarantee = 1,mostfreq = 'n',binumber = 1000, limmax = 0, sl = 0):
    # Check if it is a list with names, a list without names, a single array with a name,
        # or a single array without a name.
    if str(type(array)) == "<class 'list'>":
        if type(array[0][0]) == str and len(array[0])==2:
            name = array[0][0][:-7] + ' Value Distribution'
            array = [ray[1] for ray in array]
            na = array[0][0,0]
            for ray in array:
                ray[ray == na] = np.nan
        elif type(array[0]) == str:
            name = array[0] + ' Value Distribution'
            array = array[1]
            na = array[0,0]
            array[array == na] = np.nan
        else:
            na = array[0][0,0]
            name = "Value Distribution"
            for ray in array:
                ray[ray == na] = np.nan
    else:
        na = array[0,0]
        name = "Value Distribution"
        array[array == na] = np.nan

    # Mask the array for the histogram (Makes this easier)
    arrays = np.ma.masked_invalid(array)

    # Get min and maximum values
    amin = np.min(arrays)
    printmax = np.max(arrays)
    if limmax > 0:
        amax = limmax
    else:
        amax = np.max(arrays)

    # Get the bin width, and the frequency of values within, set some
    # graphical parameters and then plot!
    fig = plt.figure(figsize=(8, 8))
    hists,bins = np.histogram(arrays,range = [amin,amax],bins = binumber,normed = False)
    if mostfreq != 'n':
        mostfreq =  float(bins[np.where(hists == np.max(hists))])
        targetbin = mostfreq
        targethist = np.max(hists)
        firstprint = 'Most Frequent Value: '+ str(round(mostfreq,2))
    # Get bin of optional second line
    if sl != 0:
        differences = [abs(bins[i] - sl) for i in range(len(bins))]
        slindex = np.where(differences == np.nanmin(differences))
        secondline = bins[slindex]
        slheight = hists[slindex]
        secondtitle = '\nRMA Strike level: ' + str(guarantee) + ', Alt Strike Level: ' + str(round(sl,4))
    else:
        secondtitle = ''
    if mostfreq != 'n':
        if mostfreq == 0:
            secondcheck = np.copy(hists)
            seconds = secondcheck.flatten()
            seconds.sort() 
            second = float(bins[np.where(hists == seconds[-2])])
            targetbin = second
            targethist= seconds[-2]
            secondprint = '\n       Second most Frequent: '+str(round(second,2))
        else:
            secondprint = '' 
    width = .65 * (bins[1] - bins[0])
    center = (bins[:-1] + bins[1:]) / 2
    plt.bar(center, hists, align='center', width=width)
    title=(name+":\nMinimum: "+str(round(amin,2))+"\nMaximum: "+str(round(printmax,2))+secondtitle)
    plt.title(title,loc = 'center')
    if mostfreq != 'n':
        plt.axvline(targetbin, color='black', linestyle='solid', linewidth=4)
        plt.axvline(targetbin, color='r', linestyle='solid', linewidth=1.5)
    drange = np.nanmax(arrays) - np.nanmin(arrays)

    if sl != 0:
        plt.axvline(secondline, color='black', linestyle='solid', linewidth=4)
        plt.axvline(secondline, color='y', linestyle='solid', linewidth=1.5)
#        plt.annotate('Optional Threshold: \n' + str(round(sl,2)), xy=(sl-.001*drange, slheight), xytext=(min(bins)+.1*drange, slheight-.01*max(hists)),arrowprops=dict(facecolor='black', shrink=0.05))
#    cfm = plt.get_current_fig_manager()
#    cfm.window.move(850,90)

###############################################################################
########################## AWS Retrieval ######################################
###############################################################################
# For singular Numpy File - Might have to write this for a compressed numpy
def getNPY(path):
    key=[i.key for i in bucket.objects.filter(Prefix = path)][0] # Probably an easier way
    obj = resource.Object("pasture-rangeland-forage", key)
    try:
        with io.BytesIO(obj.get()["Body"].read()) as f:
            # rewind the file
            f.seek(0)
            array = np.load(f)
            array = array.f.arr_0
    except botocore.exceptions.ClientError as e:
        error = e
        if error.response['Error']['Code'] == "404":
            array = "The object does not exist."
        else:
            raise
    return array

# For 3D Numpy files
def getNPYs(numpypath,csvpath):
    # Get arrays
    key=[i.key for i in bucket.objects.filter(Prefix = numpypath)][0] # Probably an easier way
    obj = resource.Object("pasture-rangeland-forage", key)
    try:
        with io.BytesIO(obj.get()["Body"].read()) as file:
            # rewind the file
            file.seek(0)
            array = np.load(file)
            arrays = array.f.arr_0
    except botocore.exceptions.ClientError as error:
        print(error)

    # get dates
    key=[i.key for i in bucket.objects.filter(Prefix = csvpath)][0] # Probably an easier way
    obj = resource.Object("pasture-rangeland-forage", key)
    try:
        with io.BytesIO(obj.get()["Body"].read()) as df:
            datedf = pd.read_csv(df)
    except botocore.exceptions.ClientError as error:
        print(error)

    arrays = [[datedf['dates'][i],arrays[i]] for i in range(len(arrays))]
    return arrays


