import pandas as pd
import os
import json
from ..molonaviz.backend import SamplingPointManager as spm


# ----- "Real" database insertion logic with current payload ----- #
with open(os.path.join(os.path.dirname(__file__), 'config.json')) as config_file:
    config_json = json.load(config_file)

REALDB_CONFIG = config_json["database"]["realdb_config"]

def transform_payload(payload):
    """
    Transform the incoming payload into the format expected by the database insertion functions.
    payload : dict containing the data to transform
    Returns a dict with the transformed data
    """
    transformed = {
        "date": pd.to_datetime(payload["timestamp"]),
        "temp_bed": [payload["a1"]],
        "temperature_values": [[payload["a1"], payload["a2"], payload["a3"], payload["a4"]]],  # Example
        "voltage_value": payload["a0"]
    }
    return transformed


def create_sampling(con_db, config, sampling_dir, filename):
    """
    Create a new sampling point from the configuration and data files.
    """
    sp_df = pd.read_csv(os.path.join(sampling_dir, filename), header=None)
    sp_df.at[3, 1] = pd.to_datetime(sp_df.at[3, 1])
    sp_df.at[4, 1] = pd.to_datetime(sp_df.at[4, 1])
    sampling_point_manager = spm.SamplingPointManager(con_db, config["study_name"])

    # The call could simply be sampling_point_manager.insert_new_point(sp_df) with a small modification of the method
    # But I've kept it like this to minimize changes with the old Molonaviz code
    samp_id = sampling_point_manager.insert_new_point(sp_df.at[0,1],sp_df.at[1,1], sp_df.at[2,1],\
                                                      os.path.join(sampling_dir, sp_df.at[7,1]),\
                                                      os.path.join(sampling_dir, sp_df.at[8,1]),\
                                                      sp_df)
    return samp_id


def insert_payload(con_db, config, payload):
    """
    Insert temperature and pressure data from payload into the database for the sampling point defined in config.
    payload : dict containing the data to insert
    """
    sampling_point_manager = spm.SamplingPointManager(con_db, config["study_name"])
    sp_id = sampling_point_manager.get_spoint_id(config["sampling_point_name"])
    
    if sp_id is None:
        print(f"Sampling point with name {config['sampling_point_name']} not found.")
        return
    
    # Switch to dataframes to use the existing methods
    payload_df = pd.DataFrame([payload])
    payload_df["date"] = pd.to_datetime(payload_df["date"])
    
    sampling_point_manager.create_raw_temperature_point(sp_id, payload_df.copy())
    sampling_point_manager.create_raw_pressure_point(sp_id, payload_df.copy())