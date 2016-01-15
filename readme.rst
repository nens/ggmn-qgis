GGMN qgis plugin
================

Goal: integrate the GGMN data from Lizard so that you can do additional
analysis in qgis: mainly interpolation. The interpolation results (rasters)
can be uploaded to Lizard. Also you should be able to add local data points
and upload them back to Lizard.

The plugin will *not* provide a complete setup and walk-through. You should
set up a base map and the interpolation plugin yourself, for instance.


Prerequisites
-------------

Currently you must install the python ``requests`` library inside the python
used by qgis. Calling ``easy_install requests`` is often enough, but it
depends on your OS.


Installation
------------

Intention is to upload the plugin to the qgis plugin repo so that you have a
standard installation method. The plugin is called "GGMN Lizard integration".

Recommended extra plugins:

- Interpolation plugin (for doing interpolation analysis).

- QuickMapServices (for adding a base layer like openstreetmap).


Usage
-----

Zoom to the area you want to see. Currently the coordinate system needs to be
set to ``EPSG:4326``, this will be fixed later on.

Via the menu bar, open "Plugins > GGMN Lizard integration > Download from
Lizard" and fill in your username/password. (TODO: select period).

This adds a vector layer, saved as a shapefile, with the available groundwater
data. (TODO: choose filename).

For interpolation, open the plugin "Raster > interpolation >
Interpolation". Choose the ``ggmn_groundwater`` layer and one of the
min/mean/max items as source and select an output file.
