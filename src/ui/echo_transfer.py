from ipywidgets import (
    Tab,
    SelectMultiple,
    FloatText,
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
    Output,
)
from pathlib import Path
from sqlalchemy.orm import Session

from typing import List
import numpy as np

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
from utils.general import generate_array


class EchoTransferWidget:
    def __init__(self, session: Session, output_folder: Path):
        self.session = session
        self.output_folder = output_folder
        self.lib_plate_wells: List[LibraryWell] = []
        self.xtal_plate_wells: List[XtalWell] = []
        self._init_ui()

    def _init_ui(self):
        self.output = Output()
        lib_plates = get_all_lib_plate_names(self.session)
        self.lib_plates = Dropdown(
            options=lib_plates,
            description="Library Plate:",
            disabled=False,
            style=dict(description_width="initial"),
        )
        # Add call back to lib_plates
        self.lib_plates.observe(self.lib_plate_callback, "value")

        xtal_plates = get_all_xtal_plate_names(self.session)
        self.xtal_plates = Dropdown(
            options=xtal_plates,
            description="Xtal Plate:",
            disabled=False,
            style=dict(description_width="initial"),
        )
        # Add call back to xtal_plates
        self.xtal_plates.observe(self.xtal_plate_callback, "value")
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
        self.solvent_check_box.observe(self.solvent_box_changed, "value")
        self.solvent_check_box.observe(self.solvent_data_changed, "value")

        custom_layout = Layout(width="200px", description_width="initial")
        self.start_gradient_text_box = FloatText(
            value=5,
            description="Start Vol (nL):",
            disabled=True,
            layout=custom_layout,
            min=5,
            max=150,
        )
        self.start_gradient_text_box.observe(self.solvent_data_changed, "value")

        self.end_gradient_text_box = FloatText(
            value=20,
            description="End Vol (nL):",
            disabled=True,
            layout=custom_layout,
        )
        self.end_gradient_text_box.observe(self.solvent_data_changed, "value")

        self.step_gradient_text_box = FloatText(
            value=1, description="Step:", disabled=True, layout=custom_layout
        )
        self.step_gradient_text_box.observe(self.solvent_data_changed, "value")

        self.replicates_text_box = IntText(
            value=1,
            description="Replicates:",
            disabled=True,
            layout=custom_layout,
        )
        self.replicates_text_box.observe(self.solvent_data_changed, "value")

        self.widget_row1 = HBox(
            [self.lib_plates, self.xtal_plates, self.project_dropdown]
        )
        self.widget_row2 = HBox(
            [self.xtal_wells_used_slider, self.batch_name_text_box, self.batch_num]
        )
        self.widget_row3 = HBox(
            [
                self.solvent_check_box,
                self.start_gradient_text_box,
                self.end_gradient_text_box,
                self.step_gradient_text_box,
                self.replicates_text_box,
            ]
        )
        self.widget_row4 = HBox(
            [
                self.path_text_box,
                self.generate_echo_transfer_button,
            ]
        )
        self.vbox = VBox(
            [
                self.widget_row1,
                self.widget_row2,
                self.widget_row3,
                self.widget_row4,
                self.output,
            ]
        )
        # Executing call backs when the UI is initialized
        if lib_plates:
            self.lib_plate_callback({"new": lib_plates[0]})
        if xtal_plates:
            self.xtal_plate_callback({"new": xtal_plates[0]})
        if not lib_plates or not xtal_plates:
            self.generate_echo_transfer_button.disabled = True
            with self.output:
                print(
                    "No Xtal plate or Library plate in the database, cannot create a batch"
                )

    def solvent_box_changed(self, state):
        value = state["new"]

        for text_box in [
            self.start_gradient_text_box,
            self.end_gradient_text_box,
            self.step_gradient_text_box,
            self.replicates_text_box,
        ]:
            text_box.disabled = not value
        self.xtal_wells_used_slider.disabled = value

    def solvent_data_changed(self, state):
        start = self.start_gradient_text_box.value
        stop = self.end_gradient_text_box.value
        step = self.step_gradient_text_box.value
        replicates = self.replicates_text_box.value

        self.possible_volumes = generate_array(start, stop, step, replicates)
        if len(self.possible_volumes) > int(self.xtal_wells_used_slider.max):
            self.sufficient_wells = False
        else:
            self.sufficient_wells = True

        if isinstance(state["new"], bool) and state["new"] == False:
            message = ""
        elif self.sufficient_wells:
            message = "Ready to generate mapping"
        else:
            message = (
                f"Not enough xtal wells available on this plate."
                f"Wells required: {len(self.possible_volumes)}."
                f"Wells available: {self.xtal_wells_used_slider.max}"
            )
        with self.output:
            self.output.clear_output()
            print(message)

    def batch_num_changed(self, state):
        value = state["new"]
        max_batch = get_latest_batch(self.session) + 1
        if value > max_batch:
            self.batch_num.value = max_batch
        self.update_path()
        self.update_batch_name(max_batch)

    def echo_transfer_button_triggered(self, state):
        try:
            with self.output:
                print("Echo transfer triggered")
                if self.batch_num.value > get_latest_batch(self.session):  # type: ignore
                    transfer_volumes = 25
                    batch_name = str(self.batch_name_text_box.value)
                    if not batch_name:
                        batch_name = f"Batch {self.batch_num.value}"
                    if self.solvent_check_box.value:
                        # If the solvent check box is checked, we make a hard assumption
                        # that the first well in the lib plate is assumed to be transferred
                        # to all xtal wells
                        selected_plate = get_lib_plate_model(
                            self.session, str(self.lib_plates.value)
                        )
                        all_lib_plate_wells = get_unused_lib_plate_wells(
                            self.session, selected_plate, include_used=False
                        )
                        self.lib_plate_wells = [
                            all_lib_plate_wells[0]
                            for i in range(len(self.xtal_plate_wells))
                        ]
                        if not self.sufficient_wells:
                            with self.output:
                                self.output.clear_output()
                                print("Insufficient wells, cannot create mapping")
                            return
                        transfer_volumes = self.possible_volumes
                        self.xtal_wells_used_slider.value = len(self.possible_volumes)
                    create_batch(
                        self.session,
                        batch_name,
                        self.lib_plate_wells,
                        self.xtal_plate_wells,
                        self.xtal_wells_used_slider.value,
                        self.projects[self.project_dropdown.value],
                        transfer_volumes,
                    )
                write_echo_csv(
                    self.session, self.batch_num.value, self.path_text_box.value
                )
                self.lib_plate_callback({"new": self.lib_plates.value})
                self.xtal_plate_callback({"new": self.xtal_plates.value})
        except Exception as e:
            with self.output:
                self.output.clear_output()
                print(f"Exception occured: {e}")
                self.session.rollback()

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
        # path = Path(self.path_text_box.value)
        path = self.output_folder
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
