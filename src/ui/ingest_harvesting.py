import io
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from ipywidgets import Button, FileUpload, HBox, Layout, Output, VBox
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import EchoTransfer, PuckType, XtalPlate
from utils import get_rows_to_skip, write_df_to_csv
from utils.create import make_pucks, transfer_xtal_to_pin
from utils.read import get_xtal_well


class IngestHarvestingDataWidget:
    def __init__(self, session: Session, data_directory: Optional[Path]):
        if data_directory is None or not data_directory.exists():
            raise ValueError("Harvesting data directory not given or doesn't exist")
        else:
            self.data_directory = data_directory
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
                # type: ignore
                uploaded_file = self.harvesting_file_upload.value[0]
                csv_buffer = io.BytesIO(uploaded_file.content)
                skiprows = get_rows_to_skip(csv_buffer)
                csv_buffer.seek(0)
                self.df = pd.read_csv(csv_buffer, skiprows=skiprows)
                self.df.rename(columns={";PlateType": "PlateType"}, inplace=True)
                puck_names = self.df["DestinationName"].unique()
                puck_references = make_pucks(
                    self.session,
                    puck_names=list(puck_names),
                )

                if len(self.df["PlateID"].unique()) > 1:
                    raise ValueError("Cannot ingest csv with multiple plate names")

                if (
                    self.session.query(XtalPlate)
                    .filter(XtalPlate.name == self.df["PlateID"].unique()[0])
                    .one_or_none()
                    is None
                ):
                    raise ValueError("no existing xtal plate in database")

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
                                row["PickDuration"].split('.')[0], #discard <1 sec precision
                                puck_references,
                            )

                    try:
                        self.session.commit()
                    except IntegrityError:
                        self.session.rollback()
                        with self.output_widget:
                            print(
                                f"Error ingesting harvesting file: {uploaded_file['name']}\n"
                                "Found existing xtal wells in Pin table"
                            )
                            return
                write_df_to_csv(self.data_directory, self.df, uploaded_file)
                with self.output_widget:
                    print("Successfully ingested harvesting data")
                    print(f"from xtal_plate: {self.df['PlateID'].unique()[0]}")

            except Exception as e:
                with self.output_widget:
                    traceback.print_exc()
                    print(f"Exception reading file {uploaded_file['name']}: {e}")

    @property
    def ui(self):
        return self.vbox
