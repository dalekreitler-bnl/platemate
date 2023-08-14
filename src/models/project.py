#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 13 13:58:14 2023

@author: dkreitler
"""

from .base import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    CheckConstraint
)

from datetime import datetime


class Project(Base):
    __tablename__ = "project"
    uid = Column(Integer, primary_key=True)

    # used for xtal naming
    target = Column(String, nullable=False)

    # useful for checking directory tree
    proposal_id = Column(Integer)
    year = Column(Integer)
    cycle = Column(Integer)
    visit = Column(Integer)

    # simple checks
    __table_args__ = (
        CheckConstraint(
            f"year >= 2023 AND year <= {datetime.now().year}",
            name="valid_year_constraint"
        ),
        CheckConstraint(
            "cycle >= 1 AND cycle <= 3",
            name="valid_cycle_constraint"
        ),
        CheckConstraint(
            "visit >= 1",
            name="valid_visit_constraint"
        )
    )
