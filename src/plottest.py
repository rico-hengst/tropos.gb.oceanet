#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.ticker as mticker
import matplotlib.pyplot as plt
import random
import math 
import numpy as np



x_ = np.linspace(0, 1, 180)

y_ = 4 * (x_**3) + 2 * (x_**2) + 5 * x_



y_ = [ math.sin(math.pi/0.5 * i) for i in x_ ]

amin, amax = min(y_), max(y_)

y_ = [(i-amin) / (amax-amin) for i in y_ ]
y_ = [ -45 + i * 90 for i in y_ ]

bmin, bmax = min(x_), max(x_)
x_ = [(i-bmin) / (bmax-bmin) for i in x_ ]
x_ = [ -90 + i * 180 for i in x_ ]

#plt.plot(x_, y_)
#plt.show()

#print(y_)
#print(x_)


# plot track
def plot_me(x,y):
    output_file = "_track.png"
    

    
    # get max min lat lon
    lat_max = max(y)
    lat_min = min(y)
    lon_max = max(x)
    lon_min = min(x)
    
    lat_1 = lat_min -15 - 2 * abs(lat_max - lat_min) 
    lat_2 = lat_max + 15 + 2 * abs(lat_max - lat_min) 
    lon_1 = lon_min - 20 - 2 * abs(lon_max - lon_min) 
    lon_2 = lon_max + 20 + 2 * abs(lon_max - lon_min) 
    
    print(lat_min, lat_max, lon_min, lon_max)
    print(lat_1, lat_2, lon_1, lon_2)
    
    ## compute new map bounding box
    if lat_1 < -90:
        #lat_1 = -90
        lat_1 = lat_min
    if lat_2 > 90:
        #lat_2 = 90
        lat_2 = lat_max
    if lon_1 < -180:
        #lon_1 = -180
        lon_1 = lon_min
    if lon_2 > 180:
        #lon_2 = 180
        lon_2 = lon_max
        
    print(lat_1, lat_2, lon_1, lon_2)
        
    #print('Min Max Lat Lon: ', str(lat_min), ' ', str(lat_max), ' ', str(lon_min), ' ', str(lon_max))
    #print('1 2 Lat Lon: ', str(lat_1), ' ', str(lat_2), ' ', str(lon_1), ' ', str(lon_2))

    # https://scitools.org.uk/cartopy/docs/v0.5/matplotlib/advanced_plotting.html
    fig = plt.figure(figsize=(10, 8))
    
    #ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    ax.set_extent([-90, 180, 40, 90], crs=ccrs.PlateCarree())
    ax.set_extent([lon_1, lon_2, lat_1, lat_2], crs=ccrs.PlateCarree())
    
    # ad coast country
    ax.coastlines(resolution='50m', color='grey', linewidth=1)
    ax.add_feature(cfeature.LAND, facecolor=("lightgray"), alpha=0.5 )
    ax.add_feature(cfeature.BORDERS, linestyle=':', alpha=0.2, linewidth=0.5)
    
    
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                  linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.xlabels_top = False
    gl.ylabels_left = False

    


    
    ax.plot(x, y, 'm+', ms = 1, label='Mastertrack ')
    #ax.plot(x2, y2, 'g|', ms = 3, label='TSI shots')
    legend = ax.legend(shadow=True)
   
    #plt.xlabel('Longitude', labelpad=40)
    
    plt.title('Track of ')


    plt.show()
    #fig.savefig(output_file, dpi = 200)
    
    
plot_me(y_,x_)
