import csv
from PyQt5 import QtWidgets, QtCore, uic, QtGui
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from ..interactions.Containers import SamplingPoint
from ..interactions.InnerMessages import ComputationsState
from ..backend.SPointCoordinator import SPointCoordinator
from ..backend.Compute import Compute

from .GraphViews import PressureView, TemperatureView,UmbrellaView,TempDepthView,TempMapView,AdvectiveFlowView, ConductiveFlowView, TotalFlowView, WaterFluxView, Log10KView, ConductivityView, PorosityView, CapacityView
from .dialogExportCleanedMeasures import DialogExportCleanedMeasures
from .dialogConfirm import DialogConfirm
from .dialogsCleanup import DialogCleanup
from .dialogCompute import DialogCompute
from ..utils.get_files import get_ui_asset


From_SamplingPointViewer = uic.loadUiType(get_ui_asset("SamplingPointViewer.ui"))[0]

class SamplingPointViewer(QtWidgets.QWidget, From_SamplingPointViewer):

    def __init__(self, spointCoordinator : SPointCoordinator, samplingPoint: SamplingPoint):
        # Call constructor of parent classes
        super(SamplingPointViewer, self).__init__()
        QtWidgets.QWidget.__init__(self)

        self.samplingPoint = samplingPoint
        self.coordinator = spointCoordinator
        self.computeEngine = Compute(self.coordinator)
        self.computeEngine.DirectModelFinished.connect(self.updateAllViews)
        self.computeEngine.MCMCFinished.connect(self.updateAllViews)

        self.setupUi(self)

        #This should already be done in the .ui file
        self.checkBoxRawData.setChecked(True)
        self.checkBoxDirectModel.setChecked(True)
        self.radioButtonTherm1.setChecked(True)
        #By default, this widget tries to maximize the size of the boxes, even if they are empty.
        self.tempSplitterVertical.setSizes([QtGui.QGuiApplication.primaryScreen().virtualSize().height(),QtGui.QGuiApplication.primaryScreen().virtualSize().height()])
        self.tempSplitterHorizLeft.setSizes([QtGui.QGuiApplication.primaryScreen().virtualSize().width(),QtGui.QGuiApplication.primaryScreen().virtualSize().width()])
        self.tempSplitterHorizRight.setSizes([QtGui.QGuiApplication.primaryScreen().virtualSize().width(),QtGui.QGuiApplication.primaryScreen().virtualSize().width()])
        self.fluxesSplitterVertical.setSizes([QtGui.QGuiApplication.primaryScreen().virtualSize().height(),QtGui.QGuiApplication.primaryScreen().virtualSize().height()])
        self.fluxesSplitterHorizLeft.setSizes([QtGui.QGuiApplication.primaryScreen().virtualSize().width(),QtGui.QGuiApplication.primaryScreen().virtualSize().width()])
        self.fluxesSplitterHorizRight.setSizes([QtGui.QGuiApplication.primaryScreen().virtualSize().width(),QtGui.QGuiApplication.primaryScreen().virtualSize().width()])

        #Create all view and link them to the correct models
        self.graphpress = PressureView(self.coordinator.get_pressure_model())
        self.graphtemp = TemperatureView(self.coordinator.get_temp_model())
        self.waterflux_view = WaterFluxView(self.coordinator.get_water_fluxes_model())
        fluxesModel = self.coordinator.get_heatfluxes_model()
        self.advective_view = AdvectiveFlowView(fluxesModel)
        self.conductive_view = ConductiveFlowView(fluxesModel)
        self.totalflux_view = TotalFlowView(fluxesModel)
        tempMapModel = self.coordinator.get_temp_map_model()
        self.umbrella_view = UmbrellaView(tempMapModel)
        self.tempmap_view = TempMapView(tempMapModel)
        self.depth_view = TempDepthView(tempMapModel)
        paramsDistrModel = self.coordinator.get_params_distr_model()
        self.logk_view = Log10KView(paramsDistrModel)
        self.conductivity_view = ConductivityView(paramsDistrModel)
        self.porosity_view = PorosityView(paramsDistrModel)
        self.capacity_view = CapacityView(paramsDistrModel)

        self.layoutsRules = self.initialiseLayoutsRules()

        #This allows to create 4 graphs in a square with one vertical and one horizontal splitter.
        self.tempSplitterHorizLeft.splitterMoved.connect(self.adjustTempRightSplitter)
        self.tempSplitterHorizRight.splitterMoved.connect(self.adjustTempLeftSplitter)
        self.fluxesSplitterHorizLeft.splitterMoved.connect(self.adjustFluxesRightSplitter)
        self.fluxesSplitterHorizRight.splitterMoved.connect(self.adjustFluxesLeftSplitter)


        # Link every button to their function
        self.comboBoxSelectLayer.textActivated.connect(self.changeDisplayedParams)
        self.radioButtonTherm1.clicked.connect(self.refreshTempDepthView)
        self.radioButtonTherm2.clicked.connect(self.refreshTempDepthView)
        self.radioButtonTherm3.clicked.connect(self.refreshTempDepthView)
        self.checkBoxDirectModel.stateChanged.connect(self.refreshTempDepthView)
        self.pushButtonReset.clicked.connect(self.reset)
        self.pushButtonCleanUp.clicked.connect(self.cleanup)
        self.pushButtonCompute.clicked.connect(self.compute)
        self.pushButtonExportMeasures.clicked.connect(self.exportMeasures)
        self.checkBoxRawData.stateChanged.connect(self.changeMeasuresState)
        self.pushButtonRefreshBins.clicked.connect(self.refreshbins)
        self.horizontalSliderBins.valueChanged.connect(self.labelUpdate)

        #Enable or disable computations buttons
        self.handleComputationsButtons()

        #Prepare all the tabs.
        self.setWidgetInfos()
        self.setInfoTab()
        self.setupCheckboxesQuantiles()
        self.setPressureAndTemperatureTables()
        self.updateAllViews()

    def initialiseLayoutsRules(self):
        """
        Build a dictionnary containing the rules to which the layouts must abide:
            -keys are the layouts of this window
            -values are a tuple. The first element corresponds to a view, the second is a message (string).
        This way, a layout can know which view it must show, or, if it shouldn't show the view, what type of message it should show.
        """
        default_message = "No model has been computed yet"
        layoutsRules = {self.pressVBox : (self.graphpress, "Measures haven't been cleaned yet"),
                            self.tempVBox : (self.graphtemp, "Measures haven't been cleaned yet"),
                            self.waterFluxVBox : (self.waterflux_view, default_message),
                            self.advectiveFluxVBox : (self.advective_view, default_message),
                            self.conductiveFluxVBox : (self.conductive_view, default_message),
                            self.totalFluxVBox : (self.totalflux_view, default_message),
                            self.topRightVLayout : (self.depth_view, default_message),
                            self.botLeftVLayout : (self.umbrella_view, default_message),
                            self.botRightVLayout : (self.tempmap_view, default_message),
                            self.log10KVBox : (self.logk_view, default_message),
                            self.conductivityVBox : (self.conductivity_view, default_message),
                            self.porosityVBox : (self.porosity_view, default_message),
                            self.capacityVBox : (self.capacity_view, default_message)}
        return layoutsRules

    def handleComputationsButtons(self):
        """
        Disable or enable the compute button if no computations were made.
        This is a security measure so user doesn't launch computations while measures haven't been cleaned.
        """
        comp_type = self.coordinator.computation_type()
        if comp_type == ComputationsState.RAW_MEASURES:
            self.pushButtonCompute.setEnabled(False)
        else:
            self.pushButtonCompute.setEnabled(True)

    def exportMeasures(self):
        """
        Export two .csv files corresponding to the cleaned measures to the location given by the user.
        """
        dlg = DialogExportCleanedMeasures(self.samplingPoint)
        dlg.setWindowModality(QtCore.Qt.ApplicationModal)
        res = dlg.exec()
        if res == QtWidgets.QDialog.Accepted:
            pressPath, tempPath = dlg.getFilesNames()
            pressfile = open(pressPath, 'w')
            presswriter = csv.writer(pressfile)
            presswriter.writerow(["Date", "Differential pressure (m)", "Temperature (°C)"])
            tempfile = open(tempPath, 'w')
            tempwriter = csv.writer(tempfile)
            tempwriter.writerow(["Date", "Temperature 1 (°C)", "Temperature 2 (°C)", "Temperature 3 (°C)", "Temperature 4 (°C)"])

            measures = self.coordinator.all_cleaned_measures()
            for temprow, pressrow in measures:
                presswriter.writerow(pressrow)
                tempwriter.writerow(temprow)
            pressfile.close()
            tempfile.close()
            print("The cleaned measures have been exported successfully.")

    def changeMeasuresState(self):
        """
        Refresh type of data displayed (raw or processed) when the checkbox "Show Raw Measures" changes state.
        """
        self.setPressureAndTemperatureTables()
        self.graphpress.showVoltageLabel(self.checkBoxRawData.isChecked())
        self.coordinator.refresh_measures_plots(self.checkBoxRawData.isChecked())
        self.linkAllViewsLayouts()

    def refreshbins(self):
        bins = self.horizontalSliderBins.value()
        self.logk_view.updateBins(bins)
        self.logk_view.onUpdate()

        self.conductivity_view.updateBins(bins)
        self.conductivity_view.onUpdate()

        self.porosity_view.updateBins(bins)
        self.porosity_view.onUpdate()

        self.capacity_view.updateBins(bins)
        self.capacity_view.onUpdate()

    def labelUpdate(self):
        self.labelBins.setText(str(self.horizontalSliderBins.value()))

    def setWidgetInfos(self):
        self.setWindowTitle(self.samplingPoint.name)
        self.lineEditPointName.setText(self.samplingPoint.name)
        self.lineEditSensor.setText(self.samplingPoint.psensor)
        self.lineEditShaft.setText(self.samplingPoint.shaft)

    def setInfoTab(self):
        schemePath, noticePath, infosModel = self.coordinator.get_spoint_infos()
        self.labelSchema.setPixmap(QtGui.QPixmap(schemePath))
        self.labelSchema.setAlignment(QtCore.Qt.AlignHCenter)
        #The following lines allow the image to take the entire size of the widget, however it will be misshapen
        # self.labelSchema.setScaledContents(True)
        # self.labelSchema.setSizePolicy(QtWidgets.QSizePolicy.Ignored,QtWidgets.QSizePolicy.Ignored)
        #Notice
        try:
            file = open(noticePath, encoding = "latin-1") #The encoding must allow to read accents
            notice = file.read()
            self.plainTextEditNotice.setPlainText(notice)
        except Exception as e:
            self.plainTextEditNotice.setPlainText("No notice was found")

        #Infos
        self.infosModel = infosModel
        self.tableViewInfos.setModel(self.infosModel)

    def setupComboBoxLayers(self):
        """
        Setup the Combo box and which will be used to display the parameters.
        """
        layers = self.coordinator.layers_depths()
        for layer in layers:
            self.comboBoxSelectLayer.addItem(str(layer))
        if len(layers) > 0:
            # By default, show the parameters associated with the first layer.
            self.changeDisplayedParams(layers[0])

    def changeDisplayedParams(self, layer : float):
        """
        Display in the table view the parameters corresponding to the given layer, and update histograms.
        """
        self.paramsModel = self.coordinator.get_params_model(layer)
        self.tableViewParams.setModel(self.paramsModel)
        #Resize the table view so it looks pretty
        self.tableViewParams.resizeColumnsToContents()
        self.coordinator.refresh_params_distr(layer)

    def setupCheckboxesQuantiles(self):
        """
        Update the quantiles layout to display as many checkboxes as there are quantiles in the database, along with the associated RMSE.
        Also update the thermometer RMSE.
        """
        self.removeAllCheckboxes()
        directRMSE, globalRMSE, thermRMSE = self.coordinator.all_RMSE()

        self.quantilesLayout.addWidget(QtWidgets.QLabel(f"RMSE: {directRMSE if directRMSE is not None else 0:.2f} °C"),0,1)
        i = 1
        for index, (quantile, rmse) in enumerate(globalRMSE.items()):
            text_checkbox = f"Quantile {quantile}"
            quantile_checkbox = QtWidgets.QCheckBox(text_checkbox)
            quantile_checkbox.stateChanged.connect(self.refreshTempDepthView)
            self.quantilesLayout.addWidget(quantile_checkbox,i,0)
            self.quantilesLayout.addWidget(QtWidgets.QLabel(f"RMSE: {rmse:.2f} °C "),i,1)
            i +=1

        #Display the RMSE for each thermometer or 0 if it has not been computed yet (ie select_RMSE_therm has only None values)
        self.labelRMSETherm1.setText(f"RMSE: {thermRMSE[0] if thermRMSE[0] else 0:.2f} °C")
        self.labelRMSETherm2.setText(f"RMSE: {thermRMSE[1] if thermRMSE[1] else 0:.2f} °C")
        self.labelRMSETherm3.setText(f"RMSE: {thermRMSE[2] if thermRMSE[2] else 0:.2f} °C")

    def removeAllCheckboxes(self):
        """
        Remove every checkbox in the quantile layout except the one for direct model.
        As a reminder, the checkboxes have this structure:
            Direct model #Shouldn't be removed
            Quantile _  | RMSE: _ #Both widgets should be removed
            ...
            Thermometer _ | RMSE: _ #Shouldn't be removed
            ...
        """
        #Taken from Stack Overflow https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt
        for i in reversed(range(self.quantilesLayout.count())):
            wdg = self.quantilesLayout.itemAt(i).widget()
            if isinstance(wdg, QtWidgets.QCheckBox) and wdg.text() =="Direct model":
                continue
            self.quantilesLayout.itemAt(i).widget().setParent(None)

    def refreshTempDepthView(self):
        """
        This method is called when a checkbox showing a quantile or a radio buttion is changed. New curves should be plotted in the Temperature per Depth View.
        """
        quantiles = []
        for i in range (self.quantilesLayout.count()):
            checkbox = self.quantilesLayout.itemAt(i).widget()
            if isinstance(checkbox, QtWidgets.QCheckBox):
                if checkbox.isChecked():
                    txt = checkbox.text()
                    #A bit ugly but it works
                    if txt == "Direct model":
                        quantiles.append(0)
                    else:
                        #txt is "Quantile ... "
                        quantiles.append(float(txt[8:]))

        if self.radioButtonTherm1.isChecked():
            depth_id = 1
        elif self.radioButtonTherm2.isChecked():
            depth_id = 2
        elif self.radioButtonTherm3.isChecked():
            depth_id = 3
        #Hackish way to make sure depth_id is 1, 2 or 3: the app will crash if it's not one of these (depth_id not defined)
        #This shouldn't happen though, as it would violate the radio button's behaviour
        thermoDepth = self.coordinator.thermo_depth(depth_id)
        self.depth_view.updateOptions([thermoDepth,quantiles])
        self.depth_view.onUpdate() #Refresh the view

    def setPressureAndTemperatureTables(self):
        """
        Set the two tables giving direct information from the database.
        """
        # Set the Temperature and Pressure arrays
        self.currentDataModel = self.coordinator.get_table_model(self.checkBoxRawData.isChecked())
        self.tableViewDataArray.setModel(self.currentDataModel)
        #Resize the table view so it looks pretty
        self.tableViewDataArray.resizeColumnsToContents()
        width = self.tableViewDataArray.verticalHeader().width()
        for i in range(self.tableViewDataArray.model().rowCount()):
            width += self.tableViewDataArray.columnWidth(i)
        width +=20 #Approximate width of the splitter bar
        self.tableViewDataArray.setFixedWidth(width)

    def updateAllViews(self):
        """
        Update all the views displaying results by asking the backend to refresh the models.
        """
        self.comboBoxSelectLayer.clear()
        self.setupComboBoxLayers()
        self.setPressureAndTemperatureTables()
        self.setupCheckboxesQuantiles()
        self.refreshTempDepthView()

        self.linkAllViewsLayouts()

        self.coordinator.refresh_all_models(self.checkBoxRawData.isChecked(), self.comboBoxSelectLayer.currentText())

    def linkAllViewsLayouts(self):
        """
        Fill all layouts with either:
            -the appropriate view, which must be displaying data
            -a message defined in self.layoutsRules
        This is to handle nicely the drawing areas and not have ugly blank spaces.

        This function takes into account checkBoxRawData's status and the computation type given by the backend
        """
        MCMC_layouts = [self.log10KVBox, self.conductivityVBox, self.porosityVBox, self.capacityVBox]
        direct_model_layouts = [self.waterFluxVBox, self.advectiveFluxVBox, self.totalFluxVBox, self.conductiveFluxVBox, self.topRightVLayout, self.botLeftVLayout, self.botRightVLayout]
        cleaned_measures_layouts = [self.pressVBox, self.tempVBox]
        all_layouts =  cleaned_measures_layouts + direct_model_layouts + MCMC_layouts
        compute_type = self.coordinator.computation_type()

        if (compute_type == ComputationsState.RAW_MEASURES) and (not self.checkBoxRawData.isChecked()):
            #User wants cleaned data for there is no such data.
            empty_layouts = all_layouts
            filled_layouts = []
        elif compute_type == ComputationsState.RAW_MEASURES or compute_type == ComputationsState.CLEANED_MEASURES:
            empty_layouts = direct_model_layouts + MCMC_layouts
            filled_layouts = cleaned_measures_layouts
        elif compute_type == ComputationsState.DIRECT_MODEL:
            empty_layouts = MCMC_layouts
            filled_layouts = cleaned_measures_layouts + direct_model_layouts
        elif compute_type == ComputationsState.MCMC:
            empty_layouts =[]
            filled_layouts = all_layouts

        #Clear all layouts
        for layout in all_layouts:
            #Taken from Stack Overflow https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt
            for i in reversed(range(layout.count())):
                layout.itemAt(i).widget().setParent(None)

        #Display custom message for layouts not displaying data
        for layout in empty_layouts:
            label = QtWidgets.QLabel(self.layoutsRules[layout][1])
            layout.addWidget(label, QtCore.Qt.AlignCenter)
        #Fill layouts displaying data with proper view
        for layout in filled_layouts:
            view = self.layoutsRules[layout][0]
            toolbar = NavigationToolbar(view, self)
            layout.addWidget(view)
            layout.addWidget(toolbar)

    def reset(self):
        dlg = DialogConfirm("Are you sure you want to delete the cleaned measures and all computations made for this point? This cannot be undone.")
        res = dlg.exec()
        if res == QtWidgets.QDialog.Accepted:
            self.coordinator.delete_processed_data()
            self.updateAllViews()
            self.handleComputationsButtons()

    def cleanup(self):
        dlg = DialogCleanup(self.coordinator,self.samplingPoint)
        res = dlg.exec()
        if res == QtWidgets.QDialog.Accepted:
            confirm = DialogConfirm("Cleaning up the measures will delete the previous cleanup, as well as any computations made for this point. Are you sure?")
            confirmRes = confirm.exec()
            if confirmRes == QtWidgets.QDialog.Accepted:
                #Clean the database first before putting new data
                self.coordinator.delete_processed_data()
                df_cleaned = dlg.getCleanedMeasures()
                if not df_cleaned.empty:
                    self.coordinator.insert_cleaned_measures(df_cleaned)

                self.updateAllViews()
                self.handleComputationsButtons()

    def compute(self):
        dlg = DialogCompute(self.coordinator.max_depth())
        res = dlg.exec()
        if res == QtWidgets.QDialog.Accepted:
            self.coordinator.delete_computations()
            if dlg.computationIsMCMC():
                #MCMC
                nb_iter, all_priors, nb_cells, quantiles = dlg.getInputMCMC()
                self.computeEngine.compute_MCMC(nb_iter, all_priors, nb_cells, quantiles)
            else:
                #Direct Model
                params, nb_cells = dlg.getInputDirectModel()
                self.computeEngine.compute_direct_model(params, nb_cells)

            self.handleComputationsButtons()

    def adjustTempRightSplitter(self, pos : int, index : int):
        """
        This is called when the left horizontal splitter in the temperature tab is moved. Move the right one accordingly.
        """
        self.tempSplitterHorizRight.setSizes(self.tempSplitterHorizLeft.sizes())

    def adjustTempLeftSplitter(self, pos : int, index : int):
        """
        This is called when the right horizontal splitter in the temperature tab is moved. Move the left one accordingly.
        """
        self.tempSplitterHorizLeft.setSizes(self.tempSplitterHorizRight.sizes())

    def adjustFluxesRightSplitter(self, pos : int, index : int):
        """
        This is called when the left horizontal splitter in the fluxes tab is moved. Move the right one accordingly.
        """
        self.fluxesSplitterHorizRight.setSizes(self.fluxesSplitterHorizLeft.sizes())

    def adjustFluxesLeftSplitter(self, pos : int, index : int):
        """
        This is called when the right horizontal splitter in the fluxes tab is moved. Move the left one accordingly.
        """
        self.fluxesSplitterHorizLeft.setSizes(self.fluxesSplitterHorizRight.sizes())
