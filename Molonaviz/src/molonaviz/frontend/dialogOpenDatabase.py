from PyQt5 import QtWidgets, uic
from ..utils.general import displayCriticalMessage
from ..utils.get_files import get_ui_asset

From_DialogOpenDatabase = uic.loadUiType(get_ui_asset("dialogOpenDatabase.ui"))[0]
class DialogOpenDatabase(QtWidgets.QDialog,From_DialogOpenDatabase):
    """
    Enable the user to choose the path of an existing database directory or to create a new database. This "or" is mutually exclusive (only one of these two actions may be made).
    """
    def __init__(self):
        super(DialogOpenDatabase, self).__init__()
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)

        self.pushButtonExistingDir.clicked.connect(self.browseExistingDir)
        self.pushButtonCreateDir.clicked.connect(self.browseCreateDir)

    def accept(self):
        """
        This is an overloaded function, called when the user presses the "OK" button.
        If the user is trying to create a new database, make sure he has filled in the two fields.
        """
        if bool(self.lineEditCreateDataDir.text()) != bool(self.lineEditDataName.text()):
            #Trying to create a directory but either the name or the path is empty
            displayCriticalMessage("You must fill in both the path to the database you are trying to create and its name.")
            return
        super().accept()

    def browseExistingDir(self):
        """
        Display a dialog so that the user may choose an existing database directory.
        """
        fileDir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select database directory")
        if fileDir:
            self.lineEditExistingDataDir.setText(fileDir)
            self.lineEditCreateDataDir.setText("")
            self.lineEditDataName.setText("")

    def browseCreateDir(self):
        """
        Display a dialog so that the user may where to create a new database directory.
        """
        fileDir = QtWidgets.QFileDialog.getExistingDirectory(self, "Create a new database")
        if fileDir:
            self.lineEditCreateDataDir.setText(fileDir)
            self.lineEditExistingDataDir.setText("")

    def getDir(self):
        """
        Return the directory path given by the user, a boolean stating if the database should be created (True) or if it already exists (False), and the name of the new database (empty string if the user tries to open an existing one).
        """
        createDir = self.lineEditCreateDataDir.text()
        newDirName = self.lineEditDataName.text()
        existingDir = self.lineEditExistingDataDir.text()
        if createDir:
            return createDir, True, newDirName
        else:
            return existingDir, False, ""