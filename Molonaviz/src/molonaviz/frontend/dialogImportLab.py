import os
import csv
from PyQt5 import QtWidgets, uic
from ..utils.general import displayCriticalMessage
from ..utils.get_files import get_ui_asset

From_DialogImportLab = uic.loadUiType(get_ui_asset("dialogImportLab.ui"))[0]

class DialogImportLab(QtWidgets.QDialog, From_DialogImportLab):
    """
    Enable the user to pick the path to the directory required for the creation of a laboratory in the database.
    """
    def __init__(self):
        super(DialogImportLab, self).__init__()
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)

        # Load default values from a CSV file (e.g., defaults.csv)
        self.load_defaults()

        self.pushButtonBrowse.clicked.connect(self.browseDir)

    def load_defaults(self):
        # Load default values from a CSV file
        defaults_file = "defaults.csv"
        if os.path.exists(defaults_file):
            with open(defaults_file, 'r', newline='') as file:
                reader = csv.reader(file)
                defaults = next(reader, [])
                if len(defaults) == 2:
                    self.lineEditLabDir.setText(defaults[0])
                    self.lineEditLabName.setText(defaults[1]+ "_")

    def save_defaults(self):
        # Save the current values as defaults in a CSV file (e.g., defaults.csv)
        defaults = [
            self.lineEditLabDir.text(),
            self.lineEditLabName.text()
        ]
        defaults_file = "defaults.csv"
        with open(defaults_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(defaults)

    def browseDir(self):
        """
        Display a dialog so that the user may choose the laboratory's directory.
        """
        fileDir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Laboratory Directory")
        if fileDir:
            self.lineEditLabDir.setText(fileDir)

    def getLaboInfo(self):
        """
        Return the path to the directory representing the lab as well as its name. If there was some kind of problem, return two empty strings instead.
        """
        fileDir = self.lineEditLabDir.text()
        labName = self.lineEditLabName.text()
        if not os.path.isdir(fileDir):
            displayCriticalMessage("This directory was not found.")
            return "", ""
        elif labName == "":
            displayCriticalMessage("The laboratory's name cannot be empty.\nPlease also make sure a laboratory with the same name does not already exist.")
            return "", ""

        # Save the current values as defaults
        self.save_defaults()

        return fileDir, labName
