"""
Filed added by the 2025 edition of Molonari
This file regroups all the logic with the database required by the receiver to insert data into the actual database
"""

from PyQt5.QtSql import QSqlQuery, QSqlDatabase
import pandas as pd
import os
from .SPointCoordinator import SPointCoordinator


class DatabaseManager:
    def __init__(self, db_path, sql_structure_file):
        self.v_lab_path = './src/molonaviz/backend/virtual-lab/'
        self.db_path = db_path
        self.sql_structure_file = sql_structure_file
        self.con = QSqlDatabase.addDatabase("QSQLITE")
        self.con.setDatabaseName(self.db_path)

        if not self.con.open():
            self.create_real_database()
            self.fill_real_database()
    
    def create_real_database(self):
        databaseDirectory = os.path.dirname(self.db_path)
        if os.path.isdir(databaseDirectory):
            return False
        os.makedirs(databaseDirectory, exist_ok=True)
        os.mkdir(os.path.join(databaseDirectory, "Notices"))
        os.mkdir(os.path.join(databaseDirectory, "Schemes"))
        os.mkdir(os.path.join(databaseDirectory, "Scripts"))
        with open(self.db_path, "x") as f:
            pass

        self.con = QSqlDatabase.addDatabase("QSQLITE")
        self.con.setDatabaseName(self.db_path)
        self.con.open()

        sqlInitFile = self.sql_structure_file
        with open(sqlInitFile, 'r') as f:
            sqlQueries = f.read().split(";")
        for q in sqlQueries:
            QSqlQuery(self.con).exec(q)

        return True

    def add_object(self, table_name, df):
        query = QSqlQuery(self.con)
        columns = df.columns.tolist()
        placeholders = ', '.join(['?'] * len(columns))
        query_string = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        query.prepare(query_string)
        for _, row in df.iterrows():
            for col in columns:
                query.addBindValue(row[col])
            query.exec()

    def fill_real_database(self):

        import_order = [
            "Labo", "Study", "Gateway", "Relay", "Datalogger", "Thermometer", "PressureSensor", "Shaft", "SamplingPoint"
        ]
        for table_name in import_order:
            csv_file = os.path.join(self.v_lab_path, f"{table_name}.csv")
            if not os.path.exists(csv_file):
                continue
            df = pd.read_csv(csv_file)
            if not df.empty:
                self.add_object(table_name, df)
        

    def get_sampling_point_id(self, payload):
        query = QSqlQuery(self.con)
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
        return query.value(0)

    def insert_payload(self, payload):
        sp_id = self.get_sampling_point_id(payload)
        if sp_id is None:
            print(f"SamplingPoint corresponding to device {payload['device_eui']}, relay {payload['relay_id']}, gateway {payload['gateway_id']} not found.")
            return
        
        # Insert TemperatureVoltage
        query = QSqlQuery(self.con)
        query.prepare("""INSERT INTO RawMeasuresVolt (
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
        # Insert calibrated temperatures and pressure (includes temperature bed to calibrate)
        self.insert_calibrated_temperature(payload, sp_id)

    def get_study_name(self, sp_id):
        query = QSqlQuery(self.con)
        query.prepare("""SELECT S.Name FROM Study S
                      JOIN SamplingPoint SP on S.ID = SP.study
                      WHERE SP.ID = :sp_id """)
        query.bindValue(":sp_id", sp_id)
        if not query.exec():
            print(query.lastError().text())
            return None
        if not query.next():
            return None
        return query.value(0)

    def get_samplingpoint_name(self, sp_id):
        query = QSqlQuery(self.con)
        query.prepare("""SELECT SP.Name FROM SamplingPoint SP
                      WHERE SP.ID = :sp_id """)
        query.bindValue(":sp_id", sp_id)
        if not query.exec():
            print(query.lastError().text())
            return None
        if not query.next():
            return None
        return query.value(0)

    def insert_calibrated_temperature(self, payload, sp_id):
        study_name = self.get_study_name(sp_id)
        sp_name = self.get_samplingpoint_name(sp_id)
        coordinator = SPointCoordinator(self.con, study_name, sp_name)
        beta, V_ref = coordinator.thermometer_calibration_infos()
        if beta is None or V_ref is None:
            return 
        temp_values = {
            "Temp1": coordinator.calibrate_temperature(payload["a2"], beta, V_ref),
            "Temp2": coordinator.calibrate_temperature(payload["a3"], beta, V_ref),
            "Temp3": coordinator.calibrate_temperature(payload["a4"], beta, V_ref),
            "Temp4": coordinator.calibrate_temperature(payload["a5"], beta, V_ref),
        }
        query = QSqlQuery(self.con)
        query.prepare("""INSERT INTO RawMeasuresTemp (
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

        # Insert Pressure
        query = QSqlQuery(self.con)
        query.prepare("""INSERT INTO RawMeasuresPress (
                            Date,
                            TempBed,
                            Voltage,
                            SamplingPoint)
            VALUES (:Date, :TempBed, :Voltage, :SamplingPoint)
        """)
        query.bindValue(":Date", payload["timestamp"])
        query.bindValue(":Voltage", payload["a0"])
        query.bindValue(":TempBed", coordinator.calibrate_temperature(payload["a1"], beta, V_ref))
        query.bindValue(":SamplingPoint", sp_id)
        if not query.exec():
            print(query.lastError())
            return

    def close(self):
        self.con.close()
        QSqlDatabase.removeDatabase(self.con.connectionName())