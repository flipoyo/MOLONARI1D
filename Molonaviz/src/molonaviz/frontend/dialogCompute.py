from PyQt5 import QtWidgets, uic
from math import log10
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtSql import QSqlQuery

from ..utils.get_files import get_ui_asset
from ..backend.SPointCoordinator import SPointCoordinator


From_DialogCompute = uic.loadUiType(get_ui_asset("dialogCompute.ui"))[0]

class DialogCompute(QtWidgets.QDialog, From_DialogCompute):
    def __init__(self, maxdepth : int, spointcoordinator : SPointCoordinator):
        """
        To create a DialogCompute instance, one must give the maximum depth of the river in meters. This can be obtained with the maxDepth function for the sampling point coordinator.
        """
        # Call constructor of parent classes
        super(DialogCompute, self).__init__()
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)

        self.maxdepth = maxdepth * 100
        self.input = spointcoordinator.get_params_model()
        self.layers = spointcoordinator.get_layers()

        #Prevent the user from writing something in the spin box.
        self.spinBoxNLayersDirect.lineEdit().setReadOnly(True)
        #Resize the table's headers
        self.tableWidget.resizeColumnsToContents()

        self.spinBoxNLayersDirect.valueChanged.connect(self.updateNBLayers)
        self.pushButtonRestoreDefault.clicked.connect(self.setDefaultValues)
        self.pushButtonRun.clicked.connect(self.run)

        self.tableWidget.itemChanged.connect(self.SaveInput)

        self.groupBoxMCMC.setChecked(False)

        self.InitValues()

    def InitValues(self):
        """
        Set the default values in the tables for both the direct model and the MCMC
        """
        #Direct model

        self.spinBoxNLayersDirect.setValue(len(self.layers))
        self.tableWidget.setRowCount(len(self.input))

        self.lineEditChains.setText("10")
        self.lineEditDelta.setText("3")
        self.lineEditncr.setText("3")
        self.lineEditc.setText("0.1")
        self.lineEditcstar.setText("1e-6")


        num_rows = len(self.input)
        num_cols = len(self.input[0])

    
        for col in range(num_cols):
            self.tableWidget.setVerticalHeaderItem(row, QTableWidgetItem(f"Layer {col+1}"))
            self.tableWidget.setItem(row, 0, QTableWidgetItem(self.layers[col]))
            for row in range(num_rows):
                self.tableWidget.setItem(row, col, QTableWidgetItem(self.input[row][col]))
            
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
        params = list(zip(layers, depths, log10permeability, porosity, thermconduct, thermcap))
        insertlayer = QSqlQuery(self.con)
        insertlayer.prepare("INSERT INTO Layer (Name, Depth, PointKey) VALUES (:Name, :Depth, :PointKey)")
        insertlayer.bindValue(":PointKey", self.pointID)

        insertparams = QSqlQuery(self.con)
        insertparams.prepare(f"""INSERT INTO Parameters (Permeability, ThermConduct, Porosity, Capacity, Layer, PointKey)
                           VALUES (:Permeability, :ThermConduct, :Porosity, :Capacity, :Layer, :PointKey)""")
        insertparams.bindValue(":PointKey", self.pointID)

        self.con.transaction()
        for layer, depth, perm, n, lamb, rho in params:
            insertlayer.bindValue(":Name", layer)
            insertlayer.bindValue(":Depth", depth)
            insertlayer.exec()

            insertparams.bindValue(":Permeability", perm)
            insertparams.bindValue(":ThermConduct", lamb)
            insertparams.bindValue(":Porosity", n)
            insertparams.bindValue(":Capacity", rho)
            insertparams.bindValue(":Layer", insertlayer.lastInsertId())
            insertparams.exec()
        self.con.commit()
    
    
    def setDefaultValues(self):
        """
        Set the default values in the tables for both the direct model and the MCMC
        """
        #Direct model
        self.spinBoxNLayersDirect.setValue(1)
        self.tableWidget.setRowCount(1)

        self.tableWidget.setVerticalHeaderItem(0, QTableWidgetItem(f"Layer {1}"))
        layerBottom = int((self.maxdepth))
        self.tableWidget.setItem(0, 0, QTableWidgetItem(str(layerBottom))) #In cm
        self.tableWidget.setItem(0, 1, QTableWidgetItem(str(1e-5)))
        self.tableWidget.setItem(0, 2, QTableWidgetItem(str(0.15)))
        self.tableWidget.setItem(0, 3, QTableWidgetItem(str(3.4)))
        self.tableWidget.setItem(0, 4, QTableWidgetItem('{:.2e}'.format(5e6)))

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

    def updateNBLayers(self, nb_layers : int):
        """
        This function is called when the user changes the spinbox showing the number of layers: i is the new number of layers.
        """
        #Clear the table
        self.tableWidget.setRowCount(nb_layers)

        if len(self.input) < nb_layers:
    
            for _ in range(nb_layers - len(self.input)):
                self.input.append({"Perm": 1e-5, "Poro": 0.15,"ThConduct": 3.4,"ThCap": 5e6})
        elif len(self.input) > nb_layers:
    
            for _ in range(len(self.input) - nb_layers):
                self.input.pop()


        for i in range(nb_layers):
            self.tableWidget.setVerticalHeaderItem(i, QTableWidgetItem(f"Layer {i+1}")) 
            layerBottom = int((self.maxdepth/nb_layers))

            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(layerBottom*(i+1)))) #In cm
            self.tableWidget.setItem(i, 1, QTableWidgetItem(str(self.input[i]["Perm"])))
            self.tableWidget.setItem(i, 2, QTableWidgetItem(str(self.input[i]["Poro"])))
            self.tableWidget.setItem(i, 3, QTableWidgetItem(str(self.input[i]["ThConduct"])))
            self.tableWidget.setItem(i, 4, QTableWidgetItem('{:.2e}'.format(self.input[i]["ThCap"])))

            self.tableWidget.setItem(nb_layers -1, 0, QTableWidgetItem(str(int((self.maxdepth))))) #In cm

        with open(self.chemin_input_direct_compute, 'w') as fichier:
            json.dump(self.input, fichier, indent=4)


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
