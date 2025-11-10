import sys
import os
from PyQt5.QtSql import QSqlDatabase

# Ensure the Molonaviz `backend` package directory is on sys.path so
# `from backend import ...` works when this script is run from elsewhere.
# Expected backend location (relative to this file):
# ../../../Molonaviz/src/molonaviz/backend

_backend_dir = os.path.abspath(r"C:\Users\arman\Documents\MOLONARI\Molonaviz\src")

if os.path.isdir(_backend_dir) and _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
print(sys.path)


try:
    from molonaviz.backend import StudyAndLabManager as slm
    from molonaviz.backend import SamplingPointManager as spm
except ImportError as e:
    raise ImportError(f"Failed to import backend package. Ensure the path is correct: {_backend_dir}") from e

import pandas as pd

def create_sampling(config, sampling_dir, filename):
    """Create a new sampling point from the configuration and data files."""
    sp_df = pd.read_csv(os.path.join(sampling_dir, filename), header=None)
    sp_df.at[3, 1] = pd.to_datetime(sp_df.at[3, 1])
    sp_df.at[4, 1] = pd.to_datetime(sp_df.at[4, 1])
    sampling_point_manager = spm.SamplingPointManager(con, config["study_name"])

    # The call could simply be sampling_point_manager.insert_new_point(sp_df) with a small modification of the method
    # But I've kept it like this to minimize changes with the old Molonaviz code
    samp_id = sampling_point_manager.insert_new_point(sp_df.at[0,1],sp_df.at[1,1], sp_df.at[2,1],\
                                                      os.path.join(sampling_dir, sp_df.at[7,1]),\
                                                      os.path.join(sampling_dir, sp_df.at[8,1]),\
                                                      sp_df)
    return samp_id


def insert_payload(config, payload):
    """
    Insert temperature and pressure data from payload into the database for the sampling point defined in config.
    payload : dict containing the data to insert
    """
    sampling_point_manager = spm.SamplingPointManager(con, config["study_name"])
    sp_id = sampling_point_manager.get_spoint_id(config["sampling_point_name"])
    
    if sp_id is None:
        print(f"Sampling point with name {config['sampling_point_name']} not found.")
        return
    
    # Switch to dataframes to use the existing methods
    payload_df = pd.DataFrame([payload])
    payload_df["date"] = pd.to_datetime(payload_df["date"])
    
    sampling_point_manager.create_raw_temperature_point(sp_id, payload_df.copy())
    sampling_point_manager.create_raw_pressure_point(sp_id, payload_df.copy())


if __name__ == "__main__":
    payload_data = {
        "date" : "2025/10/27 17:01:00",
        "temperature_values" : [20.5, 21.0, 20.8, 21.2],
        "temp_bed" : 16.0, # Ou est-ce qu'on le trouve ???
        "voltage_value" : 2.22
    }

    config_file = {
        "sampling_point_name" : "main-sampling",
        "study_name" : "main-study",
        "labo_id" : 1
    }

    con = QSqlDatabase.addDatabase("QSQLITE")
    con.setDatabaseName(r"C:\Users\arman\Documents\MOLONARI\Molonaviz\src\molonaviz\TestDatabase\Molonari.sqlite")
    con.open()
    insert_payload(config_file, payload_data)