from PyQt5.QtSql import QSqlQuery, QSqlDatabase #QSqlDatabase in used only for type hints
import pandas as pd
import os, shutil

from ..interactions.MoloModel import MoloModel
from ..interactions.Containers import SamplingPoint

from ..utils.general import databaseDateFormat

class SamplingPointModel(MoloModel):
    """
    A model to display the sampling points.
    """
    def __init__(self, queries):
        super().__init__(queries)
        self.data = [] #List of SamplingPoint objects

    def update_data(self):
        while self.queries[0].next():
            newSPoint = SamplingPoint(self.queries[0].value(0), self.queries[0].value(1),self.queries[0].value(2),self.queries[0].value(3), self.queries[0].value(4))
            self.data.append(newSPoint)

    def get_all_sampling_points(self):
        return self.data

    def reset_data(self):
        self.data = []

class SamplingPointManager:
    def __init__(self, con : QSqlDatabase, studyName : str):
        """
        A concrete class to handle operations on a sampling points, such as adding or removing a sampling point.
        An instance of this class is always tied to a study.

        To bind the frontened view displaying the sampling points in the study, a getter is implemented returning the model.
        """
        self.con = con
        self.spointModel = SamplingPointModel([])

        select_study_id = self.build_study_id(studyName)
        select_study_id.exec()
        select_study_id.next()
        self.studyID = select_study_id.value(0)
        self.studyName = studyName

    def get_spoint_model(self):
        return self.spointModel

    def get_spoints_names(self):
        """
        This function should only be called by frontend users.
        Return a list of all the sampling points names.
        """
        select_spoints = self.build_select_spoints()
        spoints = []
        select_spoints.exec()
        while select_spoints.next():
            spoints.append(select_spoints.value(0))
        return spoints

    def get_spoint(self, spointName : str):
        """
        Return a SamplingPoint object representing the sampling point with name spointName.
        """
        select_spoints = self.build_select_spoints(spointName)
        select_spoints.exec()
        select_spoints.next()
        return SamplingPoint(select_spoints.value(0), select_spoints.value(1),select_spoints.value(2), select_spoints.value(3), select_spoints.value(4))

    def refresh_spoints(self):
        """
        This function should only be called by frontend users.
        Refresh the sampling point model with appropriate information from the database.
        """
        select_spoints = self.build_select_spoints()
        self.spointModel.new_queries([select_spoints])

    def create_new_spoint(self, pointName : str, psensorName : str, shaftName :str, noticefile : str, configfile : str, infoDF : pd.DataFrame, prawDF : pd.DataFrame, trawDF : pd.DataFrame):
        """
        This function should only be called by frontend users.
        Create a new sampling point attached to the study currently opened (ie the one linked to this instance of SamplingPointManager).
        This function takes as arguments:
            -the name of the point being created, as well as the names of detectors it refers to
            -the path to the notice (.txt file) and the path to the configuration file (.png)
            -a dataframe representing the information about the sampling point
            -two dataframes representing the raw temperatre and pressure measures. Theses dataframes must have the correct structure and must not contain empty fields (they are already processed).
        """
        pointID = self.insert_new_point(pointName, psensorName, shaftName, noticefile, configfile, infoDF)

        #Convert datetime objects (here Timestamp objects) into a string with correct date format.
        trawDF["Date"] = trawDF["Date"].dt.strftime(databaseDateFormat())
        prawDF["Date"] = prawDF["Date"].dt.strftime(databaseDateFormat())

        #Pressure records
        self.con.transaction()
        insertRawPress = self.build_insert_raw_pressures()
        insertRawPress.bindValue(":SamplingPoint", pointID)
        for row in prawDF.itertuples():
            insertRawPress.bindValue(":Date", row[1])
            insertRawPress.bindValue(":TempBed", row[3])
            insertRawPress.bindValue(":Voltage", row[2])
            insertRawPress.exec()
        self.con.commit()

        #Temperature records
        self.con.transaction()
        insertRawTemp = self.build_insert_raw_temperatures()
        insertRawTemp.bindValue(":SamplingPoint", pointID)
        for row in trawDF.itertuples():
            insertRawTemp.bindValue(":Date", row[1])
            insertRawTemp.bindValue(":Temp1", row[2])
            insertRawTemp.bindValue(":Temp2", row[3])
            insertRawTemp.bindValue(":Temp3", row[4])
            insertRawTemp.bindValue(":Temp4", row[5])
            insertRawTemp.exec()
        self.con.commit()

    def insert_new_point(self, pointName : str, psensorName : str, shaftName :str, noticefile : str, configfile : str, infoDF : pd.DataFrame,):
        """
        Create a new Sampling Point in the database with the relevant information.
        Return the ID of the created point.
        """
        #Convert date objects (or here Timestamp objets) to string with correct date format
        infoDF[1][3] = infoDF[1][3].strftime(databaseDateFormat())
        infoDF[1][4] = infoDF[1][4].strftime(databaseDateFormat())

        insertPoint = self.build_insert_sampling_point()

        insertPoint.bindValue(":Name", pointName)
        insertPoint.bindValue(":Study", self.studyID)
        #Path to the notice file
        newNoticePath = os.path.join(os.path.dirname(self.con.databaseName()),"Notices", os.path.basename(noticefile))
        shutil.copy2(noticefile, newNoticePath)
        insertPoint.bindValue(":Notice", newNoticePath)
        #Extract relevant data from the infofile.
        insertPoint.bindValue(":Setup", infoDF.iloc[3].at[1])
        insertPoint.bindValue(":LastTransfer", infoDF.iloc[4].at[1])
        insertPoint.bindValue(":Offset", infoDF.iloc[6].at[1])
        insertPoint.bindValue(":RiverBed", infoDF.iloc[5].at[1])
        #Add the shaft's ID
        select_shaft_id = self.build_shaft_id(shaftName)
        select_shaft_id.exec()
        select_shaft_id.next()
        insertPoint.bindValue(":Shaft", select_shaft_id.value(0))
        #Add the pressure sensor's ID
        select_psensor_id = self.build_psensor_id(psensorName)
        select_psensor_id.exec()
        select_psensor_id.next()
        insertPoint.bindValue(":PressureSensor", select_psensor_id.value(0))
        #Path to the configuration file
        newConfigPath = os.path.join(os.path.dirname(self.con.databaseName()),"Schemes", os.path.basename(configfile))
        shutil.copy2(configfile, newConfigPath)
        insertPoint.bindValue(":Scheme", newConfigPath)
        #Default cleanup script
        cleanupScriptPath = os.path.join(os.path.dirname(self.con.databaseName()),"Scripts", "sample_text.txt")
        insertPoint.bindValue(":CleanupScript", cleanupScriptPath)

        insertPoint.exec()
        return insertPoint.lastInsertId()

    def build_study_id(self, studyName : str):
        """
        Build and return a query giving the ID of the study called studyName.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"SELECT Study.ID FROM Study WHERE Study.Name ='{studyName}'")
        return query

    def build_select_spoints(self, spointName : str|None = None):
        """
        Build and return a query giving all the informations about the points in this study. If spointName is not None, return instead the information for this sampling point.
        """
        query = QSqlQuery(self.con)
        if spointName is None:
            query.prepare(f"""SELECT SamplingPoint.Name, PressureSensor.Name, Shaft.Name, SamplingPoint.RiverBed, SamplingPoint.Offset
                        FROM SamplingPoint
                        JOIN PressureSensor
                        ON SamplingPoint.PressureSensor = PressureSensor.ID
                        JOIN Shaft
                        ON SamplingPoint.Shaft = Shaft.ID
                        JOIN Study
                        ON SamplingPoint.Study = Study.ID
                        WHERE Study.ID = {self.studyID}
            """)
        else:
            query.prepare(f"""SELECT SamplingPoint.Name, PressureSensor.Name, Shaft.Name, SamplingPoint.RiverBed, SamplingPoint.Offset
                        FROM SamplingPoint
                        JOIN PressureSensor
                        ON SamplingPoint.PressureSensor = PressureSensor.ID
                        JOIN Shaft
                        ON SamplingPoint.Shaft = Shaft.ID
                        JOIN Study
                        ON SamplingPoint.Study = Study.ID
                        WHERE Study.ID = {self.studyID} AND SamplingPoint.Name = '{spointName}'
            """)
        return query

    def build_psensor_id(self, psensorName : str):
        """
        Build and return a query giving the ID of the pressure sensor in this study called psensorName.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"""SELECT PressureSensor.ID FROM PressureSensor
                        JOIN Labo
                        ON PressureSensor.Labo = Labo.ID
                        JOIN Study
                        ON Study.Labo = Labo.ID
                        WHERE Study.ID = '{self.studyID}' AND PressureSensor.Name = '{psensorName}'""")
        return query

    def build_shaft_id(self, shaftName : str):
        """
        Build and return a query giving the ID of the shaft in this study called shaftName.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"""SELECT Shaft.ID FROM Shaft
                        JOIN Labo
                        ON Shaft.Labo = Labo.ID
                        JOIN Study
                        ON Study.Labo = Labo.ID
                        WHERE Study.ID = '{self.studyID}' AND Shaft.Name = '{shaftName}'""")
        return query

    def build_insert_sampling_point(self):
        """
        Build and return a query which creates a Sampling Point.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"""INSERT INTO SamplingPoint (
                              Name,
                              Notice,
                              Setup,
                              LastTransfer,
                              Offset,
                              RiverBed,
                              Shaft,
                              PressureSensor,
                              Study,
                              Scheme,
                              CleanupScript)
                          VALUES (:Name, :Notice, :Setup, :LastTransfer, :Offset, :RiverBed, :Shaft, :PressureSensor, :Study, :Scheme, :CleanupScript)""")
        return query

    def build_insert_raw_pressures(self):
        """
        Build and return a query which fills the table with raw pressure readings.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"""INSERT INTO RawMeasuresPress (
                        Date,
                        TempBed,
                        Voltage,
                        SamplingPoint)
        VALUES (:Date, :TempBed, :Voltage, :SamplingPoint)""")
        return query

    def build_insert_raw_temperatures(self):
        """
        Build and return a query which fills the table with raw temperature readings.
        """
        query = QSqlQuery(self.con)
        query.prepare(f""" INSERT INTO RawMeasuresTemp (
                        Date,
                        Temp1,
                        Temp2,
                        Temp3,
                        Temp4,
                        SamplingPoint)
        VALUES (:Date, :Temp1, :Temp2, :Temp3, :Temp4, :SamplingPoint)""")
        return query