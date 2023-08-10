from .base import Base
import enum
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    ForeignKey,
    Enum,
    Boolean,
    Table,
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
import pandas


xtal_ptype_wtype_association = Table(
    "xtal_ptype_wtype",
    Base.metadata,
    Column("plate_type_uid", Integer, ForeignKey("xtal_plate_type.uid")),
    Column("well_type_uid", Integer, ForeignKey("xtal_well_type.uid")),
)


class XtalPlateType(Base):
    __tablename__ = "xtal_plate_type"
    uid = Column(Integer, primary_key=True)

    # Relationships
    # A xtal plate type can have many well types
    well_types = relationship(
        "XtalWellType",
        secondary=xtal_ptype_wtype_association,
        back_populates="plate_types",
    )
    # Each xtal plate has one plate type
    xtal_plates = relationship("XtalPlate", back_populates="plate_type")
    # Metadata
    name = Column(String, nullable=False)


class XtalPlate(Base):
    __tablename__ = "xtal_plate"
    uid = Column(Integer, primary_key=True)

    # Relationships
    # Each xtal plate has one plate type
    plate_type_id = Column(Integer, ForeignKey("xtal_plate_type.uid"))
    plate_type = relationship("XtalPlateType", back_populates="xtal_plates")
    # Each plate has different wells
    wells = relationship("XtalWell", back_populates="plate")

    # Metadata
    name = Column(String, nullable=False)


class XtalWellType(Base):
    __tablename__ = "xtal_well_type"
    uid = Column(Integer, primary_key=True)

    # Relationship
    # A xtal plate type can have many well types
    plate_types = relationship(
        "XtalPlateType",
        secondary=xtal_ptype_wtype_association,
        back_populates="well_types",
    )
    # Each xtal plate has a shifter to echo mapping
    well_map_id = Column(Integer, ForeignKey("well_map.uid"))
    well_map = relationship("WellMap", back_populates="well_types")

    # Each well has a well type
    wells = relationship("XtalWell", back_populates="well_type")

    # Metadata
    name = Column(String, nullable=False)


class XtalWell(Base):
    __tablename__ = "xtal_well"
    uid = Column(Integer, primary_key=True)

    # Relationships
    # A drop position can be associated with multiple wells
    drop_position_uid = Column(Integer, ForeignKey("drop_position.uid"))
    drop_position = relationship("DropPosition", back_populates="xtal_wells")

    # Each plate has a number of wells
    plate_uid = Column(Integer, ForeignKey("xtal_plate.uid"))
    plate = relationship("XtalPlate", back_populates="wells")

    # Each well has one well type
    well_type_uid = Column(Integer, ForeignKey("xtal_well_type.uid"))
    well_type = relationship("XtalWellType", back_populates="wells")

    pins = relationship("Pin", back_populates="xtal_well_source")

    # Metadata
    harvesting_status = Column(Boolean, default=False)  # bool


class DropPosition(Base):
    __tablename__ = "drop_position"
    uid = Column(Integer, primary_key=True)
    name = Column(String)
    x_offset = Column(Integer)
    y_offset = Column(Integer)
    xtal_wells = relationship("XtalWell", back_populates="drop_position")
