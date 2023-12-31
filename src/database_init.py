#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug  5 19:09:04 2023

@author: dkreitler
"""
from models import (
    Base,
    Project,
    LibraryPlateType,
    LibraryWellType,
    LibraryPlate,
    LibraryWell,
    XtalPlate,
    XtalPlateType,
    XtalWellType,
    XtalWell,
    WellMap,
    Batch,
    DropPosition,
    EchoTransfer,
    XrayStatusEnum,
    PuckType,
    Puck,
    Pin,
)
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm.exc import NoResultFound
import pandas

engine = create_engine("sqlite:///../test/test2.db")
Session = sessionmaker(bind=engine)
session = Session()


def init_db():
    # define project
    project = Project(target="mpro", year=2023, cycle=2, visit=1)
    session.add(project)

    # Creating types
    # Create the library labware (dsip)
    lib_plate_type = LibraryPlateType(name="1536LDV", rows=32, columns=48)

    a_to_af = [
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "I",
        "J",
        "K",
        "L",
        "M",
        "N",
        "O",
        "P",
        "Q",
        "R",
        "S",
        "T",
        "U",
        "V",
        "W",
        "X",
        "Y",
        "Z",
        "AA",
        "AB",
        "AC",
        "AD",
        "AE",
        "AF",
    ]

    lib_well_type_names = [
        {"name": f"{i}{str(j).zfill(2)}"} for i in a_to_af for j in range(1, 49)
    ]

    for name in lib_well_type_names:
        lib_well_type = LibraryWellType(**name)
        session.add(lib_well_type)
        lib_plate_type.well_types.append(lib_well_type)

    lib_plate = LibraryPlate(library_plate_type=lib_plate_type, name="DSI-poised")

    session.add_all([lib_plate_type, lib_plate])

    # fill the library wells, column by column
    df = pandas.read_csv("../test/dsip.csv")
    sequence = session.query(func.max(LibraryWell.sequence)).scalar() or 0
    for index, row in df.iterrows():
        try:
            query = session.query(LibraryWellType).filter_by(name=row["well"]).one()
        except NoResultFound:
            print(f"No matching well type found {row['well']}, double check labware")

        lib_well = LibraryWell(
            plate=lib_plate,
            library_well_type=query,
            catalog_id=row["catalog_id"],
            smiles=row["smiles"],
            sequence=sequence,
        )
        sequence += 1
        session.add(lib_well)

    # Create xtallization labware, subsequent objects are for MRC-2d geometry
    xtal_plate_type = XtalPlateType(name="SwissCI-MRC-2d")
    session.add(xtal_plate_type)

    a_to_h = ["A", "B", "C", "D", "E", "F", "G", "H"]
    a_to_p = [
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "I",
        "J",
        "K",
        "L",
        "M",
        "N",
        "O",
        "P",
    ]

    echo = [f"{i}{j}" for i in a_to_p for j in range(1, 17)]
    shifter = [f"{i}{k}{j}" for i in a_to_h for j in ["a", "b"] for k in range(1, 13)]

    plate_maps = [{"echo": i, "shifter": j} for i, j in zip(echo, shifter)]

    for plate_map in plate_maps:
        x_offset = 0
        if plate_map["shifter"][-1] == "b":
            y_offset = 1350  # microns
        else:
            y_offset = 0
        well_map = WellMap(well_pos_x=x_offset, well_pos_y=y_offset, **plate_map)
        session.add(well_map)
        xtal_well_type = XtalWellType(name=plate_map["shifter"], well_map=well_map)
        session.add(xtal_well_type)

    # Create instance of a plate with crystals, update with shifter csv

    imaging_df = pandas.read_csv("../test/imaging.csv", skiprows=8)
    # shifter app leaves semi-colons in front of all header text, fix that
    # add some light spreadsheet validation (unique plate_ids)
    imaging_df.rename(columns={";PlateType": "PlateType"}, inplace=True)
    unique_plate_ids = imaging_df["PlateID"].unique()
    if len(unique_plate_ids) != 1:
        raise ValueError("inconsistent plateIDs; plateIDs should all be the same")

    xtal_plate = XtalPlate(plate_type=xtal_plate_type, name=unique_plate_ids[0])
    session.add(xtal_plate)

    """
    Drop positions:
    Partition the well into a 9-member grid
    u = up
    d = down
    l = left
    r = right
    c = center

     ul/lu |   u   | ur/ru
    _______________________
       l   |   c   |   r
    _______________________
     dl/ld |   d   | dr/rd

    """
    drop_position_codes = [
        {"name": "ul", "x_offset": -300, "y_offset": 300},
        {"name": "lu", "x_offset": -300, "y_offset": 300},
        {"name": "u", "x_offset": 0, "y_offset": 300},
        {"name": "ru", "x_offset": 300, "y_offset": 300},
        {"name": "ur", "x_offset": 300, "y_offset": 300},
        {"name": "l", "x_offset": -300, "y_offset": 0},
        {"name": "c", "x_offset": 0, "y_offset": 0},
        {"name": "r", "x_offset": 300, "y_offset": 0},
        {"name": "dl", "x_offset": -300, "y_offset": -300},
        {"name": "ld", "x_offset": -300, "y_offset": -300},
        {"name": "dr", "x_offset": 300, "y_offset": -300},
        {"name": "rd", "x_offset": 300, "y_offset": -300},
        {"name": "d", "x_offset": -300, "y_offset": 0},
    ]

    session.add_all(
        [
            DropPosition(**drop_position_code)
            for drop_position_code in drop_position_codes
        ]
    )

    sequence = session.query(func.max(XtalWell.sequence)).scalar() or 0
    for index, row in imaging_df.iterrows():
        shifter_well_pos = (
            f"{row['PlateRow']}{row['PlateColumn']}{row['PositionSubWell']}"
        )
        try:
            query = session.query(XtalWellType).filter_by(name=shifter_well_pos).one()
        except NoResultFound:
            print("double check xtal plate labware!")
        xtal_well = XtalWell(well_type=query, plate=xtal_plate, sequence=sequence)
        sequence += 1
        session.add(xtal_well)

        # now update well with drop position
        if pandas.isna(row["ExternalComment"]):
            drop_position = session.query(DropPosition).filter_by(name="c").one()
            xtal_well.drop_position = drop_position
        else:
            drop_position = (
                session.query(DropPosition).filter_by(name=row["ExternalComment"]).one()
            )
            xtal_well.drop_position = drop_position

    # create a batch
    batch = Batch()
    session.add(batch)

    # populate transfers
    # need to ensure that we go row by row through xtal plate, column
    # by column through library plate to minimize xy motions during transfer
    # added sequence column to well tables to enforce this ordering
    xtal_well_query = (
        session.query(XtalWell)
        .order_by(XtalWell.sequence)
        .filter(XtalWell.plate.has(name="pmtest"))
    )

    library_well_query = (
        session.query(LibraryWell)
        .order_by(LibraryWell.sequence)
        .filter(LibraryWell.plate.has(name="DSI-poised"))
    )

    for xtal_well, library_well in zip(xtal_well_query, library_well_query):
        transfer = EchoTransfer(
            batch=batch, from_well=library_well, to_well=xtal_well, transfer_volume=25
        )
        session.add(transfer)

    # prepare to ingest shifter harvesting csv
    # make sure there are pucks (and puck_types)
    puck_names = [{"name": name} for name in ["testpuck", "FGZ001", "FGZ002"]]
    session.add_all([PuckType(**puck_name) for puck_name in puck_names])

    harvesting_df = pandas.read_csv("../test/harvesting.csv", skiprows=8)
    harvesting_df.rename(columns={";PlateType": "PlateType"}, inplace=True)

    puck_types = [
        {"puck_type": session.query(PuckType).filter_by(name=k).one()}
        for k in harvesting_df["DestinationName"].dropna().unique()
    ]
    pucks = [Puck(**puck_type) for puck_type in puck_types]
    session.add_all(pucks)

    for index, row in harvesting_df.iterrows():
        # this entry will be populated if something happened at the well,
        # successful or not
        if pandas.notna(row["Comment"]):
            shifter_well_pos = (
                f"{row['PlateRow']}{row['PlateColumn']}{row['PositionSubWell']}"
            )
            print(row)
            xtal_well = (
                session.query(XtalWell)
                .filter(
                    XtalWell.plate.has(name=row["PlateID"]),
                    XtalWell.well_type.has(name=shifter_well_pos),
                )
                .one()
            )
            xtal_well.harvest_comment = row["Comment"]
            xtal_well.harvesting_status = True
            xtal_well.time_arrival = pandas.to_datetime(
                row["TimeArrival"], format="%d/%m/%Y %H:%M:%S"
            )
            echo_transfer = (
                session.query(EchoTransfer)
                .filter(EchoTransfer.to_well_id == xtal_well.uid)
                .one()
            )
            library_well = echo_transfer.from_well
            library_well.used = True

            # this entry will only be populated if the pin made it into the puck
            if pandas.notna(row["DestinationLocation"]):
                puck = (
                    session.query(Puck)
                    .filter(Puck.puck_type.has(name=row["DestinationName"]))
                    .one()
                )
                pin = Pin(
                    xtal_well_source=xtal_well,
                    puck=puck,
                    position=row["DestinationLocation"],
                    time_departure=pandas.to_datetime(
                        row["TimeDeparture"], format="%d/%m/%Y %H:%M:%S"
                    ),
                )
                session.add(pin)
                xtal_well.pins.append(pin)

    session.commit()


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    init_db()
    write_echo_csv()
