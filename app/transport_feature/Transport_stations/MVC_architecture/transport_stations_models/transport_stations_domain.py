import uuid
from datetime import datetime
from app.extensions import db
from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import relationship

#many to many relationship table for stations and routes
destination_transport_routes = db.Table(
    "destination_transport_routes",
    db.Column("station_id", Uuid(as_uuid=True), ForeignKey("stations.id"), primary_key=True),
    db.Column("transport_route_id", Uuid(as_uuid=True), ForeignKey("transport_routes.id"), primary_key=True)
)



class transport_station(db.Model):
    __tablename__ = "stations"

    id = db.Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(String(100), nullable=False)
    type = db.Column(String(50), nullable=False)  # e.g., bus stop, train station, tram stop
    street = db.Column(String(255), nullable=True)
    city = db.Column(String(100), nullable=True)
    region = db.Column(String(100), nullable=True)

    # SQLite-compatible location storage as "lat,lon" text.
    location = db.Column(String(100), nullable=True)
    country = db.Column(String(100), nullable=True)

    #relationships
    routes = relationship("TransportRoute", foreign_keys="TransportRoute.origin_station_id", back_populates="origin_station")


    __table_args__ = ()


    

