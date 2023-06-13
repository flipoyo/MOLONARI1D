import os
from PyQt5 import QtWidgets, uic
from ..utils.general import displayCriticalMessage
from ..utils.get_files import get_ui_asset

From_DialogImportLab = uic.loadUiType(get_ui_asset("dialogImportLab.ui"))[0]
class DialogImportLab(QtWidgets.QDialog,From_DialogImportLab):
    """
    Enable the user to pick the path to the directory required for the creation of a laboratory in the database.
    """
    def __init__(self):
        super(DialogImportLab, self).__init__()
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)

        self.pushButtonBrowse.clicked.connect(self.browseDir)

    def browseDir(self):
        """
        Display a dialog so that the user may choose the laboratory's directory.
        """
        fileDir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Laboratory Directory")
        if fileDir:
            self.lineEditLabDir.setText(fileDir)

    def getLaboInfo(self):
        """
        Return the path to the directory representing the lab as well as it's name. If there was some kind of problem, return two empty strings instead.
        """
        fileDir = self.lineEditLabDir.text()
        labName = self.lineEditLabName.text()
        if not os.path.isdir(fileDir):
            displayCriticalMessage("This directory was not found.")
            return "",""
        elif labName =="":
            displayCriticalMessage("The laboratory's name cannot be empty.\nPlease also make sure a laboratory with the same name does not already exist.")
            return "",""
        return fileDir,labName