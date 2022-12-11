To use:

  Setup your Scenario class and supporting code/files into a directory (as described in the detailed documentation).

  Set environment variable SCENARIO_PY to the python file containing your model's Scenario class.

  Run the flask server on scenario_webapi.py

The server should find and load your Scenario class and create new instances of it for each server connection.


Core Python dependencies:

  flask
  flask-headers
  numpy

For GeoTIFF support requires:

  gdal [wheel download at: https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal]

For Shapefile support requires:

  geopandas
  osgeo