from PyQt5 import QtWidgets, uic
from ..utils.get_files import get_ui_asset

From_DialogOpenSPoint = uic.loadUiType(get_ui_asset("dialogOpenSPoint.ui"))[0]
class DialogOpenSPoint(QtWidgets.QDialog,From_DialogOpenSPoint):
    """
    Enable the user to choose a point to open from the ones already existing in the study.
    """
    def __init__(self, pointsNames : list[str]):
        """
        pointsNames should be the list of all the points in the current study.
        """
        super(DialogOpenSPoint, self).__init__()
        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)

        for point in pointsNames:
            self.comboBoxShowPoints.addItem(point)

    def selectedSPoint(self):
        """
        Return the currently selected point.
        """
        return self.comboBoxShowPoints.currentText()