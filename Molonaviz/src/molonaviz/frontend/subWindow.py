from PyQt5 import QtWidgets
from .SamplingPointViewer import SamplingPointViewer #Only used for type hints

class SubWindow(QtWidgets.QMdiSubWindow):
    """
    Concrete class for a clean implementation of a subwindow in the case multiple points are opened at the same time.
    """
    def __init__(self, wdg : SamplingPointViewer, title = "Point Viewer", modesombre = False):
        # Call constructor of parent classes
        super(SubWindow, self).__init__()
        QtWidgets.QMdiSubWindow.__init__(self)  

        modesombre = modesombre
        self.activerDesactiverModeSombre(modesombre)
        
        wdg.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)  # Fixe la taille du contenu
      
        wdg.setFixedSize(1560, 920)  # Fixe la taille du contenu
                        
        # Créez un widget de défilement (scroll area) et ajoutez le widget wdg à l'intérieur.
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidget(wdg)

        # Assurez-vous que la barre de défilement apparaît lorsque le contenu est trop grand.
        scroll_area.setWidgetResizable(True)

        # Définissez le widget de défilement comme le widget de la sous-fenêtre.
        self.setWidget(scroll_area)

        # Définissez le titre de la sous-fenêtre.
        self.setWindowTitle(title)
        



    def closeEvent(self, event):
        """
        Remove the subwindow en closing the event (this is not done by default).
        """
        mdi = self.mdiArea()
        mdi.removeSubWindow(self)
        event.accept()

    def activerDesactiverModeSombre(self, state):
        if state:
            self.setStyleSheet("background-color: rgb(50, 50, 50); color: rgb(255, 255, 255)")
        
        else:
            self.setStyleSheet("")  # Utilisez la feuille de style par défaut de l'application


