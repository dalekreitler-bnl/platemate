from .base import Base
import enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped
from datetime import datetime
from typing import List, Optional


class XrayStatusEnum(enum.Enum):
    not_collected = 1
    collection_succeeded = 2
    collection_failed = 3


class PuckType(Base):
    __tablename__ = "puck_type"
    uid: Mapped[int] = mapped_column(primary_key=True)

    # relationships
    pucks: Mapped[List["Puck"]] = relationship("Puck", back_populates="puck_type")
    # Metadata
    name: Mapped[Optional[str]]


class Puck(Base):
    __tablename__ = "puck"
    uid: Mapped[int] = mapped_column(primary_key=True)

    puck_type_uid: Mapped[int] = mapped_column(ForeignKey("puck_type.uid"))
    puck_type: Mapped["PuckType"] = relationship(back_populates="pucks")

    pins: Mapped[List["Pin"]] = relationship(back_populates="puck")

    timestamp: Mapped[datetime] = mapped_column(default=datetime.now())
    proposal_id: Mapped[int]


class Pin(Base):
    __tablename__ = "pin"
    uid: Mapped[int] = mapped_column(primary_key=True)

    puck_uid: Mapped[int] = mapped_column(ForeignKey("puck.uid"))
    puck: Mapped["Puck"] = relationship(back_populates="pins")

    position: Mapped[int]  # 1 through 16
    xtal_well_source_id: Mapped[int] = mapped_column(
        ForeignKey("xtal_well.uid")
    )  # Xtal well source
    xtal_well_source = relationship("XtalWell", back_populates="pins")

    parent_pin_id: Mapped[int] = mapped_column(ForeignKey("pin.uid"), nullable=True)
    parent: Mapped["Pin"] = relationship(back_populates="children", remote_side=[uid])
    children: Mapped[List["Pin"]] = relationship(back_populates="parent")

    time_departure: Mapped[datetime]  # harvest/freeze time

    lsdc_sample_name: Mapped[Optional[str]]
