import pandas as pd
import os
import json
from PyQt5.QtSql import QSqlQuery, QSqlDatabase
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
        "temperature_volt": [payload["a2"], payload["a3"], payload["a4"], payload["a5"]],
        "pressure_volt": payload["a0"]
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


def get_sampling_point_id(con_db, payload):
    """
    Select the sampling point based on the payload information.
    payload : dict containing the data to use for selection
    Returns the sampling point ID or None if not found
    """
    query = QSqlQuery(con_db)
    query.prepare(f""" SELECT sp.id FROM SamplingPoint sp
                  JOIN Shaft s ON sp.Shaft = s.id
                  JOIN Datalogger dl ON s.DataloggerID = dl.id AND dl.devEui = :devEui
                  JOIN Relay r ON dl.relay_id = r.id AND r.relayEui = :relayEui
                  JOIN Gateway g ON r.gateway_id = g.id AND g.gatewayEui = :gatewayEui
    """)

    query.bindValue(":devEui", payload["devEui"])
    query.bindValue(":relayEui", payload.get("relayEui"))
    query.bindValue(":gatewayEui", payload.get("gatewayEui"))

    if not query.exec():
        print(query.lastError())
        return None
    if not query.next():
        return None
    sp_id = query.value(0)
    return sp_id

def insert_payload(con_db, payload):
    """
    Insert temperature and pressure data from payload into the database for the sampling point defined in config.
    payload : dict containing the data to insert
    """
    useful_payload = transform_payload(payload)
    sp_id = get_sampling_point_id(con_db, useful_payload)
    
    if sp_id is None:
        print(f"SamplingPoint corresponding to device {payload['device_eui']},\
               relay {payload['relay_id']}, gateway {payload['gateway_id']} not found.")
        return

    # Switch to right date format
    useful_payload["timestamp"] = pd.to_datetime(useful_payload["timestamp"])
    useful_payload["relay_ts"] = pd.to_datetime(useful_payload["relay_ts"])
    useful_payload["gateway_ts"] = pd.to_datetime(useful_payload["gateway_ts"])

    # Insert Pressure into actual database

    query = QSqlQuery(con_db)
    query.prepare(f"""INSERT INTO RawMeasuresPress (
                        Date,
                        TempBed,
                        Voltage,
                        SamplingPoint)
        VALUES (:Date, :TempBed, :Voltage, :SamplingPoint)
    """)
    query.bindValue(":Date", useful_payload["timestamp"])
    query.bindValue(":TempBed", useful_payload["temp_bed"])
    query.bindValue(":Voltage", useful_payload["pressure_volt"])
    query.bindValue(":SamplingPoint", sp_id)
    if not query.exec():
        print(query.lastError())
        return


    # Insert TemperatureVoltage into actual database

    query = QSqlQuery(con_db)
    query.prepare(f"""INSERT INTO RawMeasuresVolt (
                        Date,
                        Volt1,
                        Volt2,
                        Volt3,
                        Volt4,
                        SamplingPoint)
        VALUES (:Date, :Volt1, :Volt2, :Volt3, :Volt4, :SamplingPoint)
    """)
    query.bindValue(":Date", useful_payload["timestamp"])
    query.bindValue(":Volt1", useful_payload["temperature_volt"][0])
    query.bindValue(":Volt2", useful_payload["temperature_volt"][1])
    query.bindValue(":Volt3", useful_payload["temperature_volt"][2])
    query.bindValue(":Volt4", useful_payload["temperature_volt"][3])
    query.bindValue(":SamplingPoint", sp_id)
    if not query.exec():
        print(query.lastError())
        return
    