from ast import literal_eval
import pandas as pd

from PyQt5.QtSql import QSqlQuery, QSqlDatabase #QSqlDatabase in used only for type hints
from ..utils.general import displayCriticalMessage

class StudyAndLabManager:
    """
    A concrete class to handle high-level operations on laboratories and studies, such as adding a lab to the database or creating a new study.
    """
    def __init__(self, con : QSqlDatabase):
        self.con = con

    def create_new_lab(self, labName : str, thermometersDF : list[pd.DataFrame], psensorsDF : list[pd.DataFrame], shaftsDF : list[pd.DataFrame]):
        """
        This function should only be called by frontend users.
        Create a new laboratory with the name labName, and populate it with different physical detectors. For each type of detectors (currently there are only 3), frontend users should give a list of panda dataframes with the correct information. These dataframes must be valid (no empty field, fields at the correct position...).
        """
        if not self.check_integrity(labName):
            displayCriticalMessage("Something went wrong when creating the laboratory, and it wasn't added to the database.\nPlease make sure a laboratory with the same name is not already in the database.")
        else:
            labID = self.insert_new_lab(labName)
            self.insert_detectors(labID, thermometersDF, psensorsDF, shaftsDF)

    def create_new_study(self, studyName : str, labName : str):
        """
        This function should only be called by frontend users
        Create a new study with the name studyName attached to the laboratory called labName. The names must be valid (ie studyName is unique, and there is a unique laboratory called labName).
        """
        selectLabID = self.build_lab_id(labName)
        selectLabID.exec()
        selectLabID.next()
        labID = selectLabID.value(0)

        insertStudy = self.build_insert_study()
        insertStudy.bindValue(":Name",studyName)
        insertStudy.bindValue(":Labo",labID)
        insertStudy.exec()
        print(f"The study {studyName} has been added to the database.")

    def is_study_in_database(self, studyName : str):
        """
        This function should only be called by frontend users.
        Return True if a study with the name studyName is in the database.
        """
        similar_studies = self.build_similar_studies(studyName)
        similar_studies.exec()
        if similar_studies.next():
            return True
        return False

    def get_lab_names(self, studyName = None):
        """
        This function should only be called by frontend users.
        Return a list of all the names of the laboratories in the database, or, if a valid name of a study if given, a list containing only one element: the laboratory name attached to this study.
        """
        labs_query = self.build_select_labs(studyName)
        labs = []
        labs_query.exec()
        while labs_query.next():
            labs.append(labs_query.value(0))
        return labs

    def get_study_names(self):
        """
        This function should only be called by frontend users.
        Return a list of all the names of the studies in the database.
        """
        studies_query = self.build_select_studies()
        studies = []
        studies_query.exec()
        while studies_query.next():
            studies.append(studies_query.value(0))
        return studies

    def check_integrity(self, labName : str):
        """
        Check that this Lab is not in conflict with the database.
        For now, this means checking there is no laboratory with the same name in the database.
        """
        similar_lab = self.build_similar_lab(labName)
        similar_lab.exec()
        if similar_lab.next():
            return False
        return True

    def insert_new_lab(self, labName : str):
        """
        Insert into the database a laboratory with name labName. We assume the insertion is valid and not in conflict with the database.
        Return the ID of the newly inserted laboratory.
        """
        insert_lab = self.build_insert_lab(labName)
        insert_lab.exec()
        print(f"The lab {labName} has been added to the database.")
        return insert_lab.lastInsertId()

    def insert_detectors(self, labID : int|str, thermometersDF : list[pd.DataFrame], psensorsDF : list[pd.DataFrame], shaftsDF : list[pd.DataFrame]):
        """
        Add all given detectors in the database for given lab. For now, these detectors correspond to:
            -temperature sensors
            -pressure sensors
            -shafts
        Each type of detector must be given as a list of pandas dataframe, and these dataframes MUST be valid (ie no empty field, fields must have correct type...).
        """
        #Add the thermometers
        insertQuery = self.build_insert_thermometer()
        for df in thermometersDF:
            consName = df.iloc[0].at[1]
            ref = df.iloc[1].at[1]
            name = df.iloc[2].at[1]
            sigma = float(df.iloc[3].at[1].replace(',','.'))

            insertQuery.bindValue(":Name",name)
            insertQuery.bindValue(":ManuName",consName)
            insertQuery.bindValue(":ManuRef",ref)
            insertQuery.bindValue(":Error",sigma)
            insertQuery.bindValue(":Labo",labID)
            insertQuery.exec()
        print("The thermometers have been added to the database.") #TODO: Maybe a little check before asserting this?

        insertPsensor = self.build_insert_psensor()
        for df in psensorsDF:
            name = df.iloc[0].at[1]
            datalogger = df.iloc[1].at[1]
            calibrationDate = df.iloc[2].at[1]
            intercept = float(df.iloc[3].at[1].replace(',','.'))
            dudh = float(df.iloc[4].at[1].replace(',','.'))
            dudt = float(df.iloc[5].at[1].replace(',','.'))
            sigma = float(df.iloc[6].at[1].replace(',','.'))
            thermo_name = df.iloc[7].at[1]
            select_thermo = self.build_thermo_id(labID, thermo_name)
            select_thermo.exec()
            select_thermo.next()
            thermo_model = select_thermo.value(0)

            insertPsensor.bindValue(":Name",name)
            insertPsensor.bindValue(":Datalogger",datalogger)
            insertPsensor.bindValue(":Calibration",calibrationDate)
            insertPsensor.bindValue(":Intercept",intercept)
            insertPsensor.bindValue(":DuDh",dudh)
            insertPsensor.bindValue(":DuDt",dudt)
            insertPsensor.bindValue(":Error",sigma)
            insertPsensor.bindValue(":ThermoModel",thermo_model)
            insertPsensor.bindValue(":Labo",labID)
            insertPsensor.exec()
        print("The thermometers have been added to the database.") #TODO: Maybe a little check before asserting this?

        insertShaft = self.build_insert_shaft()
        for df in shaftsDF:
            name = df.iloc[0].at[1]
            datalogger = df.iloc[1].at[1]
            tSensorName = df.iloc[2].at[1]
            depths = literal_eval(df.iloc[3].at[1]) #This is now a list
            select_thermo = self.build_thermo_id(labID, tSensorName)
            select_thermo.exec()
            select_thermo.next()
            thermo_model = select_thermo.value(0)

            insertShaft.bindValue(":Name",name)
            insertShaft.bindValue(":Datalogger", datalogger)
            insertShaft.bindValue(":Depth1",depths[0])
            insertShaft.bindValue(":Depth2",depths[1])
            insertShaft.bindValue(":Depth3",depths[2])
            insertShaft.bindValue(":Depth4",depths[3])
            insertShaft.bindValue(":ThermoModel",thermo_model)
            insertShaft.bindValue(":Labo",labID)
            insertShaft.exec()
        print("The shafts have been added to the database.")#TODO: Maybe a little check before asserting this?

    def build_similar_lab(self, labName : str):
        """
        Build and return a query to check if a lab with the same name as labName is in the database.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"SELECT Labo.Name FROM Labo WHERE Labo.Name ='{labName}'")
        return query

    def build_thermo_id(self, labID : int|str, thermoname : str):
        """
        Build and return a query giving the name of a given thermometer.
        """
        selectQuery = QSqlQuery(self.con)
        selectQuery.prepare(f"SELECT Thermometer.ID FROM Thermometer WHERE Thermometer.Name = '{thermoname}' AND Thermometer.Labo = '{labID}'")
        return selectQuery

    def build_lab_id(self, labName : str):
        """
        Build and return a query giving the ID of the laboratory called labName.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"SELECT Labo.ID FROM Labo WHERE Labo.Name ='{labName}'")
        return query

    def build_select_labs(self, studyName = None):
        """
        Build and return a query giving all available labs in the database.
        """
        query = QSqlQuery(self.con)
        if studyName is None:
            query.prepare("SELECT Labo.Name FROM Labo")
        else:
             query.prepare(f"""SELECT Labo.Name FROM Labo
                            JOIN Study
                            ON Labo.ID = Study.Labo
                            WHERE Study.name = '{studyName}' """)
        return query

    def build_select_studies(self):
        """
        Build and return a query giving all available studies in the database.
        """
        query = QSqlQuery(self.con)
        query.prepare("SELECT Study.Name FROM Study")
        return query

    def build_similar_studies(self, studyName : str):
        """
        Build and return a query giving all the studies in the database with the name studyName.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"SELECT * FROM Study WHERE Study.Name='{studyName}'")
        return query

    def build_insert_lab(self, labName : str):
        """
        Build and return a query which inserts into the database the lab with name labName.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"INSERT INTO Labo (Name) VALUES ('{labName}')")
        return query

    def build_insert_thermometer(self):
        """
        Build and return a query which creates a thermometer.
        """
        insertQuery = QSqlQuery(self.con)
        insertQuery.prepare(
        """ INSERT INTO Thermometer (
            Name,
            ManuName,
            ManuRef,
            Error,
            Labo
        )
        VALUES (:Name, :ManuName, :ManuRef, :Error, :Labo)""")
        return insertQuery

    def build_insert_psensor(self):
        """
        Build and return a query which creates a pressure sensor.
        """
        insertQuery = QSqlQuery(self.con)
        insertQuery.prepare(
        """ INSERT INTO PressureSensor (
            Name,
            Datalogger,
            Calibration,
            Intercept,
            DuDH,
            DuDT,
            Error,
            ThermoModel,
            Labo
        )
        VALUES (:Name, :Datalogger, :Calibration, :Intercept, :DuDh, :DuDt, :Error, :ThermoModel, :Labo)""")
        return insertQuery

    def build_insert_shaft(self):
        """
        Build and return a query which creates a shaft.
        """
        insertQuery = QSqlQuery(self.con)
        insertQuery.prepare("""
            INSERT INTO Shaft (
                Name,
                Datalogger,
                Depth1,
                Depth2,
                Depth3,
                Depth4,
                ThermoModel,
                Labo
            )
            VALUES (:Name, :Datalogger, :Depth1, :Depth2, :Depth3, :Depth4, :ThermoModel, :Labo)""")
        return insertQuery

    def build_insert_study(self):
        """
        Build and return a query creating a study in the database.
        """
        query = QSqlQuery(self.con)
        query.prepare("""
            INSERT INTO Study(
                Name,
                Labo)
            VALUES (:Name, :Labo)
            """)
        return query