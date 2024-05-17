#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 13 13:58:14 2023

@author: dkreitler
"""

from .base import Base
from sqlalchemy import CheckConstraint, UniqueConstraint

from datetime import datetime
from sqlalchemy.orm import mapped_column, Mapped, relationship


class Project(Base):
    __tablename__ = "project"
    uid: Mapped[int] = mapped_column(primary_key=True)

    batches = relationship("Batch", back_populates="project")

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
            f"year >= {datetime.now().year} AND year <= {datetime.now().year+4}",
            name="valid_year_constraint",
        ),
        CheckConstraint("cycle >= 1 AND cycle <= 3",
                        name="valid_cycle_constraint"),
        CheckConstraint("visit >= 1", name="valid_visit_constraint"),
        UniqueConstraint("visit", "target"),
    )


class Status(Base):
    __tablename__ = "status"
    uid: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str]
