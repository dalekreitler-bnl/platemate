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
    session: Session, plate: LibraryPlate, include_used=False
) -> List[LibraryWell]:
    """
    Returns lib plate wells that are not used and not
    part of any echo transfers, for a particular library plate
    """
    query = session.query(LibraryWell).filter(
        LibraryWell.plate_uid == plate.uid,
    )
    if not include_used:
        query = query.filter(
            LibraryWell.used == False,
            LibraryWell.echo_transfer == None,
        )

    return query.order_by(LibraryWell.sequence).all()


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


def summarize(session: Session) -> DataFrame:
    """
    Summarize mounted pins and return the results as a pandas DataFrame.

    Parameters
    ----------
    session : sqlalchemy.orm Session
        The SQLAlchemy Session object connected to the database.

    Returns
    -------
    df : pandas.DataFrame
        Tabular summary of successfully mounted pins, includes columns:
        - 'pin_uid': Unique identifier for each pin.
        - 'xtal_plate': Name of the crystal plate.
        - 'xtal_well_type': Type of the crystal well.
        - 'lsdc_sample_name': Sample name combining the project target and pin UID.
        - 'catalog_id': Catalog ID of the library well.
        - 'smiles': SMILES notation of the library well.
        - 'soak_min': Soak time in minutes.
        - 'harvest_sec': Harvest time in seconds.
    """

    result = (
        session.query(
            Pin,
            XtalWell,
            XtalPlate,
            XtalWellType,
            EchoTransfer,
            LibraryWell,
            Batch,
            Project,
        )
        .join(XtalWell, Pin.xtal_well_source_id == XtalWell.uid)
        .join(XtalPlate, XtalWell.plate_uid == XtalPlate.uid)
        .join(XtalWellType, XtalWell.well_type_uid == XtalWellType.uid)
        .join(EchoTransfer, XtalWell.uid == EchoTransfer.to_well_id)
        .join(LibraryWell, EchoTransfer.from_well_id == LibraryWell.uid)
        .join(Batch, EchoTransfer.batch_id == Batch.uid)
        .join(Project, Batch.project_id == Project.uid)
        .all()
    )

    df = DataFrame()
    for row in result:
        (
            pin,
            xtal_well,
            xtal_plate,
            xtal_well_type,
            echo_transfer,
            library_well,
            batch,
            project,
        ) = row

        row_entry = {
            "pin_uid": pin.uid,
            "xtal_plate": xtal_plate.name,
            "xtal_well_type": xtal_well_type.name,
            "lsdc_sample_name": f"{project.target}-{pin.uid}",
            "catalog_id": library_well.catalog_id,
            "smiles": library_well.smiles,
            "soak_min": round(
                (pin.time_departure.timestamp() -
                 batch.timestamp.timestamp()) / 60, 1
            ),
            "harvest_sec": round(
                (pin.time_departure.timestamp() -
                 xtal_well.time_arrival.timestamp()), 1
            ),
        }
        new_df = DataFrame([row_entry])
        df = pd.concat([df, new_df], ignore_index=True)
    return df
