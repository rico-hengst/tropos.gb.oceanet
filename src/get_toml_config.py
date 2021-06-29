#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""The script read toml configuration of oceanet project and provide metadata of a selected instrument/mission

Parameters
----------
Selection instrument/mission : str
Name (key) of instrument/misson :str

Processing
----------


Returns
-------
dictionary of metadata instrument/misiion (cfg)
dictionary of derived information
"""

import toml
import os
import sys
import argparse
import pandas as pd
import pytz
import datetime
import logging


""" Create logger, name important """
module_logger = logging.getLogger('oceanet-processing.get_config')
module_logger.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)


# set pathfile of config files (toml))
cfg_instruments_file = "conf/instruments.toml"
cfg_missions_file = "conf/missions.toml"


# check if config files exists
if not os.path.isfile( cfg_instruments_file ):
    module_logger.warn( 'File not exists '+ cfg_instruments_file )
    quit()
if not os.path.isfile( cfg_missions_file ):
    module_logger.warn( 'File not exists '+ cfg_missions_file )
    quit()


# load config files
cfg_instruments = toml.load(cfg_instruments_file)
cfg_missions = toml.load(cfg_missions_file)



# add dates vector to all missions
for mission in cfg_missions:
    #print(mission)
    if not ( cfg_missions.get(mission,{}).get("datetime_start") and cfg_missions.get(mission,{}).get("datetime_stopp") ):
        module_logger.info("start stopp date of mission not exists??")
        quit()
    """pandas time counter vector instead of loop"""   
    dates=pd.date_range(
        cfg_missions.get(mission,{}).get("datetime_start").strftime("%Y%m%d"), 
        cfg_missions.get(mission,{}).get("datetime_stopp").strftime("%Y%m%d"),
        freq='1D', 
        name=str, 
        normalize=False, 
        tz="utc") 
    
                
    # add hidden key _dates with date vectors to each mission
    
    cfg_missions[mission]['_dates'] = dates.to_pydatetime()




def get_instruments( mission_of_interest ):
    module_logger.info("Start to collect related instruments to mission of interest: " + mission_of_interest )
    module_logger.info("Show metadata starting from selected mission -> get instruments")
    
    # check if mission_of_interest exists
    if not cfg_missions.get(mission_of_interest, {}):
        module_logger.warn("Error, mission not exists: " + mission_of_interest)
        quit()

    
    # add instrument to nested dict
    nested_dict = { 
        "mission": {
            mission_of_interest : cfg_missions.get(mission_of_interest, {})
        }
        , "instruments" : []}
        
    for instrument in cfg_missions.get(mission_of_interest, {}).get('instruments'):
        #print( cfg_instruments.get(instrument, {}) )
        nested_dict['instruments'].append( { instrument : cfg_instruments.get(instrument) } )

    return nested_dict




def get_missions( instrument_of_interest ):
    module_logger.info("Start to collect related missions to instrument of interest: " + instrument_of_interest )
    module_logger.info("Show metadata starting from selected instrument -> get missions")


    # check if instrument_of_interest exists
    if not cfg_instruments.get(instrument_of_interest, {}):
        module_logger.warn("Error, instrument not exists: " + instrument_of_interest)
        quit()

    # add instrument to nested dict
    nested_dict = { "instrument": {
            instrument_of_interest : cfg_instruments.get(instrument_of_interest, {})
        }
        , "missions" : []}
        
    # iteration to find related missions, add to nested dict
    for mission in cfg_missions:
        #print(mission)
        for instrument in cfg_missions.get(mission, {}).get('instruments'):
            if instrument == instrument_of_interest:
                #print("Instrument " + instrument_of_interest + " is part of mission " + mission)
                nested_dict['missions'].append( { mission : cfg_missions.get(mission) } )
            
    return nested_dict
    
    
def add_instrument_pathfilenames(args, cfg):
    # get _dates from mission
    if (args.selected == "mission"):
        for mission in cfg["mission"]:
            dates = cfg["mission"][mission]["_dates"]

    
        # get pathfile from instrument, add to instrument
        for key in cfg:
            if(key == 'instruments'):
                for i in range( len( cfg["instruments"] )):
                    
                    for key2 in cfg["instruments"][i].keys():

                        if(cfg["mission"]):
                            for mission in cfg["mission"]:
                                
                                # add empty list
                                path_filenames_level0 = []
                                
                                # iteration via all dates
                                for date in dates:
                                    try:
                                        path_filename = cfg["instruments"][i][key2]["path_level0_fix"] + eval( cfg["instruments"][i][key2]["path_filenames_level0"] )
                                        #print(path_filename)
                                        path_filenames_level0.append(path_filename)
                                    except:
                                        k=1
                                # add path_filenames to config
                                cfg["instruments"][i][key2]["_path_filenames_level0"]   = path_filenames_level0
                                
    
    return cfg

# ###################################################################################
#
def loop(args):
    nested_dict = None
    
    if (args.selected == "instrument"):
        module_logger.info("Instrument was choosed")
        nested_dict = get_missions( args.name )
    elif (args.selected == "mission"):
        module_logger.info("Mission was choosed")
        nested_dict = get_instruments( args.name )
    else:
        module_logger.warn("error")
        quit()
        
    cfg = toml.loads( toml.dumps(nested_dict)  )
    
    cfg = add_instrument_pathfilenames(args, cfg)


    #print (cfg)
    module_logger.info("RESULTED CONFIG:\n")
    for key in cfg:
        module_logger.info(key + ":")
        module_logger.info( cfg.get(key,[]) )
        
    return cfg



#####################################################################################                                                    
# getting args, setting logger, load configs
def adjust(argv):
    print("___")
    """for calling the function from the terminal"""
    parser = argparse.ArgumentParser(description='Oceanet, read config.') 
    
    parser.add_argument('-s', required=True, type=str, dest='selected',
                    choices=['instrument', 'mission'],
                    help='Focussed on instrument or on mission')
    parser.add_argument('-n', required=True, type=str, dest='name', # la variable se guarda en args.id como string
                    help='Insert the name of the instrument or mission')

    #parser.add_argument('--loglevel', default='INFO', dest='loglevel',
                    #help="define loglevel of screen INFO (default) | WARNING | ERROR ")
    #parser.add_argument('--logfile', default=log_path_file, dest='logfile',
                    #help="define logfile (default: directory where you execute the script) ")
    args = parser.parse_args()
    
    
    
    module_logger.info("Start to read config files")
    
    
    cfg = loop( args )
    
    module_logger.info("Finish to read config files")
    
    return cfg
    

#####################################################################################                                                    
if __name__ == "__main__":
    # execute only if run as a script
    print(__file__)
    adjust(sys.argv[1:])

#####################################################################################                                                    
def run():
    # execute only if run as a setuptoolscript
    print(__file__)
    adjust(sys.argv[1:])
