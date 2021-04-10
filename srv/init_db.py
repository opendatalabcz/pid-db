import os
import time
from urllib.parse import urljoin
from pid_parser import parse_routes, parse_trips, parse_services, parse_stops, api_request, parse_shapes
from sql_declaration import get_engine
from sqlalchemy.orm.session import sessionmaker

# GFTS
gtfs_url_api = 'https://api.golemio.cz/v2/gtfs/'
# Load all list api
endpoint_parsers = {
    "routes": parse_routes,
    "trips": parse_trips,
    "services": parse_services,
    "stops": parse_stops,
}
# Engine
engine = get_engine(debug=True)
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
        with Session.begin() as session:
            session.add_all(parsed_items)
        offset += LIMIT
        time.sleep(1.54)

for shape_uid in shapes_uid:
    return_code, response = api_request(urljoin(gtfs_url_api, f"shapes/{shape_uid}"),
                                        os.environ["GOLEMIO_ACCESS_TOKEN"])
    # TODO: Resolve wrong answers
    assert return_code == 200
    parsed_items = parse_shapes(response)
    with Session.begin() as session:
        session.add_all(parsed_items)
