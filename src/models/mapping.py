from .base import Base
from sqlalchemy import CheckConstraint, ForeignKey

from datetime import datetime
from .xtal_plate import XtalWellType, XtalWell
from .library_plate import LibraryWell
from sqlalchemy.orm import relationship, mapped_column, Mapped
from typing import List


class WellMap(Base):
    __tablename__ = "well_map"
    uid: Mapped[int] = mapped_column(primary_key=True)

    # Relationships
    # Each well type has one well map
    well_types: Mapped[List["XtalWellType"]] = relationship(back_populates="well_map")

    # Metadata
    well_pos_x: Mapped[int]
    well_pos_y: Mapped[int]
    echo: Mapped[str]
    shifter: Mapped[str]


class Batch(Base):
    __tablename__ = "batch"
    uid: Mapped[int] = mapped_column(primary_key=True)

    # Relationships
    echo_transfers: Mapped[List["EchoTransfer"]] = relationship(back_populates="batch")

    # Metadata, if user forgets to manually update this is our upper bound
    timestamp: Mapped[datetime] = mapped_column(default=datetime.now())
    name: Mapped[str]


class EchoTransfer(Base):
    __tablename__ = "echo_transfer"
    uid: Mapped[int] = mapped_column(primary_key=True)

    # Relationships
    batch_id: Mapped[int] = mapped_column(ForeignKey("batch.uid"))
    batch: Mapped["Batch"] = relationship(back_populates="echo_transfers")

    from_well_id: Mapped[int] = mapped_column(ForeignKey("library_well.uid"))
    from_well: Mapped["LibraryWell"] = relationship("LibraryWell")

    to_well_id: Mapped[int] = mapped_column(ForeignKey("xtal_well.uid"))
    to_well: Mapped["XtalWell"] = relationship("XtalWell")

    transfer_volume: Mapped[int] = mapped_column(
        CheckConstraint("transfer_volume >= 5 AND transfer_volume <= 150"),
        nullable=False,
    )

    # update when the transfer actually occurs
    timestamp: Mapped[datetime] = mapped_column(nullable=True)
