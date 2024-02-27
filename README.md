# oceanet2pangaea

The repo contains scripts to convert measurements (oceanet) to the [pangaea data format](https://wiki.pangaea.de/wiki/Data_submission).
**This repo is in development** and based on former idl scripts.

The current predecessor repo contains scripts based on idl. This repo will substitute idl by python.
Furthermore the scripts are adapted to process oceanet data which are organized by instruments, not organized by Polarstern cruises.

## Requirements
### External software and libraries

todo

## Config

The json file contains the metadata information to put the netcdf attributes to the scaws netcdf file.

The configuration is stored in two toml files.

The ```get_toml_conf.py``` is made for get a dict of configs based on the provided args,

## Scripts

* ```location2TSI.py``` is made to create a textfile when allsky images were made. This info is merged to the coordinates of the cruise mastertrack where geo-positions are avaiable.

* ```reprint_radiation_SCAWS.py``` is made to parse all daily files and merge them to a cruise related netcdf file.
CAUTION: duplicate data records are avaible!!
