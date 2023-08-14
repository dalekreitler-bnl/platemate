from .base import Base
import enum
from sqlalchemy import (
    create_engine,
    Table,
    Column,
    Integer,
    String,
    ForeignKey,
    Enum,
    Boolean,
    DateTime,
    CheckConstraint
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
import pandas
from datetime import datetime


class XrayStatusEnum(enum.Enum):
    not_collected = 1
    collection_succeeded = 2
    collection_failed = 3


class PuckType(Base):
    __tablename__ = "puck_type"
    uid = Column(Integer, primary_key=True)

    # relationships
    pucks = relationship("Puck", back_populates="puck_type")
    # Metadata
    name = Column(String)


class Puck(Base):
    __tablename__ = "puck"
    uid = Column(Integer, primary_key=True)

    puck_type_uid = Column(Integer, ForeignKey("puck_type.uid"))
    puck_type = relationship("PuckType", back_populates="pucks")

    pins = relationship("Pin", back_populates="puck")

    timestamp = Column(DateTime, default=datetime.now())


class Pin(Base):
    __tablename__ = "pin"
    uid = Column(Integer, primary_key=True)

    puck_uid = Column(Integer, ForeignKey("puck.uid"))
    puck = relationship("Puck", back_populates="pins")

    position = Column(Integer, nullable=False)  # 1 through 16
    xtal_well_source_id = Column(
        Integer, ForeignKey("xtal_well.uid")
    )  # Xtal well source
    xtal_well_source = relationship("XtalWell", back_populates="pins")

    xtal_ids = relationship("XtalID", back_populates="pin")

    time_departure = Column(DateTime)  # harvest/freeze time


class XtalID(Base):
    __tablename__ = "xtal_id"
    uid = Column(Integer, primary_key=True)

    # many-to-one
    pin_uid = Column(Integer, ForeignKey("pin.uid"))
    pin = relationship("Pin", back_populates="xtal_ids", uselist=False)

    xray_status = Column(Enum(XrayStatusEnum), nullable=False)
