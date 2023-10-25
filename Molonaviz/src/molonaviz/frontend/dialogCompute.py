from PyQt5 import QtWidgets, uic
from math import log10
from PyQt5.QtWidgets import QTableWidgetItem
from ..utils.get_files import get_ui_asset
import json

# Emplacement du fichier de configuration des paramètres
SETTINGS_FILE = "settings.json"

# Charger les paramètres existants ou créer un nouveau dictionnaire vide
settings = load_settings(SETTINGS_FILE)

From_DialogCompute = uic.loadUiType(get_ui_asset("dialogCompute.ui"))[0]


class DialogCompute(QtWidgets.QDialog, From_DialogCompute):
    def __init__(self, maxdepth: int):
        """
        To create a DialogCompute instance, one must give the maximum depth of the river in meters. This can be obtained with the maxDepth function for the sampling point coordinator.
        """
        # Call constructor of parent classes
        super(DialogCompute, self).__init__()
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)

        self.defaultValues = {
            "Perm": 1e-5,
            "Poro": 0.15,
            "ThConduct": 3.4,
            "ThCap": 5e6,
        }  # Default values displayed for the layers
        self.maxdepth = maxdepth * 100

        # Prevent the user from writing something in the spin box.
        self.spinBoxNLayersDirect.lineEdit().setReadOnly(True)
        # Resize the table's headers
        self.tableWidget.resizeColumnsToContents()

        self.spinBoxNLayersDirect.valueChanged.connect(self.updateNBLayers)

        self.pushButtonRun.clicked.connect(self.run)

        self.groupBoxMCMC.setChecked(False)

        self.load_saved_settings()
        self.setDefaultValues()

    def load_settings(self, filename):
        try:
            with open(filename, "r") as file:
                settings = json.load(file)
        except FileNotFoundError:
            # Si le fichier n'existe pas encore, crée un dictionnaire vide
            settings = {}
        return settings

    def save_settings(self, filename, settings):
        with open(filename, "w") as file:
            json.dump(settings, file, indent=4)

    def setDefaultValues(self):
        """
        Set the default values in the tables for both the direct model and the MCMC
        """
        # Direct model
        self.spinBoxNLayersDirect.setValue(1)
        self.updateNBLayers(1)

        # MCMC
        self.lineEditMaxIterMCMC.setText("5000")
        self.lineEditKMin.setText("3")
        self.lineEditKMax.setText("9")
        self.lineEditMoinsLog10KSigma.setText("0.01")

        self.lineEditPorosityMin.setText("0.01")
        self.lineEditPorosityMax.setText("0.25")
        self.lineEditPorositySigma.setText("0.01")

        self.lineEditThermalConductivityMin.setText("1")
        self.lineEditThermalConductivityMax.setText("5")
        self.lineEditThermalConductivitySigma.setText("0.05")

        self.lineEditThermalCapacityMin.setText("1000")
        self.lineEditThermalCapacityMax.setText("1e7")
        self.lineEditThermalCapacitySigma.setText("100")

        self.lineEditQuantiles.setText("0.05,0.5,0.95")

    def updateNBLayers(self, nb_layers: int):
        """
        This function is called when the user changes the spinbox showing the number of layers: i is the new number of layers.
        """
        # Clear the table
        self.tableWidget.setRowCount(nb_layers)

        for i in range(nb_layers):
            self.tableWidget.setVerticalHeaderItem(i, QTableWidgetItem(f"Layer {i+1}"))
            layerBottom = int((self.maxdepth / nb_layers) * (i + 1))
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(layerBottom)))  # In cm
            self.tableWidget.setItem(i, 1, QTableWidgetItem(str(self.update_perm())))
            self.tableWidget.setItem(
                i, 2, QTableWidgetItem(str(self.defaultValues["Poro"]))
            )
            self.tableWidget.setItem(
                i, 3, QTableWidgetItem(str(self.defaultValues["ThConduct"]))
            )
            self.tableWidget.setItem(
                i, 4, QTableWidgetItem("{:.2e}".format(self.defaultValues["ThCap"]))
            )

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

        for i in range(nb_layers):
            log10permeability.append(
                -log10(abs(float(self.tableWidget.item(i, 1).text())))
            )  # Apply -log10 to the permeability values
            porosity.append(float(self.tableWidget.item(i, 2).text()))
            thermconduct.append(float(self.tableWidget.item(i, 3).text()))
            thermcap.append(float(self.tableWidget.item(i, 4).text()))
            depths.append(
                float(self.tableWidget.item(i, 0).text()) / 100
            )  # Convert the depths back to m.
        layers = [f"Layer {i+1}" for i in range(nb_layers)]
        return (
            list(
                zip(layers, depths, log10permeability, porosity, thermconduct, thermcap)
            ),
            nb_cells,
        )

    def getInputMCMC(self):
        """
        Return the values entered by the user for MCMC computation.
        """
        nb_iter = int(self.lineEditMaxIterMCMC.text())
        nb_cells = self.spinBoxNCellsDirect.value()

        # The user's input is not a permeability but a -log10(permeability)
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
            "rhos_cs": ((rhos_cs_min, rhos_cs_max), rhos_cs_sigma),
        }

        nb_layers = self.spinBoxNLayersDirect.value()
        depths = []
        for i in range(nb_layers):
            depths.append(float(self.tableWidget.item(i, 0).text()) / 100)
        layers = [f"Layer {i+1}" for i in range(nb_layers)]

        all_priors = []
        for i in range(nb_layers):
            all_priors.append([layers[i], depths[i], priors])

        quantiles = self.lineEditQuantiles.text()
        quantiles = quantiles.split(",")
        quantiles = tuple(quantiles)
        quantiles = [float(quantile) for quantile in quantiles]

        return nb_iter, all_priors, nb_cells, quantiles

    def set_parameter_value(self, param, value):
        """
        Mettre à jour l'interface utilisateur avec la valeur du paramètre donné.
        """
        if param == "Perm":
            self.tableWidget.setItem(0, 1, QTableWidgetItem(str(self.update_perm())))
        elif param == "Poro":
            self.tableWidget.setItem(
                0, 2, QTableWidgetItem(str(self.defaultValues["Poro"]))
            )
        elif param == "ThConduct":
            self.defaultValues["ThConduct"] = value
            self.tableWidget.setItem(
                0, 3, QTableWidgetItem(str(self.defaultValues["ThConduct"]))
            )
        elif param == "ThCap":
            self.defaultValues["ThCap"] = value
            self.tableWidget.setItem(
                0, 4, QTableWidgetItem(str(self.defaultValues["ThCap"]))
            )

        # Mettre à jour les champs d'interface utilisateur si nécessaire
        # Par exemple, pour mettre à jour un champ de texte :

    def save_settings(self):
        """
        Sauvegarder les paramètres actuels dans le fichier de configuration.
        """
        for param in self.defaultValues:
            value = self.defaultValues[param]
            settings[param] = value

        # Sauvegarder les paramètres dans le fichier de configuration
        save_settings(SETTINGS_FILE, settings)

    def update_perm(self):
        """
        Mettre à jour la valeur de Perm lorsque l'utilisateur modifie le champ de texte.
        """
        # Récupérez l'élément de la cellule à la ligne 0 et la colonne 1
        perm_item = self.tableWidget.item(0, 1)

        # Vérifiez si l'élément existe
        if perm_item is not None:
            # Obtenez le texte de l'élément
            perm_text = perm_item.text()

            try:
                # Convertissez le texte en nombre à virgule flottante
                perm_value = float(perm_text)
                return perm_value
            except ValueError:
                # Gérez l'erreur si la conversion échoue
                pass
        elif perm_item is None:
            perm_item = str(self.defaultValues["Perm"])
            return perm_item

    def update_poro(self):
        """
        Mettre à jour la valeur de Poro lorsque l'utilisateur modifie le champ de texte.
        """
        text = self.lineEditPoro.text()
        try:
            value = float(text)
            self.defaultValues["Poro"] = value
            self.set_parameter_value("Poro", value)
            self.save_settings()
        except ValueError:
            pass  # Gérer les erreurs ici

    def update_th_conduct(self):
        """
        Mettre à jour la valeur de ThConduct lorsque l'utilisateur modifie le champ de texte.
        """
        text = self.lineEditThConduct.text()
        try:
            value = float(text)
            self.defaultValues["ThConduct"] = value
            self.set_parameter_value("ThConduct", value)
            self.save_settings()
        except ValueError:
            pass  # Gérer les erreurs ici

    def update_th_cap(self):
        """
        Mettre à jour la valeur de ThCap lorsque l'utilisateur modifie le champ de texte.
        """
        text = self.lineEditThCap.text()
        try:
            value = float(text)
            self.defaultValues["ThCap"] = value
            self.set_parameter_value("ThCap", value)
            self.save_settings()
        except ValueError:
            pass  # Gérer les erreurs ici
