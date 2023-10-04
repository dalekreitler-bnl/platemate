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
    Output,
    Text,
)
from pathlib import Path
from sqlalchemy.orm import Session

from typing import List
from utils.read import get_all_batches
from utils.create import write_lsdc_puck_data
from models import LibraryWell, XtalWell, Batch


class LSDCDataGeneratorWidget:
    def __init__(self, session: Session, output_folder: Path):
        self.session = session
        self.output_folder = output_folder
        self._init_ui()

    def _init_ui(self):
        batches = get_all_batches(self.session)
        self.all_batches = {f"{batch.uid} {batch.name}": batch for batch in batches}
        batch_keys = list(self.all_batches.keys())
        self.output_widget = Output()
        self.batch_dropdown = Dropdown(
            options=batch_keys,
            description="Batch:",
            disabled=False,
            style=dict(description_width="initial"),
        )
        self.batch_dropdown.observe(self.batch_change_callback, "value")  # type: ignore

        self.proposal_number_text_box = Text(
            value="",
            description="Proposal Number:",
            style=dict(description_width="initial"),
        )
        self.path_text_box = Text(
            value="",
            placeholder="Path to output file",
            description="Output file:",
            disabled=False,
            style=dict(description_width="initial"),
        )

        self.generate_button = Button(
            description="Generate LSDC file",
            layout=Layout(width="200px"),
        )
        self.generate_button.on_click(self.generate_harvest_file)

        widget_row1 = HBox([self.batch_dropdown, self.path_text_box])

        self.vbox = VBox([widget_row1, self.generate_button, self.output_widget])

        self.batch_change_callback({"new": self.batch_dropdown.value})

    def batch_change_callback(self, state):
        value = state["new"]
        batch = self.all_batches.get(value, None)
        if batch:
            path = f"LSDC_{batch.uid}_{batch.name}.xlsx"
        else:
            path = "LSDC_0.xlsx"
        self.path_text_box.value = str(self.output_folder / Path(path))

    def generate_harvest_file(self, state):
        try:
            write_lsdc_puck_data(
                self.session,
                self.all_batches[str(self.batch_dropdown.value)],
                str(self.path_text_box.value),
            )
        except Exception as e:
            with self.output_widget:
                print(f"Exception while creating harvest file: {e}")

    @property
    def ui(self):
        return self.vbox
