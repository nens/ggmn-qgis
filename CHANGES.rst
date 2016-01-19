GGMN Lizard qgis plugin changelog
=================================

0.8 (unreleased)
----------------

- Note: 0.5/0.6-0.7 were test releases for testing new release procedure.


0.4 (2016-01-18)
----------------

- Removed debug function that writes into ``/tmp/`` which doesn't exist on
  windows.


0.3 (2016-01-15)
----------------

- Placing the test shapefile in the user's home directory instead of in
  ``/tmp`` which doesn't exist on windows.


0.2 (2016-01-15)
----------------

- Removed dependency on requests library and replaced it by urllib2.

- Added hardcoded bounding box so that we get all the data.


0.1 (2016-01-13)
----------------

- Generated the plugin with qgis' plugin builder.

- Added lizard download module from the GGMN website.

- Integrated download code with qgis' plugin mechanism.
