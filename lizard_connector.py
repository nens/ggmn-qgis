__author__ = 'roel.vandenberg@nelen-schuurmans.nl'

import datetime as dt
import json
from pprint import pprint  # left here for debugging purposes
from time import time
import urllib2
import urllib

import numpy as np
import jsdatetime as jsdt

## When you use this script stand alone, please set your login information here:
USR = None  # Replace the with your user name.
PWD = None  # Replace the with your password.
ORGANISATION_ID = None

GGMN_CUSTOM = 'GGMN_CUSTOM_DEV'
DOWNLOADED_MARKER = 'dl'


def join_urls(*args):
    return '/'.join(args)


class LizardApiError(Exception):
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
    username = USR
    password = PWD
    max_results = 1000

    @property
    def extra_queries(self):
        """
        Overwrite class to add queries
        :return: dictionary with extra queries
        """
        return {}

    def organisation_query(self, organisation, added_query_string='location__'):
        org_query = {}
        if isinstance(organisation, str):
            org_query.update({added_query_string + "organisation__unique_id":
            organisation})
        elif organisation:
            org_query.update({
                added_query_string + "organisation__unique_id": ','.join(
                    org for org in organisation)
            })
        if org_query:
            return dict([urllib.parse.urlencode(org_query).split('=')])
        else:
            return {}

    def __init__(self, base="https://ggmn.un-igrac.org", use_header=False):
        """
        :param base: the site one wishes to connect to. Defaults to the
                     Lizard staging site.
        """
        self.use_header = use_header
        self.queries = {}
        self.results = []
        if base.startswith('http'):
            self.base = base
        else:
            self.base = join_urls('https:/', base)  # without extra '/', this is
                                                    # added in join_urls
        self.base_url = join_urls(self.base, 'api/v2', self.data_type) + '/'

    def get(self, **queries):
        """
        Query the api.
        For possible queries see: https://nxt.staging.lizard.net/doc/api.html
        Stores the api-response as a dict in the results attribute.
        :param queries: all keyword arguments are used as queries.
        :return: a dictionary of the api-response.
        """
        if self.max_results:
            queries.update({'page_size': self.max_results})
        queries.update(self.extra_queries)
        queries.update(getattr(self, "queries", {}))
        query = '?' + '&'.join(str(key) + '=' +
                               (('&' + str(key) + '=').join(value)
                               if isinstance(value, list) else str(value))
                               for key, value in queries.items())
        url = self.base_url + query
        self.fetch(url)
        try:
            print('Number found {} : {} with URL: {}'.format(
                self.data_type, self.json.get('count', 0), url))
        except (KeyError, AttributeError):
            print('Got results from {} with URL: {}'.format(
                self.data_type, url))
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
        request_obj = urllib2.Request(url, headers=self.header)
        response = urllib2.urlopen(request_obj)
        content = response.read().decode('UTF-8')
        response.close()
        self.json = json.loads(content)

        return self.json

    # def post(self, UUID, data):
    #     """
    #     POST data to the api.
    #     :param UUID: UUID of the object in the database you wish to store
    #                  data to.
    #     :param data: Dictionary with the data to post to the api
    #     """
    #     post_url = join_urls(self.base_url, UUID, 'data')
    #     if self.use_header:
    #         requests.post(post_url, data=json.dumps(data), headers=self.header)
    #     else:
    #         requests.post(post_url, data=json.dumps(data))

    def parse(self):
        """
        Parse the json attribute and store it to the results attribute.
        All pages of a query are parsed. If the max_results attribute is
        exceeded an ApiError is raised.
        """
        while True:
            try:
                if self.json['count'] > self.max_results:
                    raise LizardApiError('Too many results: {} found, while max {} '
                                   'are accepted'.format(
                        self.json['count'], self.max_results))
                self.results += self.json['results']
                next_url = self.json.get('next')
                if next_url:
                    self.fetch(next_url)
                else:
                    break
            except KeyError:
                self.results += [self.json]
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
        if self.use_header:
            return {
                "username": self.username,
                "password": self.password
            }
        return {}


class Organisations(Base):
    """
    Makes a connection to the organisations endpoint of the lizard api.
    """
    data_type = 'organisations'

    def all(self, organisation=None):
        """
        :return: a list of organisations belonging one has access to
                (with the credentials from the header attribute)
        """
        if organisation:
            self.get(unique_id=organisation)
        else:
            self.get()
        self.parse()
        return self.parse_elements('unique_id')


class Locations(Base):
    """
    Makes a connection to the locations endpoint of the lizard api.
    """

    def __init__(self, base="https://ggmn.un-igrac.org", use_header=False):
        self.data_type = 'locations'
        self.uuids = []
        super(Locations).__init__(base, use_header)

    def bbox(self, south_west, north_east, organisation=None):
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
        org_query = self.organisation_query(organisation, '')
        self.get(in_bbox=coords, **org_query)

    def distance_to_point(self, distance, lat, lon, organisation=None):
        """
        Returns records with distance meters from point. Distance in meters
        is converted to WGS84 degrees and thus an approximation.
        :param distance: meters from point
        :param lon: longtitude of point
        :param lat: latitude of point
        :return: a dictionary of the api-response.
        """
        coords = self.commaify(lon, lat)
        org_query = self.organisation_query(organisation, '')
        self.get(distance=distance, point=coords, **org_query)

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

    def __init__(self, base="https://ggmn.un-igrac.org", use_header=False):
        self.data_type = 'timeseries'
        self.uuids = []
        self.statistic = None
        super(TimeSeries).__init__(base, use_header)

    def location_name(self, name, organisation=None):
        """
        Returns time series metadata for a location by name.
        :param name: name of a location
        :return: a dictionary of with nested location, aquo quantities and
                 events.
        """
        org_query = self.organisation_query(organisation)
        return self.get(location__name=name, **org_query)

    def location_uuid(self, loc_uuid, start='0001-01-01T00:00:00Z', end=None,
                      organisation=None):
        """
        Returns time series for a location by location-UUID.
        :param loc_uuid: name of a location
        :param start: start timestamp in ISO 8601 format
        :param end: end timestamp in ISO 8601 format, defaults to now
        :return: a dictionary of with nested location, aquo quantities and
                 events.
        """
        org_query = self.organisation_query(organisation)
        self.get(location__uuid=loc_uuid, **org_query)
        timeseries_uuids = [x['uuid'] for x in self.results]
        self.results = []
        for ts_uuid in timeseries_uuids:
            ts = TimeSeries(self.base, use_header=self.use_header)
            ts.uuid(ts_uuid, start, end, organisation)
            self.results += ts.results
        return self.results

    def uuid(self, ts_uuid, start='0001-01-01T00:00:00Z', end=None,
             organisation=None):
        """
        Returns time series for a timeseries by timeseries-UUID.
        :param ts_uuid: uuid of a timeseries
        :param start: start timestamp in ISO 8601 format
        :param end: end timestamp in ISO 8601 format
        :return: a dictionary of with nested location, aquo quantities and
                 events.
        """
        if not end:
            end = jsdt.now_iso()
        old_base_url = self.base_url
        self.base_url += ts_uuid + "/"
        org_query = self.organisation_query(organisation)
        self.get(start=start, end=end, **org_query)
        self.base_url = old_base_url


    def bbox(self, south_west, north_east, statistic=None,
                  start='0001-01-01T00:00:00Z', end=None, organisation=None):
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
        if not end:
            end = jsdt.now_iso()
        if isinstance(start, int):
            start -= 10000
        if isinstance(end, int):
            end += 10000

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
        geom_within = {'a': 'POLYGON ((' + ', '.join(points) + '))'}
        geom_within = urllib.parse.urlencode(geom_within).split('=')[1]
        org_query = self.organisation_query(organisation)
        self.statistic = statistic
        if statistic == 'mean':
            statistic = ['count', 'sum']
        elif not statistic:
            statistic = ['min', 'max', 'count', 'sum']
            self.statistic = None
        elif statistic == 'range (max - min)':
            statistic = ['min', 'max']
        elif statistic == 'difference (last - first)':
            statistic = 'count'
        elif statistic == 'difference (mean last - first year)':
            year = dt.timedelta(days=366)
            first_end = jsdt.datetime_to_js(jsdt.js_to_datetime(start) + year)
            last_start = jsdt.datetime_to_js(jsdt.js_to_datetime(end) - year)
            self.get(
                start=start,
                end=first_end,
                min_points=1,
                fields=['count', 'sum'],
                location__geom_within=geom_within,
                **org_query
            )
            first_year = {}
            for r in self.results:
                try:
                    first_year[r['location']['uuid']] = {
                      'first_value_timestamp': r['first_value_timestamp'],
                      'mean': r['events'][0]['sum'] / r['events'][0]['count']
                    }
                except IndexError:
                    first_year[r['location']['uuid']] = {
                      'first_value_timestamp': np.nan,
                      'mean': np.nan
                    }
            self.results = []
            self.get(
                start=last_start,
                end=end,
                min_points=1,
                fields=['count', 'sum'],
                location__geom_within=geom_within,
                **org_query
            )
            for r in self.results:
                try:
                    r['events'][0]['difference (mean last - first year)'] = \
                        r['events'][0]['sum'] / r['events'][0]['count'] - \
                        first_year[r['location']['uuid']]['mean']
                    r['first_value_timestamp'] = \
                        first_year[
                            r['location']['uuid']]['first_value_timestamp']
                except IndexError:
                    r['events'] = [{'difference (mean last - first year)':
                                       np.nan}]
                    r['first_value_timestamp'] = np.nan
                    r['last_value_timestamp'] = np.nan
            return

        self.get(
            start=start,
            end=end,
            min_points=1,
            fields=statistic,
            location__geom_within=geom_within,
            **org_query
        )


    def ts_to_dict(self, statistic=None, values=None,
                   start_date=None, end_date=None, date_time='js'):
        """
        :param date_time: default: js. Several options:
            'js': javascript integer datetime representation
            'dt': python datetime object
            'str': date in date format (dutch representation)
        """
        if len(self.results) == 0:
            self.response = {}
            return self.response
        if values:
            values = values
        else:
            values = {}
        if not statistic and self.statistic:
            statistic = self.statistic

        # np array with cols: 'min', 'max', 'sum', 'count', 'first', 'last'
        if not statistic:
            stats1 = ('min', 'max', 'sum', 'count')
            stats2 = (
                (0, 'min'),
                (1, 'max'),
                (2, 'mean'),
                (3, 'range (max - min)'),
                (4, 'difference (last - first)'),
                (5, 'difference (mean last - first year)')  #TODO: update code above
            )
            start_index, end_index = 6, 7
        else:
            if statistic == 'mean':
                stats1 = ('sum', 'count')
            elif statistic == 'range (max - min)':
                stats1 = ('min', 'max')
            else:
                stats1 = (statistic, )
            stats2 = ((0, statistic), )
            start_index = int(statistic == 'mean') + 1
            end_index = start_index + 1
        ts = []
        for result in self.results:
            try:
                timestamps = [int(result['first_value_timestamp']),
                              int(result['last_value_timestamp'])]
            except ValueError:
                timestamps = [np.nan, np.nan]
            if not len(result['events']):
                y = 2 if statistic == 'difference (mean last - first year)' \
                    else 0
                ts.append([np.nan for _ in range(len(stats1) + y)] + timestamps)
            else:
                ts.append([float(result['events'][0][s]) for s in stats1] +
                          timestamps)
        npts = np.array(ts)
        if statistic:
            if statistic == 'mean':
                stat = (npts[:, 0] / npts[:, 1]).reshape(-1, 1)
            elif statistic == 'range (max - min)':
                stat = (npts[:, 1] - npts[:, 0]).reshape(-1, 1)
            elif statistic == 'difference (last - first)':
                stat = (npts[:, 1] - npts[:, 0]).reshape(-1, 1)
            else:
                stat = npts[:, 0].reshape(-1, 1)
            npts_calculated = np.hstack((stat, npts[:, slice(start_index, -1)]))
        else:
            npts_calculated = np.hstack((
                npts[:, 0:2],
                (npts[:, 2] / npts[:, 3]).reshape(-1, 1),
                (npts[:, 1] - npts[:, 0]).reshape(-1, 1),

                npts[:, 4:]
            ))

        for i, row in enumerate(npts_calculated):
            location_uuid = self.results[i]['location']['uuid']
            loc_dict = values.get(location_uuid, {})
            loc_dict.update({stat: 'NaN' if np.isnan(row[i]) else row[i]
                             for i, stat in stats2})
            loc_dict['timeseries_uuid'] = self.results[i]['uuid']
            values[location_uuid] = loc_dict
        npts_min = np.nanmin(npts_calculated, 0)
        npts_max = np.nanmax(npts_calculated, 0)
        extremes = {
            stat: {
                'min': npts_min[i] if not np.isnan(npts_min[i]) else 0,
                'max': npts_max[i] if not np.isnan(npts_max[i])  else 0
            } for i, stat in stats2
        }
        dt_conversion = {
            'js': lambda x: x,
            'dt': jsdt.js_to_datetime,
            'str': jsdt.js_to_datestring
        }[date_time]
        if statistic != 'difference (mean last - first year)':
            start = dt_conversion(max(jsdt.round_js_to_date(start_date),
                                      jsdt.round_js_to_date(npts_min[-2])))
            end = dt_conversion(min(jsdt.round_js_to_date(end_date),
                                    jsdt.round_js_to_date(npts_max[-1])))
        else:
            start = dt_conversion(jsdt.round_js_to_date(start_date))
            end = dt_conversion(jsdt.round_js_to_date(end_date))
        self.response = {
            "extremes": extremes,
            "dates": {
                "start": start,
                "end": end
            },
            "values": values
        }
        return self.response


class GroundwaterLocations(Locations):
    """
    Makes a connection to the locations endpoint of the lizard api.
    Only selects GroundwaterStations.
    """

    @property
    def extra_queries(self):
        return {
            "object_type__id": 107,
        }


class GroundwaterTimeSeries(TimeSeries):
    """
    Makes a connection to the timeseries endpoint of the lizard api.
    Only selects GroundwaterStations.
    """

    @property
    def extra_queries(self):
        return {
            "location__object_type__id": 107,
        }


class GroundwaterTimeSeriesAndLocations(object):

    def __init__(self):
        self.locs = GroundwaterLocations()
        self.ts = GroundwaterTimeSeries()
        self.values = {}

    def bbox(self, south_west, north_east, start='0001-01-01T00:00:00Z',
             end=None, groundwater_type="GWmMSL"):
        if not end:
            self.end = jsdt.now_iso()
        else:
            self.end = end
        self.start = start
        self.ts.queries = {"name": groundwater_type}
        self.locs.bbox(south_west, north_east)
        self.ts.bbox(south_west=south_west, north_east=north_east, start=start,
                     end=self.end)

    def locs_to_dict(self, values=None):
        if values:
            self.values = values
        for loc in self.locs.results:
            self.values.get(loc['uuid'], {}).update({
                    'coordinates': loc['geometry']['coordinates'],
                    'name': loc['name']
                })
        self.response = self.values

    def results_to_dict(self):
        self.locs_to_dict()
        self.ts.ts_to_dict(values=self.values)
        return self.ts.response


class RasterFeatureInfo(Base):
    data_type = 'raster-aggregates'

    def wms(self, lat, lng, layername):
        if 'igrac' in layername:
            self.base_url = "https://raster.staging.lizard.net/wms"
            lat_f = float(lat)
            lng_f = float(lng)
            self.get(request="getfeatureinfo",
                     layers=layername,
                     width=1,
                     height=1,
                     i=0,
                     j=0,
                     srs="epsg:4326",
                     bbox=','.join([lng, lat, str(lng_f+0.00001), str(lat_f+0.00001)]),
                     index="world"
                     )
            try:
                self.results = {"data": [self.results[1]]}
            except IndexError:
                self.results = {"data": ['null']}
        else:
            self.get(
                agg='curve',
                geom='POINT(' + lng + '+' + lat + ')',
                srs='EPSG:4326',
                raster_names=layername,
                count=False
            )
        return self.results

    def parse(self):
        self.results = self.json


class RasterLimits(Base):
    data_type = 'wms'

    def __init__(self, base="https://raster.lizard.net",
                 use_header=False):
        super(RasterLimits).__init__(base, use_header)
        self.base_url = join_urls(base, self.data_type)
        self.max_results = None

    def get_limits(self, layername, bbox):
        if 'igrac' in layername:
            self.base_url = "https://raster.staging.lizard.net/wms"
        try:
            return self.get(
                request='getlimits',
                layers=layername,
                bbox=bbox,
                width=16,
                height=16,
                srs='epsg:4326'
            )
        except urllib2.HTTPError:
            return [[-1000, 1000]]

    def parse(self):
        self.results = self.json


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
