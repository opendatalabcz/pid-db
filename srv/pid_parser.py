from typing import List, Tuple, Union, Callable, Dict
from requests import get
from datetime import datetime
import dateutil.parser as dateparser
from sql_declaration import Stop, Route, Trip, Service, Shape


def parse_stop(entry: Dict) -> Stop:
    """
    Parsing stop given by https://api.golemio.cz/v2/gtfs/stops
    :param entry: Json entry
    :return: SQL Stop Object
    """
    props = entry['properties']
    lat, lon = entry['geometry']['coordinates']
    return Stop(uid=props['stop_id'],
                name=props['stop_name'],
                lat=lat, lon=lon,
                zone_id=props['zone_id'],
                parent_station=props['parent_station'],
                wheelchair=props['wheelchair_boarding'])


def parse_route(entry: Dict) -> Route:
    """
    Parsing single response given by https://api.golemio.cz/v2/gtfs/routes
    :param entry: Json entry
    :return: SQL Routes Object
    """
    return Route(
        uid=entry['route_id'],
        long_name=entry['route_long_name'],
        short_name=entry['route_short_name'],
        desc=entry.get('route_desc', None),
        agency=entry['agency_id'],
        color=entry['route_color'],
        text_color=entry['route_text_color'],
        type=entry['route_type'],
        url=entry['route_url'],
        is_night=bool(entry['is_night']),
        created_time=entry.get('created_time', None),
        modified_time=entry.get('last_modified', None)
    )


def parse_trip(entry: Dict) -> Trip:
    """
    Parsing response given by https://api.golemio.cz/v2/gtfs/trips
    :param entry: Json entry
    :return: SQL Trip Object
    """
    return Trip(
        uid=entry['trip_id'],
        route_id=entry['route_id'],
        service_id=entry['service_id'],
        shape_id=entry['shape_id'],
        direction=entry.get('direction_id', None),
        exceptional=entry.get('exceptional', None),
        headsign=entry['trip_headsign'],
        wheelchair=bool(entry['wheelchair_accessible']),
        bikes_allowed=bool(entry['bikes_allowed']),
        block_id=entry.get('block_id', None),
        created_time=entry.get('created_time', None),
        modified_time=entry.get('modified_time', None),
    )


def parse_service(entry: Dict) -> Service:
    """
    Parsing response given by https://api.golemio.cz/v2/gtfs/service
    :param entry: Json entry
    :return: SQL Service Object
    """
    modified_time = None if 'last_modify' not in entry else dateparser.parse(entry['last_modify'])
    return Service(
        uid=entry['service_id'],
        end_time=datetime.strptime(entry['end_date'], '%Y%m%d'),
        monday=bool(entry['monday']),
        tuesday=bool(entry['tuesday']),
        wednesday=bool(entry['wednesday']),
        thursday=bool(entry['thursday']),
        friday=bool(entry['friday']),
        saturday=bool(entry['saturday']),
        sunday=bool(entry['sunday']),
        created_time=dateparser.parse(entry['created_at']),
        modified_time=modified_time
    )


def parse_shape(entry: Dict) -> Shape:
    """
    Parsing response given by https://api.golemio.cz/v2/gtfs/shapes/{SHAPE_ID}
    :param entry: Json response
    :return: SQL Shape Object
    """
    props = entry['properties']
    lat, lon = entry['geometry']['coordinates']
    return Shape(uid=props['shape_id'],
                 lat=lat,
                 lon=lon,
                 dist_traveled=props['shape_dist_traveled'],
                 pt_sequence=props['shape_pt_sequence'])


def _parse_feature_collection(response: Dict, parser: Callable) -> List:
    """
    Parse FeatureCollection response
    :param response: Json body
    :param parser: Fuction parsing each item
    :return: List of items
    """
    assert 'features' in response
    assert ('type' in response) and (response['type'] == 'FeatureCollection')
    items = []
    for entry in response['features']:
        items.append(parser(entry))
    return items


def api_request(url: str, token: str, **params) -> Tuple[Dict, Union[List, Dict]]:
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'x-access-token': token
    }
    request = get(url,
                  headers=headers,
                  params=params)
    return request.status_code, request.json()


def parse_routes(response: List) -> List[Route]:
    return list(map(parse_route, response))


def parse_services(response: List) -> List[Service]:
    return list(map(parse_service, response))


def parse_trips(response: List) -> List[Trip]:
    return list(map(parse_trip, response))


def parse_stops(response: Dict) -> List[Stop]:
    return _parse_feature_collection(response, parse_stop)


def parse_shapes(response: Dict) -> List[Shape]:
    return _parse_feature_collection(response, parse_shape)
