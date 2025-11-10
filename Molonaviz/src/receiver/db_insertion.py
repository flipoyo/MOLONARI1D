import pandas as pd
import os
import json
from PyQt5.QtSql import QSqlQuery, QSqlDatabase

# Load configuration from JSON file
with open(os.path.join(os.path.dirname(__file__), './settings/config.json')) as config_file:
    config = json.load(config_file)

def createRealDatabase():
    """
    Given a directory and the name of the database, create a folder with the name databaseName and the correct structure. Also create the empty database with correct table structure based on the sqlInitFile.
    Return True if the directory was successfully created, False otherwise
    """
    databasePath = config['database']['filename']
    databaseDirectory = os.path.dirname(databasePath)

    if os.path.isdir(databaseDirectory):
        return False
    os.makedirs(databaseDirectory, exist_ok=True)
    os.mkdir(os.path.join(databaseDirectory, "Notices"))
    os.mkdir(os.path.join(databaseDirectory, "Schemes"))
    os.mkdir(os.path.join(databaseDirectory, "Scripts"))
    f = open(databasePath,"x")
    f.close()

    con = QSqlDatabase.addDatabase("QSQLITE")
    con.setDatabaseName(databasePath)
    con.open()

    sqlInitFile = config['database']['ERD_structure']
    f = open(sqlInitFile, 'r')
    sqlQueries = f.read()
    f.close()
    sqlQueries = sqlQueries.split(";")
    query = QSqlQuery(con)
    for q in sqlQueries:
        query.exec(q)
    con.close()
    QSqlDatabase.removeDatabase(con.databaseName())
    return True


def add_object(con_db, table_name, df):
    """
    Builds and execute a SQL query from a DataFrame.
    """
    query = QSqlQuery(con_db)
    columns = df.columns.tolist()
    placeholders = ', '.join(['?'] * len(columns))
    query_string = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    query.prepare(query_string)
    for _, row in df.iterrows():
        for col in columns:
            query.addBindValue(row[col])
        query.exec()


def fillRealDatabase():
    """
    The directory `objects` contains CSV files with data to insert into the database.
    Each file has the name of the table to fill, and represents the table content to insert.
    Required files for proper functioning: 
        - Labo.csv
        - Study.csv
        - Gateway.csv
        - Relay.csv
        - Datalogger.csv
        - Thermometer.csv
        - PressureSensor.csv
        - Shaft.csv
        - SamplingPoint.csv
    """
    con_db = QSqlDatabase.addDatabase("QSQLITE")
    con_db.setDatabaseName(config['database']['filename'])
    con_db.open()

    objects_dir = os.path.join(os.path.dirname(__file__), './objects')
    for filename in os.listdir(objects_dir):
        if not filename.endswith(".csv"):
            continue
        table_name = filename[:-4]
        df = pd.read_csv(os.path.join(objects_dir, filename))
        add_object(con_db, table_name, df)
    
    return con_db


def get_sampling_point_id(con_db, payload):
    """
    Select the sampling point based on the payload information.
    payload : dict containing the data to use for selection
    Returns the sampling point ID or None if not found
    """
    query = QSqlQuery(con_db)
    query.prepare("""
        SELECT sp.id FROM SamplingPoint sp
        JOIN Shaft s ON sp.Shaft = s.ID
        JOIN Datalogger dl ON s.DataloggerID = dl.ID
        JOIN Relay r ON dl.Relay = r.ID
        JOIN Gateway g ON r.Gateway = g.ID
        WHERE dl.devEui = :devEui
          AND r.relayEui = :relayEui
          AND g.gatewayEui = :gatewayEui
    """)
    
    query.bindValue(":devEui", payload["device_eui"])
    query.bindValue(":relayEui", payload.get("relay_id"))
    query.bindValue(":gatewayEui", payload.get("gateway_id"))

    if not query.exec():
        print(query.lastError().text())
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
    
    insert_calibrated_temperature(con_db,payload,sp_id)

def get_study_name(con_db,sp_id):
    """
    Select the study name based on the sampling point information.
    """

    query = QSqlQuery(con_db)
    query.prepare("""SELECT S.Name FROM Study S
                  JOIN SamplingPoint SP on S.ID = SP.study
                  WHERE SP.ID = :sp_id """)
    
    query.bindValue(":sp_id",sp_id)

    if not query.exec():
        print(query.lastError().text())
        return None
    if not query.next():
        return None
    
    study_name = query.value(0)
    return study_name

def get_samplingpoint_name(con_db,sp_id):
    """
    Select the study name based on the sampling point information.
    """

    query = QSqlQuery(con_db)
    query.prepare("""SELECT SP.Name FROM SamplingPoint SP
                  WHERE SP.ID = :sp_id """)
    
    query.bindValue(":sp_id",sp_id)

    if not query.exec():
        print(query.lastError().text())
        return None
    if not query.next():
        return None
    
    sp_name = query.value(0)
    return sp_name

def insert_calibrated_temperature(con_db: QSqlDatabase, payload: dict, sp_id: int):
    """
   Convert the voltage into temperature using calibration parameters from the SPointCoordinator and insert the calibrated temperatures into the RawMeasuresTemp table.
    """
    study_name = get_study_name(con_db, sp_id)
    sp_name = get_samplingpoint_name(con_db,sp_id)
    coordinator = SPointCoordinator(con_db, study_name, sp_name)

    # get calibration parameters from SPointCoordinator
    beta, V_ref = coordinator.thermometer_calibration_infos()
    if beta is None or V_ref is None:
        return 
        
    # 2. Calibrate temperatures
    temp_values = {
        "Temp1": coordinator.calibrate_temperature(payload["a2"], beta, V_ref),
        "Temp2": coordinator.calibrate_temperature(payload["a3"], beta, V_ref),
        "Temp3": coordinator.calibrate_temperature(payload["a4"], beta, V_ref),
        "Temp4": coordinator.calibrate_temperature(payload["a5"], beta, V_ref),
    }

    # 3. Insert inside RawMeasuresTemp
    query = QSqlQuery(con_db)
    query.prepare(f"""INSERT INTO RawMeasuresTemp (
                        Date, Temp1, Temp2, Temp3, Temp4, SamplingPoint)
        VALUES (:Date, :Temp1, :Temp2, :Temp3, :Temp4, :SamplingPoint)
    """)
    query.bindValue(":Date", payload["timestamp"])
    query.bindValue(":Temp1", temp_values["Temp1"])
    query.bindValue(":Temp2", temp_values["Temp2"])
    query.bindValue(":Temp3", temp_values["Temp3"])
    query.bindValue(":Temp4", temp_values["Temp4"])
    query.bindValue(":SamplingPoint", sp_id)
    
    if not query.exec():
        print(f"Error inserting into RawMeasuresTemp: {query.lastError().text()}")