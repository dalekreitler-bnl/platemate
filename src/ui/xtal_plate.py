import io
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from ipywidgets import Button, Dropdown, FileUpload, HBox, IntText, Layout, Output, VBox
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import XtalPlate
from utils.create import add_xtal_wells_to_plate
from utils.read import get_all_xtal_plate_names, get_xtal_plate_model


class XtalPlateCreatorWidget:
    def __init__(self, session: Session, data_directory: Optional[Path] = None):
        self.session = session
        self.data_directory = data_directory
        self._init_ui()

    def _init_ui(self):
        self.output_widget = Output()
        xtal_plate_types = get_all_xtal_plate_names(self.session, get_types=True)
        self.xtal_plate_types_dropdown = Dropdown(
            options=xtal_plate_types,
            description="Xtal plate type:",
            disabled=False,
            style=dict(description_width="initial"),
        )
        self.drop_volume = IntText(
            description="Est. drop vol. (nl)",
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
        self.create_xtal_plate_button.on_click(self.create_xtal_plate_button_triggered)
        self.widget_row = HBox(
            [self.xtal_plate_types_dropdown, self.drop_volume, self.imaging_file_upload]
        )
        self.vbox = VBox(
            [self.widget_row, self.create_xtal_plate_button, self.output_widget]
        )

    def get_rows_to_skip(self, csv_buffer):
        csv_buffer.seek(0)
        skiprows = 0
        for line in csv_buffer:
            if line.startswith(b";"):
                skiprows += 1
            else:
                break
        return skiprows - 1

    def strip_brackets(self, value):
        if isinstance(value, str):
            return value.strip("[]")
        return value

    def create_xtal_plate_button_triggered(self, state):
        self.df = None
        if self.imaging_file_upload.value:
            try:
                uploaded_file = self.imaging_file_upload.value[0]
                csv_buffer = io.BytesIO(uploaded_file.content)
                skiprows = self.get_rows_to_skip(csv_buffer)
                csv_buffer.seek(0)
                self.df = pd.read_csv(csv_buffer, skiprows=skiprows)
                # shifter app leaves semi-colons in front of all header text, fix that
                # add some light spreadsheet validation (unique PlateIDs, PlateTypes)

                self.df.rename(columns={";PlateType": "PlateType"}, inplace=True)
                unique_plate_types = self.df["PlateType"].unique()

                if len(unique_plate_types) != 1:
                    with self.output_widget:
                        print("problem with spreadsheet, multiple PlateTypes detected")
                        return
                if unique_plate_types[0] != self.xtal_plate_types_dropdown.value:
                    with self.output_widget:
                        print(
                            "Mismatch between selected PlateType and spreadsheet PlateType"
                        )
                        return

                unique_plate_ids = self.df["PlateID"].unique()
                if len(unique_plate_ids) != 1:
                    with self.output_widget:
                        print("Inconsistent PlateIDs; PlateIDs should all be the same")
                        return

                # Apply the function to the 'ExternalComment' column
                self.df["ExternalComment"] = self.df["ExternalComment"].apply(
                    self.strip_brackets
                )

                xtal_plate_type = get_xtal_plate_model(
                    self.session, self.xtal_plate_types_dropdown.value, get_type=True
                )
                xtal_plate = XtalPlate(
                    plate_type=xtal_plate_type, name=unique_plate_ids[0]
                )

                if self.drop_volume.value < 20:
                    with self.output_widget:
                        print("Drop volume less than 20 nL not allowed.")
                        return
                else:
                    xtal_plate.drop_volume = self.drop_volume.value

                # add xtal_plate to db
                self.session.add(xtal_plate)

                try:
                    self.session.commit()
                except IntegrityError:
                    self.session.rollback()
                    with self.output_widget:
                        print(
                            "Error uploading imaging file: "
                            f"Xtal plate named {unique_plate_ids[0]} already exists in the database."
                        )
                        return

                # now add xtal wells to xtal plate
                add_xtal_wells_to_plate(self.session, self.df, xtal_plate)
                self.session.commit()
                self.write_df_to_csv(uploaded_file)
                with self.output_widget:
                    print("Successfully uploaded imaging file")
                    print(
                        f"xtal_plate: {xtal_plate.name}, no. wells: {len(xtal_plate.wells)}"
                    )
            except Exception as e:
                with self.output_widget:
                    print(f"Exception type: {type(e).__name__}")
                    print(f"Exception while reading file: {e}")

    @property
    def ui(self):
        return self.vbox

    def write_df_to_csv(self, uploaded_file):
        # Dump the dataframe into a csv file
        if self.data_directory and self.df is not None:
            imaging_dir = self.data_directory / Path("imaging")
            imaging_dir.mkdir(parents=True, exist_ok=True)
            # Get the current timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            uploaded_filename = Path(uploaded_file.name)
            new_filename = Path(
                f"{uploaded_filename.stem}_{timestamp}{uploaded_filename.suffix}"
            )

            self.df.to_csv(imaging_dir / new_filename)
