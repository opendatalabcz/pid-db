from os import environ
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


def get_engine(debug=True):
    prefix = environ['DB_PREFIX']
    user = environ['DB_USER']
    psw = environ['DB_PASSWORD']
    host = environ['DB_HOST']
    port = environ['DB_PORT']
    db = environ['DB_NAME']
    db_url = f"{prefix}{user}:{psw}@{host}:{port}/{db}"
    return create_engine(db_url, echo=debug)


def create_schema():
    Base.metadata.create_all(bind=get_engine())


class Stop(Base):
    __tablename__ = "stop"

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
    route_id = Column(String, ForeignKey("routes.uid"), nullable=False),
    shape_id = Column(String, nullable=False)
    service_id = Column(String, ForeignKey("services.uid"), nullable=False)
    direction = Column(Integer, nullable=True)
    exceptional = Column(Integer, nullable=True)
    headsign = Column(String, nullable=False)
    wheelchair = Column(Boolean, nullable=False)
    bikes_allowed = Column(Boolean, nullable=False)
    block_id = Column(String, nullable=True)
    created_time = Column(DateTime, nullable=True)
    modified_time = Column(DateTime, nullable=True)
