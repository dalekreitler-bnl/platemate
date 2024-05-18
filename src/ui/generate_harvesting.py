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
from utils.read import get_all_batches
from utils.create import write_harvest_file
from typing import List

from models import LibraryWell, XtalWell, Batch


class GenerateHarvestDataWidget:
    def __init__(self, session: Session, output_folder: Path):
        if output_folder is None or not output_folder.exists():
            raise ValueError("Template harvesting output directory not given or doesn't exist")
        else:
            self.output_folder = output_folder
        self.session = session
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
        self.batch_dropdown.observe(self.batch_change_callback, "value")
        self.path_text_box = Text(
            value="",
            placeholder="Path to output file",
            description="Output file:",
            disabled=False,
            style=dict(description_width="initial"),
        )

        self.generate_button = Button(
            description="Generate harvest file",
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
            path = f"harvesting_{batch.uid}_{batch.name}.csv"
        else:
            path = "harvesting_0.csv"
        self.path_text_box.value = str(self.output_folder / Path(path))

    def generate_harvest_file(self, state):
        try:
            write_harvest_file(
                self.session,
                self.all_batches[self.batch_dropdown.value],
                self.path_text_box.value,
            )
            with self.output_widget:
                print(
                    f"Successfully generated harvest file at {self.path_text_box.value}"
                )
        except Exception as e:
            with self.output_widget:
                print(f"Exception while creating harvest file: {e}")

    @property
    def ui(self):
        return self.vbox
