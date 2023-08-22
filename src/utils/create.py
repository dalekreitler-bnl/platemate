# Utility functions to create rows in different tables
from typing import List, Dict
import typing
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from pandas import DataFrame
import pandas as pd

# if typing.TYPE_CHECKING:
from models import (
    LibraryWellType,
    LibraryPlateType,
    LibraryWell,
    LibraryPlate,
    XtalPlate,
    XtalWell,
    XtalWellType,
    DropPosition,
    Pin,
    Puck,
)


def add_well_type_to_plate_type(
    session: Session,
    well_type_names: List[Dict[str, str]],
    plate_type: LibraryPlateType,
) -> None:
    """
    Adds a library well type to a library plate type
    """
    for name in well_type_names:
        lib_well_type = LibraryWellType(**name)
        session.add(lib_well_type)
        plate_type.well_types.append(lib_well_type)


def add_lib_well_to_plate(
    session: Session, df: DataFrame, lib_plate: LibraryPlate
) -> None:
    """
    Adds a library well to a library plate
    """
    for index, row in df.iterrows():
        query = None
        try:
            query = session.query(LibraryWellType).filter_by(name=row["well"]).one()
        except NoResultFound:
            print(f"No matching well type found {row['well']}, double check labware")

        if query:
            lib_well = LibraryWell(
                plate=lib_plate,
                library_well_type=query,
                catalog_id=row["catalog_id"],
                smiles=row["smiles"],
            )
            session.add(lib_well)


def add_xtal_wells_to_plate(
    session: Session, df: DataFrame, xtal_plate: XtalPlate
) -> None:
    """
    Add xtal well to xtal plate
    """
    for index, row in df.iterrows():
        shifter_well_pos = (
            f"{row['PlateRow']}{row['PlateColumn']}{row['PositionSubWell']}"
        )
        query = None
        try:
            query = session.query(XtalWellType).filter_by(name=shifter_well_pos).one()
        except NoResultFound:
            print("double check xtal plate labware!")
        if query:
            xtal_well = XtalWell(well_type=query, plate=xtal_plate)
            session.add(xtal_well)

            # now update well with drop position
            if pd.isna(row["ExternalComment"]):
                drop_position = session.query(DropPosition).filter_by(name="c").one()
                xtal_well.drop_position = drop_position
            else:
                drop_position = (
                    session.query(DropPosition)
                    .filter_by(name=row["ExternalComment"])
                    .one()
                )
                xtal_well.drop_position = drop_position


def transfer_xtal_to_pin(
    session: Session,
    xtal_well: XtalWell,
    destination_puck: str,
    pin_location: int,
    departure_time: str,
):
    puck = session.query(Puck).filter(Puck.puck_type.has(name=destination_puck)).one()
    pin = Pin(
        xtal_well_source=xtal_well,
        puck=puck,
        position=pin_location,
        time_departure=pd.to_datetime(departure_time, format="%d/%m/%Y %H:%M:%S"),
    )
    session.add(pin)
    xtal_well.pins.append(pin)
