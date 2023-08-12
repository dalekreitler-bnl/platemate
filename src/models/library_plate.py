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

lib_ptype_wtype_association = Table(
    "lib_ptype_wtype",
    Base.metadata,
    Column("plate_type_uid", Integer, ForeignKey("library_plate_type.uid")),
    Column("well_type_uid", Integer, ForeignKey("library_well_type.uid")),
)


class LibraryPlateType(Base):
    __tablename__ = "library_plate_type"
    uid = Column(Integer, primary_key=True)

    # Relationships
    # Multiple library plate types can have multiple well types
    well_types = relationship(
        "LibraryWellType",
        secondary=lib_ptype_wtype_association,
        back_populates="library_plate_type",
    )
    # Plates related to this type
    library_plates = relationship(
        "LibraryPlate", back_populates="library_plate_type")

    # Metadata
    name = Column(String, nullable=False)
    rows = Column(Integer)
    columns = Column(Integer)


class LibraryPlate(Base):
    __tablename__ = "library_plate"
    uid = Column(Integer, primary_key=True)

    # Relationships
    # Every plate has a related plate type
    library_plate_type_uid = Column(
        Integer, ForeignKey("library_plate_type.uid"))
    library_plate_type = relationship(
        "LibraryPlateType", back_populates="library_plates"
    )

    # Metadata
    name = Column(String, nullable=False)
    wells = relationship("LibraryWell", back_populates="plate")


class LibraryWellType(Base):
    __tablename__ = "library_well_type"
    uid = Column(Integer, primary_key=True)

    # Relationships
    # Well types can be shared between different plate types, therefore many-to-many
    library_plate_type = relationship(
        "LibraryPlateType",
        secondary=lib_ptype_wtype_association,
        back_populates="well_types",
    )
    # Multiple wells can have the same type, therefore many-to-one
    library_wells = relationship(
        "LibraryWell", back_populates="library_well_type")

    # Metadata
    name = Column(String, nullable=False)


class LibraryWell(Base):
    __tablename__ = "library_well"
    uid = Column(Integer, primary_key=True)

    # Metadata
    # Multiple wells belong to the same plate. Therefore many-to-one
    plate_uid = Column(Integer, ForeignKey("library_plate.uid"))
    plate = relationship("LibraryPlate", back_populates="wells")
    # Multiple wells have the same type, therefore many-to-one
    library_well_type_uid = Column(
        Integer, ForeignKey("library_well_type.uid"))
    library_well_type = relationship(
        "LibraryWellType", back_populates="library_wells")

    # Relationships
    used = Column(Boolean, default=False)
    catalog_id = Column(String, nullable=True)
    smiles = Column(String, nullable=True)

    sequence = Column(Integer, nullable=False)
