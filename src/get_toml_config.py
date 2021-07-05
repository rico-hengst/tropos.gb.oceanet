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
import pprint





# set pathfile of config files (toml))
cfg_instruments_file = os.path.dirname(os.path.realpath(__file__))  + "/../conf/instruments.toml"
cfg_missions_file = os.path.dirname(os.path.realpath(__file__))  + "/../conf/missions.toml"


# check if config files exists
if not os.path.isfile( cfg_instruments_file ):
    logger.warn( 'File not exists '+ cfg_instruments_file )
    quit()
if not os.path.isfile( cfg_missions_file ):
    logger.warn( 'File not exists '+ cfg_missions_file )
    quit()


# load config files
cfg_instruments = toml.load(cfg_instruments_file)
cfg_missions = toml.load(cfg_missions_file)



# add dates vector to all missions
for mission in cfg_missions:
    #print(mission)
    if not ( cfg_missions.get(mission,{}).get("datetime_start") and cfg_missions.get(mission,{}).get("datetime_stopp") ):
        logger.info("start stopp date of mission not exists??")
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
    
    #cfg_missions[mission]['_dates'] = dates.to_pydatetime()
    cfg_missions[mission]['_'] = { 'dates' :dates.to_pydatetime() }




def get_instruments( mission_of_interest, logger ):
    logger.info("Start to collect related instruments to mission of interest: " + mission_of_interest )
    logger.info("Show metadata starting from selected mission -> get instruments")
    
    # check if mission_of_interest exists
    if not cfg_missions.get(mission_of_interest, {}):
        logger.warn("Error, mission not exists: " + mission_of_interest)
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




def get_missions( instrument_of_interest, logger ):
    logger.info("Start to collect related missions to instrument of interest: " + instrument_of_interest )
    logger.info("Show metadata starting from selected instrument -> get missions")


    # check if instrument_of_interest exists
    if not cfg_instruments.get(instrument_of_interest, {}):
        logger.warn("Error, instrument not exists: " + instrument_of_interest)
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
    if (args["selected"] == "mission"):
        for mission in cfg["mission"]:
            dates = cfg["mission"][mission]["_"]["dates"]

    
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
def loop(args, logger):
    nested_dict = None
    
    if (args["selected"] == "instrument"):
        logger.info("Instrument was choosed")
        nested_dict = get_missions( args["name"], logger )
    elif (args["selected"] == "mission"):
        logger.info("Mission was choosed")
        nested_dict = get_instruments( args["name"], logger )
    else:
        logger.warn("error")
        quit()
        
    cfg = toml.loads( toml.dumps(nested_dict)  )
    
    cfg = add_instrument_pathfilenames(args, cfg)


    #print (cfg)
    #logger.info("RESULTED CONFIG:\n")
    for key in cfg:
        logger.info(key + ":")
       # logger.info( cfg.get(key,[]) )
        
        
        pp = pprint.PrettyPrinter(width=71, compact=True, depth=3,  indent=3)

        pp.pprint(cfg.get(key,[]) )
        
    return cfg



#####################################################################################                                                    
# getting args, setting logger, load configs
def adjust(argv):

    # get name of directory where main script is located
    current_dirname = os.path.dirname(os.path.realpath(__file__))
    
    # get the name of the directory from where the script was executed
    exec_dirname = os.getcwd()
    
    # define log_path_file + create dir
    #log_path_file = current_dirname + "/log/uv_processing.log"
    log_path_file = current_dirname + "/../log/oceanet.log"
    
    
    """ Create logger, name important """
 
    # create logger with
    logger = logging.getLogger('oceanet')
    logger.setLevel(logging.DEBUG)
    
    # create file handler which logs even debug messages
    fh = logging.FileHandler( log_path_file )
    fh.setLevel(logging.DEBUG)
    
    # create/check level
    screen_level = logging.getLevelName(argv["loglevel"])
    
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    #ch.setLevel(logging.WARNING)
    ch.setLevel(screen_level)
    
    # create formatter and add it to the handlers
    formatter = logging.Formatter(fmt='%(asctime)s | %(name)-14s | %(levelname)-8s | %(message)s | %(module)s (%(lineno)d)', datefmt='%Y-%m-%d %H:%M:%S',)
    
    # add formatter to the handlers
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    
    
    logger.info("Start to read config files")
    
    
    cfg = loop( argv, logger )
    
    logger.info("Finish to read config files")
    
    return cfg
    

#####################################################################################                                                    
if __name__ == "__main__":
    # execute only if run as a script
    print(__file__)
    
    # parse cmd args
    parser = argparse.ArgumentParser(description='Oceanet, read config.') 
    
    parser.add_argument('-s', required=True, type=str, dest='selected',
                    choices=['instrument', 'mission'],
                    help='Focussed on instrument or on mission')
    parser.add_argument('-n', required=True, type=str, dest='name', # la variable se guarda en args.id como string
                    help='Insert the name of the instrument or mission')

    parser.add_argument('--loglevel', default='INFO', dest='loglevel',
                    help="define loglevel of screen INFO (default) | WARNING | ERROR ")
    #parser.add_argument('--logfile', default=log_path_file, dest='logfile',
                    #help="define logfile (default: directory where you execute the script) ")
    args = parser.parse_args()
    
    
    # args to dict
    thisdict = {
      "selected": args.selected,
      "name": args.name,
      "loglevel": args.loglevel
    }
    
    
    adjust( thisdict )


