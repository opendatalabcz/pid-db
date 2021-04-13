import os
import time
import logging
from urllib.parse import urljoin
from golemio.parser import api_request, parse_vehicles, parse_shapes, parse_services, parse_stops, parse_trips, \
    parse_routes
from golemio.sql_declaration import get_engine, create_schema, Route, Service, Stop, Trip, Vehicle
from sqlalchemy.orm.session import sessionmaker

# Set log level
logging.basicConfig(level=logging.DEBUG)
# GFTS
gtfs_url_api = 'https://api.golemio.cz/v2/'
WAIT_TIME = 2.53
SECURITY_TOKEN = os.environ["GOLEMIO_ACCESS_TOKEN"]
# Load all list api
endpoint_parsers = {
    "gtfs/routes": parse_routes,
    "gtfs/services": parse_services,
    "gtfs/stops": parse_stops,
    "gtfs/trips": parse_trips,
    "vehiclepositions": parse_vehicles,
}
endpoint_types = {
    "gtfs/routes": Route,
    "gtfs/services": Service,
    "gtfs/stops": Stop,
    "gtfs/trips": Trip,
    "vehiclepositions": Vehicle,
}


def update_shapes(shape_uid):
    return_code, response = api_request(urljoin(gtfs_url_api, f"gtfs/shapes/{shape_uid}"),
                                        SECURITY_TOKEN)
    assert return_code == 200, f"Database init shape addding failed with {return_code}"
    parsed_items = parse_shapes(response)
    with Session.begin() as session:
        session.add_all(parsed_items)


# Engine
engine = get_engine(debug=False)
create_schema(engine)
Session = sessionmaker(bind=engine)
# Load Tables PID
shapes_uid = set()
for endpoint, parser in endpoint_parsers.items():
    endpoint_type = endpoint_types[endpoint]
    LIMIT = 10000
    offset = 0
    parsed_items = [-1]

    # Skip already filled tables
    with Session.begin() as session:
        if session.query(endpoint_type).count() != 0:
            logging.debug(f"Skipping the filled table {endpoint}")
            continue

    logging.debug(f"Loading table {endpoint}")
    while len(parsed_items) != 0:

        return_code, response = api_request(urljoin(gtfs_url_api, endpoint),
                                            SECURITY_TOKEN,
                                            limit=LIMIT,
                                            offset=offset)
        assert return_code == 200, f"Database table {endpoint} init failed with {return_code}"
        parsed_items = parser(response)
        # Adding shapes, there is no option to get all the shapes from API
        if endpoint == "gtfs/trips":
            trip_shapes = {item.shape_id for item in parsed_items}
            for shape_uid in (trip_shapes - shapes_uid):
                update_shapes(shape_uid)
            shapes_uid.update(trip_shapes)

        with Session.begin() as session:
            session.add_all(parsed_items)
        offset += LIMIT
        time.sleep(WAIT_TIME)
