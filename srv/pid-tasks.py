import os
from celery import Celery, Task
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from urllib.parse import urljoin
from golemio.parser import parse_vehicles, api_request
from golemio.sql_declaration import get_engine, create_schema

app = Celery(__name__,
             backend=os.environ["CELERY_REDIS"],
             broker=os.environ["CELERY_REDIS"],)

SECRET_TOKEN = os.environ['GOLEMIO_ACCESS_TOKEN']
LIMIT = 10000
GTFS_URL_API = 'https://api.golemio.cz/v2/'
TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.000Z'


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    print('Setting up periodic tasks')
    sender.add_periodic_task(10.0, update_positions.s(), name='check every 10')
    print('Done periodic tasks')


class VehiclePositionUpdate(Task):
    def __init__(self):
        self.updated_since = None


@app.task(bind=True, base=VehiclePositionUpdate)
def update_positions(self):
    print(f"Getting updates from {str(self.updated_since)}")
    offset = 0
    engine = get_engine(debug=False)
    Session = sessionmaker(bind=engine)
    parsed_items = [-1]
    while len(parsed_items) != 0:
        kwargs = dict(limit=LIMIT, offset=offset)
        if self.updated_since is not None:
            kwargs['updatedSince'] = self.updated_since
        return_code, response = api_request(urljoin(GTFS_URL_API, 'vehiclepositions'),
                                            SECRET_TOKEN,
                                            **kwargs)
        assert return_code == 200, f"Updating vehicle position failed with {return_code}"
        parsed_items = parse_vehicles(response)
        print(f'Return code {return_code} - {len(parsed_items)}')
        if len(parsed_items) < LIMIT:
            self.updated_since = datetime.utcnow().strftime(TIME_FORMAT)
        if len(parsed_items) != 0:
            with Session.begin() as session:
                for item in parsed_items:
                    session.merge(item)
            offset += LIMIT
