#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug  5 19:09:04 2023

@author: dkreitler
"""

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
import pandas

engine = create_engine("sqlite:///test3.db")
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


class LibraryPlate(Base):
    __tablename__ = "library_plate"
    id = Column(String, primary_key=True)
    wells = relationship("LibraryWell", back_populates="plate")
    plate_type = Column(String, nullable=False)


class LibraryWell(Base):
    __tablename__ = "library_well"
    id = Column(Integer, primary_key=True)
    smiles = Column(String, nullable=False)
    well = Column(String, nullable=False)
    catalog_id = Column(String, nullable=False)
    plate_id = Column(Integer, ForeignKey("library_plate.id"))
    plate = relationship("LibraryPlate", back_populates="wells")


class XtalPlate(Base):
    __tablename__ = "xtal_plate"
    id = Column(String, primary_key=True)
    plate_type = Column(String, nullable=False)
    wells = relationship("XtalWell", back_populates="plate")


class XtalWell(Base):
    __tablename__ = "xtal_well"
    id = Column(Integer, primary_key=True)
    well = Column(String, nullable=False)
    position = Column(String)
    plate_id = Column(String, ForeignKey("xtal_plate.id"))
    plate = relationship("XtalPlate", back_populates="wells")


class PlateMap(Base):
    __tablename__ = "plate_map"
    id = Column(Integer, primary_key=True)
    echo = Column(String, nullable=False)
    shifter = Column(String, nullable=False)
    plate_type = Column(String, nullable=False)


Base.metadata.create_all(engine)


# populating the database
df = pandas.read_csv("~/Documents/dsip.csv")
df2 = pandas.read_csv("~/Documents/imaging.csv", skiprows=8)
df2.rename(columns={";PlateType": "PlateType"}, inplace=True)
library_plate = LibraryPlate(id=df["plate_id"][1], plate_type="1536LDV")
xtal_plate = XtalPlate(id=df2["PlateID"][1], plate_type=df2["PlateType"][1])

#2 vertical drop plate map

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
