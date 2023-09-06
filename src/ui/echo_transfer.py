from ipywidgets import (
    Tab,
    SelectMultiple,
    Accordion,
    Checkbox,
    VBox,
    HBox,
    HTML,
    IntText,
    Button,
    Layout,
    Dropdown,
    IntSlider,
    Text,
)
from pathlib import Path
from sqlalchemy.orm import Session

from typing import List

from models import LibraryWell, XtalWell, Batch
from utils.create import write_echo_csv, create_batch
from utils.read import (
    get_all_lib_plate_names,
    get_all_xtal_plate_names,
    get_lib_plate_model,
    get_unused_lib_plate_wells,
    get_unused_xtal_plate_wells,
    get_latest_batch,
    get_xtal_plate_model,
    get_instance,
    get_all_projects,
)


class EchoTransferWidget:
    def __init__(self, session: Session):
        self.session = session
        self.lib_plate_wells: List[LibraryWell] = []
        self.xtal_plate_wells: List[XtalWell] = []
        self._init_ui()

    def _init_ui(self):
        lib_plates = get_all_lib_plate_names(self.session)
        self.lib_plates = Dropdown(
            options=lib_plates,
            description="Library Plate:",
            disabled=False,
            style=dict(description_width="initial"),
        )
        # Add call back to lib_plates
        self.lib_plates.observe(self.lib_plate_callback)

        xtal_plates = get_all_xtal_plate_names(self.session)
        self.xtal_plates = Dropdown(
            options=xtal_plates,
            description="Xtal Plate:",
            disabled=False,
            style=dict(description_width="initial"),
        )
        # Add call back to xtal_plates
        self.xtal_plates.observe(self.xtal_plate_callback)
        self.projects = {
            proj.target: proj for proj in get_all_projects(session=self.session)
        }
        self.project_dropdown = Dropdown(
            options=self.projects.keys(),
            description="Project:",
            disabled=False,
            style=dict(description_width="initial"),
        )

        self.xtal_wells_used_slider = IntSlider(
            value=0,
            min=0,
            max=0,
            step=1,
            description="Xtal wells to be used",
            continuous_update=False,
            style=dict(description_width="initial"),
        )

        self.generate_echo_transfer_button = Button(
            description="Generate Echo Transfer",
            disabled=False,
            button_style="",  # 'success', 'info', 'warning', 'danger' or ''
            layout=Layout(width="200px"),
        )
        self.generate_echo_transfer_button.on_click(self.echo_transfer_button_triggered)

        self.path_text_box = Text(
            value="./echo_protocol_0.csv",
            placeholder="Path to output file",
            description="Output file:",
            disabled=False,
            style=dict(description_width="initial"),
        )
        self.batch_name_text_box = Text(
            value="", description="Batch Name:", style=dict(description_width="initial")
        )
        self.batch_num = IntText(
            value=0,
            description="Batch:",
            disabled=False,
            style=dict(description_width="initial"),
        )
        self.batch_num.observe(self.batch_num_changed, "value")

        self.solvent_check_box = Checkbox(
            value=False,
            description="Solvent Library Plate",
            disabled=False,
            indent=False,
        )

        self.widget_row1 = HBox(
            [self.lib_plates, self.xtal_plates, self.project_dropdown]
        )
        self.widget_row2 = HBox(
            [
                self.xtal_wells_used_slider,
            ]
        )
        self.widget_row3 = HBox(
            [self.path_text_box, self.batch_name_text_box, self.batch_num]
        )
        self.vbox = VBox(
            [
                self.widget_row1,
                self.widget_row2,
                self.widget_row3,
                self.generate_echo_transfer_button,
            ]
        )
        # Executing call backs when the UI is initialized
        self.lib_plate_callback({"new": lib_plates[0]})
        self.xtal_plate_callback({"new": xtal_plates[0]})

    def batch_num_changed(self, state):
        value = state["new"]
        max_batch = get_latest_batch(self.session) + 1
        if value > max_batch:
            self.batch_num.value = max_batch
        self.update_path()
        self.update_batch_name(max_batch)

    def echo_transfer_button_triggered(self, state):
        print("Echo transfer triggered")
        if self.batch_num.value > get_latest_batch(self.session):
            batch_name = str(self.batch_name_text_box.value)
            if not batch_name:
                batch_name = f"Batch {self.batch_num.value}"
            if self.solvent_check_box.value:
                # If the solvent check box is checked, we make a hard assumption
                # that the first well in the lib plate is assumed to be transferred
                # to all xtal wells
                self.lib_plate_wells = [
                    self.lib_plate_wells[0] for i in range(len(self.xtal_plate_wells))
                ]
            create_batch(
                self.session,
                batch_name,
                self.lib_plate_wells,
                self.xtal_plate_wells,
                self.xtal_wells_used_slider.value,
                self.projects[self.project_dropdown.value],
            )
        write_echo_csv(self.session, self.batch_num.value, self.path_text_box.value)
        self.lib_plate_callback({"new": self.lib_plates.value})
        self.xtal_plate_callback({"new": self.xtal_plates.value})

    def set_widget_values(self):
        if self.solvent_check_box.value == False:
            self.xtal_wells_used_slider.max = min(
                len(self.xtal_plate_wells), len(self.lib_plate_wells)
            )
            self.xtal_wells_used_slider.value = min(
                len(self.xtal_plate_wells), len(self.lib_plate_wells)
            )
        else:
            self.xtal_wells_used_slider.max = len(self.xtal_plate_wells)
            self.xtal_wells_used_slider.value = len(self.xtal_plate_wells)
        batch_id = get_latest_batch(self.session) + 1
        self.batch_num.value = batch_id
        self.update_path()
        self.update_batch_name(batch_id)

    def update_batch_name(self, max_batch):
        batch = None
        if self.batch_num.value < max_batch:
            batch = get_instance(self.session, Batch, **{"uid": self.batch_num.value})

        if batch:
            self.batch_name_text_box.value = batch.name
        else:
            self.batch_name_text_box.value = f"Batch {self.batch_num.value}"

    def update_path(self):
        batch_id = self.batch_num.value
        path = Path(self.path_text_box.value)
        batch_name = f"{self.xtal_plates.value}-{batch_id}"
        filename = f"echo_protocol_{batch_name}.csv"
        if path.is_dir():
            updated_path = path / filename
        else:
            updated_path = path.with_name(filename)
        self.path_text_box.value = str(updated_path)

    def lib_plate_callback(self, state):
        selected_plate_name = state["new"]
        selected_plate = get_lib_plate_model(self.session, selected_plate_name)
        if selected_plate:
            self.lib_plate_wells = get_unused_lib_plate_wells(
                self.session, selected_plate
            )
            self.set_widget_values()

    def xtal_plate_callback(self, state):
        selected_xtal_plate_name = state["new"]
        selected_plate = get_xtal_plate_model(self.session, selected_xtal_plate_name)
        if selected_plate:
            self.xtal_plate_wells = get_unused_xtal_plate_wells(
                self.session, selected_plate
            )
            self.set_widget_values()

    @property
    def ui(self):
        return self.vbox
