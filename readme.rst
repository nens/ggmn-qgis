GGMN qgis plugin
================

Goal: integrate the GGMN data from Lizard so that you can do additional
analysis in qgis: mainly interpolation. The interpolation results (rasters)
can be uploaded to Lizard. Also you should be able to add local data points
and upload them back to Lizard.

The plugin will *not* provide a complete setup and walk-through. You should
set up a base map and the interpolation plugin yourself, for instance.


Installation
------------

Intention is to upload the plugin to a custom plugin repository so that you
have a standard installation method. The plugin is called "GGMN Lizard
integration".

Recommended extra plugins:

- Interpolation plugin (for doing interpolation analysis).

- QuickMapServices (for adding a base layer like openstreetmap).


Usage
-----

Via the menu bar, open "Plugins > GGMN Lizard integration > Download from
Lizard" and fill in your username/password. (TODO: select period).

This adds a vector layer, saved as a shapefile, with the available groundwater
data. Currently the shapefile is called ``ggmn_test.shp`` and it is placed in
your home directory. (TODO: choose filename and location).

For interpolation, open the plugin "Raster > interpolation >
Interpolation". Choose the ``ggmn_groundwater`` layer and one of the
min/mean/max items as source and select an output file.


TODO: better messages, better error handling, data upload, documentation.


Internal note: releasing the plugin
-----------------------------------

Use zest.releaser with the qgispluginreleaser extension installed. You'll have
to install it either globally or in a virtualenv.

This copies a zipfile with the right version number to the current directory.
