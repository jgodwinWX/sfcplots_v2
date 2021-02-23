import datetime
import pandas as pd
import math
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

from metpy.calc import wind_components
from metpy.units import units
from matplotlib.ticker import MultipleLocator

def roundup(x):
    return math.ceil(x / 10.0) * 10
def rounddown(x):
    return math.floor(x / 10.0) * 10
def colorpicker(x):
    if x == 'tmpf':
        return 'red'

# user settings
datafile = 'dfw.csv'                        # CSV from IEM METAR archive
outfile = 'dfw.png'                         # outfile path
primary_field = 'tmpf'                      # main field to plot on y-axis of final plot
primary_label = 'Temperature'               # label for primary field
wind_on = True                              # plot wind barbs?
mintemp = True                              # plot minimum temperature?
barb_spacing = 1                            # spacing between wind barbs

titlestr = 'Temperature at Dallas/Fort Worth International Airport (KDFW)'

# import the surface observation file
df = pd.read_csv(datafile)

# convert stuff to floats
df[primary_field] = df[primary_field].astype(float)
primary_mask = np.isfinite(df[primary_field])
if wind_on:
    df['sknt'] = df['sknt'].astype(float)
    df['drct'] = df['drct'].astype(float)

# do some conversions
df['valid'] = pd.to_datetime(df['valid'])   # convert valid times to datetimes
if wind_on:
    u,v = wind_components(df['sknt'].values * units.knots,df['drct'].values * units.degree)
y_lower = rounddown(df[primary_field].min()) - 5.0
y_upper = roundup(df[primary_field].max()) + 5.0

# plot the stuff
plt.clf()
fig = plt.figure(figsize=(24,16))
ax = fig.add_subplot(1,1,1)

plt.plot(df['valid'][primary_mask],df[primary_field][primary_mask],color=colorpicker(primary_field)\
    ,label=primary_label,marker='o')
if wind_on:
    '''
    plt.barbs(df['valid'][::barb_spacing],\
        (np.ones(df[primary_field].shape)*(y_lower + y_upper)/2)[::barb_spacing],u[::barb_spacing],\
        v[::barb_spacing])
    '''
    plt.barbs(df['valid'][::barb_spacing],df[primary_field][::barb_spacing],u[::barb_spacing],\
        v[::barb_spacing])

# plot aesthetics
plt.grid()

# x-axis
plt.xticks(rotation=90)
plt.xlabel('Date/Time (UTC)')
ax.xaxis.set_major_locator(mdates.HourLocator((0,6,12,18)))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%a %d/%H'))
plt.xlim([df['valid'].min(),df['valid'].max()])
ax.hlines(y=32,xmin=df['valid'].min(),xmax=df['valid'].max(),linewidth=2,color='blue')
ax.hlines(y=0,xmin=df['valid'].min(),xmax=df['valid'].max(),linewidth=2,color='purple')
plt.xlabel('Date/Time (UTC)',fontsize=18)

# y-axis
plt.ylim([y_lower,y_upper])
ax.yaxis.set_major_locator(MultipleLocator(10))
ax.yaxis.set_minor_locator(MultipleLocator(2))
ax.yaxis.grid(True,which='minor',linestyle='--')
plt.ylabel('Temperature ($^\circ$F)',fontsize=18)
ax.tick_params(axis='both',which='major',labelsize=14)

# shade areas based on present weather
fzra = []
ra = []
sn = []
fzfg = []
up = []

# find the intervals for each weather type
for i in range(len(df['wxcodes'])):
    try:
        # snow
        if 'SN' in df['wxcodes'][i]:
            sn.append([df['valid'][i],df['valid'][i+1]])
        # freezing rain
        elif 'FZRA' in df['wxcodes'][i]:
            fzra.append([df['valid'][i],df['valid'][i+1]])
        # rain
        elif 'ra' in df['wxcodes'][i] and 'FZ' not in df['wxcodes'][i]:
            ra.append([df['valid'][i],df['valid'][i+1]])
        # freezing fog or freezing drizzle
        elif 'FZFG' in df['wxcodes'][i] or 'FZDZ' in df['wxcodes'][i]:
            fzfg.append([df['valid'][i],df['valid'][i+1]])
        # unknown precipitation or sleet
        elif 'UP' in df['wxcodes'][i] or 'PL' in df['wxcodes'][i]:
            up.append([df['valid'][i],df['valid'][i+1]])
    except TypeError:
        continue

# color in the areas
for ix,j in enumerate(fzra):
    plt.axvspan(j[0],j[1],facecolor='magenta',alpha=0.5,label='Frezing Rain' if ix == 0 else '')
for ix,j in enumerate(ra):
    plt.axvspan(j[0],j[1],facecolor='green',alpha=0.5,label='Rain' if ix == 0 else '')
for ix,j in enumerate(sn):
    plt.axvspan(j[0],j[1],facecolor='cyan',alpha=0.5,label='Snow' if ix == 0 else '')
for ix,j in enumerate(fzfg):
    plt.axvspan(j[0],j[1],facecolor='yellow',alpha=0.5,\
        label='Freezing Fog/Freezing Drizzle' if ix == 0 else '')
for ix,j in enumerate(up):
    plt.axvspan(j[0],j[1],facecolor='purple',alpha=0.5,\
        label='Sleet/Unknown Ptype' if ix == 0 else '')

# annotate coldest temperature
if mintemp:
    ymin = df[primary_field].min()
    xpos = df[primary_field].idxmin()
    xmin = df['valid'][xpos]
    minstr = datetime.datetime.strftime(xmin,'%a %b %d %H:%M')
    ax.annotate('%.0f$^\circ$F (%s)' % (ymin,minstr),xy=(xmin,ymin),xytext=(xmin,ymin-5),\
        color='blue',arrowprops=dict(width=2,facecolor='blue',shrink=0.05),fontsize=14)

# legend and title
plt.legend(loc='lower left',fontsize=18)
plt.title(titlestr,fontsize=24)

# save figure to output file
plt.savefig(outfile,bbox_inches='tight')
