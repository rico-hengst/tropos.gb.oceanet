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
import io
import logging
import argparse
import logging
from datetime import datetime, timezone
import pytz
# pip install git+https://github.com/hdeneke/trosat-base
from trosat import cfconv as cf
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
        total_df = read_scaw1_file(path_filename_level0, total_df)
        
    return total_df
        

def read_scaw1_file(pathfile, total_df):
    
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
    
    
    # check if datetime is unique
    #if len(df['DateTime [UTC]'].unique())>0:
        #logger.error('{0} / {1} duplicates in rows of DateTime exists!'.format( str( len(df['DateTime [UTC]'].unique()) ), str(len(df)) ) )
        #logger.error( 'First/last duplicates are: {0} ... {1}'.format( df['DateTime [UTC]'].unique()[0], df['DateTime [UTC]'].unique()[-1] ) )
        
    # check if datetime is unique
    if df.duplicated(subset=['DateTime [UTC]']).sum() > 0:
        module_logger.warn('{0} / {1} duplicates in rows of DateTime exists!'.format( str( df.duplicated(subset=['DateTime [UTC]']).sum() ), str(len(df)) ) )
        module_logger.warn( 'Duplicates are: \n{0}'.format( df['DateTime [UTC]'][ df['DateTime [UTC]'].duplicated() ] ) )
        
    
    # append selected columns to total dataframe
    #total_df.append( df[["DT", "DSR",'DLR']], ignore_index=True )
    module_logger.debug('Add data of current file to total DataFrame.')
    total_df = pd.concat([total_df,df[ list( mapping_table.values()) ] ])
    
    
    return total_df
    

def write_data( args, total_df ):
    
    module_logger.info('Write data to file.')
    
    nc_file = args.cruise + "_" + args.instrument + '.nc'


    
    # sort
    total_df.sort_values(by='DateTime [UTC]', inplace=True)

    if total_df.duplicated(subset=['DateTime [UTC]']).sum() > 0:
        module_logger.error('{0} / {1} duplicates / total number of records in row DateTime exists!'.format( str( total_df.duplicated(subset=['DateTime [UTC]']).sum()), str(len(total_df))  ) )
        module_logger.error( 'Duplicates are: \n{0}'.format( total_df['DateTime [UTC]'][ total_df['DateTime [UTC]'].duplicated() ] ) )
        
        # excption
        ans = input("Save data although duplicates exists, otherwise duplicated will be dropped? [y/n] ")
        if ans == "y":
            nc_file = nc_file + '_include_duplicates.nc'
            module_logger.info( "Your choise: save data include duplicates!" )
        elif ans == "n":
            module_logger.error( "Your choise: exit the script!" )
            #exit()
            
            total_df.drop_duplicates(subset=['DateTime [UTC]'], keep='first', inplace=True)
            module_logger.info( "Drop duplicates, kept first occurence!" )
            
            if total_df.duplicated(subset=['DateTime [UTC]']).sum() > 0:
                exit()
            
            # check unsorted
            if not (total_df[DateTime ['UTC]'].is_monotonic_increasing:
                module_logger.error( "Dataset is not sorted: no monotonic" )
                exit()
        
    
    
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
        
    # write nc file
    module_logger.info('Write data to file: ' + nc_file )
    """ Creating and saving the netCDF-File """
    f = cf.create_file(nc_file, cfdict=cfjson)
    
    f.close()
    

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
    
    total_df = find_scaw1_files( config )

    write_data(args, total_df)


    #df_multiindex = total_df.set_index(['DT', 'Latitude', 'Longitude'])
    #print(df_multiindex.to_xarray())
    
    


