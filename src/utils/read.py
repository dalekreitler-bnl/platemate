from typing import List, Dict
import typing
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from sqlalchemy import func
from pandas import DataFrame
import pandas as pd

# if typing.TYPE_CHECKING:
from models import (
    LibraryWellType,
    LibraryPlateType,
    LibraryWell,
    LibraryPlate,
    XtalPlate,
    XtalPlateType,
    XtalWell,
    XtalWellType,
    DropPosition,
    Project,
    Pin,
    Puck,
    Batch,
    EchoTransfer,
)


# Library plate functions


def get_all_lib_plate_names(session: Session) -> List[str]:
    return [row.name for row in session.query(LibraryPlate).all()]


def get_lib_plate_model(session: Session, name: str) -> LibraryPlate | None:
    return session.query(LibraryPlate).filter_by(name=name).first()


def get_unused_lib_plate_wells(
    session: Session, plate: LibraryPlate
) -> List[LibraryWell]:
    """
    Returns lib plate wells that are not used and not
    part of any echo transfers, for a particular library plate
    """
    return (
        session.query(LibraryWell)
        .filter(
            LibraryWell.used == False,
            LibraryWell.plate_uid == plate.uid,
            LibraryWell.echo_transfer == None,
        )
        .order_by(LibraryWell.sequence)
        .all()
    )


# Xtal plate functions


def get_all_xtal_plate_names(session: Session, get_types=False) -> List[str]:
    model = XtalPlate
    if get_types:
        model = XtalPlateType
    return [row.name for row in session.query(model).all()]


def get_xtal_plate_model(
    session: Session, name: str, get_type=False
) -> XtalPlate | XtalPlateType | None:
    model = XtalPlate
    if get_type:
        model = XtalPlateType
    return session.query(model).filter_by(name=name).first()


def get_unused_xtal_plate_wells(session: Session, plate: XtalPlate) -> List[XtalWell]:
    """
    Returns xtal plate wells that have not been harvested and not
    part of any echo transfers, for a particular xtal plate
    """
    return (
        session.query(XtalWell)
        .filter(
            XtalWell.harvesting_status == False,
            XtalWell.plate_uid == plate.uid,
            XtalWell.echo_transfer == None,
        )
        .order_by(XtalWell.sequence)
        .all()
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


def get_latest_batch(session: Session) -> int:
    num_batches = session.query(func.max(Batch.uid)).scalar()
    if not num_batches:
        return 0
    else:
        return num_batches


def get_all_projects(session: Session):
    return session.query(Project).all()


def get_instance(session, model, **kwargs):
    return session.query(model).filter_by(**kwargs).first()


def get_or_create(session, model, **kwargs):
    """
    Tries to get an instance of a table based on kwargs,
    if it doesn't exist, creates one and returns it
    """
    instance = get_instance(session, model, **kwargs)
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance


def get_all_batches(session: Session):
    return session.query(Batch).all()
