import pandas as pd
import os
import json
from PyQt5.QtSql import QSqlQuery, QSqlDatabase
from ..molonaviz.backend import SamplingPointManager as spm


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

    query.bindValue(":devEui", payload["device_eui"])
    query.bindValue(":relayEui", payload.get("relay_id"))
    query.bindValue(":gatewayEui", payload.get("gateway_id"))

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
    sp_id = get_sampling_point_id(con_db, payload)
    
    if sp_id is None:
        print(f"SamplingPoint corresponding to device {payload['device_eui']},\
               relay {payload['relay_id']}, gateway {payload['gateway_id']} not found.")
        return

    # Switch to right date format
    # useful_payload["timestamp"] = pd.to_datetime(useful_payload["timestamp"])
    # useful_payload["relay_ts"] = pd.to_datetime(useful_payload["relay_ts"])
    # useful_payload["gateway_ts"] = pd.to_datetime(useful_payload["gateway_ts"])

    # Insert Pressure into actual database

    query = QSqlQuery(con_db)
    query.prepare(f"""INSERT INTO RawMeasuresPress (
                        Date,
                        TempBed,
                        Voltage,
                        SamplingPoint)
        VALUES (:Date, :TempBed, :Voltage, :SamplingPoint)
    """)
    query.bindValue(":Date", payload["timestamp"])
    query.bindValue(":Voltage", payload["a0"])
    query.bindValue(":TempBed", payload["a1"])
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
    query.bindValue(":Date", payload["timestamp"])
    query.bindValue(":Volt1", payload["a2"])
    query.bindValue(":Volt2", payload["a3"])
    query.bindValue(":Volt3", payload["a4"])
    query.bindValue(":Volt4", payload["a5"])
    query.bindValue(":SamplingPoint", sp_id)
    if not query.exec():
        print(query.lastError())
        return

    return query.lastInsertId()
    