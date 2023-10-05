from ipywidgets import (
    Tab,
    SelectMultiple,
    Accordion,
    ToggleButton,
    VBox,
    HBox,
    HTML,
    Output,
    Button,
    Layout,
    Dropdown,
    IntSlider,
    Text,
    FileUpload,
)
from pathlib import Path
from sqlalchemy.orm import Session
from typing import List
from models import PuckType, EchoTransfer
from utils.read import get_xtal_well
from utils.create import transfer_xtal_to_pin, make_pucks
import pandas as pd
import io
import traceback


class IngestHarvestingDataWidget:
    def __init__(self, session: Session):
        self.session = session

        self._init_ui()

    def _init_ui(self):
        self.output_widget = Output()
        self.harvesting_file_upload = FileUpload(
            description="Upload harvest file:",
            accept=".csv",
            multiple=False,
            layout=Layout(width="200px"),
        )
        self.puck_data = {
            puck.name: puck for puck in self.session.query(PuckType).all()
        }
        self.import_harvesting_file_button = Button(
            description="Import Harvest Data", layout=Layout(width="200px")
        )
        self.import_harvesting_file_button.on_click(self.import_harvest_file)

        self.widget_row = HBox([self.harvesting_file_upload])

        self.vbox = VBox(
            [self.widget_row, self.import_harvesting_file_button, self.output_widget]
        )

    def import_harvest_file(self, value):
        self.df = None
        if self.harvesting_file_upload.value:
            try:
                uploaded_file = self.harvesting_file_upload.value[0]  # type: ignore
                self.df = pd.read_csv(io.BytesIO(uploaded_file.content), skiprows=8)
                self.df.rename(columns={";PlateType": "PlateType"}, inplace=True)
                puck_names = self.df["DestinationName"].unique()
                puck_references = make_pucks(
                    self.session,
                    puck_names=list(puck_names),
                )
                for index, row in self.df.iterrows():
                    # this entry will be populated if something happened at the well,
                    # successful or not
                    if pd.notna(row["Comment"]):
                        shifter_well_pos = f"{row['PlateRow']}{row['PlateColumn']}{row['PositionSubWell']}"
                        xtal_well = get_xtal_well(
                            self.session, row["PlateID"], shifter_well_pos
                        )
                        xtal_well.harvest_comment = row["Comment"]
                        xtal_well.harvesting_status = True
                        xtal_well.time_arrival = pd.to_datetime(
                            row["TimeArrival"], format="%d/%m/%Y %H:%M:%S"
                        )
                        echo_transfer = (
                            self.session.query(EchoTransfer)
                            .filter(EchoTransfer.to_well_id == xtal_well.uid)
                            .first()
                        )
                        if echo_transfer:
                            library_well = echo_transfer.from_well
                            library_well.used = True

                        # this entry will only be populated if the pin made it into the puck
                        if pd.notna(row["DestinationLocation"]):
                            transfer_xtal_to_pin(
                                self.session,
                                xtal_well,
                                row["DestinationName"],
                                row["DestinationLocation"],
                                row["TimeDeparture"],
                                puck_references,
                            )
                with self.output_widget:
                    print("Successfully ingested harvesting data")
            except Exception as e:
                with self.output_widget:
                    traceback.print_exc()
                    print(f"Exception while reading file: {e}")

    @property
    def ui(self):
        return self.vbox
