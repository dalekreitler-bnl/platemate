from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from .create import *
from .delete import *
from .read import *
from .update import *


def write_df_to_csv(data_directory: Optional[Path], df: pd.DataFrame, uploaded_file):
    # Dump the dataframe into a csv file
    if data_directory and df is not None:
        # Get the current timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        uploaded_filename = Path(uploaded_file.name)
        new_filename = Path(
            f"{uploaded_filename.stem}_{timestamp}{uploaded_filename.suffix}"
        )

        df.to_csv(data_directory / new_filename)


def get_rows_to_skip(csv_buffer):
    csv_buffer.seek(0)
    skiprows = 0
    for line in csv_buffer:
        if line.startswith(b";"):
            skiprows += 1
        else:
            break
    return skiprows - 1
