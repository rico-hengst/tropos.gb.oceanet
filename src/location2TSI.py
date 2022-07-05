#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""The script creates a csv-file and contains DatETime/Lat/Lon/Filename of images
Execution
---------
./location2TSI.py -c PS95 -i tsi

Parameters
----------
Cruise : str
Instrument :str 

Processing
----------
The tracking file is loaded (timezone UTC expected).
The directory tree of TSI collects all images.
The filename/images are sorted to a list.
The exposure_datetime of the image (do not trust the exif data ar taken from
  * date=directory name, time=string of image file name OR
  * datetime = stat mtime of the image file
  * ASSUMPTION files are located at server oceanet timezone CET!!!!!!!!!!!!!!!!!!!! if files are moved to rsd2 please use timezone UTC
All images will be not included if their exposure_datetime do not match the time interval in the tracking files.
Via interpolation the exposure_datetime images get their Latitude(Longitude via interpolation from the tracking file.

Returns
-------
a csv file to publishing via pangaea.de
"""


import pandas as pd
from datetime import datetime, timezone
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import glob
import re
import os
import sys
import platform
from stat import *
import argparse
import logging
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import pytz

import get_toml_config
import zipfile




""" Create logger, name important """
module_logger = logging.getLogger('oceanet.tsi')


# read location track
# https://www.datacamp.com/community/tutorials/pandas-read-csv
# https://realpython.com/python-csv/
def read_my_file(track_pathfile):
    module_logger.info('Read Polarstern track: ' + track_pathfile)
    
    filename, file_extension = os.path.splitext(track_pathfile)
    
    if file_extension == '.tab':
        # load data csv tab separated
        #df = pandas.read_csv('PS95.2_link-to-mastertrack.tab', sep='\t', skiprows = 18, index_col='Date/Time')
        #https://doi.pangaea.de/10.1594/PANGAEA.859020?format=html#download
        
        
        # detect line numer end of header
        file = open(track_pathfile, "r")
        pattern = "\*\/"
        linenumber = 0
        for line in file:
            linenumber = linenumber + 1
            if re.search(pattern, line):
                print(line + ' in line: ' + str(linenumber))
                module_logger.info('End of file header detected: ' + track_pathfile)
                # if detected, break the for loop
                break
            
            # if no end of header detected, exit script
            if linenumber > 100:
                module_logger.warning('No end of file header detected: ' + track_pathfile)
                exit()
        
        df = pd.read_csv(track_pathfile, sep='\t', skiprows = linenumber)
    elif file_extension == '.txt':
        df = pd.read_csv(track_pathfile, sep='\t', skiprows = 0, converters={"Date/Time (UTC)": str})
        #print(df[df['Longitude'].apply(lambda x: not isinstance(x, float))])
    else:
        module_logger.error('Exit, wrong file extension of track file: ' + filename)
        exit()
    
    # https://doi.pangaea.de/10.1594/PANGAEA.863107?format=html#download
    # df = pd.read_csv('PS98_link-to-mastertrack.tab', sep='\t', skiprows = 18)
    
    # find DateTime column name 
    df_date_time_column_name = ''
    for col in df.columns:
        if 'Date/Time' in col:
            df_date_time_column_name = col
    
    if len(df_date_time_column_name) < 5:
        module_logger.error('Track file ' + track_pathfile + ' doesnt contain a column with name Date/Time')
        exit()

    ## convert to timestamp and add new column if not exists
    df['DateTime [UTC]'] = pd.to_datetime(df[df_date_time_column_name])
    # set timezone
    df['DateTime [UTC]'] = df['DateTime [UTC]'].dt.tz_localize(pytz.timezone('UTC'))

    ## get first DatTime
    df_firstdate = df['DateTime [UTC]'][0]


    # compute list of timedelta
    local_timedelta = df['DateTime [UTC]'] - df_firstdate

    ## transform dattime to seconds, to use as time axis for interpolation
    df['diff_seconds'] = local_timedelta.dt.total_seconds()
    
    return df, df_firstdate




# compute interpolation parameters for Lat and Lon
# https://docs.scipy.org/doc/scipy/reference/tutorial/interpolate.html
def get_interpol_parameters(df):
    module_logger.info('Compute interpolation parameters of DataFrame lat lon')
    f2_lat = interp1d(df['diff_seconds'], df['Latitude'], kind='cubic')
    f2_lon = interp1d(df['diff_seconds'], df['Longitude'], kind='cubic')
    
    return f2_lat, f2_lon
    

# get datetime of image file
# 1. time from filename if filename = 002136_0001.JPG please use 00 time as hour, 21 as minutes, 36 as seconds, and date use from folder name 
# 2. datetime from stat mtime
def get_exposure_datetime(pathfile):
        
    basename=os.path.basename(pathfile)
    
    dir_last = os.path.dirname(pathfile).split('/')[-1]
    date_from_dir = datetime.strptime(dir_last, '%Y-%m-%d')
    # set timezone to UTC
    date_from_dir = timezoneUTC.localize(date_from_dir)
    
    exposure_datetime = None


    # time 00:21:36 from imagename :  002136_0001.JPG
    # date from directoryname
    if re.match("^\d{6}_\d{4}", basename): #hhmmss_0001
        m = re.search('^(\d{6})_\d{4}', basename)
        time_from_filename = m.group(1) # cause 0 = whole string
        
        exposure_datetime = datetime.strptime(date_from_dir.strftime("%Y-%m-%d") + ' ' + time_from_filename, '%Y-%m-%d %H%M%S')
        
        # set timezone to UTC
        exposure_datetime = timezoneUTC.localize(exposure_datetime)
        #module_logger.debug('Image DateTime: time is taken from filename and Date is taken from directoryname')
        
        
    # datetime is taken from file stat mtime    
    else:
        # get time from stat
        # example PS95 stat 2015-10-29/20151029_234413_2307.JPG = Modify: 2015-10-30 00:48:15.000000000 +0100
        # file was modified in timezone CET
        exposure_datetime = os.stat(pathfile).st_mtime
        exposure_datetime = datetime.fromtimestamp( exposure_datetime )#, tz=timezone.utc)
        
        # set timezone to CET
        exposure_datetime = timezoneCET.localize(exposure_datetime)
        
        # check if directory date if less equal than 24h than stst mtime
        d =  exposure_datetime - date_from_dir
        if abs( d.seconds ) > 24*60*60:
            module_logger.error('DateTime diff between directorydate ' +  dir_last + ' and file mtime > 1 day: ' + str(d.seconds) + ' seconds')
            quit()
            
        #module_logger.debug('Image DateTime is taken from file stat mtime')
        
    return dir_last, basename, exposure_datetime

# find files and sort
# ! Note: function sorted and glob does'nt return a sorted list, a workaround is required to sort the list of strings
# files = glob.glob('/home/hengst/scripte/python' + '/**/*.py', recursive=True)
# files = sorted( glob.glob('/home/hengst/scripte/python' + '/**/*.py', recursive=True), key=os.path.getsize)
def find_files_to_dfpics(df, args, config):
    
    # get metadata of instrument
    instrument = None  
    for x in config["instruments"]:
        if args.instrument in x:
            instrument = x[args.instrument]
            
          
    if not (instrument):
        module_logger.warning('Instrument "' + args.instrument +  '" not exists in misson "' + args.cruise + '".')
        quit()
    
    # create new config dict with two main keys: instrument & mission
    config_singular = {}
    config_singular["instrument"] = instrument 
    config_singular["mission"] = config["mission"][args.cruise]

    
    # get metadata of mission
    mission = config["mission"][args.cruise]
    
    # check if dir exists
    if not (os.path.isdir(instrument["path_level0_fix"])):
        module_logger.warning('Data directory not exists: ' + instrument["path_level0_fix"])
        quit()
    else:
        module_logger.info('Find files in directory: ' + instrument["path_level0_fix"])
        
        
     # add dataframe
    dfpics = pd.DataFrame(columns=['DateTime [UTC]', 'File'])
        

    # iteration
    index=-1
    for path_filename_level0 in instrument["_path_filenames_level0"]:
        index=index+1
        
        # name of current diretcory
        dirname = os.path.dirname(path_filename_level0)
        
        # check if directory exists
        if not (os.path.isdir( dirname )):
            module_logger.warning('Data sub-directory not exists: ' + dirname)
            continue
        
        # check is direcoty is readable       
        if not (os.access(dirname, os.R_OK)):
            module_logger.warning("No read access to path: " + dirname)
            quit()
        
        # this test is only for testing the program with less data files
        if index == 13:
            #break    # break here
            ok = 1
        
        files = sorted( glob.glob( path_filename_level0, recursive=True), key=os.path.realpath )
        
        module_logger.info('Found {0:4d} image files in directory {1:20s}'.format(len(files), path_filename_level0) )

        #https://thispointer.com/python-get-list-of-files-in-directory-sorted-by-name/
        #files = sorted( filter( os.path.isfile,\
        #                        glob.glob('/vols/oceanet-archive_chief/OCEANET_DATEN_BACKUP/Test/DATA/WOLKENKAMERA' + '/**/*.JPG', recursive=True) ) )

        for pathfile in files:

            dir_last, basename, exposure_datetime = get_exposure_datetime(pathfile)
            
            if exposure_datetime:
                dfpics = dfpics.append({'DateTime [UTC]': exposure_datetime, 'File' : dir_last + "/" + basename, 'FileFullPath' : pathfile}, ignore_index=True)
            else:
                 module_logger.warning('No exposure datetime traceable: ' + pathfile )
    
    # check if images are in the dataframe
    nn = dfpics['DateTime [UTC]'].count()
    if nn == 0:
        module_logger.warning('In total no images were found!')
        quit()
    else:
        module_logger.info('In total ' + str(nn) + ' images were found.')
    
    # set dfpics timezone to UTC)
    
    # convert dfpics to timezone UTC, cause stat mtime has CET timezone
    dfpics['DateTime [UTC]'] = dfpics['DateTime [UTC]'].dt.tz_convert(pytz.timezone('UTC'))
    
    # get smallest DT, cause smallest must not be the first element
    # please use df NOT dfpics, cause df is the interpolation bases
    df_firstdate = df['DateTime [UTC]'].min()


    # create new timedelta related to first datetime
    local_timedelta3 = dfpics['DateTime [UTC]'] - df_firstdate
    dfpics['diff_seconds'] = local_timedelta3.dt.total_seconds()

    # sort by timedaelta cause list of files seems to be un-sorted
    dfpics = dfpics.sort_values(by='diff_seconds', ascending=True)
    
    
    # check if NaN exists
    number_nan_values = dfpics.isnull().sum().sum()
    if number_nan_values > 0:
        module_logger.error('Warning, {0} NaN values exists in Dataframe'.format(number_nan_values))
        quit()
    

    return dfpics, config_singular
    
# remove records in dfpics dataframe if records not fite in interval of df
def remove_dfpics_outside(df, dfpics):
    module_logger.info('Remove dfpics records outside df period')
    
    #print(df)
    #print(dfpics)

    ## remove row in dataframe pics, if pics.DT out of df.DT
    l_old1 = len(dfpics)
    dfpics = dfpics[ dfpics['DateTime [UTC]'] >= df['DateTime [UTC]'].min()  ]
    module_logger.info(str(l_old1 - len(dfpics)) + ' records removed (next min(datetime) of track)')
    
    l_old2 = len(dfpics)
    dfpics = dfpics[ dfpics['DateTime [UTC]'] <= df['DateTime [UTC]'].max() ]
    module_logger.info(str(l_old2 - len(dfpics)) + ' records removed (previous max(datetime) of track)')
    
    module_logger.info('Number of originally collected dfpics records: ' + str(l_old1) )
    module_logger.info('Number of remained dfpics records: ' + str(len(dfpics)))
    
    return dfpics
    
# interpolate lat, lon to dfpics dataframe
def interpolation_dfpics(dfpics, f2_lat, f2_lon):
    module_logger.info('Compute interpolation of dfpics')
    dfpics['Latitude'] = f2_lat(dfpics['diff_seconds'])
    dfpics['Longitude'] = f2_lon(dfpics['diff_seconds'])
    
    
    # check if NaN exists
    number_nan_values = dfpics.isnull().sum().sum()
    if number_nan_values > 0:
        module_logger.error('Warning, {0} NaN values exists in Dataframe'.format(number_nan_values))
        module_logger.error('Maybe number of point in mastertrack is to large {0}, interpolation problem?, please use a mastertrack with less resolution!'.format(len(df['Latitude'])))
        quit()
    
    return dfpics
    


# plot track
def plot_me(df, dfpics, config_singular):
    
    if not os.path.isdir(config_singular["instrument"]["path_level1a_image"]):
        module_logger.error('Directory to write image not exists: ' + config_singular["instrument"]["path_level1a_image"]  )
        exit()
        
    output_file = config_singular["instrument"]["path_level1a_image"] + "_" + args.cruise + "_track.png"
    module_logger.info('Plot track to file: ' + output_file)
    
    # get max min lat lon
    lat_max = df['Latitude'].max()
    lat_min = df['Latitude'].min()
    lon_max = df['Longitude'].max()
    lon_min = df['Longitude'].min()
    
    lat_1 = lat_min -15 - 2 * abs(lat_max - lat_min) 
    lat_2 = lat_max + 15 + 2 * abs(lat_max - lat_min) 
    lon_1 = lon_min - 20 - 2 * abs(lon_max - lon_min) 
    lon_2 = lon_max + 20 + 2 * abs(lon_max - lon_min) 
    
    # compute new map bounding box
    if lat_1 < -90:
        lat_1 = -90
    if lat_2 > 90:
        lat_2 = 90
    if lon_1 < -180:
        lon_1 = -180
    if lon_2 > 180:
        lon_2 = 180
        
    #print('Min Max Lat Lon: ', str(lat_min), ' ', str(lat_max), ' ', str(lon_min), ' ', str(lon_max))
    #print('1 2 Lat Lon: ', str(lat_1), ' ', str(lat_2), ' ', str(lon_1), ' ', str(lon_2))

    # https://scitools.org.uk/cartopy/docs/v0.5/matplotlib/advanced_plotting.html
    fig = plt.figure(figsize=(10, 10))
    
    #ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    #ax = plt.axes(projection=ccrs.PlateCarree())
    
    ax = plt.axes(projection=ccrs.Orthographic(central_longitude=0.0, central_latitude=lat_min + (lat_max - lat_min)*0.5))
    
    
    
    #ax.set_extent([-160, 160, -90, 90], crs=ccrs.PlateCarree())
    #ax.set_extent([lon_1, lon_2, lat_1, lat_2], crs=ccrs.PlateCarree())
    
    # ad coast country
    ax.coastlines(resolution='50m', color='grey', linewidth=1)
    ax.add_feature(cfeature.LAND, facecolor=("lightgray"), alpha=0.5 )
    ax.add_feature(cfeature.BORDERS, linestyle=':', alpha=0.2, linewidth=0.5)
    
    geo = ccrs.Geodetic()
    

    
    # grid
    #gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                  #linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    #gl.xlabels_top = False
    #gl.ylabels_left = False
    

    x, y = (df['Longitude'].tolist(), df['Latitude'].tolist() )
    #m.plot(x, y, 'm+', ms = 1)

    x2, y2 = (dfpics['Longitude'].tolist(), dfpics['Latitude'].tolist() )
    #m.plot(x, y, 'g|', ms = 3)
    
    ax.plot(x, y, 'm+', ms = 1, label='Cruise mastertrack ', transform=geo)
    ax.plot(x2, y2, 'g|', ms = 3, label='TSI shots', transform=geo)
    legend = ax.legend(shadow=True)
    ax.set_global()

   
    #plt.xlabel('Longitude', labelpad=40)
    
    plt.title(args.cruise)
    plt.suptitle(str( dfpics['DateTime [UTC]'].iloc[0] )  + ' - ' + str( dfpics['DateTime [UTC]'].iloc[-1] ) + ' UTC', fontsize=10)

    #plt.show()
    fig.savefig(output_file, dpi = 200)
    


# write dfpics to output
def write_file(dfpics, config_singular):
    
    
    output_file =  args.cruise + '_' + args.instrument + '.txt'
    output_file =  config_singular["instrument"]["path_level1a_csv"] + args.cruise + '_' + args.instrument + '.txt'
    
    if not os.path.isdir(config_singular["instrument"]["path_level1a_csv"]  ):
        module_logger.error('Directory to write data not exists: ' + config_singular["instrument"]["path_level1a_csv"]  )
        exit()
    
    module_logger.info('Write dfpics to file: ' + output_file)
    dfpics.to_csv(output_file, sep='\t', header=True, index=False, columns=['DateTime [UTC]', 'Latitude', 'Longitude', 'File', 'FileFullPath'], float_format='%.5f', date_format='%Y-%m-%dT%H:%M:%S %z')
    #dfpics.to_csv(output_file, sep='\t', header=True, index=False, columns=['DateTime [UTC]', 'Latitude', 'Longitude', 'File'], float_format='%.5f')



# write all related pics to zip
def write_piczipfile(dfpics, config_singular):
    output_file =  config_singular["instrument"]["path_level1a_csv"] + args.cruise + '_' + args.instrument + '.zip'
    if not os.path.isdir(config_singular["instrument"]["path_level1a_csv"]  ):
        module_logger.error('Directory to write data not exists: ' + config_singular["instrument"]["path_level1a_csv"]  )
        exit()
    
    module_logger.info('Write pics to zip archive: ' + output_file)
    
    zf = zipfile.ZipFile(output_file, "w")
    
    
    for index, row in dfpics.iterrows():
        zf.write(row['FileFullPath'], row["File"])


#####################################################################################                                                    
# getting args, setting logger
def adjust(argv):
    
    # get name of directory where main script is located
    current_dirname = os.path.dirname(os.path.realpath(__file__))
    
    # get the name of the directory from where the script was executed
    exec_dirname = os.getcwd()
    
    # define log_path_file + create dir
    #log_path_file = current_dirname + "/log/uv_processing.log"
    #log_path_file = exec_dirname + "/../log/oceanet.log"
    
    
        
    """Insert de initial and final dates as strings as 20190107(year:2019/month:01/day:07)"""
    
    """for calling the function from the terminal"""
    parser = argparse.ArgumentParser(description='Process oceanet tsi.') 
    parser.add_argument('-c', required=True, type=str, dest='cruise', # la variable se guarda en args.id como string
                    help='Insert the name of the cruise (e.g: PS95 or PS122_1)')
    parser.add_argument('-i', required=True, type=str, dest='instrument',
                    help='Name of the instrument')
    parser.add_argument('-p', type=str, dest='root_path', default='/vols/oceanet-archive_chief/OCEANET_DATEN_BACKUP/',
                    help='Insert the froot path of the oceanet data (e.g: /vols/oceanet-archive_chief/OCEANET_DATEN_BACKUP/')
    parser.add_argument('--loglevel', default='INFO', dest='loglevel',
                    help="define loglevel of screen INFO (default) | WARNING | ERROR ")
    args = parser.parse_args()
    
    
    #config = get_toml_config.run()
    l = ["-s", "mission", "-n" , args.cruise]
    
    thisdict = {
      "selected": "mission",
      "name": args.cruise,
      "loglevel": "INFO"
    }
    
    
    """Check python version"""
    python_version = platform.python_version().split(".")
    if int(python_version[0]) < 3:
        module_logger.error( "Your python version is: " + platform.python_version() )
        module_logger.error( "Script will be terminated cause python version < 3 is required !" )
        exit()
    
    
    # get config
    config = get_toml_config.adjust( thisdict )
    
    
    
    
        
    
    # add first log mesage
    module_logger.info('Start oceanet tsi processing')
    
    if args.cruise is None:
        module_logger.error('Cruise name is not provided!')
        exit()
    
    if args.instrument is None:
        module_logger.error('Instrument is not provided!')
        exit()
        
    if not os.path.isfile(  config["mission"][args.cruise]["track"] ):
        module_logger.error('Cruise track file not exists: ' + config["mission"][args.cruise]["track"] )
        exit()
    
    
    # return
    return args, config




#####################################################################################                                                    
if __name__ == "__main__":
    # execute only if run as a script
    print(__file__)
    
    args, config = adjust(sys.argv[1:])
    

    

    # set timezones
    timezoneCET = pytz.timezone("CET")
    timezoneUTC = pytz.timezone("UTC")

    df, df_firstdate = read_my_file( config["mission"][args.cruise]["track"] )
    f2_lat, f2_lon = get_interpol_parameters(df)
    dfpics, config_singular = find_files_to_dfpics(df, args, config)

    dfpics = remove_dfpics_outside(df, dfpics)
    dfpics = interpolation_dfpics(dfpics, f2_lat, f2_lon)




    if len(dfpics)>100:
        plot_me(df, dfpics, config_singular)
        write_file(dfpics, config_singular)
        write_piczipfile(dfpics, config_singular)
    else:
        module_logger.error('Impossible to show track, to less records')
    
