#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug  5 19:09:04 2023

@author: dkreitler
"""
from models import Base, LibraryPlateType, LibraryWellType, LibraryPlate, LibraryWell
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import pandas

engine = create_engine("sqlite:///../test/test.db")
Session = sessionmaker(bind=engine)
session = Session()


def init_db():
    # Creating types
    lib_well_type = LibraryWellType(name="1536LDV well", smiles="C")
    lib_plate_type = LibraryPlateType(name="1536LDV", rows=100, columns=100)
    lib_plate_type.well_types.append(lib_well_type)

    lib_plate = LibraryPlate(library_plate_type=lib_plate_type, name="1536LDV #1")
    lib_well = LibraryWell(plate=lib_plate, library_well_type=lib_well_type)

    session.add_all([lib_well_type, lib_plate_type, lib_plate, lib_well])
    session.commit()


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    init_db()

"""
# populating the database
df = pandas.read_csv("~/Documents/dsip.csv")
df2 = pandas.read_csv("~/Documents/imaging.csv", skiprows=8)
df2.rename(columns={";PlateType": "PlateType"}, inplace=True)
library_plate = LibraryPlate(id=df["plate_id"][1], plate_type="1536LDV")
xtal_plate = XtalPlate(id=df2["PlateID"][1], plate_type=df2["PlateType"][1])

# 2 vertical drop plate map

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
a_to_h = ["A", "B", "C", "D", "E", "F", "G", "H"]
echo = [f"{i}{j}" for i in a_to_p for j in range(1, 17)]
shifter = [f"{i}{k}{j}" for i in a_to_h for j in ["a", "b"] for k in range(1, 13)]

plate_maps = [
    {"echo": i, "shifter": j, "plate_type": "SwissCI-MRC-2d"}
    for i, j in zip(echo, shifter)
]

[session.add(PlateMap(**plate_map)) for plate_map in plate_maps]

for index, row in df2.iterrows():
    xtal_well = XtalWell(
        well="%s%s%s" % (row["PlateRow"], row["PlateColumn"], row["PositionSubWell"]),
        plate_id=row["PlateID"],
        plate=xtal_plate,
    )
    session.add(xtal_plate)
    session.add(xtal_well)

for index, row in df.iterrows():
    library_well = LibraryWell(
        smiles=row["smiles"],
        well=row["well"],
        catalog_id=row["catalog_id"],
        plate=library_plate,
    )
    session.add(library_plate)
    session.add(library_well)

session.commit()

"""
