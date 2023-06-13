from PyQt5 import QtWidgets, uic
from ..utils.get_files import get_ui_asset

From_DialogConfirm = uic.loadUiType(get_ui_asset("dialogConfirm.ui"))[0]

class DialogConfirm(QtWidgets.QDialog,From_DialogConfirm):
    """
    Just a simple Confirm/Cancel window.
    """
    def __init__(self, message : str):
        """
        labs is the list of the names of all the laboratories in the database.
        """
        super(DialogConfirm, self).__init__()
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)
        self.plainTextEdit.insertPlainText(message)
