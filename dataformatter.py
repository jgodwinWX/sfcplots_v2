#!/usr/bin/python3
''' Downloads the latest METAR data file from NOAA and outputs the data into a pandas readable CSV
    file for the creation of surface station plots in stationplots2.py.

    Packages used: metar (pip install metar), urllib, shutil, csv, datetime

    Version History:
    1.0 - Designed for use in Python 2.7.
    2.0 - Designed for use in Python 3. (release: 2019/12/23)
'''
import csv
import datetime
import urllib.request
import shutil

from metar import Metar

__author__ = 'Jason Godwin'
__license__ = 'GPL'
__version__ = '2.0'
__maintainer__ = 'Jason Godwin'
__email__ = 'jasonwgodwin@gmail.com'
__status__ = 'PRODUCTION'

def skyFraction(category):
    if category == 'SKC' or category == 'CLR' or category == 'NSC' or category == 'NCD' or category == 'VV' or category == '///':
        return 0.00
    elif category == 'FEW':
        return 0.25
    elif category == 'SCT':
        return 0.50
    elif category == 'BKN':
        return 0.75
    elif category == 'OVC':
        return 1.00
    else:
        raise Exception("Invalid cloud cover!")

def main():
    ### START OF USER SETTINGS BLOCK ###

    # working directory
    directory = '/home/jgodwin/python/sfc_observations'
    # path to station lat/lon information file
    stationfile = '/home/jgodwin/python/sfc_observations/station_locations.csv'

    ### END OF USER SETTINGS BLOCK ###

    print("Running dataformatter.py")

    # constants
    INHG_TO_HPA = 33.8639   # inches of mercury to hectopascal conversion factor

    # get current hour and most recent synoptic hour
    hour = datetime.datetime.now().hour

    # get data file from NOAA
    print('using time: %02d' % hour)
    url = 'http://tgftp.nws.noaa.gov/data/observations/metar/cycles/%02dZ.TXT' % hour
    with urllib.request.urlopen(url) as response, open("%s/metar_file.txt" % directory,"wb") as out_file:
        shutil.copyfileobj(response,out_file)

    # look up lat and lons for station sites
    with open(stationfile,mode="r") as infile:
        reader = csv.reader(infile)
        station_dict = dict((row[0],[row[1],row[2]]) for row in reader)

    # get individual fields from file
    f = open("%s/metar_file.txt" % directory,"r")
    validtimes = []
    stations = {}
    lats = {}
    lons = {}
    slp = {}
    temp = {}
    sky = {}
    dewpt = {}
    wx = {}
    vdir = {}
    vspd = {}

    for line in f:
        # separate out lines that are valid times, but save them because we will need them later
        if len(line) == 17:
            try:
                tau = datetime.datetime.strptime(line,"%Y/%m/%d %H:%M\n")
                validtimes.append(datetime.datetime.strftime(tau,"%Y-%m-%d %H:%M:00Z"))
            except ValueError:
                continue
        else:
            site = line[0:4]
            stations[site] = site                       # station IDs
            try:
                lats[site] = round(float(station_dict[site][0]),3) # station latitude (decimal degrees)
                lons[site] = round(float(station_dict[site][1]),3) # station longitude (decimal degrees)
                try:
                    obs = Metar.Metar(line)                 # decode the METAR
                except:
                    continue
                try:
                    slp[site] = round(float(obs.press_sea_level.value()),2) # sea-level pressure (mb)
                except AttributeError:
                    try:
                        if obs.press.value() < 100:
                            slp[site] = round(float(obs.press.value() * INHG_TO_HPA),2)
                        else:
                            slp[site] = round(float(obs.press.value()),2)
                    except AttributeError:
                        slp[site] = float('NaN')
                try:
                    temp[site] = float(obs.temp.value())           # temperature (deg C)
                except AttributeError:
                    temp[site] = float('NaN')
                try:
                    sky[site] = float(skyFraction(obs.sky[0][0]))  # sky condition
                except AttributeError:
                    sky[site] = float(0.0)
                except IndexError:
                    sky[site] = float(0.0)
                try:
                    dewpt[site] = float(obs.dewpt.value())         # dewpoint temperature (deg C)
                except AttributeError:
                    dewpt[site] = float('NaN')
                try:
                    # present weather
                    wx[site] = ''.join([x for x in obs.weather[0] if x is not None])
                except AttributeError:
                    wx[site] = ''
                except IndexError:
                    wx[site] = ''
                try:
                    vdir[site] = float(obs.wind_dir.value())       # wind direction (deg)
                except AttributeError:
                    vdir[site] = float('NaN')
                try:
                    vspd[site] = float(obs.wind_speed.value())     # wind speed (kt)
                except AttributeError:
                    vspd[site] = float('NaN')
            except KeyError:
                lats[site] = float('NaN')
                lons[site] = float('NaN')
                continue

    lasttime = validtimes[-1]

    # rearrange data into format to be used by MetPy
    metpy_file = open("%s/surface_observations.txt" % directory,"w")
    metpy_file.write('siteID,lat,lon,slp,temp,sky,dpt,wx,wdr,wsp\n')
    for key in slp:
        metpy_file.write("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9}\n".format(stations[key],lats[key],lons[key],\
            slp[key],temp[key],sky[key],dewpt[key],wx[key],vdir[key],vspd[key]))
    metpy_file.close()

    time_file = open('%s/validtime.txt' % directory,'w')
    time_file.write('%s' % lasttime)
    time_file.close()

if __name__ == '__main__':
    main()
