from os import environ
from enum import IntEnum
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, MetaData
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker

Base = declarative_base()


def get_engine(url=None, debug=True):
    if url is None:
        prefix = environ['DB_PREFIX']
        user = environ['DB_USER']
        psw = environ['DB_PASSWORD']
        host = environ['DB_HOST']
        port = environ['DB_PORT']
        db = environ['DB_NAME']
        db_url = f"{prefix}{user}:{psw}@{host}:{port}/{db}"
        return create_engine(db_url, echo=debug)
    else:
        return create_engine(url, echo=debug)


def create_schema(engine):
    Base.metadata.create_all(bind=engine)


class Stop(Base):
    __tablename__ = "stops"

    uid = Column(String, primary_key=True, unique=True, nullable=False)
    name = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    zone_id = Column(String)
    wheelchair = Column(Integer)
    parent_station = Column(String)


class Route(Base):
    __tablename__ = "routes"

    uid = Column(String, primary_key=True, unique=True, nullable=False)
    long_name = Column(String, nullable=True)
    short_name = Column(String, nullable=False)
    desc = Column(String, nullable=True)
    agency = Column(String, nullable=False)
    color = Column(String, nullable=False)
    text_color = Column(String, nullable=False)
    type = Column(String, nullable=False)
    url = Column(String, nullable=False)
    is_night = Column(Boolean, nullable=False)
    created_time = Column(DateTime, nullable=True)
    modified_time = Column(DateTime, nullable=True)


class Shape(Base):
    __tablename__ = "shapes"

    uid = Column(String, primary_key=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    dist_traveled = Column(Float, nullable=False)
    pt_sequence = Column(Integer, primary_key=True, nullable=False)


class Service(Base):
    __tablename__ = "services"

    uid = Column(String, primary_key=True, unique=True, nullable=False)
    end_time = Column(DateTime, nullable=False)
    monday = Column(Boolean, nullable=False)
    tuesday = Column(Boolean, nullable=False)
    wednesday = Column(Boolean, nullable=False)
    thursday = Column(Boolean, nullable=False)
    friday = Column(Boolean, nullable=False)
    saturday = Column(Boolean, nullable=False)
    sunday = Column(Boolean, nullable=False)
    created_time = Column(DateTime, nullable=False)
    modified_time = Column(DateTime, nullable=True)


class Trip(Base):
    __tablename__ = "trips"

    uid = Column(String, primary_key=True, unique=True, nullable=False)
    route_id = Column(String, ForeignKey("routes.uid"), nullable=False)
    service_id = Column(String, ForeignKey("services.uid"), nullable=False)
    shape_id = Column(String, nullable=False)
    direction = Column(Integer, nullable=True)
    exceptional = Column(Integer, nullable=True)
    headsign = Column(String, nullable=False)
    wheelchair = Column(Boolean, nullable=False)
    bikes_allowed = Column(Boolean, nullable=False)
    block_id = Column(String, nullable=True)
    created_time = Column(DateTime, nullable=True)
    modified_time = Column(DateTime, nullable=True)


class VehicleTypeEnum(IntEnum):
    Metro = 1
    Tram = 2
    Bus = 3
    RegionalBus = 4
    NightBus = 5
    NightTram = 6
    TemporaryService = 7
    CableCar = 8
    SchoolService = 9
    DisabledTransportService = 10
    ContractedService = 11
    Ferry = 12
    Train = 13
    TemporaryBusOnTrainLine = 14
    TemporaryTram = 15
    NightRegionalBus = 16
    Other = 17


class Vehicle(Base):
    __tablename__ = "vehicles"

    trip_id = Column(String, ForeignKey("trips.uid"), primary_key=True, nullable=False)
    origin_route_name = Column(String, nullable=False)
    cis_line_id = Column(String, nullable=True)
    cis_trip_number = Column(Integer, nullable=False)
    start_timestamp = Column(DateTime, nullable=False)
    last_modified_timestamp = Column(DateTime, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    speed = Column(Integer, nullable=True)
    dist_traveled = Column(Float, nullable=True)
    tracking = Column(Boolean, nullable=False)
    bearing = Column(Integer, nullable=True)
    trip_sequence_id = Column(Integer, nullable=False)
    delay = Column(Integer, nullable=True)
    delay_last_stop = Column(Integer, nullable=True)
    is_canceled = Column(Boolean, nullable=False)
    last_stop_id = Column(String, ForeignKey("stops.uid"), nullable=True)
    last_stop_departure = Column(DateTime, nullable=True)
    next_stop_id = Column(String, ForeignKey("stops.uid"), nullable=True)
    next_stop_arrival = Column(DateTime, nullable=True)
    agency_name = Column(String, nullable=True)
    scheduled_agency_name = Column(String, nullable=True)
    registration_number = Column(String, nullable=True)
    vehicle_type = Column(Enum(VehicleTypeEnum, name='vehicle_types'), nullable=True)
    all_position = Column(Integer, nullable=False)


class VehiclePosition(Base):
    __tablename__ = "positions"

    trip_id = Column(String, ForeignKey("trips.uid"), primary_key=True, nullable=False)
    last_modified_timestamp = Column(DateTime, primary_key=True, nullable=False)
    start_timestamp = Column(DateTime, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    trip_sequence_id = Column(Integer, nullable=False)
    bearing = Column(Integer, nullable=True)
    dist_traveled = Column(Float, nullable=True)
    next_stop_id = Column(String, ForeignKey("stops.uid"), nullable=True)
    last_stop_id = Column(String, ForeignKey("stops.uid"), nullable=True)
    is_canceled = Column(Boolean, nullable=False)


@event.listens_for(Vehicle, 'before_update')
def receive_before_update(mapper, connection, target):
    "listen for the 'before_update' event"
    state = inspect(target)

    traced_attr = ['last_modified_timestamp',
                   'start_timestamp',
                   'lat',
                   'lon',
                   'bearing',
                   'dist_traveled',
                   'trip_sequence_id',
                   'next_stop_id',
                   'last_stop_id',
                   'is_canceled']
    last_position = {
        "trip_id": target.trip_id
    }
    changed = False
    for attr in traced_attr:
        hist = state.get_history(attr, True)

        if not hist.has_changes():
            last_position[attr] = hist.unchanged[0]
        else:
            last_position[attr] = hist.deleted[0]
            changed = True
    if changed:
        pos = VehiclePosition(**last_position)
        Session = sessionmaker(bind=connection.engine)
        with Session.begin() as session:
            session.merge(pos)
