from ipywidgets import (
    Tab,
    SelectMultiple,
    Accordion,
    ToggleButton,
    VBox,
    HBox,
    HTML,
    IntText,
    Button,
    Layout,
    Dropdown,
    IntSlider,
    Text,
    FileUpload,
    Output,
)
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from typing import List

from models import LibraryWell, XtalWell, XtalPlate
from utils.read import get_all_xtal_plate_names, get_xtal_plate_model
from utils.create import add_xtal_wells_to_plate
import io
import pandas as pd


class XtalPlateCreatorWidget:
    def __init__(self, session: Session):
        self.session = session
        self._init_ui()

    def _init_ui(self):
        self.output_widget = Output()
        xtal_plate_types = get_all_xtal_plate_names(
            self.session, get_types=True)
        self.xtal_plate_types_dropdown = Dropdown(
            options=xtal_plate_types,
            description="Xtal plate type:",
            disabled=False,
            style=dict(description_width="initial"),
        )
        self.imaging_file_upload = FileUpload(
            description="Upload imaging file:",
            accept=".csv",
            multiple=False,
            style=dict(description_width="initial"),
        )
        self.create_xtal_plate_button = Button(
            description="Import Shifter Data", layout=Layout(width="200px")
        )
        self.create_xtal_plate_button.on_click(
            self.create_xtal_plate_button_triggered)
        self.widget_row = HBox(
            [self.xtal_plate_types_dropdown, self.imaging_file_upload]
        )
        self.vbox = VBox(
            [self.widget_row, self.create_xtal_plate_button, self.output_widget]
        )

    def create_xtal_plate_button_triggered(self, state):
        self.df = None
        if self.imaging_file_upload.value:
            try:
                uploaded_file = self.imaging_file_upload.value[0]
                self.df = pd.read_csv(io.BytesIO(
                    uploaded_file.content), skiprows=8)
                # shifter app leaves semi-colons in front of all header text, fix that
                # add some light spreadsheet validation (unique plate_ids)
                self.df.rename(
                    columns={";PlateType": "PlateType"}, inplace=True)
                unique_plate_ids = self.df["PlateID"].unique()
                if len(unique_plate_ids) != 1:
                    with self.output_widget:
                        print(
                            "Inconsistent plateIDs; plateIDs should all be the same")
                        return
                xtal_plate_type = get_xtal_plate_model(
                    self.session, self.xtal_plate_types_dropdown.value, get_type=True
                )
                xtal_plate = XtalPlate(
                    plate_type=xtal_plate_type, name=unique_plate_ids[0]
                )
                # add xtal_plate to db
                self.session.add(xtal_plate)
                try:
                    self.session.commit()
                except IntegrityError:
                    with self.output_widget:
                        print(
                            "Error uploading imaging file: "
                            f"Xtal plate named {unique_plate_ids[0]} already exists in the database."
                        )
                        return

                # now add xtal wells to xtal plate
                add_xtal_wells_to_plate(self.session, self.df, xtal_plate)
                self.session.commit()
                with self.output_widget:
                    print("Successfully uploaded imaging file")
                    print(
                        f"xtal_plate: {xtal_plate.name}, no. wells: {len(xtal_plate.wells)}")
            except Exception as e:
                with self.output_widget:
                    print(f"Exception type: {type(e).__name__}")
                    print(f"Exception while reading file: {e}")

    @property
    def ui(self):
        return self.vbox
