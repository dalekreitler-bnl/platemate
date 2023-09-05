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

from typing import List

from models import LibraryWell, XtalWell, XtalPlate
from utils.read import get_all_batches

from datetime import datetime


class BatchTimeStamp:
    def __init__(self, session: Session):
        self.session = session
        self._init_ui()

    def _init_ui(self):
        self.datetime_format = "%m/%d/%Y %H:%M:%S"
        batches = get_all_batches(self.session)
        self.all_batches = {f"{batch.uid} {batch.name}": batch for batch in batches}

        self.output_widget = Output()
        self.batch_dropdown = Dropdown(
            options=self.all_batches.keys(),
            description="Batch:",
            disabled=False,
            style=dict(description_width="initial"),
        )
        self.batch_dropdown.observe(self.batch_change_callback, "value")

        self.timestamp_textbox = Text(
            value="",
            description="Batch Timestamp",
            style=dict(description_width="initial"),
        )
        self.timestamp_now_button = Button(
            description="Set current time", layout=Layout(width="200px")
        )
        self.timestamp_now_button.on_click(self.set_timestamp_now)
        self.save_timestamp_button = Button(
            description="Save batch timestamp", layout=Layout(width="200px")
        )
        self.save_timestamp_button.on_click(self.save_timestamp)
        self.widget_row1 = HBox(
            [self.batch_dropdown, self.timestamp_textbox, self.timestamp_now_button]
        )
        self.vbox = VBox(
            [self.widget_row1, self.save_timestamp_button, self.output_widget]
        )
        self.batch_change_callback({"new": self.batch_dropdown.value})

    def batch_change_callback(self, state):
        value = state["new"]
        batch = self.all_batches[value]
        self.timestamp_textbox.value = batch.timestamp.strftime(self.datetime_format)

    def set_timestamp_now(self, state):
        self.timestamp_textbox.value = datetime.now().strftime(self.datetime_format)

    def save_timestamp(self, state):
        try:
            new_timestamp = datetime.strptime(
                str(self.timestamp_textbox.value), self.datetime_format
            )
            batch = self.all_batches[str(self.batch_dropdown.value)]
            batch.timestamp = new_timestamp
            self.session.add(batch)
        except Exception as e:
            with self.output_widget:
                print(
                    f"Exception while parsing date and time : {e}. Date time should be formatted as {self.datetime_format}"
                )

    @property
    def ui(self):
        return self.vbox
