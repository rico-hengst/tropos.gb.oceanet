#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""The script 
* collects and read the text files from a cruise from the SCAW device,
* extract the focussed variables (radiation currently)
* and save the data to a netcdf file

Make sure that the toml files mission and instruments hold the most current metadata.

Parameters
----------
Mission : str
Instrument :str

Processing
----------
#Find SCAW1 files
#Import file to dataframe
#Append to total_dataframe
#Export total_dataframe

Returns
-------
a netcdf file to publishing via pangaea,de that
"""


import glob
import os
import sys
import platform
import pandas as pd
import xarray as xr
import io
import logging
import argparse
import logging
from datetime import datetime, timezone
import pytz
# pip install git+https://github.com/hdeneke/trosat-base
from trosat import cfconv as cf
from trosat import sunpos as sp
import netCDF4
import numpy as np
import get_toml_config


""" Create logger, name important """
module_logger = logging.getLogger('oceanet.reprint_radiation')

mapping_table={
        0:'DateTime [UTC]',
        5:'Latitude',
        6:'Longitude',
        19:'DSR',
        20:'DLR',
    }

# find files and sort
# ! Note: function sorted and glob does'nt return a sorted list, a workaround is required to sort the list of strings
# files = glob.glob('/home/hengst/scripte/python' + '/**/*.py', recursive=True)
# files = sorted( glob.glob('/home/hengst/scripte/python' + '/**/*.py', recursive=True), key=os.path.getsize)
def find_scaw1_files(config):
    module_logger.info('Find files in directory tree')
    
    instrument = None
    
    # get metadata of instrument
    for x in config["instruments"]:
        if args.instrument in x:
            instrument = x[args.instrument]
            
    #instrument = None        
    if not (instrument):
        module_logger.warning('Instrument "' + args.instrument +  '" not exists in misson "' + args.cruise + '".')
        quit()
    
    # get metadata of mission
    mission = config["mission"][args.cruise]
    
    # check if dir exists
    if not (os.path.isdir(instrument["path_level0_fix"])):
        module_logger.warning('Data directory not exists: ' + instrument["path_level0_fix"])
        quit()
    else:
        module_logger.info('Find files in directory: ' + instrument["path_level0_fix"])
        
        
    total_df = pd.DataFrame()

        

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
    
    
        # read file
        total_df = read_single_scaw1_file(path_filename_level0, total_df)
        
    return total_df
        

def read_single_scaw1_file(pathfile, total_df):
    
    if not (os.path.exists(pathfile) ):
        module_logger.warning("File not exists: " + pathfile)
        return total_df
    else:
        module_logger.info('Read scaw1 file: ' + pathfile)

    
    
    
    # simple csv read via pandas not possible, cause files contains "
    # wor around 
    #   * read file
    #   * remove "
    #   * put content ti io buffer
    #   * read via read_csv from buffer
    
    content = open(pathfile).read()
    content = content.replace("\"", "")
   

    
    # put string content to io buffer to read via panda
    # https://stackoverflow.com/questions/56842369/how-do-you-use-pandas-read-csv-method-if-the-csv-is-stored-as-a-variable
    buffer = io.StringIO(content)
    #df = pd.read_csv(buffer, sep=',', skiprows = 0, header = None, parse_dates = [0], na_values='NAN')
    df = pd.read_csv(buffer, sep=',', skiprows = 0, header = None, parse_dates = [0], na_values='NAN', usecols=list(mapping_table.keys()) )
    module_logger.debug( "\n"+ str( df.head(2) ) )
   
    # reanme relevant columns
    df.rename( columns = mapping_table, inplace = True )
    
    # set UTC timezone
    module_logger.debug('Set timezone UTC')
    df['DateTime [UTC]'] = df['DateTime [UTC]'].dt.tz_localize(pytz.timezone('UTC'))
   
   # print(df)
    
    # check NaN, drop rows
    dsr_nan = df['DSR'].isna().sum()
    dlr_nan = df['DLR'].isna().sum()
    
    lat_nan = df['Latitude'].isna().sum()
    lon_nan = df['Longitude'].isna().sum()
    if dsr_nan > 0 or dlr_nan > 0 or lat_nan > 0 or lon_nan > 0:
        module_logger.info('NaN values found in Lat {0}, in Lon {0}'.format(lat_nan, lon_nan))
        module_logger.info('NaN values found in DSR {0}, in DLR {0}'.format(dsr_nan, dlr_nan))
        module_logger.info('Rows with NaN values are dropped')
        df.dropna(inplace=True)
        
   # print(df)
    
     # check nan
    number_nan_values = df[ list( mapping_table.values()) ].isnull().sum().sum()
    if number_nan_values>0:
        module_logger.error( '{0} NaN values detected!'.format( str( number_nan_values ) ) )
        
        is_NaN = df.isnull()
        row_has_NaN = is_NaN.any(axis=1)
        module_logger.error(df[row_has_NaN] )
        quit()
    
    # sort data
    df.sort_values(by='DateTime [UTC]', inplace=True)
    
    #print(df)
    # check if datetime is unique
    #if len(df['DateTime [UTC]'].unique())>0:
        #logger.error('{0} / {1} duplicates in rows of DateTime exists!'.format( str( len(df['DateTime [UTC]'].unique()) ), str(len(df)) ) )
        #logger.error( 'First/last duplicates are: {0} ... {1}'.format( df['DateTime [UTC]'].unique()[0], df['DateTime [UTC]'].unique()[-1] ) )
        
    # check if datetime is unique
    if df.duplicated(subset=['DateTime [UTC]']).sum() > 0:
        module_logger.warning('{0} / {1} duplicates in rows of DateTime exists!'.format( str( df.duplicated(subset=['DateTime [UTC]']).sum() ), str(len(df)) ) )
        module_logger.warning( 'Duplicates are: \n{0}'.format( df['DateTime [UTC]'][ df['DateTime [UTC]'].duplicated() ] ) )
        
    
    # append selected columns to total dataframe
    #total_df.append( df[["DT", "DSR",'DLR']], ignore_index=True )
    module_logger.debug('Add data of current file to total DataFrame.')
    
    total_df = pd.concat([total_df,df[ list( mapping_table.values()) ] ])
    
    
    return total_df
    
    
################
def handle_duplicates(args, total_df):
        # sort
    total_df.sort_values(by='DateTime [UTC]', inplace=True)

    if total_df.duplicated(subset=['DateTime [UTC]']).sum() > 0:
        module_logger.error('{0} / {1} duplicates / total number of records in row DateTime exists!'.format( str( total_df.duplicated(subset=['DateTime [UTC]']).sum()), str(len(total_df))  ) )
        module_logger.error( 'Duplicates are: \n{0}'.format( total_df['DateTime [UTC]'][ total_df['DateTime [UTC]'].duplicated() ] ) )
        
        # excption
        ans = input("Save data although duplicates exists, otherwise duplicated will be dropped? [y/N] ")
        if ans == "y":
            nc_file = nc_file + '_include_duplicates.nc'
            module_logger.info( "Your choise: save data include duplicates!" )
        elif ans == "N":
            
            total_df.drop_duplicates(subset=['DateTime [UTC]'], keep='first', inplace=True)
            module_logger.info( "Drop duplicates, kept first occurence!" )
            
            if total_df.duplicated(subset=['DateTime [UTC]']).sum() > 0:
                module_logger.error( "Duplicates still exists" )
                exit()
            
            # check unsorted
            if not (total_df['DateTime [UTC]'].is_monotonic_increasing):
                module_logger.error( "Dataset is not sorted: no monotonic" )
                exit()
                
    return total_df
    
    
################
def flag_sun_angle(args, total_df):
    """ Calculate cosine of zenith, angle and earth-sun-distance """
    szen, sazi = sp.sun_angles( total_df["DateTime [UTC]"], total_df["Latitude"] , total_df["Longitude"] )
    total_df['szen'] = szen
    total_df['sazi'] = sazi
   # total_df['nautical twilight'] = total_df['szen'] - 12
    
    # flag data solar night
    total_df['ok_flag_dsr_sun_zen'] = 0
    
    total_df.loc[total_df['szen'] < 90, 'ok_flag_dsr_sun_zen'] = 1
    
   
    
    
    flagged_dsr = total_df[total_df["ok_flag_dsr_sun_zen"] == 0]
    
    module_logger.info( "Flagging about sunlight NOT visible, in total: " + str(len(total_df["ok_flag_dsr_sun_zen"])) + " / " + str( len(flagged_dsr["ok_flag_dsr_sun_zen"]) ) )
    
    return total_df
    
    
    
################
def flag_outlier(args, total_df):
    sigma = 6
    z_dsr, avg_dsr, std_dsr, total_df["ok_flag_dsr_outlier"] = zscore(total_df["DSR"], window=86400, thresh=sigma, return_all=True)
    z_dlr, avg_dlr, std_dlr, total_df["ok_flag_dlr_outlier"] = zscore(total_df["DLR"], window=86400, thresh=sigma, return_all=True)
    
    # if outlier flag = 0 = outlier!
    
    module_logger.info( "Flagging dsr outlier with sigma=" + str(sigma) + ", in total flagged records: " + str( len(  total_df[ total_df["ok_flag_dsr_outlier"].map(lambda x: x==00 or x==1111) ]) ))
    return total_df
    
################ 
def plot_data ( args) :
    nc_file = args.cruise + "_" + args.instrument + '.nc'
    sigma = 6
    print(nc_file)
    data_xr=xr.open_dataset( nc_file, engine="netcdf4" )
    #flagged_dsr = data_xr[data_xr["flag"] == 0]
    
    
    # flagged outlier
    outlier_dsr = data_xr.where(data_xr['ok_flag_dsr_outlier'] == 0, drop=True)
    #outlier_dsr = data_xr[data_xr["ok_flag_dsr_outlier"] == 0]
    #outlier_dlr = data_xr[data_xr["ok_flag_dlr_outlier"] == 0]
    outlier_dlr = data_xr.where(data_xr['ok_flag_dlr_outlier'] == 0, drop=True)
    
    # flagged dsr zenith
    flagged_zenith_dsr = data_xr.where(data_xr['ok_flag_dsr_sun_zen'] == 0, drop=True)
    
    import matplotlib.pyplot as plt
    
    
    fig, ax1 = plt.subplots(3,figsize=(10, 10))
    
    # subplot 1 plot values and flags
    color = 'tab:red'
    ax1[0].set_xlabel('Date and Time [UTC]')
    ax1[0].set_ylabel('exp', color=color)
    ax1[0].set_title("Surface downwelling flux and outlier flags at " + args.cruise)
    lsn1=ax1[0].plot(data_xr['time'], data_xr['DSR'] , label='Shortwave radiation flux', color=color)
    ax1[0].tick_params(axis='y', labelcolor=color)
    
    lsn11=ax1[0].plot(outlier_dsr['time'], outlier_dsr['ok_flag_dsr_outlier'] + outlier_dsr['DSR'], marker='o', ls='' , label='Flag outlier $\\sigma>$' + str(sigma) + ", shortwave radiation, flags in total = " +str(len(outlier_dsr['DSR'])), color="peru")

    ax2 = ax1[0].twinx()  # instantiate a second axes that shares the same x-axis
    
    color = 'tab:blue'
    ax2.set_ylabel('sin', color=color)  # we already handled the x-label with ax1
    lsn2=ax2.plot(data_xr['time'], data_xr['DLR'] , label='Longwave radiation flux ', color=color)
    ax2.tick_params(axis='y', labelcolor=color)
    
    
    
    lsn21=ax2.plot(outlier_dlr['time'], outlier_dlr['ok_flag_dlr_outlier'] + outlier_dlr['DLR'], marker='o', ls='' , label='Flag outlier $\\sigma>$' + str(sigma) + ", longwave radiation, flags in total = " + str(len(outlier_dlr['ok_flag_dlr_outlier'] )), color="magenta")
    
    leg = lsn1 + lsn11+ lsn2 +lsn21
    labs = [l.get_label() for l in leg]
    ax1[0].legend(leg, labs, loc=0, framealpha=0.9)
    
    
    # ylim for data and flags
    if args.cruise in ['PS122_1', 'PS122_2', 'PS122_5no']:
        ax1[0].set_ylim([-3,70])
        ax2.set_ylim([150, 400])
    else:
        ax1[0].set_ylim([-3,900])
        ax2.set_ylim([150, 550])
    
    
    
    
    fig.tight_layout() 
    
    
    # subplot 2 plot azi zen angle
    color = 'tab:green'
    lsn3 = ax1[1].plot(data_xr['time'], data_xr['szen'] , label='Zenit angle ', color=color)
    ax1[1].set_ylabel('Zenith angle', color=color)
    ax1[1].tick_params(axis='y', labelcolor=color)
    ax1[1].set_title("Sun angle at " + args.cruise)
    
    color = 'tab:orange'
    ax4 = ax1[1].twinx()
    ax4.tick_params(axis='y', labelcolor=color)
    lsn4 = ax4.plot(data_xr['time'], data_xr['sazi'] , label='Azimuth angle ', color=color)
    ax4.set_ylabel('Azimuth angle', color=color)
    
    ax1[1].set_ylim([55,125])
    ax4.set_ylim([-150,500])
    
    # Solution for having two legends
    leg = lsn3 + lsn4
    labs = [l.get_label() for l in leg]
    ax1[1].legend(leg, labs, loc=0)
    
    
    # subplot 3 plot data and sun angle flag dsr
    color = 'tab:red'
    ax1[2].set_ylabel('DSR flux [W*m^{-2}]', color=color)
    ax1[2].set_title("Surface downwelling shortwave flux and sun angle flags at " + args.cruise)
    lsn5=ax1[2].plot(data_xr['time'], data_xr['DSR'] , label='Shortwave radiation ', color=color)
    lsn51=ax1[2].plot(flagged_zenith_dsr['time'], flagged_zenith_dsr['ok_flag_dsr_sun_zen'] + flagged_zenith_dsr['DSR'], marker='o', ls='',label='Flag (sun zenit angle), total flags = ' + str(len(flagged_zenith_dsr['DSR'])), color="green")
    leg = lsn5 + lsn51 
    labs = [l.get_label() for l in leg]
    ax1[2].legend(leg, labs, loc=0)
    
    # plot to file
    my_fn = args.cruise + "_" + args.instrument + ".png"
    plt.savefig(my_fn)
    
################
def write_data( args, total_df ):
    
    module_logger.info('Write data to file.')
    
    nc_file = args.cruise + "_" + args.instrument + '.nc'


    
    
    
    
    # read json
    json_file  = os.path.dirname(os.path.realpath(__file__))  + '/../conf/scaw1_js_meta.json'
    module_logger.info('Read json metadata file to generate netCDF: ' + json_file )
    
    if not os.path.isfile( json_file ):
        module_logger.error( 'File json not exists '+ json_file )
        quit()

    cfjson=cf.read_cfjson(json_file)
    
    # compute seconds since
    second_since = netCDF4.date2num(total_df['DateTime [UTC]'], cfjson['variables']['time']['attributes']['units'])
    
    
    # add metadata
    cfjson["attributes"]["file_created"] = datetime.utcnow().strftime('%Y-%m-%d')
    cfjson["attributes"]["project_mission"] = args.cruise
    cfjson["attributes"]["time_coverage_start"] = str( total_df['DateTime [UTC]'].min() )
    cfjson["attributes"]["time_coverage_end"] = str( total_df['DateTime [UTC]'].max() )
    cfjson["attributes"]["geospatial_lat_min"] = total_df['Latitude'].min()
    cfjson["attributes"]["geospatial_lat_max"] = total_df['Latitude'].max()
    cfjson["attributes"]["geospatial_lon_min"] = total_df['Longitude'].min()
    cfjson["attributes"]["geospatial_lon_max"] = total_df['Longitude'].max()
    
    
    del cfjson["attributes"]['geospatial_lon_max']
    
   
    
    
    for mykey in list(cfjson["attributes"].keys()):
        t = mykey.find("g", 0, 1)
        if not (t):
            module_logger.info('Delete global attribute, it seems to be a comment: ' + mykey )
            del cfjson["attributes"][mykey]
            
    
    # set Dim
    cfjson.setDim('time', len(second_since))
    
    # add data to json
    module_logger.info( "Add tmp data to json variable" )
    for index , local_column_name in mapping_table.items():
        if "DateTime" in local_column_name:
            cfjson.setData('time',second_since)
        else:
            cfjson.setData(local_column_name, total_df[ local_column_name ])
    
    # add some variables to netcdf
    cfjson.setData('szen', total_df[ 'szen' ])
    cfjson.setData('sazi', total_df[ 'sazi' ])
    cfjson.setData('ok_flag_dsr_sun_zen', total_df[ 'ok_flag_dsr_sun_zen' ])
    cfjson.setData('ok_flag_dsr_outlier', total_df[ 'ok_flag_dsr_outlier' ])
    cfjson.setData('ok_flag_dlr_outlier', total_df[ 'ok_flag_dlr_outlier' ])
    
    
    # write nc file
    module_logger.info('Write data to file: ' + nc_file )
    """ Creating and saving the netCDF-File """
    f = cf.create_file(nc_file, cfdict=cfjson)
    
    f.close()



#################
# https://stackoverflow.com/questions/75938497/outlier-detection-of-time-series-data
def zscore(s, window, thresh=3, return_all=False):
    roll = s.rolling(window=window, min_periods=1, center=True)
    avg = roll.mean()
    std = roll.std(ddof=0)
    z = s.sub(avg).div(std)   
    m = z.between(-thresh, thresh)
    
    if return_all:
        return z, avg, std, m
    return s.where(m, avg)

#####################################################################################                                                    
# getting args, setting logger
def adjust(argv):
    
    # get name of directory where main script is located
    current_dirname = os.path.dirname(os.path.realpath(__file__))
    
    # get the name of the directory from where the script was executed
    exec_dirname = os.getcwd()
    
    # define log_path_file + create dir
    #log_path_file = current_dirname + "/log/uv_processing.log"
    log_path_file = exec_dirname + "/oceanet.log"
    
    
        
    """Insert de initial and final dates as strings as 20190107(year:2019/month:01/day:07)"""
    
    """for calling the function from the terminal"""
    parser = argparse.ArgumentParser(description='Process oceanet scaw1.') 
    parser.add_argument('-c', required=True, type=str, dest='cruise', # la variable se guarda en args.id como string
                    help='Insert the name of the cruise (e.g: PS95 or PS122_1)')
    parser.add_argument('-i', required=True, type=str, dest='instrument',
                    help='Name of the instrument')
    parser.add_argument('--loglevel', default='INFO', dest='loglevel',
                    help="define loglevel of screen INFO (default) | WARNING | ERROR ")
    parser.add_argument('--zenit_angle', default=90, type=int, dest='zenit_angle_used_for_flagging',
                    help="define zenith angle of sun when shortwave data will get a flag (default 90 degree) ")
    parser.add_argument('--sigma', default=6, type=int, dest='sigma_used_for_outlier_flagging',
                    help="define sigma that is used for outlier flagging of a rolling window (deafult 6) ")
    args = parser.parse_args()
    
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
    module_logger.info('Start oceanet radiation processing')
    
    
    # return
    return args, config


#####################################################################################                                                    
if __name__ == "__main__":
    # execute only if run as a script
    print(__file__)
    
    args, config = adjust(sys.argv[1:])
    
    #total_df = find_scaw1_files( config )
      
    #total_df = handle_duplicates(args, total_df)

    #total_df = flag_sun_angle(args, total_df)
    #total_df = flag_outlier(args, total_df)

    #write_data(args, total_df)
    
    plot_data(args)


    #df_multiindex = total_df.set_index(['DT', 'Latitude', 'Longitude'])
    #print(df_multiindex.to_xarray())
    
    


