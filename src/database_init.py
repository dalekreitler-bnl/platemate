#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug  5 19:09:04 2023

@author: dkreitler
"""
from models import (
    Base,
    LibraryPlateType,
    LibraryWellType,
    LibraryPlate,
    LibraryWell,
    XtalPlate,
    XtalPlateType,
    XtalWellType,
    XtalWell,
    WellMap
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm.exc import NoResultFound
import pandas

engine = create_engine("sqlite:///../test/test2.db")
Session = sessionmaker(bind=engine)
session = Session()


def init_db():
    # Creating types
    # Create the library labware (dsip)
    lib_plate_type = LibraryPlateType(name="1536LDV", rows=32, columns=48)

    a_to_af = [
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
        "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
        "U", "V", "W", "X", "Y", "Z", "AA", "AB", "AC", "AD",
        "AE", "AF"
    ]

    lib_well_type_names = [
        {"name": f"{i}{str(j).zfill(2)}"} for i in a_to_af for j in range(1, 49)]

    for name in lib_well_type_names:
        lib_well_type = LibraryWellType(**name)
        session.add(lib_well_type)
        lib_plate_type.well_types.append(lib_well_type)

    lib_plate = LibraryPlate(
        library_plate_type=lib_plate_type, name="DSI-poised")

    session.add_all([lib_plate_type, lib_plate])

    # fill the library wells
    df = pandas.read_csv("~/Documents/dsip.csv")
    for index, row in df.iterrows():
        try:
            query = session.query(LibraryWellType).filter_by(
                name=row['well']).one()
        except NoResultFound:
            print("No matching well type found, double check labware")

        lib_well = LibraryWell(plate=lib_plate, library_well_type=query,
                               catalog_id=row['catalog_id'], smiles=row['smiles'])
        session.add(lib_well)

    # Create xtallization labware, subsequent objects are for MRC-2d geometry
    xtal_plate_type = XtalPlateType(name="SwissCI-MRC-2d")
    session.add(xtal_plate_type)

    a_to_h = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    a_to_p = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
              'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']

    echo = [f"{i}{j}" for i in a_to_p for j in range(1, 17)]
    shifter = [f"{i}{k}{j}" for i in a_to_h for j in ["a", "b"]
               for k in range(1, 13)]

    plate_maps = [
        {"echo": i, "shifter": j}
        for i, j in zip(echo, shifter)
    ]

    for plate_map in plate_maps:
        x_offset = 0
        if plate_map['shifter'][-1] == 'b':
            y_offset = 1350  # microns
        else:
            y_offset = 0
        well_map = WellMap(well_pos_x=x_offset,
                           well_pos_y=y_offset, **plate_map)
        session.add(well_map)
        xtal_well_type = XtalWellType(
            name=plate_map['shifter'], well_map=well_map)
        session.add(xtal_well_type)

    # Create instance of a plate with crystals, update with shifter csv

    imaging_df = pandas.read_csv("../test/imaging.csv", skiprows=8)
    # shifter app leaves semi-colons in front of all header text, fix that
    imaging_df.rename(columns={";PlateType": "PlateType"}, inplace=True)
    unique_plate_ids = imaging_df["PlateID"].unique()
    if len(unique_plate_ids) != 1:
        raise ValueError(
            "inconsistent plateIDs; plateIDs should all be the same")

    xtal_plate = XtalPlate(plate_type=xtal_plate_type,
                           name=unique_plate_ids[0])
    session.add(xtal_plate)

    for index, row in imaging_df.iterrows():
        shifter_well_pos = f"{row['PlateRow']}{row['PlateColumn']}{row['PositionSubWell']}"
        try:
            query = session.query(XtalWellType).filter_by(
                name=shifter_well_pos).one()
        except NoResultFound:
            print("double check xtal plate labware!")
        xtal_well = XtalWell(well_type=query, plate=xtal_plate)
        session.add(xtal_well)

    #lib_well = LibraryWell(plate=lib_plate, library_well_type=lib_well_type)

    '''
        # populating the database
        # 1. populate library plates <- dsip.csv
        # 2. populate xtal plates <- imaging.csv
        # 3. populate mappings <- create these on the fly
        # 4. populate pucks/pins <- harvesting.csv
        df = pandas.read_csv("~/Documents/dsip.csv")
    
        for index, row in df.iterrows():
            library_well = LibraryWell(
                smiles=row["smiles"],
                well=row["well"],
                catalog_id=row["catalog_id"],
                plate=lib_plate,
            )
            session.add(library_well)
    '''
    session.commit()


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    init_db()
