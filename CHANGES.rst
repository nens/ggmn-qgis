GGMN Lizard qgis plugin changelog
=================================

1.4 (unreleased)
----------------

- Fixed layer names: include 'msl' in the name.

- Using 'mean sea level' instead of 'below ground surface'.

- Fixed numpy errors.


1.3 (2016-02-01)
----------------

- Opening tiff in binary mode: fixes windows problem.


1.2 (2016-02-01)
----------------

- Trying to get uploads from windows right.


1.1 (2016-02-01)
----------------

- Fixed code for uploading the raster. (A temporary file wasn't properly
  closed).


1.0 (2016-01-29)
----------------

- Uploading raster to the server works.


0.11 (2016-01-27)
-----------------

- Uploading new custom points works!


0.10 (2016-01-25)
-----------------

- Added dummy 'upload raster' action.

- Improved the download of organisations for the selection box.


0.9 (2016-01-25)
----------------

- Added download for virtual point layer.


0.8 (2016-01-22)
----------------

- Added separate login dialog. You first have to log in before the list of
  organisations can be downloaded. And the organisation list is needed for the
  actual download selection dialog.

- Added start/end date and organisation selection to Lizard import.

- Added file save-as dialog.

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
