from PyQt5.QtSql import QSqlDatabase #Used only for type hints
import pandas as pd
from ..utils.general import convertDates

from ..backend.SamplingPointManager import SamplingPointManager
from ..backend.SPointCoordinator import SPointCoordinator
from .SamplingPointViewer import SamplingPointViewer

class StudyHandler:
    """
    A high-level concrete frontend class to handle the user's actions regarding a study.
    An instance of this class can:
        -open and close a study
        -call the backend to add or remove sampling points (SamplingPointManager)
        -open subwindows showing the results and computations related to sampling points in this study.
    An instance of this class is always linked to a study.
    """
    def __init__(self, con : QSqlDatabase, studyName : str):
        self.con = con
        self.studyName = studyName
        self.spointManager = SamplingPointManager(self.con, studyName)

        self.spointCoordinator = None
        self.spointViewer = None

    def getSPointModel(self):
        """
        Return the sampling point model.
        """
        return self.spointManager.get_spoint_model()

    def getSPointsNames(self):
        """
        Return the list of the names of the sampling points.
        """
        return self.spointManager.get_spoints_names()

    def refreshSpoints(self):
        """
        Refresh sampling points information
        """
        self.spointManager.refresh_spoints()

    def importSPoint(self, name : str, psensor : str, shaft : str, infofile : str, noticefile : str, configfile : str, prawfile : str, trawfile : str):
        """
        Import a new sampling point from given files.
        """
        #Cleanup the .csv files
        infoDF = pd.read_csv(infofile, header=None)
        infoDF[1][3] = pd.to_datetime(infoDF[1][3])
        infoDF[1][4] = pd.to_datetime(infoDF[1][4]) #Convert dates to datetime (or here Timestamp) objects
        #Readings csv
        dfpress = pd.read_csv(prawfile)
        dfpress.columns = ["Date", "Voltage", "Temp_Stream"]
        dfpress.dropna(inplace=True)
        convertDates(dfpress) #Convert dates to datetime (or here Timestamp) objects

        dftemp = pd.read_csv(trawfile)
        dftemp.columns = ["Date", "Temp1", "Temp2", "Temp3", "Temp4"]
        dftemp.dropna(inplace=True)
        convertDates(dftemp) #Convert dates to datetime (or here Timestamp) objects

        #Give the dataframes to the backend
        self.spointManager.create_new_spoint(name, psensor, shaft, noticefile, configfile, infoDF, dfpress, dftemp)
        self.spointManager.refresh_spoints()

    def openSPoint(self, spointName : str):
        """
        Open the sampling point with the name spointName.
        Return a viewer instance which can be added to a subwindow like a widget.
        """
        self.spointCoordinator = SPointCoordinator(self.con, self.studyName, spointName)
        samplingPoint = self.spointManager.get_spoint(spointName)
        self.spointViewer = SamplingPointViewer(self.spointCoordinator, samplingPoint)
        self.spointViewer.setWindowTitle(self.studyName)
        return self.spointViewer

    def close(self):
        """
        Close all subwindows and related processes.
        """
        pass