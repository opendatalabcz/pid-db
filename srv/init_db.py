import os
import time
import pytz
from datetime import datetime, timedelta
from urllib.parse import urljoin
from pid_parser import parse_routes, parse_trips, parse_services, parse_stops, api_request, parse_shapes, parse_vehicles
from sql_declaration import get_engine, create_schema
from sqlalchemy.orm.session import sessionmaker

# GFTS
gtfs_url_api = 'https://api.golemio.cz/v2/'
# Load all list api
endpoint_parsers = {
    # "gtfs/routes": parse_routes,
    # "gtfs/services": parse_services,
    # "gtfs/stops": parse_stops,
    # "gtfs/trips": parse_trips,
    "vehiclepositions": parse_vehicles,
}
# Engine
engine = get_engine('sqlite:///test.db', debug=True)
create_schema(engine)
Session = sessionmaker(bind=engine)
# Load Tables PID
shapes_uid = set()
for endpoint, parser in endpoint_parsers.items():
    # TODO: Must be called iteratively with limit and offset :)
    LIMIT = 10000
    offset = 0
    parsed_items = [-1]

    while len(parsed_items) != 0:
        return_code, response = api_request(urljoin(gtfs_url_api, endpoint),
                                            os.environ["GOLEMIO_ACCESS_TOKEN"],
                                            limit=LIMIT,
                                            offset=offset)
        # TODO: Resolve wrong response
        assert return_code == 200
        parsed_items = parser(response)
        if endpoint == 'trips':
            shapes_uid.update({item.shape_id for item in parsed_items})
        for item in parsed_items:
            with Session.begin() as session:
                session.merge(item)
        offset += LIMIT
        time.sleep(1.54)

_time_format = '%Y-%m-%dT%H:%M:%S.000Z'
updated_since = datetime.utcnow().strftime(_time_format)
LIMIT=10000
offset = 0
while True:
    parsed_items = [-1]
    while len(parsed_items) != 0:
        return_code, response = api_request(urljoin(gtfs_url_api, 'vehiclepositions'),
                                            os.environ["GOLEMIO_ACCESS_TOKEN"],
                                            limit=LIMIT,
                                            offset=offset,
                                            updatedSince=updated_since)
        parsed_items = parse_vehicles(response)
        if len(parsed_items) != 0:
            updated_since = datetime.utcnow().strftime(_time_format)
            for item in parsed_items:
                with Session.begin() as session:
                    session.merge(item)
        time.sleep(10.5)

for shape_uid in shapes_uid:
    return_code, response = api_request(urljoin(gtfs_url_api, f"shapes/{shape_uid}"),
                                        os.environ["GOLEMIO_ACCESS_TOKEN"])
    # TODO: Resolve wrong answers
    assert return_code == 200
    parsed_items = parse_shapes(response)
    with Session.begin() as session:
        session.add_all(parsed_items)
