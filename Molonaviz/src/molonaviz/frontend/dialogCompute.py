from PyQt5 import QtWidgets, uic
import numpy as np
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtSql import QSqlQuery

from ..utils.get_files import get_ui_asset
from ..backend.SPointCoordinator import SPointCoordinator
from ..backend.Compute import Compute


From_DialogCompute = uic.loadUiType(get_ui_asset("dialogCompute.ui"))[0]

class DialogCompute(QtWidgets.QDialog, From_DialogCompute):
    def __init__(self, maxdepth : int, spointcoordinator : SPointCoordinator, compute : Compute, statusNightMode : bool = False):
        """
        To create a DialogCompute instance, one must give the maximum depth of the river in meters. This can be obtained with the maxDepth function for the sampling point coordinator.
        """
        # Call constructor of parent classes
        super(DialogCompute, self).__init__()
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)

        self.activerDesactiverModeSombre(statusNightMode)

        self.defaultParamValues = [12.0, 0.15, 3.4, 5000000.0]
        self.maxdepth = maxdepth
        self.layers = spointcoordinator.layers_depths()
        self.params = [] 
        for layer in self.layers:
            self.params.append(spointcoordinator.get_params_model(layer))
        self.input = []
        num_rows = len(self.layers)
        num_cols = 5 # Layer depth + 4 parameters
        self.compute = compute

        if self.params:
            for row in range(num_rows):
                self.input.append([])
                for col in range(num_cols):
                    valeur = self.params[row].index(0, col).data()
                    self.input[row].append(valeur)

        self.inputMCMC = spointcoordinator.get_params_MCMC_model()

        #Prevent the user from writing something in the spin box.
        self.spinBoxNLayersDirect.lineEdit().setReadOnly(True)
        #Resize the table's headers
        self.tableWidget.resizeColumnsToContents()

        self.spinBoxNLayersDirect.valueChanged.connect(self.updateNBLayers)
        self.pushButtonRestoreDefault.clicked.connect(self.setDefaultValues)
        self.pushButtonRestoreDefault.clicked.connect(self.setDefaultValuesMCMC)
        self.pushButtonRun.clicked.connect(self.run)

        self.groupBoxMCMC.setChecked(False)

        if self.input == []:
            self.setDefaultValues()
        else:
            self.InitValues()

        if self.inputMCMC == []:
            self.setDefaultValuesMCMC()
        else:
            self.InitValuesMCMC()

    def InitValues(self):
        """
        Set the default values in the tables for both the direct model and the MCMC
        """
        #Direct model

        self.spinBoxNLayersDirect.setValue(len(self.layers))
        self.tableWidget.setRowCount(len(self.input))

        for i in range(len(self.input)):
            self.tableWidget.setVerticalHeaderItem(i, QTableWidgetItem(f"Layer {i+1}"))
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(self.layers[i])))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(str(self.input[i][0])))
            self.tableWidget.setItem(i, 2, QTableWidgetItem(str(self.input[i][1])))
            self.tableWidget.setItem(i, 3, QTableWidgetItem(str(self.input[i][2])))
            self.tableWidget.setItem(i, 4, QTableWidgetItem(str(self.input[i][3])))

    def InitValuesMCMC(self):

        #MCMC
        # Same order than SPointCoordinator build_params_MCMC_query
        self.lineEditMaxIterMCMC.setText(str(self.inputMCMC[0]))
        self.lineEditDelta.setText(str(self.inputMCMC[1]))

        self.lineEditChains.setText(str(self.inputMCMC[2]))
        self.lineEditncr.setText(str(self.inputMCMC[3]))
        self.lineEditc.setText(str(self.inputMCMC[4]))
        self.lineEditcstar.setText(str(self.inputMCMC[5]))

        self.lineEditKMin.setText(str(self.inputMCMC[6]))
        self.lineEditKMax.setText(str(self.inputMCMC[7]))
        self.lineEditmoinslog10IntrinKSigma.setText(str(self.inputMCMC[8]))

        self.lineEditPorosityMin.setText(str(self.inputMCMC[9]))
        self.lineEditPorosityMax.setText(str(self.inputMCMC[10]))
        self.lineEditPorositySigma.setText(str(self.inputMCMC[11]))

        self.lineEditThermalConductivityMin.setText(str(self.inputMCMC[12]))
        self.lineEditThermalConductivityMax.setText(str(self.inputMCMC[13]))
        self.lineEditThermalConductivitySigma.setText(str(self.inputMCMC[14]))

        self.lineEditThermalCapacityMin.setText(str(self.inputMCMC[15]))
        self.lineEditThermalCapacityMax.setText(str(self.inputMCMC[16]))
        self.lineEditThermalCapacitySigma.setText(str(self.inputMCMC[17]))

        self.lineEditPersi.setText(str(self.inputMCMC[18]))
        self.lineEditThresh.setText(str(self.inputMCMC[19]))

        self.lineEditIterStep.setText(str(self.inputMCMC[20]))
        self.lineEditSpaceStep.setText(str(self.inputMCMC[21]))
        self.lineEditTimeStep.setText(str(self.inputMCMC[22]))

        self.lineEditQuantiles.setText(str(self.inputMCMC[23]))


        
    def setDefaultValues(self):
        """
        Set the default values in the tables for both the direct model and the MCMC
        """
        #Direct model (1 layer)
        self.spinBoxNLayersDirect.setValue(1)
        self.tableWidget.setRowCount(1)

        self.input = [self.defaultParamValues]

        self.tableWidget.setVerticalHeaderItem(0, QTableWidgetItem(f"Layer 1"))
        layerBottom = self.maxdepth
        self.tableWidget.setItem(0, 0, QTableWidgetItem(str(layerBottom)))
        self.tableWidget.setItem(0, 1, QTableWidgetItem(str(self.input[0][0])))
        self.tableWidget.setItem(0, 2, QTableWidgetItem(str(self.input[0][1])))
        self.tableWidget.setItem(0, 3, QTableWidgetItem(str(self.input[0][2])))
        self.tableWidget.setItem(0, 4, QTableWidgetItem(str(self.input[0][3])))

    def setDefaultValuesMCMC(self):

        #MCMC
        self.lineEditMaxIterMCMC.setText("50")

        self.lineEditChains.setText("10")
        self.lineEditDelta.setText("3")
        self.lineEditncr.setText("3")
        self.lineEditc.setText("0.1")
        self.lineEditcstar.setText("1e-6")
        self.lineEditPersi.setText("1")
        self.lineEditThresh.setText("1.2")

        self.lineEditIterStep.setText("10")
        self.lineEditSpaceStep.setText("1")
        self.lineEditTimeStep.setText("1")

        self.lineEditKMin.setText("11")
        self.lineEditKMax.setText("15")
        self.lineEditmoinslog10IntrinKSigma.setText("0.01")

        self.lineEditPorosityMin.setText("0.01")
        self.lineEditPorosityMax.setText("0.25")
        self.lineEditPorositySigma.setText("0.01")

        self.lineEditThermalConductivityMin.setText("1")
        self.lineEditThermalConductivityMax.setText("5")
        self.lineEditThermalConductivitySigma.setText("0.05")

        self.lineEditThermalCapacityMin.setText("1e6")
        self.lineEditThermalCapacityMax.setText("1e7")
        self.lineEditThermalCapacitySigma.setText("100")

        self.lineEditQuantiles.setText("0.05,0.5,0.95")

    def updateNBLayers(self, nb_layers : int):
        """
        This function is called when the user changes the spinbox showing the number of layers: i is the new number of layers.
        """
        #Clear the table
        self.tableWidget.setRowCount(nb_layers)

        if len(self.input) < nb_layers:
    
            for _ in range(nb_layers - len(self.input)):
                self.input.append(self.defaultParamValues)

        elif len(self.input) > nb_layers:
    
            for _ in range(len(self.input) - nb_layers):
                self.input.pop()

        layerBottoms = np.linspace(0, self.maxdepth, nb_layers+1)[1:nb_layers+1]
        for i in range(nb_layers):
            self.tableWidget.setVerticalHeaderItem(i, QTableWidgetItem(f"Layer {i+1}")) 
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(round(layerBottoms[i],3)))) # Round to 1 mm
            self.tableWidget.setItem(i, 1, QTableWidgetItem(str(self.input[i][0])))
            self.tableWidget.setItem(i, 2, QTableWidgetItem(str(self.input[i][1])))
            self.tableWidget.setItem(i, 3, QTableWidgetItem(str(self.input[i][2])))
            self.tableWidget.setItem(i, 4, QTableWidgetItem(str(self.input[i][3])))

    def run(self):
        """
        This function is called when the user presses the "Run" button: it corresponds to the "Accept" button.
        """
        super().accept()

    def computationIsMCMC(self):
        """
        Return True if the user wishes to compute the MCMC, and false if he wants to compute the direct model.
        """
        return self.groupBoxMCMC.isChecked()

    def getInputDirectModel(self):
        """
        Return the values entered by the user for direct model computations as a list of list and the number of cells. The list of list corresponds to the parameters for each layer.
        """
        nb_cells = self.spinBoxNCellsDirect.value()
        nb_layers = self.spinBoxNLayersDirect.value()
        depths = []
        permeability = []
        porosity = []
        thermconduct = []
        thermcap = []

        # Same format as ColumnMCMCRunner.get_last_best_params
        for i in range (nb_layers):
            depths.append(float(self.tableWidget.item(i, 0).text()))
            permeability.append(float(self.tableWidget.item(i, 1).text()))
            porosity.append(float(self.tableWidget.item(i, 2).text()))
            thermconduct.append(float(self.tableWidget.item(i, 3).text()))
            thermcap.append(float(self.tableWidget.item(i, 4).text()))
        layers = [f"Layer {i+1}" for i in range(nb_layers)]
        return list(zip(layers, depths, permeability, porosity, thermconduct, thermcap)), nb_cells

    def getInputMCMC(self):
        """
        Return the values entered by the user for MCMC computation.
        """
        nb_iter = int(self.lineEditMaxIterMCMC.text())
        nb_cells = self.spinBoxNCellsDirect.value()

        nb_chains = int(self.lineEditChains.text())
        delta = int(self.lineEditDelta.text())
        ncr = int(self.lineEditncr.text())
        c = float(self.lineEditc.text())
        cstar = float(self.lineEditcstar.text())
        remanence = float(self.lineEditPersi.text())
        thresh = float(self.lineEditThresh.text())

        nb_sous_ech_iter = int(self.lineEditIterStep.text())
        nb_sous_ech_space = int(self.lineEditSpaceStep.text())
        nb_sous_ech_time = int(self.lineEditTimeStep.text())

        # The user's input is not a permeability but a -log10(permeability)
        moins10logKmin = float(self.lineEditKMin.text())
        moins10logKmax = float(self.lineEditKMax.text())
        moins10logKsigma = float(self.lineEditmoinslog10IntrinKSigma.text())

        nmin = float(self.lineEditPorosityMin.text())
        nmax = float(self.lineEditPorosityMax.text())
        nsigma = float(self.lineEditPorositySigma.text())

        lambda_s_min = float(self.lineEditThermalConductivityMin.text())
        lambda_s_max = float(self.lineEditThermalConductivityMax.text())
        lambda_s_sigma = float(self.lineEditThermalConductivitySigma.text())

        rhos_cs_min = float(self.lineEditThermalCapacityMin.text())
        rhos_cs_max = float(self.lineEditThermalCapacityMax.text())
        rhos_cs_sigma = float(self.lineEditThermalCapacitySigma.text())

        priors = {
        "moinslog10IntrinK": ((moins10logKmin, moins10logKmax), moins10logKsigma),
        "n": ((nmin, nmax), nsigma),
        "lambda_s": ((lambda_s_min, lambda_s_max), lambda_s_sigma),
        "rhos_cs": ((rhos_cs_min, rhos_cs_max), rhos_cs_sigma) }

        nb_layers = self.spinBoxNLayersDirect.value()
        depths = []
        for i in range (nb_layers):
            depths.append(float(self.tableWidget.item(i, 0).text()))
        layers = [f"Layer {i+1}" for i in range(nb_layers)]

        all_priors = []
        for i in range(nb_layers):
            all_priors.append([layers[i], depths[i], priors])

        quantiles = self.lineEditQuantiles.text()

        # Warning: order must be the same than ColumnMCMCRunner constructor (otherwise use a dictionary)
        return [nb_iter, all_priors, nb_cells, quantiles, nb_chains, delta, ncr, c, cstar, remanence, nb_sous_ech_iter, nb_sous_ech_time, nb_sous_ech_space, thresh]

    def activerDesactiverModeSombre(self, state):
        if state:
            self.setStyleSheet("background-color: rgb(50, 50, 50); color: rgb(255, 255, 255);")
            self.tableWidget.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #232326; color: white; }")
            self.tableWidget.verticalHeader().setStyleSheet("QHeaderView::section { background-color: #232326; color: white; }")
        else:
            self.setStyleSheet("")  # Utilisez la feuille de style par défaut de l'application
