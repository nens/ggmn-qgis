__author__ = 'roel.vandenberg@nelen-schuurmans.nl'

# from pprint import pprint  # left here for debugging purposes

import jsdatetime as jsdt
import json
import numpy as np
import urllib2
import urllib

## When you use this script stand alone, please set your login information here:
USR = None  # Replace the with your user name.
PWD = None  # Replace the with your password.
ORGANISATION_ID = None

GGMN_CUSTOM = 'GGMN_CUSTOM_DEV'
DOWNLOADED_MARKER = 'dl'


def join_urls(*args):
    return '/'.join(args)


def tryfloat(x):
    try:
        return float(x)
    except TypeError:
        return np.nan


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
    organisation_id = ORGANISATION_ID
    use_header = True
    max_results = 1000

    @property
    def extra_queries(self):
        """
        Overwrite class to add queries
        :return: dictionary with extra queries
        """
        return {}

    def __init__(self, base="https://ggmn.lizard.net"):
        """
        :param base: the site one wishes to connect to. Defaults to the
                     Lizard production site.
        """
        self.queries = {}
        self.results = []
        if base.startswith('http'):
            self.base = base
        else:
            self.base = join_urls('https:/', base)  # without extra '/', this is
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

        # print(url)
        self.fetch(url)
        # if 'count' in self.json:
        #     print('Number found {} : {} with URL: {}'.format(
        #         self.data_type, self.json.get('count', 0), url))
        # else:
        #     print('Number found {} : {} with URL: {}'.format(
        #         self.data_type, len(self.json), url))
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

    def add_new_one(self, values):
        url = self.base_url + '/'
        # print(url)
        data = urllib.urlencode(values)
        # pprint(data)
        request_obj = urllib2.Request(url, data, headers=self.header)
        response = urllib2.urlopen(request_obj)
        content = response.read().decode('UTF-8')
        response.close()
        result = json.loads(content)
        uuid = result.get('uuid') or result.get('id')
        return uuid

    def parse(self):
        """
        Parse the json attribute and store it to the results attribute.
        All pages of a query are parsed. If the max_results attribute is
        exceeded an ApiError is raised.
        """
        if 'results' in self.json:
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
        else:
            # Results aren't paginated, just return them.
            self.results = self.json

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


class SingleUserInfo(Base):
    data_type = 'users'

    def organisations_url(self):
        self.get(username=self.username)
        # pprint(self.results)
        assert len(self.results) == 1
        return self.results[0]['organisations_url']


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
        return self.parse_elements('unique_id')

    def for_dialog(self):
        """
        :return: a list of organisations belonging one has access to
                (with the credentials from the header attribute)
        """
        self.get()
        return [{'unique_id': organisation['unique_id'],
                 'name': organisation['name']} for organisation in self.results]


class Locations(Base):
    """
    Makes a connection to the locations endpoint of the lizard api.
    """
    data_type = 'locations'

    def __init__(self):
        self.uuids = []
        super(Locations, self).__init__()

    def bbox(self):
        """
        Find all locations
        :return: a dictionary of the api-response.
        """
        self.get()

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
        self.statistic = ['min', 'max', 'count', 'sum']
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

    def bbox(self,
             start='0001-01-01T00:00:00Z',
             end=None):
        self.get(start=start, end=end, min_points=1, fields=self.statistic)

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
        if not values:
            # print("No values passed on, using an empty dict")
            values = {}

        stats1 = ('min', 'max', 'sum', 'count')
        stats2 = (
            (0, 'min'),
            (1, 'max'),
            (2, 'mean'),
        )

        ts = []
        for result in self.results:
            try:
                timestamps = [int(result['first_value_timestamp']),
                              int(result['last_value_timestamp'])]
            except (ValueError, TypeError):
                timestamps = [np.nan, np.nan]
            if not len(result['events']):
                ts.append([np.nan for _ in range(len(stats1))] + timestamps)
            else:
                ts.append([tryfloat(result['events'][0][s]) for s in stats1] +
                          timestamps)
        npts = np.array(ts)
        npts_calculated = np.hstack((
            npts[:, 0:2],
            (npts[:, 2] / npts[:, 3]).reshape(-1, 1),
            npts[:, 3:]
        ))

        for i, row in enumerate(npts_calculated):
            location_uuid = self.results[i]['location']['uuid']
            loc_dict = values.get(location_uuid, {})
            loc_dict.update({stat: 'NaN' if np.isnan(row[i]) else row[i]
                             for i, stat in stats2})
            loc_dict['timeseries_uuid'] = self.results[i]['uuid']
            values[location_uuid] = loc_dict
        self.response = {
            "values": values
        }
        return self.response

    def add_value(self,
                  ts_id,
                  timestamp="1970-01-01T00:00:01Z",
                  value=None):
        data_url = self.base_url + '/%s/data/' % ts_id
        data = json.dumps([{'value': value,
                            'datetime': timestamp}])
        # pprint(data_url)
        headers = {}
        headers.update(self.header)
        headers['Content-Type'] = 'application/json'
        request_obj = urllib2.Request(data_url, data, headers=headers)
        response = urllib2.urlopen(request_obj)
        content = response.read().decode('UTF-8')
        response.close()
        result = json.loads(content)
        # pprint(result)


class GroundwaterLocations(Locations):
    """
    Makes a connection to the locations endpoint of the lizard api.
    Only selects GroundwaterStations.
    """

    @property
    def extra_queries(self):
        return {
            "object_type__model": 'filter',
            "organisation__unique_id": self.organisation_id
        }


class GroundwaterTimeSeries(TimeSeries):
    """
    Makes a connection to the timeseries endpoint of the lizard api.
    Only selects GroundwaterStations.
    """

    @property
    def extra_queries(self):
        return {
            "location__object_type__model": 'filter',
            "location__organisation__unique_id": self.organisation_id
        }


class CustomGroundwaterLocations(Locations):
    """
    Makes a connection to the locations endpoint of the lizard api.
    Only selects GroundwaterStations.
    """

    @property
    def extra_queries(self):
        return {
            "name": GGMN_CUSTOM,
            "organisation__unique_id": self.organisation_id
        }


class CustomGroundwaterTimeSeries(TimeSeries):
    """
    Makes a connection to the timeseries endpoint of the lizard api.
    Only selects GroundwaterStations.
    """

    @property
    def extra_queries(self):
        return {
            "name": GGMN_CUSTOM,
            "location__organisation__unique_id": self.organisation_id
        }


class GroundwaterTimeSeriesAndLocations(object):

    def __init__(self):
        self.locs = GroundwaterLocations()
        self.ts = GroundwaterTimeSeries()
        self.values = {}

    def bbox(self,
             start='0001-01-01T00:00:00Z',
             end=None,
             groundwater_type="GWmMSL"):
        if end:
            self.end = end
        else:
            self.end = jsdt.now_iso()
        self.start = start
        self.ts.queries = {"name": groundwater_type}
        self.locs.bbox()
        self.ts.bbox(start=start,
                     end=self.end)

    def locs_to_dict(self, values=None):
        if values:
            self.values = values
        for loc in self.locs.results:
            if not loc['geometry']:
                continue
            if loc['uuid'] in self.values:
                self.values[loc['uuid']].update({
                    'coordinates': loc['geometry']['coordinates'],
                    'name': loc['name']
                })
            else:
                self.values[loc['uuid']] = {
                    'coordinates': loc['geometry']['coordinates'],
                    'name': loc['name']
                }
        self.response = self.values

    def results_to_dict(self):
        self.locs_to_dict()
        self.ts.ts_to_dict(values=self.values, date_time='dt')
        return self.ts.response


class CustomGroundwaterTimeSeriesAndLocations(object):

    def __init__(self):
        self.locs = CustomGroundwaterLocations()
        self.ts = CustomGroundwaterTimeSeries()
        self.values = {}

    def bbox(self,
             start='0001-01-01T00:00:00Z',
             end=None):
        if end:
            self.end = end
        else:
            self.end = jsdt.now_iso()
        self.start = start
        self.locs.bbox()
        self.ts.bbox(start=start,
                     end=self.end)

    def locs_to_dict(self, values=None):
        if values:
            self.values = values
        for loc in self.locs.results:
            if not loc['geometry']:
                continue
            if loc['uuid'] in self.values:
                self.values[loc['uuid']].update({
                    'coordinates': loc['geometry']['coordinates'],
                    'name': loc['name']
                })
            else:
                self.values[loc['uuid']] = {
                    'coordinates': loc['geometry']['coordinates'],
                    'name': loc['name']
                }
        self.response = self.values

    def results(self):
        self.locs_to_dict()
        output = {}

        for timeserie in self.ts.results:
            if not timeserie['events']:
                continue
            value = timeserie['last_value']
            location_id = timeserie['location']['uuid']
            output[location_id] = self.values[location_id]
            output[location_id]['value'] = value

        return output
