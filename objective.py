#!/usr/bin/python3
''' This program creates objective analyses with a Cressman analysis using real-time
    observation data. Data is imported using the dataformatter.py program.

    Dependencies: Cartopy, matplotlib, numpy, pandas, metpy

    Version History: 1.0 - initial build (released 2019/12/23)
'''
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from matplotlib.colors import BoundaryNorm
from metpy.calc import wind_components
from metpy.cbook import get_test_data
from metpy.interpolate import interpolate_to_grid, remove_nan_observations
from metpy.plots import add_metpy_logo
from metpy.units import units

__author__ = 'Jason Godwin'
__license__ = 'GPL'
__version__ = '1.0'
__maintainer__ = 'Jason Godwin'
__email__ = 'jasonwgodwin@gmail.com'
__status__ = 'PRODUCTION'

def cToF(x):
    return x * (9.0/5.0) + 32.0

def main():
    ### START OF USER SETTINGS BLOCK ###
    # FILE/DATA SETTINGS
    # file path to input
    datafile = '/home/jgodwin/python/sfc_observations/surface_observations.txt'
    timefile = '/home/jgodwin/python/sfc_observations/validtime.txt'

    # MAP SETTINGS
    # map names (for tracking purposes)
    maps = ['CONUS','Texas']
    # map boundaries
    west = [-120,-108]
    east = [-70,-93]
    south = [20,25]
    north = [50,38]

    # OUTPUT SETTINGS
    # save directory for output
    savedir = '/var/www/html/images/'
    # filenames ("_[variable].png" will be appended, so only a descriptor like "conus" is needed)
    savenames = ['conus','texas']

    # TEST MODE SETTINGS
    test = False
    testnum = 1

    ### END OF USER SETTINGS BLOCK ###

    # create the map projection
    to_proj = ccrs.AlbersEqualArea(central_longitude=-97., central_latitude=38.)

    # open the data
    vt = open(timefile).read()
    with open(datafile) as f:
        data = pd.read_csv(f,header=0,names=['siteID','lat','lon','slp','temp','sky','dpt','wx','wdr',\
            'wsp'],na_values=-99999)

    # project lat/lon onto final projection
    print("Creating map projection.")
    lon = data['lon'].values
    lat = data['lat'].values
    xp, yp, _ = to_proj.transform_points(ccrs.Geodetic(), lon, lat).T

    # remove missing data from pressure and interpolate
    print("Performing Cressman interpolation.")
    x_masked, y_masked, pres = remove_nan_observations(xp, yp, data['slp'].values)
    slpgridx, slpgridy, slp = interpolate_to_grid(x_masked, y_masked, pres, interp_type='cressman',
                                                  minimum_neighbors=1, search_radius=400000,
                                                  hres=100000)

    # get wind information and remove missing data
    wind_speed = (data['wsp'].values * units('knots'))
    wind_dir = data['wdr'].values * units.degree
    good_indices = np.where((~np.isnan(wind_dir)) & (~np.isnan(wind_speed)))
    x_masked = xp[good_indices]
    y_masked = yp[good_indices]
    wind_speed = wind_speed[good_indices]
    wind_dir = wind_dir[good_indices]
    u, v = wind_components(wind_speed, wind_dir)
    windgridx, windgridy, uwind = interpolate_to_grid(x_masked, y_masked, np.array(u),
                                                      interp_type='cressman', search_radius=400000,
                                                      hres=100000)
    _, _, vwind = interpolate_to_grid(x_masked, y_masked, np.array(v), interp_type='cressman',
                                      search_radius=400000, hres=100000)

    # get temperature information
    data['temp'] = cToF(data['temp'])
    x_masked, y_masked, t = remove_nan_observations(xp, yp, data['temp'].values)
    tempx, tempy, temp = interpolate_to_grid(x_masked, y_masked, t, interp_type='cressman',
                                             minimum_neighbors=3, search_radius=400000, hres=35000)
    temp = np.ma.masked_where(np.isnan(temp), temp)

    # get dewpoint information
    data['dpt'] = cToF(data['dpt'])
    x_masked,y_masked,td = remove_nan_observations(xp,yp,data['dpt'].values)
    dptx,dpty,dewp = interpolate_to_grid(x_masked,y_masked,td,interp_type='cressman',\
        minimum_neighbors=3,search_radius=400000,hres=35000)
    dewp = np.ma.masked_where(np.isnan(dewp),dewp)

    # interpolate wind speed
    x_masked,y_masked,wspd = remove_nan_observations(xp,yp,data['wsp'].values)
    wspx,wspy,speed = interpolate_to_grid(x_masked,y_masked,wspd,interp_type='cressman',\
        minimum_neighbors=3,search_radius=400000,hres=35000)
    speed = np.ma.masked_where(np.isnan(speed),speed)

    # set up the state borders
    state_boundaries = cfeature.NaturalEarthFeature(category='cultural',\
        name='admin_1_states_provinces_lines',scale='50m',facecolor='none')

    # SCALAR VARIABLES TO PLOT
    # variable names (will appear in plot title)
    variables = ['Temperature','Dewpoint','Wind Speed']
    # units (for colorbar label)
    unitlabels = ['F','F','kt']
    # list of actual variables to plot
    vardata = [temp,dewp,speed]
    # tag in output filename
    varplots = ['temp','dewp','wspd']

    for i in range(len(maps)):
        print(maps[i])
        for j in range(len(variables)):
            print("\t%s" % variables[j])
            fig = plt.figure(figsize=(20, 10))
            view = fig.add_subplot(1, 1, 1, projection=to_proj)
            
            # set up the map and plot the interpolated grids
            levels = [list(range(-20,105,5)),list(range(30,85,5)),list(range(0,70,5))][j]
            cmap = [plt.get_cmap('hsv_r'),plt.get_cmap('Greens'),plt.get_cmap('plasma')][j]
            norm = BoundaryNorm(levels, ncolors=cmap.N, clip=True)
            labels = variables[j] + " (" + unitlabels[j] + ")"

            # add map features
            view.set_extent([west[i],east[i],south[i],north[i]])
            view.add_feature(state_boundaries,edgecolor='black')
            view.add_feature(cfeature.OCEAN,zorder=-1)
            view.add_feature(cfeature.COASTLINE,zorder=2)
            view.add_feature(cfeature.BORDERS, linewidth=2,edgecolor='black')

            # plot the sea-level pressure
            cs = view.contour(slpgridx, slpgridy, slp, colors='k', levels=list(range(990, 1034, 4)))
            view.clabel(cs, inline=1, fontsize=12, fmt='%i')

            # plot the scalar background
            mmb = view.pcolormesh(tempx, tempy, vardata[j], cmap=cmap, norm=norm)
            fig.colorbar(mmb, shrink=.4, orientation='horizontal', pad=0.02, boundaries=levels, \
                extend='both',label=labels)

            # plot the wind barbs
            view.barbs(windgridx, windgridy, uwind, vwind, alpha=.4, length=5)

            # plot title and save
            view.set_title('%s (shaded), SLP, and Wind (valid %s)' % (variables[j],vt))
            plt.savefig('/var/www/html/images/%s_%s.png' % (savenames[i],varplots[j]),bbox_inches='tight')

            # close everything
            fig.clear()
            view.clear()
            plt.close(fig)
            f.close()

    print("Script finished.")

if __name__ == '__main__':
    main()
