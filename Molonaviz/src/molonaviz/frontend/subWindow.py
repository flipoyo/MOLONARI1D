from PyQt5 import QtWidgets
from .SamplingPointViewer import SamplingPointViewer #Only used for type hints

class SubWindow(QtWidgets.QMdiSubWindow):
    """
    Concrete class for a clean implementation of a subwindow in the case multiple points are opened at the same time.
    """
    def __init__(self, wdg : SamplingPointViewer):
        # Call constructor of parent classes
        super(SubWindow, self).__init__()
        QtWidgets.QMdiSubWindow.__init__(self)
        self.setWidget(wdg)

    def closeEvent(self, event):
        """
        Remove the subwindow en closing the event (this is not done by default).
        """
        mdi = self.mdiArea()
        mdi.removeSubWindow(self)
        event.accept()



