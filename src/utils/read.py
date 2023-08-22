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


def get_xtal_well(session: Session, plate_name: str, shifter_well_pos: str) -> XtalWell:
    return (
        session.query(XtalWell)
        .filter(
            XtalWell.plate.has(name=plate_name),
            XtalWell.well_type.has(name=shifter_well_pos),
        )
        .one()
    )
