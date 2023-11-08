from PyQt5 import QtWidgets, uic
from math import log10
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtSql import QSqlQuery

from ..utils.get_files import get_ui_asset
from ..backend.SPointCoordinator import SPointCoordinator
from ..backend.Compute import Compute


From_DialogCompute = uic.loadUiType(get_ui_asset("dialogCompute.ui"))[0]

class DialogCompute(QtWidgets.QDialog, From_DialogCompute):
    def __init__(self, maxdepth : int, spointcoordinator : SPointCoordinator, compute : Compute):
        """
        To create a DialogCompute instance, one must give the maximum depth of the river in meters. This can be obtained with the maxDepth function for the sampling point coordinator.
        """
        # Call constructor of parent classes
        super(DialogCompute, self).__init__()
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)

        self.interaction_occurred = False
        self.maxdepth = maxdepth * 100
        self.layers = spointcoordinator.layers_depths()
        self.params =[]
        for layer in self.layers:
            self.params.append(spointcoordinator.get_params_model(layer))
        self.input = []
        num_rows = len(self.layers) 
        num_cols = 5
        self.compute = compute

        if self.params:
            for row in range(num_rows):
                self.input.append([])
                for col in range(num_cols):
                    valeur = self.params[row].index(0, col).data()
                    self.input[row].append(valeur)
                

        

        #Prevent the user from writing something in the spin box.
        self.spinBoxNLayersDirect.lineEdit().setReadOnly(True)
        #Resize the table's headers
        self.tableWidget.resizeColumnsToContents()

        self.spinBoxNLayersDirect.valueChanged.connect(self.updateNBLayers)
        self.pushButtonRestoreDefault.clicked.connect(self.setDefaultValues)
        self.pushButtonRun.clicked.connect(self.run)
        self.tableWidget.itemChanged.connect(self.SaveInput)

        self.groupBoxMCMC.setChecked(False)

        if (self.input == []) or (self.input[0] == []) or (self.input[0][3] is None):
            self.setDefaultValues()
        else:
            self.InitValues()

        self.interaction_occurred = True

    def InitValues(self):
        """
        Set the default values in the tables for both the direct model and the MCMC
        """
        #Direct model

        self.spinBoxNLayersDirect.setValue(len(self.layers))
        self.tableWidget.setRowCount(len(self.input))

        layerBottom = int((self.maxdepth))

        for i in range(len(self.input)):
            self.tableWidget.setVerticalHeaderItem(i, QTableWidgetItem(f"Layer {i+1}"))
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(self.layers[i]*100)))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(str(self.input[i][0])))
            self.tableWidget.setItem(i, 2, QTableWidgetItem(str(self.input[i][1])))
            self.tableWidget.setItem(i, 3, QTableWidgetItem(str(self.input[i][2])))
            self.tableWidget.setItem(i, 4, QTableWidgetItem('{:.2e}'.format(self.input[i][3])))


        self.lineEditChains.setText("10")
        self.lineEditDelta.setText("3")
        self.lineEditncr.setText("3")
        self.lineEditc.setText("0.1")
        self.lineEditcstar.setText("1e-6")

        #MCMC
        self.lineEditMaxIterMCMC.setText("5000")
        self.lineEditKMin.setText("4")
        self.lineEditKMax.setText("9")
        self.lineEditMoinsLog10KSigma.setText("0.01")

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


    def SaveInput(self):

        """
        Save the layers and the last parameters in the database.
        """
        if self.interaction_occurred:

            nb_cells = self.spinBoxNCellsDirect.value()
            nb_layers = self.spinBoxNLayersDirect.value()
            depths = []
            log10permeability = []
            porosity = []
            thermconduct = []
            thermcap = []

            for i in range (nb_layers):
                if (self.tableWidget.item(i, 1) is not None) & (self.tableWidget.item(i, 2) is not None) & (self.tableWidget.item(i, 3) is not None) & (self.tableWidget.item(i, 4) is not None) :
                    log10permeability.append(float(self.tableWidget.item(i, 1).text())) #Apply -log10 to the permeability values
                    porosity.append(float(self.tableWidget.item(i, 2).text()))
                    thermconduct.append(float(self.tableWidget.item(i, 3).text()))
                    thermcap.append(float(self.tableWidget.item(i, 4).text()))
                    depths.append(float(self.tableWidget.item(i, 0).text())/100) #Convert the depths back to m.

            layers = [f"Layer {i+1}" for i in range(nb_layers)]
            params =  list(zip(layers, depths, log10permeability, porosity, thermconduct, thermcap))
        
            self.compute.save_layers_and_params(params)
        
    def setDefaultValues(self):
        """
        Set the default values in the tables for both the direct model and the MCMC
        """
        #Direct model
        self.spinBoxNLayersDirect.setValue(1)
        self.tableWidget.setRowCount(1)

        self.input = [[1e-5, 0.15, 3.4, 5e6]]

        self.tableWidget.setVerticalHeaderItem(0, QTableWidgetItem(f"Layer {1}"))
        layerBottom = int((self.maxdepth))
        self.tableWidget.setItem(0, 0, QTableWidgetItem(str(layerBottom))) #In cm
        self.tableWidget.setItem(0, 1, QTableWidgetItem(str(self.input[0][0])))
        self.tableWidget.setItem(0, 2, QTableWidgetItem(str(self.input[0][1])))
        self.tableWidget.setItem(0, 3, QTableWidgetItem(str(self.input[0][2])))
        self.tableWidget.setItem(0, 4, QTableWidgetItem(str('{:.2e}'.format(self.input[0][3]))))

        #MCMC
        self.lineEditMaxIterMCMC.setText("5000")

        self.lineEditChains.setText("10")
        self.lineEditDelta.setText("3")
        self.lineEditncr.setText("3")
        self.lineEditc.setText("0.1")
        self.lineEditcstar.setText("1e-6")

        self.lineEditKMin.setText("4")
        self.lineEditKMax.setText("9")
        self.lineEditMoinsLog10KSigma.setText("0.01")

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

        self.SaveInput()

    def updateNBLayers(self, nb_layers : int):
        """
        This function is called when the user changes the spinbox showing the number of layers: i is the new number of layers.
        """
        if self.interaction_occurred == True:
                    #Clear the table
            self.tableWidget.setRowCount(nb_layers)
            nb_col = len(self.input)

            if nb_col < nb_layers:
        
                for _ in range(nb_layers - nb_col):
                    self.input.append([ 1e-5, 0.15, 3.4, 5e6])
            elif nb_col > nb_layers:
        
                for _ in range(nb_col - nb_layers):
                    self.input.pop()


            for i in range(len(self.input)):
                self.tableWidget.setVerticalHeaderItem(i, QTableWidgetItem(f"Layer {i+1}")) 
                layerBottom = int((self.maxdepth/nb_layers))
                self.tableWidget.setItem(i, 0, QTableWidgetItem(str(layerBottom*(i+1)))) #In cm
                self.tableWidget.setItem(i, 1, QTableWidgetItem(str(self.input[i][0])))
                self.tableWidget.setItem(i, 2, QTableWidgetItem(str(self.input[i][1])))
                self.tableWidget.setItem(i, 3, QTableWidgetItem(str(self.input[i][2])))
                self.tableWidget.setItem(i, 4, QTableWidgetItem('{:.2e}'.format(self.input[i][3])))


    def run(self):
        """
        This function is called when the user presses the "Run" button: it corresponds to the "Accept" button.
        """
        self.interaction_occurred = True
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
        log10permeability = []
        porosity = []
        thermconduct = []
        thermcap = []

        for i in range (nb_layers):
            log10permeability.append(-log10(abs(float(self.tableWidget.item(i, 1).text())))) #Apply -log10 to the permeability values
            porosity.append(float(self.tableWidget.item(i, 2).text()))
            thermconduct.append(float(self.tableWidget.item(i, 3).text()))
            thermcap.append(float(self.tableWidget.item(i, 4).text()))
            depths.append(float(self.tableWidget.item(i, 0).text())/100) #Convert the depths back to m.

        layers = [f"Layer {i+1}" for i in range(nb_layers)]
        return list(zip(layers, depths, log10permeability, porosity, thermconduct, thermcap)), nb_cells

    def getInputMCMC(self):
        """
        Return the values entered by the user for MCMC computation.
        """
        nb_iter = int(self.lineEditMaxIterMCMC.text())
        nb_cells = self.spinBoxNCellsDirect.value()

        nb_chains = int(self.lineEditChains.text())
        delta = float(self.lineEditDelta.text())
        ncr = float(self.lineEditncr.text())
        c = float(self.lineEditc.text())
        cstar = float(self.lineEditcstar.text())

        #The user's input is not a permeability but a -log10(permeability)
        moins10logKmin = float(self.lineEditKMin.text())
        moins10logKmax = float(self.lineEditKMax.text())
        moins10logKsigma = float(self.lineEditMoinsLog10KSigma.text())

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
        "moinslog10K": ((moins10logKmin, moins10logKmax), moins10logKsigma),
        "n": ((nmin, nmax), nsigma),
        "lambda_s": ((lambda_s_min, lambda_s_max), lambda_s_sigma),
        "rhos_cs": ((rhos_cs_min, rhos_cs_max), rhos_cs_sigma) }

        nb_layers = self.spinBoxNLayersDirect.value()
        depths = []
        for i in range (nb_layers):
            depths.append(float(self.tableWidget.item(i, 0).text())/100)
        layers = [f"Layer {i+1}" for i in range(nb_layers)]

        all_priors = []
        for i in range(nb_layers):
            all_priors.append([layers[i], depths[i], priors])

        quantiles = self.lineEditQuantiles.text()
        quantiles = quantiles.split(",")
        quantiles = tuple(quantiles)
        quantiles = [float(quantile) for quantile in quantiles]

        return nb_iter, all_priors, nb_cells, quantiles, nb_chains, delta, ncr, c, cstar
