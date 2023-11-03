import pandas as pd

from PyQt5 import QtWidgets, uic
from scipy import stats

# from src.backend.SPointCoordinator import SPointCoordinator
# from src.Containers import SamplingPoint
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
import numpy as np

from .cleanupCanvases import CompareCanvas, SelectCanvas, createEmptyDf
from ..utils.general import convertDates, displayCriticalMessage
from ..utils.get_files import get_ui_asset

from ..backend.SPointCoordinator import SPointCoordinator
from ..interactions.Containers import SamplingPoint
from ..interactions.InnerMessages import CleanupStatus

From_DialogCleanup= uic.loadUiType(get_ui_asset("dialogCleanup.ui"))[0]
From_DialogSelectPoints= uic.loadUiType(get_ui_asset("dialogSelectPoints.ui"))[0]

class InvalidCSVStructure(Exception):
    pass

class DialogSelectPoints(QtWidgets.QDialog, From_DialogSelectPoints):
    """
    A small dialog to show a canvas (SelectCanvas) so the user can manually select points.
    """
    def __init__(self, reference_data : pd.DataFrame, field : str,  cleanedData : pd.DataFrame, selectedData : pd.DataFrame):
        # Call constructor of parent classes
        super(DialogSelectPoints, self).__init__()
        QtWidgets.QDialog.__init__(self)

        self.setupUi(self)
        self.pushButtonReset.clicked.connect(self.reset)

        self.mplCanvas = SelectCanvas(reference_data, field)
        self.mplCanvas.set_cleaned_data(cleanedData)
        self.mplCanvas.set_selected_data(selectedData)
        self.toolBar = NavigationToolbar2QT(self.mplCanvas, self)

        self.widgetToolBar.addWidget(self.toolBar)
        self.widgetSelectPoints.addWidget(self.mplCanvas)
        self.mplCanvas.plotData(field)

    def reset(self):
        self.mplCanvas.reset()

    def getSelectedPoints(self):
        return self.mplCanvas.getSelectedPoints()

class DialogCleanup(QtWidgets.QDialog, From_DialogCleanup):
    """
    A dialog to either automatically clean the raw measures, of to import cleaned measures.
    This dialog holds deals with 3 dataframes:
    - self.data is a big dataframe with all the measures (= raw measures)
    - self.manuallySelected is a subset of self.data holding the points selected by the user which should be removed
    - cleanedData is a subset of self.data holding the points selected by the outliers methods which should be removed

    Note: currently cleanedData is recomputed everytime we need it. If this becomes an issue, we should change it.
    """
    def __init__(self, coordinator : SPointCoordinator, spoint : SamplingPoint):# coordinator : SPointCoordinator, point : SamplingPoint):
        super(DialogCleanup, self).__init__()
        QtWidgets.QDialog.__init__(self)

        self.setupUi(self)
        self.coordinator = coordinator
        self.spoint = spoint

        self.uiToDF = {"Differential pressure" : "Pressure",
                    "Temperature at depth 1": "Temp1",
                    "Temperature at depth 2": "Temp2",
                    "Temperature at depth 3": "Temp3",
                    "Temperature at depth 4": "Temp4",
                    "Stream Temperature" : "TempBed"
                    } # Conversion between what is displayed on the ui and the corresponding DF column.
        self.comboBoxRawVar.addItems(list(self.uiToDF.keys()))

        self.radioButtonNone.setChecked(True) # This should already be done in the UI
        self.radioButtonC.setChecked(True) # This should already be done in the UI

        self.radioButtonNone.clicked.connect(self.setNoneComputation) # This should already be done in the UI
        self.radioButtonIQR.clicked.connect(self.setIQRComputation)
        self.radioButtonZScore.clicked.connect(self.setZScoreComputation)
        self.radioButtonF.clicked.connect(self.refreshPlot)
        self.radioButtonK.clicked.connect(self.refreshPlot)
        self.radioButtonC.clicked.connect(self.refreshPlot)
        self.comboBoxRawVar.currentIndexChanged.connect(self.showNewVar)
        self.pushButtonResetAll.clicked.connect(self.reset)
        self.tabWidget.currentChanged.connect(self.switchTab)
        self.pushButtonBrowse.clicked.connect(self.browse)
        self.pushButtonSelectPoints.clicked.connect(self.openSelectPointsWindow)

        self.spinBoxStartDay.valueChanged.connect(self.refreshPlot)
        self.spinBoxStartMonth.valueChanged.connect(self.refreshPlot)
        self.spinBoxStartYear.valueChanged.connect(self.refreshPlot)
        self.spinBoxEndDay.valueChanged.connect(self.refreshPlot)
        self.spinBoxEndMonth.valueChanged.connect(self.refreshPlot)
        self.spinBoxEndYear.valueChanged.connect(self.refreshPlot)

        self.varStatus = {"Pressure" : CleanupStatus.NONE,
                          "Temp1" : CleanupStatus.NONE,
                          "Temp2" : CleanupStatus.NONE,
                          "Temp3" : CleanupStatus.NONE,
                          "Temp4" : CleanupStatus.NONE,
                          "TempBed" : CleanupStatus.NONE
                        } # The cleanup status for every variable: initially, we don't do anything.
        self.data = None
        self.intercept, self.dUdH, self.dUdT = self.coordinator.calibration_infos()
        self.buildDF()
        self.convertVoltagePressure()
        self.setupStartEndDates()

        self.manuallySelected = createEmptyDf()

        self.mplCanvas = CompareCanvas(self.data)
        self.toolBar = NavigationToolbar2QT(self.mplCanvas,self)
        self.widgetToolBar.addWidget(self.toolBar)
        self.widgetRawData.addWidget(self.mplCanvas)

        self.refreshPlot()

    def buildDF(self):
        """
        Fetch raw measures from the coordinator, and arrange them all in one big panda dataframe stored in self.data.
        """
        backend_data = self.coordinator.all_raw_measures()
        self.data = pd.DataFrame(backend_data, columns = ["Date","Temp1", "Temp2", "Temp3", "Temp4", "TempBed", "Voltage"])

    def convertVoltagePressure(self):
        """
        Convert the Voltage column into a (differential) Pressure field, taking into account the calibration information.
        This should only be called once, as we'd rather have the user speak in terms of differential pressure than in Voltage.
        """
        self.data["Pressure"] = (self.data["Voltage"] - self.data["TempBed"]*self.dUdT - self.intercept)/self.dUdH
        self.data.drop(labels="Voltage", axis = 1, inplace = True)

    def setupStartEndDates(self):
        """
        Fill the combo boxes with the first date and the last date in the dataframe.
        """
        # Block the signals so refreshPlot isn't called 6 times.
        for spin in [self.spinBoxStartDay, self.spinBoxStartMonth, self.spinBoxStartYear, self.spinBoxEndDay, self.spinBoxEndMonth, self.spinBoxEndYear]:
            spin.blockSignals(True)

        startDate = self.data["Date"].iloc[0]
        self.spinBoxStartDay.setValue(startDate.day)
        self.spinBoxStartMonth.setValue(startDate.month)
        self.spinBoxStartYear.setValue(startDate.year)
        endDate = self.data["Date"].iloc[-1]
        self.spinBoxEndDay.setValue(endDate.day)
        self.spinBoxEndMonth.setValue(endDate.month)
        self.spinBoxEndYear.setValue(endDate.year)

        # Re-enable the signals
        for spin in [self.spinBoxStartDay, self.spinBoxStartMonth, self.spinBoxStartYear, self.spinBoxEndDay, self.spinBoxEndMonth, self.spinBoxEndYear]:
            spin.blockSignals(False)

    def setNoneComputation(self):
        """
        Set None cleanup rule for the current variable.
        """
        var = self.uiToDF[self.comboBoxRawVar.currentText()]
        self.varStatus[var] = CleanupStatus.NONE
        self.refreshPlot()

    def setIQRComputation(self):
        """
        Set IQR cleanup rule for the current variable.
        """
        var = self.uiToDF[self.comboBoxRawVar.currentText()]
        self.varStatus[var] = CleanupStatus.IQR
        self.refreshPlot()

    def setZScoreComputation(self):
        """
        Set Z-Score cleanup rule for the current variable.
        """
        var = self.uiToDF[self.comboBoxRawVar.currentText()]
        self.varStatus[var] = CleanupStatus.ZSCORE
        self.refreshPlot()

    def showNewVar(self):
        """
        Refresh the plots and update the radio buttons for the current variable.
        """
        var = self.uiToDF[self.comboBoxRawVar.currentText()]
        if self.varStatus[var] == CleanupStatus.NONE:
            self.radioButtonNone.setChecked(True)
        elif self.varStatus[var] == CleanupStatus.IQR:
            self.radioButtonIQR.setChecked(True)
        elif self.varStatus[var] == CleanupStatus.ZSCORE:
            self.radioButtonZScore.setChecked(True)

        self.refreshPlot()

    def computeCleanedData(self):
        """
        Create and return a new dataframe holding the points which should be removed. These points are given by the ouliers methods.
        """
        cleanedData = createEmptyDf()
        cleanedData = self.applyCleanupChanges(cleanedData)
        cleanedData = self.applyDateBoundariesChanges(cleanedData)
        return cleanedData

    def refreshPlot(self):
        """
        Refresh the plot according to the variable the user is looking at.
        Currently, this implies recomputing the for every variable the decomposition (IQR, Zscore or None). If this is problem, this should be changed: however, we are only looking at ~10 variables on a dataframe of ~5000 entries, so it really shouldn't be a limitation.
        """
        cleanedData = self.computeCleanedData()
        reference_data, cleanedData = self.applyTemperatureChanges(cleanedData)

        self.mplCanvas.setReferenceData(reference_data)
        self.mplCanvas.set_cleaned_data(cleanedData)
        self.mplCanvas.set_selected_data(self.manuallySelected)
        displayVar = self.uiToDF[self.comboBoxRawVar.currentText()]
        self.mplCanvas.plotData(displayVar)

    def applyDateBoundariesChanges(self, cleanedData : pd.DataFrame):
        """
        Apply date restriction on the total dataframe. The rejected points (ie those which should not be kept) should be merged into the dataframe given as argument.
        Return the total merged dataframe (original + point outside date of the boundaries given by the spinboxes)
        In any of the following cases, no point is rejected, and the input dataframe is returned:
        - the start date is after the last date in the dataframe
        - the end date is before the first date in the dataframe
        - the end date is before the start date
        """
        pd_startDate = pd.Timestamp(day = self.spinBoxStartDay.value(),
                                    month = self.spinBoxStartMonth.value(),
                                    year = self.spinBoxStartYear.value(),
                                    hour = 0,
                                    minute = 0,
                                    second = 0)
        pd_endDate = pd.Timestamp(day = self.spinBoxEndDay.value(),
                                month = self.spinBoxEndMonth.value(),
                                year = self.spinBoxEndYear.value(),
                                hour = 23,
                                minute = 59,
                                second = 59)
        if pd_startDate > self.data["Date"].max():
            return cleanedData
        elif pd_endDate < self.data["Date"].min():
            return cleanedData
        elif pd_startDate > pd_endDate:
            return cleanedData
        else:
            mask =  (self.data["Date"] > pd_endDate) | (self.data["Date"] < pd_startDate)
            cleanedData = pd.concat([cleanedData, self.data[mask]], axis = 0)
            cleanedData.drop_duplicates(inplace = True)
            cleanedData.dropna(inplace = True) # For sanity purposes
            return cleanedData

    def applyCleanupChanges(self, cleanedData : pd.DataFrame):
        """
        Apply the cleanup changes requested for every variable. The rejected points (ie those which should not be kept) should be merged into the dataframe given as argument.
        Return the total merged dataframe (original + all changed made by every outlier method)
        """
        for i, (varName, varStatus) in enumerate(self.varStatus.items()):
            if varStatus == CleanupStatus.NONE:
                # Nothing to be done, move on!
                continue
            elif varStatus == CleanupStatus.IQR:
                df_to_remove = self.applyIQR(varName)
            elif varStatus == CleanupStatus.ZSCORE:
                df_to_remove = self.applyZScore(varName)

            cleanedData = pd.concat([cleanedData, df_to_remove], axis = 0)
            cleanedData.drop_duplicates(inplace = True)
        cleanedData.dropna(inplace = True) # For sanity purposes
        return cleanedData

    def applyIQR(self, varName : str):
        """
        Applies IQR method to the total dataframe on variable varName. Return a list of the points which should be removed.
        """
        q1 = self.data[varName].quantile(0.25)
        q3 = self.data[varName].quantile(0.75)
        iqr = q3-q1 #Interquartile range
        fence_low  = q1-1.5*iqr
        fence_high = q3+1.5*iqr

        mask = (self.data[varName] < fence_low) | (self.data[varName] > fence_high)
        return self.data[mask]

        # cleanedData.drop(cleanedData.loc[cleanedData[varName] < fence_low].index, inplace = True)
        # cleanedData.drop(cleanedData.loc[cleanedData[varName] > fence_high].index, inplace = True)

    def applyZScore(self, varName : str):
        """
        Applies IQR method to the total dataframe on variable varName. Return a list of the points which should be removed.
        """
        mask = (np.abs(stats.zscore(self.data[varName])) > 3)
        return self.data[mask]

    def CtoF(self, x):
        return x*1.8 + 32

    def CtoK(self,x):
        return x+273.15

    def applyTemperatureChanges(self, cleanedData : pd.DataFrame):
        """
        Return two dataframes:
            - the first is a copy of self.data, with a temperature conversion. self.data must not be modified.
            - the second is the given cleanedData dataframe onto which a temperature conversion has been done. cleanedData can be modified
        This function builds on the fact that self.data and cleanedData have values in °C.
        """
        if self.radioButtonC.isChecked():
            return self.data, cleanedData # Nothing to change
        else:
            if self.radioButtonF.isChecked():
                convertFun = self.CtoF
            elif self.radioButtonK.isChecked():
                convertFun = self.CtoK

            referenceData = self.data.copy(deep = True)
            referenceData[["Temp1","Temp2","Temp3","Temp4", "TempBed"]] = referenceData[["Temp1","Temp2","Temp3","Temp4", "TempBed"]].apply(convertFun)
            cleanedData[["Temp1","Temp2","Temp3","Temp4", "TempBed"]] = cleanedData[["Temp1","Temp2","Temp3","Temp4", "TempBed"]].apply(convertFun)

            return referenceData, cleanedData

    def reset(self):
        """
        Discard all cleanup changes made.
        """
        self.varStatus = {"Pressure" : CleanupStatus.NONE,
                          "Temp1" : CleanupStatus.NONE,
                          "Temp2" : CleanupStatus.NONE,
                          "Temp3" : CleanupStatus.NONE,
                          "Temp4" : CleanupStatus.NONE,
                          "TempBed" : CleanupStatus.NONE
                        } # No cleanup done by default.
        self.radioButtonNone.setChecked(True)
        self.manuallySelected = createEmptyDf()
        self.mplCanvas.set_cleaned_data(createEmptyDf())
        self.setupStartEndDates()

        self.refreshPlot()

    def openSelectPointsWindow(self):
        """
        Open a small windwo allowing the user to select manually points for the current variable.
        WARNING: this should be the last thing the user does before quitting the Cleanup window. If the user selects points THEN applies an outlier method, the selected points will be discarded.
        """
        field = self.uiToDF[self.comboBoxRawVar.currentText()]
        cleanedData = self.computeCleanedData()
        dlg = DialogSelectPoints(self.data, field, cleanedData, self.manuallySelected)
        res = dlg.exec()
        if res == QtWidgets.QDialog.Accepted:
            selected = dlg.getSelectedPoints()
            self.manuallySelected = pd.concat([self.manuallySelected, selected], axis = 0)
            self.manuallySelected.drop_duplicates(inplace = True)
            self.manuallySelected.dropna(inplace=True)
            self.refreshPlot()

    def browse(self):
        filePath = QtWidgets.QFileDialog.getOpenFileName(self, "Get Cleaned Measures File","", "CSV files (*.csv)")[0]
        if filePath:
            self.lineEditBrowseCleaned.setText(filePath)

    def switchTab(self):
        """
        Method called when user switches tab. For now, this resets the line edit with the path to the cleaned measures.
        """
        self.lineEditBrowseCleaned.setText("")

    def importCleanedData(self, path):
        """
        Given a path to a .csv file, open it and get relevant information for the backend. Return a dataframe with the correct structure.
        WARNING: this function MUST return a dataframe with exactly the structure defined, and without any NaNs, empty blanks...
        """
        # TODO: improve this function!
        df = pd.read_csv(path)
        columnnames = df.columns.values.tolist()
        if columnnames != ["Date","Temp1", "Temp2", "Temp3", "Temp4", "TempBed", "Pressure"]:
            displayCriticalMessage("The columns must be named (in this order): Date, Temp1, Temp2, Temp3, Temp4, TempBed, Pressure.")
            raise InvalidCSVStructure
        #The backend will call something like row[1] to have the Date. The first column must be the index, and not relevant data. Check if there is an index.
        if not(pd.Index(np.arange(0,len(df))).equals(df.index)):
            displayCriticalMessage("The dataframe must have the default index column as a numbering method.")
            raise InvalidCSVStructure
        df.dropna(inplace=True)

        try:
            convertDates(df)
        except Exception as e:
            displayCriticalMessage("The 'Date' column can't be converted to datetime objects.")
            raise InvalidCSVStructure
        return df

    def getCleanedMeasures(self):
        """
        Return the dataframe with the cleaned measures.
        Return an empty dataframe if something went wrong and the measures couldn't get extracted.
        """
        pathToCleaned = self.lineEditBrowseCleaned.text()
        if pathToCleaned == "":
            cleanedData = self.computeCleanedData()
            cleaned_u_selected = pd.concat([cleanedData, self.manuallySelected], axis = 0)
            cleaned_u_selected.drop_duplicates(inplace = True)
            cleaned_u_selected.dropna(inplace=True)

            df_to_keep = self.data.merge(cleaned_u_selected, on=["Date", "Temp1","Temp2", "Temp3", "Temp4", "TempBed", "Pressure"], how = 'left', indicator = True)
            untouched = df_to_keep[df_to_keep["_merge"] == "left_only"].copy(deep = True)
            return untouched
        else:
            try:
                cleanedData = self.importCleanedData(pathToCleaned)
            except Exception as e:
                cleanedData = pd.DataFrame() #Empty Dataframe
        return cleanedData
