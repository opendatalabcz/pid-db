from typing import List, Tuple, Callable, Dict, Any
from requests import get
from datetime import datetime
import dateutil.parser as dateparser
from sql_declaration import Stop, Route, Trip, Service, Shape, Vehicle


def parse_stop(entry: Dict) -> Stop:
    """
    Parsing stop given by https://api.golemio.cz/v2/gtfs/stops
    :param entry: Json entry
    :return: SQL Stop Object
    """
    props = entry['properties']
    lon, lat = entry['geometry']['coordinates']
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
    lon, lat = entry['geometry']['coordinates']
    return Shape(uid=props['shape_id'],
                 lat=lat,
                 lon=lon,
                 dist_traveled=props['shape_dist_traveled'],
                 pt_sequence=props['shape_pt_sequence'])


def parse_vehicle(entry: Dict) -> Vehicle:
    """
    Parsing response given by https://api.golemio.cz/v2/vehiclepositions
    :param entry: Json response
    :return: SQL Vehicle Object
    """
    props = entry['properties']
    last_position = props['last_position']
    trip = props['trip']
    all_position = props['all_positions']
    lon, lat = entry['geometry']['coordinates']
    departure_time = None if last_position['last_stop']['departure_time'] is None else dateparser.parse(last_position['last_stop']['departure_time'])
    arrival_time = None if last_position['next_stop']['arrival_time'] is None else dateparser.parse(last_position['next_stop']['arrival_time'])
    return Vehicle(
        trip_id=trip['gtfs']['trip_id'],
        origin_route_name=trip['origin_route_name'],
        cis_line_id=trip['cis']['line_id'],
        cis_trip_number=trip['cis']['trip_number'],
        start_timestamp=dateparser.parse(trip['start_timestamp']),
        last_modified_timestamp=dateparser.parse(trip['updated_at']),
        lat=lat,
        lon=lon,
        speed=last_position['speed'],
        dist_traveled=last_position['shape_dist_traveled'],
        tracking=bool(last_position['tracking']),
        bearing=last_position['bearing'],
        trip_sequence_id=trip['sequence_id'],
        delay=last_position['delay']['actual'],
        delay_last_stop=last_position['delay']['last_stop_departure'],
        is_canceled=last_position['is_canceled'],
        last_stop_id=last_position['last_stop']['id'],
        last_stop_departure=departure_time,
        next_stop_id=last_position['next_stop']['id'],
        next_stop_arrival=arrival_time,
        agency_name=trip['agency_name']['real'],
        scheduled_agency_name=trip['agency_name']['scheduled'],
        registration_number=trip['vehicle_registration_number'],
        vehicle_type=trip['vehicle_type']['id'],
        all_position=len(all_position)
    )


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


def api_request(url: str, token: str, **params) -> Tuple[int, Any]:
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


def parse_vehicles(response: Dict) -> List[Vehicle]:
    return _parse_feature_collection(response, parse_vehicle)
