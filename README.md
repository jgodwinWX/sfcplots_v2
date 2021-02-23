# sfcplots_v2

Description: This program creates some basic surface station plots using MetPy. This is largely
based on the example at https://unidata.github.io/MetPy/latest/examples/plots/Station_Plot.html.

Live Examples: http://www.jasonsweathercenter.com/brief.html

Packages required:
-MetPy (pip install metpy)
-metar (pip install metar)
-numpy
-matplotlib
-urllib
-shutil
-Possibly some other (see docstrings)

Files included:
-dataformatter.py: downloads the METAR data from NOAA and puts it into a pandas readable CSV
    file for use in stationplots2.py.
-stationplot2.py: creates the station plot maps.
-examples/: contains some example images (old and needs updating, live examples at link above)

Information on the archive plotter:

I didn't know where else to put this code, so I figured since this repo is already surface 
observation stuff, this was a good spot. This code will plot temperature traces (or any other
user-specified scalar quantity), wind barbs (on top of the temperature trace), and present
weather. Right now, present weather codes are only snow, rain, freezing rain, freezing fog,
and sleet, since this was for a project following a winter storm. The block in the section
commented "find the intervals for each weather type" could be easily expanded to add more
present weather codes (or change the ones currently there).

IMPORTANT NOTE: This is designed to use a single-site METAR CSV from the Iowa State
website (here: https://mesonet.agron.iastate.edu/request/download.phtml). Most critically,
make sure to download as a CSV and make sure "How to representing missing data?" is set to
"Use blank/empty string".
