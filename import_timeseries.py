__author__ = 'roel.vandenberg@nelen-schuurmans.nl'

from lizard_api import GroundwaterTimeSeriesAndLocations
from pprint import pprint
from qgis.core import QgsVectorLayer
from qgis.core import QgsMapLayerRegistry

import os
import osgeo.ogr as ogr
import osgeo.osr as osr


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

    def download(self, south_west, north_east, start, end, groundwater_type):
        self.groundwater.bbox(south_west, north_east, start, end,
                              groundwater_type)
        self.data = self.groundwater.results_to_dict()
        # pprint(self.data)

    def data_to_shape(self, filename="ggmn_groundwater.shp",
                      overwrite=False):
        # set up the shapefile driver
        driver = ogr.GetDriverByName("ESRI Shapefile")
        print("Driver: %s" % driver)

        # create the data source
        print("File location: %r" % filename)

        if os.path.exists(filename):
            if overwrite:
                os.remove(filename)
            else:
                raise WriteShapefileError(
                    "File %s already exists, remove/rename it first" % filename)

        data_source = driver.CreateDataSource(filename)
        print("data_source: %r" % data_source)
        if data_source is None:
            raise WriteShapefileError(
                "Could not create shapefile %s" % filename)

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

        # Process the text file and add the attributes and features to the
        # shapefile
        for uuid, row in self.data['values'].items():
            # create the feature
            feature = ogr.Feature(layer.GetLayerDefn())
            # Set the attributes using the values from the delimited text file
            feature.SetField("name", row['name'].encode('ascii', 'ignore'))
            feature.SetField("loc_UUID", str(row['timeseries uuid']))
            feature.SetField("ts_UUID", str(uuid))
            feature.SetField("longitude", row['coordinates'][0])
            feature.SetField("latitude", row['coordinates'][1])
            feature.SetField("min", row['min'])
            feature.SetField("mean", row['mean'])
            feature.SetField("max", row['max'])
            feature.SetField("range", row['range'])

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
        layer = QgsVectorLayer(filename, "ggmn_groundwater", "ogr")
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
    filename='/vagrant/TeSt/test2.shp'
    GWinfo.data_to_shape(filename,
                         overwrite=True)
    GWinfo.load_shape(filename)
