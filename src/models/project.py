#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 13 13:58:14 2023

@author: dkreitler
"""

from .base import Base
from sqlalchemy import CheckConstraint

from datetime import datetime
from sqlalchemy.orm import mapped_column, Mapped


class Project(Base):
    __tablename__ = "project"
    uid: Mapped[int] = mapped_column(primary_key=True)

    # used for xtal naming
    target: Mapped[str] = mapped_column(nullable=False)

    # useful for checking directory tree
    proposal_id: Mapped[int] = mapped_column(nullable=True)
    year: Mapped[int]
    cycle: Mapped[int]
    visit: Mapped[int]

    # simple checks
    __table_args__ = (
        CheckConstraint(
            f"year >= 2023 AND year <= {datetime.now().year}",
            name="valid_year_constraint",
        ),
        CheckConstraint("cycle >= 1 AND cycle <= 3", name="valid_cycle_constraint"),
        CheckConstraint("visit >= 1", name="valid_visit_constraint"),
    )


class Status(Base):
    __tablename__ = "status"
    uid: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str]
