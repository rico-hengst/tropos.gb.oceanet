#!/usr/bin/env python3
# -*- coding: utf-8 -*-


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





import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

fff = xr.open_dataset("PS122_1_scaw1.nc_include_duplicates.nc")

fig,ax = plt.subplots(2,1, figsize=(10,6))
#_ = ax[0].plot(fff.time, fff.DSR)

j=list(range(0, len(fff.time)))


ax[0].plot(j,fff.time)
ax[1].plot(fff.time, fff.DSR)

print(len(fff.time))

plt.show()
