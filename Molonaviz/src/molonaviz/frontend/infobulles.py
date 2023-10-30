import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from mainwindow import Ui_MainWindow

app = QApplication([])

fenetre = QMainWindow()
ui = Ui_MainWindow()
ui.setupUi(fenetre)

Compute = ui.pushButtonCompute  # Supposons que le bouton a pour nom "monBouton"
Compute.setToolTip("Ceci est une info-bulle pour mon bouton.")


fenetre.show()
sys.exit(app.exec_())
