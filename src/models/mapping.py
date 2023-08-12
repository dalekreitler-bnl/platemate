from .base import Base
import enum
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    CheckConstraint,
    String,
    ForeignKey,
    Enum,
    Boolean,
    DateTime
)
from datetime import datetime
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
import pandas


class WellMap(Base):
    __tablename__ = "well_map"
    uid = Column(Integer, primary_key=True)

    # Relationships
    # Each well type has one well map
    well_types = relationship("XtalWellType", back_populates="well_map")

    # Metadata
    well_pos_x = Column(Integer, nullable=False)
    well_pos_y = Column(Integer, nullable=False)
    echo = Column(String, nullable=False)
    shifter = Column(String, nullable=False)


class Batch(Base):
    __tablename__ = "batch"
    uid = Column(Integer, primary_key=True)

    # Relationships
    echo_transfers = relationship("EchoTransfer", back_populates="batch")

    # Metadata, if user forgets to manually update this is our upper bound
    timestamp = Column(DateTime, default=datetime.now())


class EchoTransfer(Base):
    __tablename__ = "echo_transfer"
    uid = Column(Integer, primary_key=True)

    # Relationships
    batch_id = Column(Integer, ForeignKey("batch.uid"), nullable=False)
    batch = relationship("Batch", back_populates="echo_transfers")

    from_well_id = Column(Integer, ForeignKey("library_well.uid"))
    from_well = relationship("LibraryWell")

    to_well_id = Column(Integer, ForeignKey("xtal_well.uid"))
    to_well = relationship("XtalWell")

    transfer_volume = Column(
        Integer,
        CheckConstraint("transfer_volume >= 5 AND transfer_volume <= 150"),
        nullable=False
    )

    # update when the transfer actually occurs
    timestamp = Column(DateTime, nullable=True)
