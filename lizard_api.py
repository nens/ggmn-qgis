__author__ = 'roel.vandenberg@nelen-schuurmans.nl'

import json
from pprint import pprint  # left here for debugging purposes
from time import time

import requests
import numpy as np

import jsdatetime as jsdt

## When you use this script stand alone, please set your login information here:
USR = None  # Replace the with your user name.
PWD = None  # Replace the with your password.


def join_urls(*args):
    return '/'.join(args)


class ApiError(Exception):
    pass


class Base(object):
    """
    Base class to connect to the different endpoints of the lizard-api.
    :param data_type: endpoint of the lizard-api one wishes to connect to.
    :param username: login username
    :param password: login password
    :param use_header: no login and password is send with the query when set
                       to False
    :param extra_queries: In case one wishes to set default queries for a
                          certain data type this is the plase.
    :param max_results:
    """
    data_type = None
    username = USR
    password = PWD
    use_header = True
    max_results = 1000

    @property
    def extra_queries(self):
        """
        Overwrite class to add queries
        :return: dictionary with extra queries
        """
        return {}

    def __init__(self, base="http://ggmn.un-igrac.org"):
        """
        :param base: the site one wishes to connect to. Defaults to the
                     Lizard staging site.
        """
        self.queries = {}
        self.results = []
        if base.startswith('http'):
            self.base = base
        else:
            self.base = join_urls('https:/', base) # without extra '/', this is
                                                   # added in join_urls
        self.base_url = join_urls(self.base, 'api/v2', self.data_type)

    def get(self, **queries):
        """
        Query the api.
        For possible queries see: https://nxt.staging.lizard.net/doc/api.html
        Stores the api-response as a dict in the results attribute.
        :param queries: all keyword arguments are used as queries.
        :return: a dictionary of the api-response.
        """
        queries.update({'page_size': self.max_results})
        queries.update(self.extra_queries)
        queries.update(getattr(self, "queries", {}))
        query = '?' + '&'.join(str(key) + '=' +
                               (('&' + str(key) + '=').join(value)
                               if isinstance(value, list) else str(value))
                               for key, value in queries.items())
        url = join_urls(self.base_url, query)

        # A bit dirty, but store the url for later debugging.
        self.url = url

        open('/tmp/url.txt', 'a').write(url + '\n')
        self.fetch(url)
        print('Number found {} : {} with URL: {}'.format(
            self.data_type, self.json.get('count', 0), url))
        # open('/tmp/contents.txt', 'w').write(json.dumps(self.json))
        self.parse()
        return self.results

    def fetch(self, url):
        """
        GETs parameters from the api based on an url in a JSON format.
        Stores the JSON response in the json attribute.
        :param url: full query url: should be of the form:
                    [base_url]/api/v2/[endpoint]/?[query_key]=[query_value]&...
        :return: the JSON from the response
        """
        if self.use_header:
            response = requests.get(url, headers=self.header)
        else:
            response = requests.get(url)
        self.json = response.json()
        return self.json

    def post(self, UUID, data):
        """
        POST data to the api.
        :param UUID: UUID of the object in the database you wish to store
                     data to.
        :param data: Dictionary with the data to post to the api
        """
        post_url = join_urls(self.base_url, UUID, 'data')
        if self.use_header:
            requests.post(post_url, data=json.dumps(data), headers=self.header)
        else:
            requests.post(post_url, data=json.dumps(data))

    def parse(self):
        """
        Parse the json attribute and store it to the results attribute.
        All pages of a query are parsed. If the max_results attribute is
        exceeded an ApiError is raised.
        """
        while True:
            try:
                if self.json['count'] > self.max_results:
                    raise ApiError('Too many results: {} found, while max {} '
                                   'are accepted'.format(
                        self.json['count'], self.max_results))
                self.results += self.json['results']
                next_url = self.json.get('next')
                if next_url:
                    self.fetch(next_url)
                else:
                    break
            except IndexError:
                break

    def parse_elements(self, element):
        """
        Get a list of a certain element from the root of the results attribute.
        :param element: the element you wish to get.
        :return: A list of all elements in the root of the results attribute.
        """
        self.parse()
        return [x[element] for x in self.results]

    @property
    def header(self):
        """
        The header with credentials for the api.
        """
        return {
            "username": self.username,
            "password": self.password
        }


class Organisations(Base):
    """
    Makes a connection to the organisations endpoint of the lizard api.
    """
    data_type = 'organisations'

    def all(self):
        """
        :return: a list of organisations belonging one has access to
                (with the credentials from the header attribute)
        """
        self.get()
        self.parse()
        return self.parse_elements('unique_id')


class Locations(Base):
    """
    Makes a connection to the locations endpoint of the lizard api.
    """
    data_type = 'locations'

    def __init__(self):
        self.uuids = []
        super(Locations, self).__init__()

    def bbox(self, south_west, north_east):
        """
        Find all locations within a certain bounding box.
        returns records within bounding box using Bounding Box format (min Lon,
        min Lat, max Lon, max Lat). Also returns features with overlapping
        geometry.
        :param south_west: lattitude and longtitude of the south-western point
        :param north_east: lattitude and longtitude of the north-eastern point
        :return: a dictionary of the api-response.
        """
        min_lat, min_lon = south_west
        max_lat, max_lon = north_east
        coords = self.commaify(min_lon, min_lat, max_lon, max_lat)
        self.get(in_bbox=coords)

    def distance_to_point(self, distance, lat, lon):
        """
        Returns records with distance meters from point. Distance in meters
        is converted to WGS84 degrees and thus an approximation.
        :param distance: meters from point
        :param lon: longtitude of point
        :param lat: latitude of point
        :return: a dictionary of the api-response.
        """
        coords = self.commaify(lon, lat)
        self.get(distance=distance, point=coords)

    def commaify(self, *args):
        """
        :return: a comma-seperated string of the given arguments
        """
        return ','.join(str(x) for x in args)

    def coord_uuid_name(self):
        """
        Filters out the coordinates UUIDs and names of the locations in results.
        Use after a query is made.
        :return: a dictionary with coordinates, UUIDs and names
        """
        result = {}
        for x in self.results:
            if x['uuid'] not in self.uuids:
                result[x['uuid']] = {
                        'coordinates': x['geometry']['coordinates'],
                        'name': x['name']
                }
                self.uuids.append(x['uuid'])
        return result


class TimeSeries(Base):
    """
    Makes a connection to the timeseries endpoint of the lizard api.
    """
    data_type = 'timeseries'

    def __init__(self, base="http://ggmn.un-igrac.org"):
        self.uuids = []
        super(TimeSeries, self).__init__()

    def location_name(self, name):
        """
        Returns time series metadata for a location by name.
        :param name: name of a location
        :return: a dictionary of with nested location, aquo quantities and
                 events.
        """
        return self.get(location__name=name)

    def location_uuid(self, uuid, start='0001-01-01T00:00:00Z', end=None):
        """
        Returns time series for a location by location-UUID.
        :param uuid: name of a location
        :param start: start timestamp in ISO 8601 format
        :param end: end timestamp in ISO 8601 format, defaults to now
        :return: a dictionary of with nested location, aquo quantities and
                 events.
        """
        self.get(location__uuid=uuid)
        timeseries_uuids = [x['uuid'] for x in self.results]
        self.results = []
        for uuid in timeseries_uuids:
            ts = TimeSeries(self.base)
            ts.uuid(uuid, start, end)
            self.results += ts.results
        return self.results

    def uuid(self, uuid, start='0001-01-01T00:00:00Z', end=None):
        """
        Returns time series for a location by location-UUID.
        :param uuid: name of a location
        :param start: start timestamp in ISO 8601 format
        :param end: end timestamp in ISO 8601 format
        :return: a dictionary of with nested location, aquo quantities and
                 events.
        """
        if not end:
            end = jsdt.now_iso()
        self.get(uuid=uuid, start=start, end=end)

    def bbox(self, south_west, north_east, statistic='mean',
                  start='0001-01-01T00:00:00Z', end=None):
        """
        Find all timeseries within a certain bounding box.
        Returns records within bounding box using Bounding Box format (min Lon,
        min Lat, max Lon, max Lat). Also returns features with overlapping
        geometry.
        :param south_west: lattitude and longtitude of the south-western point
        :param north_east: lattitude and longtitude of the north-eastern point
        :param start: start timestamp in ISO 8601 format
        :param end: end timestamp in ISO 8601 format
        :return: a dictionary of the api-response.
        """
        self.statistic = statistic
        if statistic == 'mean':
            statistic = ['count', 'sum']
        if not end:
            end = jsdt.now_iso()

        min_lat, min_lon = south_west
        max_lat, max_lon = north_east

        polygon_coordinates = [
            [min_lon, min_lat],
            [min_lon, max_lat],
            [max_lon, max_lat],
            [max_lon, min_lat],
            [min_lon, min_lat],
        ]
        points = [' '.join([str(x), str(y)]) for x, y in polygon_coordinates]
        geom_within = 'POLYGON ((' + ', '.join(points) + '))'
        self.get(start=start, end=end, min_points=1, fields=statistic,
                 location__geom_within=geom_within)

    def minmax(self, extreme, results):
        args = {
            'mean': ('events', 0),
            'first': ('first_value_timestamp', ),
            'last': ('last_value_timestamp', )
        }.get(extreme, ('events', 0, extreme))
        def lambda_func(x):
            for arg in args:
                x = x[arg]
            return x
        lmbd = {
            'mean': lambda x: lambda_func(x)['sum']/ lambda_func(x)['count']
        }.get(extreme, lambda_func)
        return {
            'min': lmbd(min(results, key=lmbd)),
            'max': lmbd(max(results, key=lmbd))
        }

    def min_max_mean(self, start_date, end_date):
        values = {}
        for x in self.results:
            val = x['events'][0][self.statistic] if self.statistic != 'mean' \
                else x['events'][0]['sum'] / x['events'][0]['count']
            if x['uuid'] not in self.uuids:
                values.update({
                    x['location']['uuid']: val
                })
                self.uuids.append(x['uuid'])
        first = max(int(self.minmax('first', self.results)['min']),
                    jsdt.datestring_to_js(date_string=start_date, iso=False))
        last = min(int(self.minmax('last', self.results)['max']),
                    jsdt.datestring_to_js(date_string=end_date, iso=False))
        start_date = jsdt.js_to_datestring(js_date=first, iso=False)
        end_date = jsdt.js_to_datestring(js_date=last, iso=False)
        return {
                "extremes": self.minmax(self.statistic, self.results),
                "dates": {
                    "start": start_date,
                    "end": end_date
                },
                "values": values
            }


class GroundwaterLocations(Locations):
    """
    Makes a connection to the locations endpoint of the lizard api.
    Only selects GroundwaterStations.
    """

    @property
    def extra_queries(self):
        return {
            "object_type\__model": "GroundwaterStation",
            "organisation__unique_id": "f757d2eb6f4841b1a92d57d7e72f450c"
        }


class GroundwaterTimeSeries(TimeSeries):
    """
    Makes a connection to the timeseries endpoint of the lizard api.
    Only selects GroundwaterStations.
    """

    @property
    def extra_queries(self):
        return {
            "object_type\__model": "GroundwaterStation",
            "location__organisation__unique_id": "f757d2eb6f4841b1a92d57d7e72f450c"
        }


class GroundwaterTimeSeriesAndLocations(object):

    def __init__(self):
        st = time()
        self.locs = GroundwaterLocations()
        self.ts = GroundwaterTimeSeries()
        print('init', time() - st)

    def bbox(self, south_west, north_east, start='0001-01-01T00:00:00Z',
             end=None, groundwater_type="GWmMSL"):
        if end:
            self.end = end
        else:
            self.end = jsdt.now_iso()
        self.start = start
        self.ts.queries = {"name": groundwater_type}
        st1 = time()
        self.locs.bbox(south_west, north_east)
        st2 = time()
        print('locs.bbox', st2 - st1)
        self.ts.bbox(south_west, north_east, ['min', 'max', 'count', 'sum'],
                     start,
                     self.end)
        print('ts.bbox', time() - st2)

    def results_to_dict(self):
        values = {}
        for loc in self.locs.results:
            values[loc['uuid']] = {
                    'coordinates': loc['geometry']['coordinates'],
                    'name': loc['name']
                }
        # np array with columns: 'min', 'max', 'sum', 'count', first, last
        stats = ('min', 'max', 'sum', 'count')
        if not self.ts.results:
            return
        npts = np.array([
            [float(x['events'][0][y]) for y in stats] +
            [int(x['first_value_timestamp']), int(x['last_value_timestamp'])]
            for x in self.ts.results
        ])

        npts_calculated = np.hstack((
            npts[:, 0:2], (npts[:, 1] - npts[:, 0]).reshape(-1, 1),
            (npts[:, 2] / npts[:, 3]).reshape(-1, 1), npts[:,4:]
        ))
        stats = ((0, 'min'), (1, 'max'), (2, 'range'), (3, 'mean'))
        for i, row in enumerate(npts_calculated):
            location_uuid = self.ts.results[i]['location']['uuid']
            gw_point = {stat: row[i] for i, stat in stats}
            gw_point['timeseries uuid'] = self.ts.results[i]['uuid']
            values[location_uuid].update(gw_point)
        npts_min = npts_calculated.min(0)
        npts_max = npts_calculated.max(0)
        extremes = {stat: {'min': npts_min[i], 'max': npts_max[i]}
                    for i, stat in stats}
        return {
                "extremes": extremes,
                "dates": {
                    "start": jsdt.js_to_datetime(npts_min[4]),
                    "end": jsdt.js_to_datetime(npts_max[5])
                },
                "values": values
            }


if __name__ == '__main__':
    end="1452470400000"
    start="-2208988800000"
    start_time = time()
    GWinfo = GroundwaterTimeSeriesAndLocations()
    GWinfo.bbox(south_west=[-65.80277639340238, -223.9453125], north_east=[
        81.46626086056541, 187.3828125], start=start, end=end)
    x = GWinfo.results_to_dict()
    print(time() - start_time)
    pprint(x)
