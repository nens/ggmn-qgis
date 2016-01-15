__author__ = 'roel.vandenberg@nelen-schuurmans.nl'

import os
from pprint import pprint

import osgeo.ogr as ogr
import osgeo.osr as osr

from qgis.core import *

from lizard_api import GroundwaterTimeSeriesAndLocations


class WriteShapefileError(Exception):
    pass


class QGisLizardImporter(object):

    def __init__(self, username, password):
        self.groundwater = GroundwaterTimeSeriesAndLocations()
        self.groundwater.locs.username = username
        self.groundwater.locs.password = password
        self.groundwater.ts.username = username
        self.groundwater.ts.password = password

    def download(self, south_west, north_east, start, end, groundwater_type):
        self.groundwater.bbox(south_west, north_east, start, end,
                                groundwater_type)
        self.data = self.groundwater.results_to_dict()
        # pprint(self.data)

    def data_to_shape(self, directory="", filename="ggmn_groundwater.shp",
                      overwrite=False):
        # set up the shapefile driver
        driver = ogr.GetDriverByName("ESRI Shapefile")
        print("Driver: %s" % driver)

        # create the data source
        self.file_location = os.path.join(directory, filename)
        print("File location: %r" % self.file_location)

        if os.path.exists(self.file_location):
            if overwrite:
                os.remove(self.file_location)
            else:
                raise WriteShapefileError(
                    "File %s already exists, remove/rename it first" % self.file_location)

        if not os.path.exists(directory):
            os.makedirs(directory)
        data_source = driver.CreateDataSource(self.file_location)
        print("data_source: %r" % data_source)
        if data_source is None:
            raise WriteShapefileError(
                "Could not create shapefile %s" % self.file_location)

        # create the spatial reference, WGS84
        spatial_reference = osr.SpatialReference()
        spatial_reference.ImportFromEPSG(4326)

        # create the layer
        layer = data_source.CreateLayer("ggmn_groundwater",
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
        layer.CreateField(ogr.FieldDefn("range", ogr.OFTReal))

        # Process the text file and add the attributes and features to the shapefile
        for uuid, row in self.data['values'].items():
            # create the feature
            feature = ogr.Feature(layer.GetLayerDefn())
            # Set the attributes using the values from the delimited text file
            feature.SetField("name", str(row['name']))
            feature.SetField("loc_UUID", str(row['timeseries uuid']))
            feature.SetField("ts_UUID", str(uuid))
            feature.SetField("longitude", str(row['coordinates'][0]))
            feature.SetField("latitude", str(row['coordinates'][1]))
            feature.SetField("min", str(row['min']))
            feature.SetField("mean", str(row['mean']))
            feature.SetField("max", str(row['max']))
            feature.SetField("range", str(row['range']))


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

    def load_shape(self):
        # load the shapefile
        layer = QgsVectorLayer(self.file_location, "ggmn_groundwater", "ogr")
        QgsMapLayerRegistry.instance().addMapLayer(layer)


if __name__ == '__main__':
    'Example how to use: '

    from freq.secretsettings import USR, PWD
    end = "1452470400000"
    start = "-2208988800000"
    GWinfo = QGisLizardImporter(username=USR, password=PWD)
    GWinfo.download(
        south_west=[-65.80277639340238, -223.9453125],
        north_east=[81.46626086056541, 187.3828125],
        start=start,
        end=end,
        groundwater_type='GWmMSL'
    )
    GWinfo.data_to_shape(directory='/vagrant/TeSt',
                         filename='test2.shp',
                         overwrite=True)
    GWinfo.load_shape()
