from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QPixmap
from ..utils.get_files import get_ui_asset, get_imgs

From_DialogAboutUs = uic.loadUiType(get_ui_asset("dialogAboutUs.ui"))[0]

class DialogAboutUs(QtWidgets.QDialog,From_DialogAboutUs):
    """
    Display some text and a picture about the app's creators.
    """
    def __init__(self):
        super(DialogAboutUs, self).__init__()
        QtWidgets.QDialog.__init__(self)

        self.setupUi(self)

        logoMines = get_imgs("LogoMines.jpeg")
        logoMolonaviz = get_imgs("MolonavizIcon.png")
        self.labelMolonaviz.setPixmap(QPixmap(logoMolonaviz))
        self.labelMines.setPixmap(QPixmap(logoMines))

