import os
import re #Regular expression, to check if a pattern is in a string.
from PyQt5 import QtWidgets, uic
import pandas as pd
from numpy import float64
from ..utils.general import displayCriticalMessage
from ..utils.get_files import get_ui_asset

from .StudyHandler import StudyHandler
from .LabHandler import LabHandler

From_DialogImportSPoint = uic.loadUiType(get_ui_asset("dialogImportSPoint.ui"))[0]

class DialogImportSPoint(QtWidgets.QDialog, From_DialogImportSPoint):
    """
    Enable the user to pick the paths to the files needed for the creation of a sampling point in the database. Also check if the overall structure of the files is correct.
    """
    def __init__(self, studyHandler : StudyHandler, labHandler : LabHandler):
        super(DialogImportSPoint, self).__init__()
        QtWidgets.QDialog.__init__(self)

        self.setupUi(self)
        self.studyHandler = studyHandler
        self.labHandler = labHandler

        self.radioButtonAuto.clicked.connect(self.changeEntryType)
        self.radioButtonManual.clicked.connect(self.changeEntryType)

        self.pushButtonBrowseDataDir.clicked.connect(self.browseDataDir)
        self.pushButtonBrowseInfo.clicked.connect(self.browseInfo)
        self.pushButtonBrowsePressures.clicked.connect(self.browsePressures)
        self.pushButtonBrowseTemperatures.clicked.connect(self.browseTemperatures)
        self.pushButtonBrowseNotice.clicked.connect(self.browseNotice)
        self.pushButtonBrowseConfig.clicked.connect(self.browseConfig)

        #By default, check the automatic entry.
        self.radioButtonAuto.click()

    def accept(self):
        """
        This is an overloaded function, called when the user presses the "OK" button.
        This function runs integrity checks on the database before allowing the dialog to be closed. Theses checks make sure the name of the point, the pressure sensor and the shaft respect database integrity: the point must not already be in the study and the sensors must exist.
        """
        points = self.studyHandler.getSPointsNames()
        psensors = self.labHandler.getPSensorsNames()
        shafts = self.labHandler.getShaftsNames()

        if not self.lineEditPointName.text() or not self.lineEditPSensorName.text() or not self.lineEditShaftName.text():
            displayCriticalMessage("The name of the point, the pressure sensor and the shaft cannot be empty.")
            return
        if self.lineEditPointName.text() in points:
            displayCriticalMessage(f"There is already a point with the name {self.lineEditPointName.text()} in the database for this laboratory. Please select an other name.")
            return
        if self.lineEditPSensorName.text() not in psensors:
            displayCriticalMessage(f"There is no pressure sensor with the name {self.lineEditPSensorName.text()} in the database for this laboratory.")
            return
        if self.lineEditShaftName.text() not in shafts:
            displayCriticalMessage(f"There is no shaft with the name {self.lineEditShaftName.text()} in the database for this laboratory.")
            return

        if not self.lineEditPressures.text() or not self.lineEditTemperatures.text() or not self.lineEditNotice.text() or not self.lineEditConfig.text():
            displayCriticalMessage(f"All file paths must be completed.")
            return
        #All test have been passed: close the dialog.
        super().accept()

    def changeEntryType(self):
        """
        According to the state of the radio buttons, either enable auto entry while disabling manual entry or disable auto entry while enabling manual entry.
        """
        if self.radioButtonAuto.isChecked():
            self.pushButtonBrowseDataDir.setEnabled(True)
            self.pushButtonBrowseInfo.setEnabled(False)
            self.pushButtonBrowsePressures.setEnabled(False)
            self.pushButtonBrowseTemperatures.setEnabled(False)
            self.pushButtonBrowseNotice.setEnabled(False)
            self.pushButtonBrowseConfig.setEnabled(False)
        else:
            self.pushButtonBrowseDataDir.setEnabled(False)
            self.pushButtonBrowseInfo.setEnabled(True)
            self.pushButtonBrowsePressures.setEnabled(True)
            self.pushButtonBrowseTemperatures.setEnabled(True)
            self.pushButtonBrowseNotice.setEnabled(True)
            self.pushButtonBrowseConfig.setEnabled(True)

    def browseDataDir(self):
        """
        Display a dialog allowing the user to choose the directory from which the point should be imported. Then, try to extract from this directory the necessary files and check if the critical csv files have the correct structure.
        """
        dirPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Point Directory")
        if dirPath:
            self.lineEditDataDir.setText(dirPath)
            files = list(os.listdir(dirPath))
            #The following list is used to check if there is at least one file for all fields.
            paths = [None,None,None,None,None] #Info, .png, notice, P_, T_
            for file in files :
                if re.search('info', file) and not paths[0]:
                    filePath = os.path.join(dirPath, file)
                    success, pointName, psensorName, shaftName = self.checkInfoIntegrity(filePath)
                    if success:
                        paths[0] = filePath
                        self.lineEditPointName.setText(pointName)
                        self.lineEditPSensorName.setText(psensorName)
                        self.lineEditShaftName.setText(shaftName)
                        self.lineEditInfo.setText(filePath)
                    #The file is ignored if pandas can't read the file or extract data.
                if re.search('.png', file) and not paths[1]:
                    filePath = os.path.join(dirPath, file)
                    paths[1] = filePath
                    self.lineEditConfig.setText(filePath)
                if re.search('notice', file) and not paths[2]:
                    filePath = os.path.join(dirPath, file)
                    paths[2] = filePath
                    self.lineEditNotice.setText(filePath)
                if re.search('P_', file) and not paths[3]:
                    filePath = os.path.join(dirPath, file)
                    if self.checkPressureFileIntegrity(filePath):
                        paths[3] = filePath
                        self.lineEditPressures.setText(filePath)
                if re.search('T_', file) and not paths[4]:
                    filePath = os.path.join(dirPath, file)
                    if self.checkTemperatureFileIntegrity(filePath):
                        paths[4] = filePath
                        self.lineEditTemperatures.setText(filePath)
            #Now handle all error messages.
            nPath = len([elem for elem in paths if elem])
            if nPath<5 :
                displayCriticalMessage(f'Only {nPath} lines have been successfully filled. Please check your files have the correct structure and fill in the missing information manually.')
                self.lineEditDataDir.setText('')
                self.radioButtonManual.click()

    def browseInfo(self):
        """
        Display a dialog so that the user may choose the Info file: then, check if it has the correct structure.
        """
        filePath = QtWidgets.QFileDialog.getOpenFileName(self, "Get Info File","", "CSV files (*.csv)")[0]
        if filePath:
            success, pointName, psensorName, shaftName = self.checkInfoIntegrity(filePath)
            if success:
                self.lineEditPointName.setText(pointName)
                self.lineEditPSensorName.setText(psensorName)
                self.lineEditShaftName.setText(shaftName)
                self.lineEditInfo.setText(filePath)
            else:
                displayCriticalMessage("Something went wrong and the file couldn't be imported. Check its structure and try again")
                self.lineEditPointName.setText('')
                self.lineEditPSensorName.setText('')
                self.lineEditShaftName.setText('')
                self.lineEditInfo.setText('')

    def browsePressures(self):
        """
        Display a dialog so that the user may choose the file with the pressure readings: then, check if it has the correct structure.
        """
        filePath = QtWidgets.QFileDialog.getOpenFileName(self, "Get Pressure Measures File","", "CSV files (*.csv)")[0]
        if filePath:
            if self.checkPressureFileIntegrity(filePath):
                self.lineEditPressures.setText(filePath)

    def browseTemperatures(self):
        """
        Display a dialog so that the user may choose the file with the themperature readings: then, check if it has the correct structure.
        """
        filePath = QtWidgets.QFileDialog.getOpenFileName(self, "Get Temperature Measures File","", "CSV files (*.csv)")[0]
        if filePath:
            if self.checkTemperatureFileIntegrity(filePath):
                self.lineEditTemperatures.setText(filePath)

    def browseNotice(self):
        """
        Display a dialog so that the user may choose the notice file (a .txt file).
        """
        filePath = QtWidgets.QFileDialog.getOpenFileName(self, "Get Notice File","", "Text files (*.txt)")[0]
        if filePath:
            self.lineEditNotice.setText(filePath)

    def browseConfig(self):
        """
        Display a dialog so that the user may choose the config file (a .png or .jpg file).
        """
        filePath = QtWidgets.QFileDialog.getOpenFileName(self, "Get Configuration File","", "Image files (*.jpg *png)")[0]
        if filePath:
            self.lineEditConfig.setText(filePath)

    def checkInfoIntegrity(self, filePath : str):
        """
        If the Info file has the correct configuration, return True and the name of the point, pressure sensor and shaft.
        If the Info file has the wrong configuration, return False and empty strings.
        """
        try:
            df = pd.read_csv(filePath, header=None, index_col=0)
            pointName = df.iloc[0].at[1]
            psensorName = df.iloc[1].at[1]
            shaftName = df.iloc[2].at[1]
            return True, pointName, psensorName,shaftName
        except:
            return False, "", "", ""

    def checkPressureFileIntegrity(self, filePath : str):
        """
        Return True if the file with the pressure readings has the correct structure (at least 4 columns with 2 columns - voltage and temperature - being floats).
        """
        try:
            df = pd.read_csv(filePath)
            if df.shape[1] != 3 : # Date + Voltage + Temperature
                print(f"The number of columns in pressure file {os.path.basename(filePath)} doesn't match. This file will be ignored.")
                return False
            if df.dtypes[1]!=float64 or df.dtypes[2]!=float64: #Voltage and Temperature must be floats
                print(f"The Voltage and Temperature columns are not floats in file {os.path.basename(filePath)}. This file will be ignored.")
                return False
        except Exception as e:
            print(f"An error has occured while reading the file {os.path.basename(filePath)} : {str(e)}. This file will be ignored.")
            return False
        return True


    def checkTemperatureFileIntegrity(self, filePath : str):
        """
        Return True if the file with the temperature readings has the correct structure (at least 6 columns with 4 columns - corresponding to the temperatures - being floats).
        """
        try:
            df = pd.read_csv(filePath)
            if df.shape[1] != 5 : #Date + 4 Temperatures
                print(f"The number of columns in temperature file {os.path.basename(filePath)} doesn't match. This file will be ignored.")
                return False
            if df.dtypes[1]!=float64 or df.dtypes[2]!=float64 or df.dtypes[3]!=float64 or df.dtypes[4]!=float64: #the 4 temperatures must be floats
                print(f"The Temperature columns are not floats in file {os.path.basename(filePath)}. This file will be ignored.")
                return False
        except Exception as e:
            print(f"An error has occured while reading the file {os.path.basename(filePath)} : {str(e)}. This file will be ignored.")
            return False
        return True

    def getSPointInfo(self):
        """
        Retrieve all data from the dialog: the name of the point and the sensors, as well as the paths to the files.
        """
        name = self.lineEditPointName.text()
        psensor = self.lineEditPSensorName.text()
        shaft = self.lineEditShaftName.text()
        infofile = self.lineEditInfo.text()
        prawfile = self.lineEditPressures.text()
        trawfile = self.lineEditTemperatures.text()
        noticefile = self.lineEditNotice.text()
        configfile = self.lineEditConfig.text()
        return name, psensor, shaft, infofile, noticefile, configfile, prawfile, trawfile