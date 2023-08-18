from .base import Base
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Table,
)
from sqlalchemy.orm import relationship, mapped_column, Mapped
from typing import List, Optional

lib_ptype_wtype_association = Table(
    "lib_ptype_wtype",
    Base.metadata,
    Column("plate_type_uid", Integer, ForeignKey("library_plate_type.uid")),
    Column("well_type_uid", Integer, ForeignKey("library_well_type.uid")),
)


class LibraryPlateType(Base):
    __tablename__ = "library_plate_type"
    uid: Mapped[int] = mapped_column(primary_key=True)

    # Relationships
    # Multiple library plate types can have multiple well types
    well_types: Mapped[List["LibraryWellType"]] = relationship(
        secondary=lib_ptype_wtype_association,
        back_populates="library_plate_type",
    )
    # Plates related to this type
    library_plates: Mapped[List["LibraryPlate"]] = relationship(
        back_populates="library_plate_type"
    )

    # Metadata
    name: Mapped[str]
    rows: Mapped[Optional[int]]
    columns: Mapped[Optional[int]]


class LibraryPlate(Base):
    __tablename__ = "library_plate"
    uid: Mapped[int] = mapped_column(primary_key=True)

    # Relationships
    # Every plate has a related plate type
    library_plate_type_uid: Mapped[int] = mapped_column(
        ForeignKey("library_plate_type.uid")
    )
    library_plate_type: Mapped["LibraryPlateType"] = relationship(
        back_populates="library_plates"
    )
    wells: Mapped[List["LibraryWell"]] = relationship(back_populates="plate")

    # Metadata
    name: Mapped[str]


class LibraryWellType(Base):
    __tablename__ = "library_well_type"
    uid: Mapped[int] = mapped_column(primary_key=True)

    # Relationships
    # Well types can be shared between different plate types, therefore many-to-many
    library_plate_type: Mapped[List["LibraryPlateType"]] = relationship(
        secondary=lib_ptype_wtype_association,
        back_populates="well_types",
    )
    # Multiple wells can have the same type, therefore many-to-one
    library_wells: Mapped[List["LibraryWell"]] = relationship(
        back_populates="library_well_type"
    )

    # Metadata
    name: Mapped[str]


class LibraryWell(Base):
    __tablename__ = "library_well"
    uid: Mapped[int] = mapped_column(primary_key=True)

    # Metadata
    # Multiple wells belong to the same plate. Therefore many-to-one
    plate_uid: Mapped[int] = mapped_column(ForeignKey("library_plate.uid"))
    plate: Mapped["LibraryPlate"] = relationship(back_populates="wells")
    # Multiple wells have the same type, therefore many-to-one
    library_well_type_uid: Mapped[int] = mapped_column(
        ForeignKey("library_well_type.uid")
    )
    library_well_type: Mapped["LibraryWellType"] = relationship(
        back_populates="library_wells"
    )

    # Relationships
    used: Mapped[bool] = mapped_column(default=False)
    catalog_id: Mapped[str]
    smiles: Mapped[str]

    sequence: Mapped[int]
