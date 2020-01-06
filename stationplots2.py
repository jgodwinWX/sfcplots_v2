#!/usr/bin/python3
''' This program takes in decoded METAR data created in dataformatter.py and creates surface
    station plot maps. The maps are configurable in the user settings block in main().

    Packages used: matplotlib, cartopy, numpy, pandas, metpy (pip install metpy).

    Version History:
    1.0 - Designed for use in Python 2.7.
    2.0 - Designed for use in Python 3. MetPy no longer supports Python 2.7! (released: 2019/12/23)
'''

import matplotlib
matplotlib.use('Agg')

import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from metpy.calc import reduce_point_density
from metpy.calc import wind_components
from metpy.plots import current_weather, sky_cover, StationPlot, wx_code_map
from metpy.units import units

__author__ = 'Jason Godwin'
__license__ = 'GPL'
__version__ = '2.0'
__maintainer__ = 'Jason Godwin'
__email__ = 'jasonwgodwin@gmail.com'
__status__ = 'PRODUCTION'

# funtion to convert Celsius to Fahrenheit
def cToF(x):
    return x * (9.0/5.0) + 32.0

def main():
    ### START OF USER SETTINGS BLOCK ###

    # FILE/DATA SETTINGS
    # file path to input file
    datafile = '/home/jgodwin/python/sfc_observations/surface_observations.txt'
    timefile = '/home/jgodwin/python/sfc_observations/validtime.txt'
    # file path to county shapefile
    ctyshppath = '/home/jgodwin/python/sfc_observations/shapefiles/counties/countyl010g.shp'

    # MAP SETTINGS
    # map names (doesn't go anywhere (yet), just for tracking purposes)
    maps = ['CONUS','Texas','Great Plains','Southern Rockies']
    # minimum radius allowed between points (in km)
    radius = [100.0,50.0,75.0,50.0]
    # map boundaries (longitude/latitude degrees)
    west = [-122,-108,-105,-112]
    east = [-73,-93,-90,-102]
    south = [23,25,30,34]
    north = [50,38,50,42]
    # use county map? (True/False): warning, counties load slow!
    usecounties = [False,False,False,False]

    # OUTPUT SETTINGS
    # save directory for output
    savedir = '/var/www/html/images/'
    # filenames for output
    savenames = ['conus.png','texas.png','plains.png','srockies.png']

    # TEST MODE SETTINGS
    test = False    # True/False
    testnum = 4     # which map are you testing? corresponds to index in "maps" above

    ### END OF USER SETTING SECTION ###

    # if there are any missing weather codes, add them here
    wx_code_map.update({'-RADZ':59,'-TS':17,'VCTSSH':80,'-SGSN':77,'SHUP':76,'FZBR':48,'FZUP':76})

    ### READ IN DATA / SETUP MAP ###
    # read in the valid time file
    vt = open(timefile).read()
    # read in the data
    for i in range(len(maps)):
        if test and i != testnum:
            continue
        with open(datafile) as f:
            data = pd.read_csv(f,header=0,names=['siteID','lat','lon','elev','slp','temp','sky','dpt','wx','wdr',\
                'wsp'],na_values=-99999)
            # drop rows with missing winds
            data = data.dropna(how='any',subset=['wdr','wsp'])

        # remove data not within our domain
        
        data = data[(data['lat'] >= south[i]-2.0) & (data['lat'] <= north[i]+2.0) \
            & (data['lon'] >= west[i]-2.0) & (data['lon'] <= east[i]+2.0)]

        # filter data (there seems to be one site always reporting a really anomalous temperature
        data = data[data['temp'] <= 50]

        print("Working on %s" % maps[i])
        # set up the map projection
        proj = ccrs.LambertConformal(central_longitude=-95,central_latitude=35,standard_parallels=[35])
        point_locs = proj.transform_points(ccrs.PlateCarree(),data['lon'].values,data['lat'].values)
        data = data[reduce_point_density(point_locs,radius[i]*1000)]
        # state borders
        state_boundaries = cfeature.NaturalEarthFeature(category='cultural',\
            name='admin_1_states_provinces_lines',scale='50m',facecolor='none')
        # county boundaries
        if usecounties[i]:
            county_reader = shpreader.Reader(ctyshppath)
            counties = list(county_reader.geometries())
            COUNTIES = cfeature.ShapelyFeature(counties,ccrs.PlateCarree())
        ### DO SOME CONVERSIONS ###
        # get the wind components
        u,v = wind_components(data['wsp'].values*units('knots'),data['wdr'].values*units.degree)
        # convert temperature from Celsius to Fahrenheit
        data['temp'] = cToF(data['temp'])
        data['dpt'] = cToF(data['dpt'])
        # convert the cloud fraction value into a code of 0-8 (oktas) and compenate for NaN values
        cloud_frac = (8 * data['sky'])
        cloud_frac[np.isnan(cloud_frac)] = 10
        cloud_frac = cloud_frac.astype(int)
        # map weather strings to WMO codes (only use first symbol if multiple are present
        data['wx'] = data.wx.str.split('/').str[0] + ''
        wx = [wx_code_map[s.split()[0] if ' ' in s else s] for s in data['wx'].fillna('')]

        # get the minimum and maximum temperatures in domain
        searchdata = data[(data['lat'] >= south[i]) & (data['lat'] <= north[i]) \
            & (data['lon'] >= west[i]) & (data['lon'] <= east[i])]
        min_temp = searchdata.loc[searchdata['temp'].idxmin()]
        max_temp = searchdata.loc[searchdata['temp'].idxmax()]
        max_dewp = searchdata.loc[searchdata['dpt'].idxmax()]
        text_str = "Max temp: %.0f F at %s\nMin temp: %.0f F at %s\nMax dewpoint: %.0f F at %s"\
             % (min_temp['temp'],min_temp['siteID'],max_temp['temp'],max_temp['siteID'],\
                max_dewp['dpt'],max_dewp['siteID'])

        ### PLOTTING SECTION ###
        # change the DPI to increase the resolution
        plt.rcParams['savefig.dpi'] = 255
        # create the figure and an axes set to the projection
        fig = plt.figure(figsize=(20,10))
        ax = fig.add_subplot(1,1,1,projection=proj)
        # add various map elements
        ax.add_feature(cfeature.LAND,zorder=-1)
        ax.add_feature(cfeature.OCEAN,zorder=-1)
        ax.add_feature(cfeature.LAKES,zorder=-1)
        ax.add_feature(cfeature.COASTLINE,zorder=2,edgecolor='black')
        ax.add_feature(state_boundaries,edgecolor='black')
        if usecounties[i]:
            ax.add_feature(COUNTIES,facecolor='none',edgecolor='gray',zorder=-1)
        ax.add_feature(cfeature.BORDERS,linewidth=2,edgecolor='black')
        # set plot bounds
        ax.set_extent((west[i],east[i],south[i],north[i]))

        ### CREATE STATION PLOTS ###
        # lat/lon of the station plots
        stationplot = StationPlot(ax,data['lon'].values,data['lat'].values,clip_on=True,\
            transform=ccrs.PlateCarree(),fontsize=6)
        # plot the temperature and dewpoint
        stationplot.plot_parameter('NW',data['temp'],color='red')
        stationplot.plot_parameter('SW',data['dpt'],color='darkgreen')
        # plot the SLP using the standard trailing three digits
        stationplot.plot_parameter('NE',data['slp'],formatter=lambda v: format(10*v,'.0f')[-3:])
        # plot the sky condition
        stationplot.plot_symbol('C',cloud_frac,sky_cover)
        # plot the present weather
        stationplot.plot_symbol('W',wx,current_weather)
        # plot the wind barbs
        stationplot.plot_barb(u,v)
        # plot the text of the station ID
        stationplot.plot_text((2,0),data['siteID'])
        # plot the valid time
        plt.title('Surface Observations valid %s' % vt)
        # plot the min/max temperature info and draw circle around warmest and coldest obs
        props = dict(boxstyle='round',facecolor='wheat',alpha=0.5)
        plt.text(west[i],south[i],text_str,fontsize=12,verticalalignment='top',bbox=props,transform=ccrs.Geodetic())
        projx1,projy1 = proj.transform_point(min_temp['lon'],min_temp['lat'],ccrs.Geodetic())
        ax.add_patch(matplotlib.patches.Circle(xy=[projx1,projy1],radius=50000,facecolor="None",edgecolor='blue',linewidth=3,transform=proj))
        projx2,projy2 = proj.transform_point(max_temp['lon'],max_temp['lat'],ccrs.Geodetic())
        ax.add_patch(matplotlib.patches.Circle(xy=[projx2,projy2],radius=50000,facecolor="None",edgecolor='red',linewidth=3,transform=proj))
        projx3,projy3 = proj.transform_point(max_dewp['lon'],max_dewp['lat'],ccrs.Geodetic())
        ax.add_patch(matplotlib.patches.Circle(xy=[projx3,projy3],radius=30000,facecolor="None",edgecolor='green',linewidth=3,transform=proj))
        # save the figure
        outfile_name = savedir + savenames[i]
        plt.savefig(outfile_name,bbox_inches='tight')

        # clear and close everything
        fig.clear()
        ax.clear()
        plt.close(fig)
        f.close()

    print("Script finished.")

if __name__ == '__main__':
    main()
