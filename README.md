# sfcplots_v2

Description: This program creates some basic surface station plots using MetPy.

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
-examples/: contains some example images
