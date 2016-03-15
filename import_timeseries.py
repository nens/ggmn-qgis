__author__ = 'roel.vandenberg@nelen-schuurmans.nl'

from lizard_api import GroundwaterTimeSeriesAndLocations
from lizard_api import CustomGroundwaterTimeSeriesAndLocations
from lizard_api import DOWNLOADED_MARKER
# from pprint import pprint
from qgis.core import QgsVectorLayer
from qgis.core import QgsMapLayerRegistry

import os
import osgeo.ogr as ogr
import osgeo.osr as osr


LAYER_NAME = "ggmn_groundwater_msl"
CUSTOM_LAYER_NAME = "ggmn_groundwater_msl_virtual"


class WriteShapefileError(Exception):
    pass


class QGisLizardImporter(object):

    def __init__(self, username, password, organisation_id):
        self.groundwater = GroundwaterTimeSeriesAndLocations()
        self.groundwater.locs.username = username
        self.groundwater.locs.password = password
        self.groundwater.locs.organisation_id = organisation_id
        self.groundwater.ts.username = username
        self.groundwater.ts.password = password
        self.groundwater.ts.organisation_id = organisation_id

    def download(self, start, end, groundwater_type):
        self.groundwater.bbox(start=start,
                              end=end,
                              groundwater_type=groundwater_type)
        self.data = self.groundwater.results_to_dict()
        # pprint(self.data)

    def data_to_shape(self, filename="ggmn_groundwater.shp",
                      overwrite=False):
        # set up the shapefile driver
        driver = ogr.GetDriverByName("ESRI Shapefile")
        # print("Driver: %s" % driver)

        # create the data source
        # print("File location: %r" % filename)

        if os.path.exists(filename):
            if overwrite:
                os.remove(filename)
            else:
                raise WriteShapefileError(
                    "File %s already exists, remove/rename it first" % filename)

        data_source = driver.CreateDataSource(filename)
        # print("data_source: %r" % data_source)
        if data_source is None:
            raise WriteShapefileError(
                "Could not create shapefile %s" % filename)

        # create the spatial reference, WGS84
        spatial_reference = osr.SpatialReference()
        spatial_reference.ImportFromEPSG(4326)

        # create the layer
        layer = data_source.CreateLayer(LAYER_NAME,
                                        spatial_reference, ogr.wkbPoint)

        # Add the fields
        field_name = ogr.FieldDefn("name", ogr.OFTString)
        field_name.SetWidth(24)
        layer.CreateField(field_name)
        field_loc_UUID = ogr.FieldDefn("loc_UUID", ogr.OFTString)
        field_loc_UUID.SetWidth(36)
        layer.CreateField(field_loc_UUID)
        field_ts_UUID = ogr.FieldDefn("ts_UUID", ogr.OFTString)
        field_ts_UUID.SetWidth(36)
        layer.CreateField(field_ts_UUID)
        layer.CreateField(ogr.FieldDefn("latitude", ogr.OFTReal))
        layer.CreateField(ogr.FieldDefn("longitude", ogr.OFTReal))
        layer.CreateField(ogr.FieldDefn("min", ogr.OFTReal))
        layer.CreateField(ogr.FieldDefn("mean", ogr.OFTReal))
        layer.CreateField(ogr.FieldDefn("max", ogr.OFTReal))
        # layer.CreateField(ogr.FieldDefn("range", ogr.OFTReal))

        # Process the text file and add the attributes and features to the
        # shapefile
        for uuid, row in self.data['values'].items():

            if not 'timeseries_uuid' in row:
                # print("Just a location, no timeseries. "
                #       "Probably custom locations: %r" % row)
                continue
            if not 'name' in row:
                # print("Just a timeseries, no location. Probably location "
                #       "without geometry: %r" % row)
                continue
            # create the feature
            feature = ogr.Feature(layer.GetLayerDefn())
            # Set the attributes using the values from the delimited text file
            feature.SetField("name", row['name'].encode('ascii', 'ignore'))
            feature.SetField("loc_UUID", str(row['timeseries_uuid']))
            feature.SetField("ts_UUID", str(uuid))
            feature.SetField("longitude", row['coordinates'][0])
            feature.SetField("latitude", row['coordinates'][1])
            feature.SetField("min", row['min'])
            feature.SetField("mean", row['mean'])
            feature.SetField("max", row['max'])
            # feature.SetField("range", row['range'])

            # create the WKT for the feature using Python string formatting
            wkt = "POINT({lon} {lat})".format(lon=row['coordinates'][0],
                                              lat=row['coordinates'][1])

            # Create the point from the Well Known Txt
            point = ogr.CreateGeometryFromWkt(wkt)

            # Set the feature geometry using the point
            feature.SetGeometry(point)
            # Create the feature in the layer (shapefile)
            layer.CreateFeature(feature)
            # Destroy the feature to free resources
            feature.Destroy()

        # Destroy the data source to free resources
        data_source.Destroy()

    def load_shape(self, filename):
        # load the shapefile
        layer = QgsVectorLayer(filename, LAYER_NAME, "ogr")
        QgsMapLayerRegistry.instance().addMapLayer(layer)


class QGisLizardCustomImporter(object):

    def __init__(self, username, password, organisation_id):
        self.groundwater = CustomGroundwaterTimeSeriesAndLocations()
        self.groundwater.locs.username = username
        self.groundwater.locs.password = password
        self.groundwater.locs.organisation_id = organisation_id
        self.groundwater.ts.username = username
        self.groundwater.ts.password = password
        self.groundwater.ts.organisation_id = organisation_id

    def download(self, start, end, groundwater_type):
        self.groundwater.bbox(start=start,
                              end=end)
        self.data = self.groundwater.results()
        # pprint(self.data)

    def data_to_custom_shape(self, filename="ggmn_groundwater_custom.shp",
                      overwrite=False):
        # set up the shapefile driver
        driver = ogr.GetDriverByName("ESRI Shapefile")
        # print("Driver: %s" % driver)

        # create the data source
        # print("File location: %r" % filename)

        if os.path.exists(filename):
            if overwrite:
                os.remove(filename)
            else:
                raise WriteShapefileError(
                    "File %s already exists, remove/rename it first" % filename)

        data_source = driver.CreateDataSource(filename)
        # print("data_source: %r" % data_source)
        if data_source is None:
            raise WriteShapefileError(
                "Could not create shapefile %s" % filename)

        # create the spatial reference, WGS84
        spatial_reference = osr.SpatialReference()
        spatial_reference.ImportFromEPSG(4326)

        # create the layer
        layer = data_source.CreateLayer(CUSTOM_LAYER_NAME,
                                        spatial_reference, ogr.wkbPoint)

        # Add the fields
        layer.CreateField(ogr.FieldDefn("value", ogr.OFTReal))
        internal_use_field = ogr.FieldDefn("internal", ogr.OFTString)
        internal_use_field.SetWidth(10)
        layer.CreateField(internal_use_field)
        # Process the text file and add the attributes and features to the
        # shapefile
        for uuid, row in self.data.items():
            # create the feature
            feature = ogr.Feature(layer.GetLayerDefn())
            # Set the attributes using the values from the delimited text file
            feature.SetField("value", row['value'])
            # ^^^ Note: there should be only one value, ideally. I'm taking
            # the mean, at least we'll have one value then, guaranteed. And
            # the rest of the code can remain the same.
            feature.SetField('internal', DOWNLOADED_MARKER)

            # create the WKT for the feature using Python string formatting
            wkt = "POINT({lon} {lat})".format(lon=row['coordinates'][0],
                                              lat=row['coordinates'][1])

            # Create the point from the Well Known Txt
            point = ogr.CreateGeometryFromWkt(wkt)

            # Set the feature geometry using the point
            feature.SetGeometry(point)
            # Create the feature in the layer (shapefile)
            layer.CreateFeature(feature)
            # Destroy the feature to free resources
            feature.Destroy()

        # Destroy the data source to free resources
        data_source.Destroy()

    def load_custom_shape(self, filename):
        """Load the shapefile created above and return the layer"""
        # load the shapefile
        layer = QgsVectorLayer(filename, CUSTOM_LAYER_NAME, "ogr")
        QgsMapLayerRegistry.instance().addMapLayer(layer)
        layer.startEditing()
        return layer
