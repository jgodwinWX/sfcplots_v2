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
