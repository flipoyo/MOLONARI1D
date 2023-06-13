from PyQt5 import QtWidgets, uic
from ..utils.get_files import get_ui_asset

From_DialogCreateStudy = uic.loadUiType(get_ui_asset("dialogCreateStudy.ui"))[0]
class DialogCreateStudy(QtWidgets.QDialog,From_DialogCreateStudy):
    """
    Enable the user to pick a laboratory and the name of the study being created.
    """
    def __init__(self, labs : list[str]):
        """
        labs is the list of the names of all the laboratories in the database.
        """
        super(DialogCreateStudy, self).__init__()
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)

        for lab in labs:
            self.comboBoxShowLabs.addItem(lab)

    def selectedLab(self):
        """
        Return the currently selected laboratory.
        """
        return self.comboBoxShowLabs.currentText()

    def studyName(self):
        """
        Return the name of the study.
        """
        return self.lineEditStudyName.text()