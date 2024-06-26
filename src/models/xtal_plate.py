from .base import Base
import enum
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Table,
)
from sqlalchemy.orm import relationship, mapped_column, Mapped, Session
from sqlalchemy.event import listens_for
from typing import List, Optional
from .puck import Pin
from datetime import datetime


# can be many pins to one xtal well now, in future many-to-many both ways
# when we develop multiple wells on one pin/mount
xtal_ptype_wtype_association = Table(
    "xtal_ptype_wtype",
    Base.metadata,
    Column("plate_type_uid", Integer, ForeignKey("xtal_plate_type.uid")),
    Column("well_type_uid", Integer, ForeignKey("xtal_well_type.uid")),
)


class XtalPlateType(Base):
    __tablename__ = "xtal_plate_type"
    uid: Mapped[int] = mapped_column(primary_key=True)

    # Relationships
    # A xtal plate type can have many well types
    well_types = relationship(
        "XtalWellType",
        secondary=xtal_ptype_wtype_association,
        back_populates="plate_types",
    )
    # Each xtal plate has one plate type
    xtal_plates: Mapped[List["XtalPlate"]] = relationship(
        back_populates="plate_type")
    # Metadata
    name: Mapped[str] = mapped_column(unique=True, nullable=False)


pin_xtal_well_association = Table(
    "pin_xtal_well",
    Base.metadata,
    Column("pin_uid", Integer, ForeignKey("pin.uid")),
    Column("well_uid", Integer, ForeignKey("xtal_well.uid")),
)


class XtalPlate(Base):
    __tablename__ = "xtal_plate"
    uid: Mapped[int] = mapped_column(primary_key=True)

    # Relationships
    # Each xtal plate has one plate type
    plate_type_id: Mapped[int] = mapped_column(
        ForeignKey("xtal_plate_type.uid"))
    plate_type: Mapped["XtalPlateType"] = relationship(
        back_populates="xtal_plates")
    # Each plate has different wells
    wells: Mapped[List["XtalWell"]] = relationship(back_populates="plate")

    drop_volume: Mapped[int]
    # Metadata
    name: Mapped[str] = mapped_column(unique=True)


class XtalWellType(Base):
    __tablename__ = "xtal_well_type"
    uid: Mapped[int] = mapped_column(primary_key=True)

    # Relationship
    # A xtal plate type can have many well types
    plate_types: Mapped["XtalPlateType"] = relationship(
        secondary=xtal_ptype_wtype_association,
        back_populates="well_types",
    )
    # Each xtal plate has a shifter to echo mapping
    well_map_id: Mapped[int] = mapped_column(ForeignKey("well_map.uid"))
    well_map = relationship("WellMap", back_populates="well_types")

    # Each well has a well type
    wells: Mapped[List["XtalWell"]] = relationship(back_populates="well_type")

    # Metadata
    name: Mapped[str]


class XtalWell(Base):
    __tablename__ = "xtal_well"
    uid: Mapped[int] = mapped_column(primary_key=True)

    # Relationships
    # A drop position can be associated with multiple wells
    drop_position_uid: Mapped[int] = mapped_column(
        ForeignKey("drop_position.uid"), nullable=True
    )
    drop_position: Mapped["DropPosition"] = relationship(
        back_populates="xtal_wells")

    # Each plate has a number of wells
    plate_uid: Mapped[int] = mapped_column(
        ForeignKey("xtal_plate.uid"), nullable=True)
    plate: Mapped["XtalPlate"] = relationship(back_populates="wells")

    # Each well has one well type
    well_type_uid: Mapped[int] = mapped_column(
        ForeignKey("xtal_well_type.uid"))
    well_type: Mapped[XtalWellType] = relationship(
        "XtalWellType", back_populates="wells"
    )

    pins: Mapped[List["Pin"]] = relationship(
        secondary=pin_xtal_well_association, back_populates="xtal_well_source"
    )

    echo_transfer = relationship("EchoTransfer", back_populates="to_well")

    # Metadata
    harvesting_status: Mapped[bool] = mapped_column(default=False)
    sequence: Mapped[int] = mapped_column(nullable=False)

    # harvesting results
    time_arrival: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    harvest_comment: Mapped[str] = mapped_column(
        nullable=True
    )  # success/fail or other info about result


class DropPosition(Base):
    __tablename__ = "drop_position"
    uid: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    x_offset: Mapped[int]
    y_offset: Mapped[int]
    xtal_wells: Mapped["XtalWell"] = relationship(
        back_populates="drop_position")


@listens_for(XtalWell, "before_insert")
def increment_sequence(mapper, connection, target):
    # Retrieve the current session
    session = Session.object_session(target)

    if session:
        # Get the current maximum sequence number for the group
        current_max = (
            session.query(XtalWell.sequence)
            .filter_by(plate_uid=target.plate_uid)
            .order_by(XtalWell.sequence.desc())
            .first()
        )

        # If there's a current maximum, increment it, otherwise start from 1
        target.sequence = (current_max[0] + 1) if current_max else 1
