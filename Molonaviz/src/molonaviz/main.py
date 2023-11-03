from PyQt5 import QtWidgets, QtGui, QtCore, uic
from PyQt5.QtSql import QSqlDatabase
from queue import Queue
import sys, os.path
from pathlib import Path

from .frontend.dialogAboutUs import DialogAboutUs
from .frontend.dialogOpenDatabase import DialogOpenDatabase
from .frontend.dialogImportLab import DialogImportLab
from .frontend.dialogOpenStudy import DialogOpenStudy
from .frontend.dialogCreateStudy import DialogCreateStudy
from .frontend.dialogOpenSPoint import DialogOpenSPoint
from .frontend.dialogImportSPoint import DialogImportSPoint
from .frontend.subWindow import SubWindow
from .frontend.StudyHandler import StudyHandler
from .frontend.LabHandler import LabHandler

from .backend.StudyAndLabManager import StudyAndLabManager

from .frontend.printThread import InterceptOutput, Receiver
from .frontend.MoloTreeView import ThermometerTreeView, PSensorTreeViewModel, ShaftTreeView, SamplingPointTreeView
from .utils.general import InvalidFile, displayCriticalMessage, createDatabaseDirectory, checkDbFolderIntegrity, extractDetectorsDF
from .utils.get_files import get_ui_asset, get_imgs, get_interactions_asset, get_docs

From_MainWindow = uic.loadUiType(get_ui_asset("mainwindow.ui"))[0]
class MainWindow(QtWidgets.QMainWindow,From_MainWindow):
    """
    The main window of the Molonaviz application.
    """
    def __init__(self):
        # Call constructor of parent classes
        super(MainWindow, self).__init__()
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)

        #Setup the views
        self.thermoView = ThermometerTreeView(None)
        self.treeViewThermometers.setModel(self.thermoView)
        self.treeViewThermometers.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.psensorView = PSensorTreeViewModel(None)
        self.treeViewPressureSensors.setModel(self.psensorView)
        self.treeViewPressureSensors.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.shaftView = ShaftTreeView(None)
        self.treeViewShafts.setModel(self.shaftView)
        self.treeViewShafts.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.spointView = SamplingPointTreeView(None)
        self.treeViewDataSPoints.setModel(self.spointView)
        self.treeViewDataSPoints.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)


        #TODO: models for psensors and others.
        #Connect the actions to the appropriate slots
        self.pushButtonClear.clicked.connect(self.clearText)
        self.actionImportLab.triggered.connect(self.importLab)
        self.actionAboutMolonaViz.triggered.connect(self.aboutUs)
        self.actionOpenUserguideFR.triggered.connect(self.openUserGuideFR)
        self.actionQuitMolonaViz.triggered.connect(self.close)
        self.actionCreateStudy.triggered.connect(self.createStudy)
        self.actionOpenStudy.triggered.connect(self.chooseStudyName)
        self.actionCloseStudy.triggered.connect(self.closeStudy)
        self.actionImportSPoint.triggered.connect(self.importSPoint)
        self.actionOpenSPoint.triggered.connect(self.openSPointFromAction)
        self.actionHideShowSPoints.triggered.connect(self.changeDockSPointsStatus)
        self.actionHideShowSensors.triggered.connect(self.changeDockSensorsStatus)
        self.actionHideShowAppMessages.triggered.connect(self.changeDockAppMessagesStatus)
        self.actionSwitchToTabbedView.triggered.connect(self.switchToTabbedView)
        self.actionSwitchToSubWindowView.triggered.connect(self.switchToSubWindowView)
        self.actionSwitchToCascadeView.triggered.connect(self.switchToCascadeView)
        self.actionChangeDatabase.triggered.connect(self.closeDatabase)

        self.treeViewDataSPoints.doubleClicked.connect(self.openSPointFromDock)

        #Some actions or menus should not be enabled: disable them
        self.actionCloseStudy.setEnabled(False)
        self.menuSPoint.setEnabled(False)

        #Setup the queue used to display application messages.
        self.messageQueue = Queue()
        sys.stdout = InterceptOutput(self.messageQueue)

        self.con = None #Connection to the database
        self.openDatabase()

        self.study_lab_manager = StudyAndLabManager(self.con)
        self.currentStudy = None
        self.currentLab = None

    def openDatabase(self):
        """
        If the user has never opened the database of if the config file is not valid (as a reminder, config is a text document containing the path to the database), display a dialog so the user may choose th e database directory.
        Then, open the database in the directory.
        """
        databaseDir = None
        createNewDatabase = False
        newDatabaseName = ""
        remember = False
        try:
            with open(os.path.join(os.path.dirname(__file__),'config.txt')) as f:
                databaseDir = f.readline()
        except OSError:
            #The config file does not exist.
            dlg = DialogOpenDatabase()
            dlg.setWindowModality(QtCore.Qt.ApplicationModal)
            res = dlg.exec()
            if res == QtWidgets.QDialog.Accepted:
                databaseDir, createNewDatabase, newDatabaseName = dlg.getDir()
                remember = dlg.checkBoxRemember.isChecked()
            else:
                #If the user cancels or quits the dialog, quit Molonaviz.
                #This is a bit brutal. Maybe there can be some other way to quit via Qt: the problem is that, at this point in the script, the app (QtWidgets.QApplication) has not been executed yet.
                sys.exit()

        #Now create or check the integrity of the folder given by databaseDir
        if createNewDatabase:
            #Create all folders and subfolders
            noerror = createDatabaseDirectory(databaseDir, newDatabaseName, get_interactions_asset('sample_text.txt'), get_docs("ERD_structure.sql"))
            if noerror:
                databaseDir = os.path.join(databaseDir, newDatabaseName)
            else:
                displayCriticalMessage(f"Something went wrong when creating the directory and the database creation was aborted.\nPlease make sure a directory with the name {newDatabaseName} does not already exist at path {databaseDir}")
                self.openDatabase()
        else:
            #Check if the folder has the correct format
            if not checkDbFolderIntegrity(databaseDir):
                displayCriticalMessage("The specified folder does not have the correct structure. Please try again.")
                #The database with the given path cannot be opened. If this is because the config.txt file was modified (and the path is not valid or points to somewhere else), then the config file needs to be deleted in order to prevent an infinite loop when opening Molonaviz.
                configPath = os.path.join(os.path.dirname(__file__),'config.txt')
                if os.path.isfile(configPath):
                    os.remove(configPath)
                self.openDatabase()

        #Now, databaseDir is the path to a valid folder containing a database. Open it!
        databaseFile = os.path.join(databaseDir,"Molonari.sqlite")
        self.con = QSqlDatabase.addDatabase("QSQLITE")
        self.con.setDatabaseName(databaseFile)
        self.con.open()

        self.showDatabaseName()

        if remember:
            with open(os.path.join(os.path.dirname(__file__),'config.txt'), 'w') as f:
                #Write (or overwrite) the path to the database file
                f.write(databaseDir)

    def showDatabaseName(self):
        """
        Display in the corresponding dock widget the name of the database. Try to do something not too ugly.
        """
        # Let's use a Path object, it's so much easier than os's paths.
        fullpath = Path(self.con.databaseName())
        # As a reminder, the database is always called "Molonari.sqlite". This is not what we want: we want the
        # directory above Molonari.sqlite.
        self.dockDatabaseName.setWindowTitle("Database directory: " + fullpath.parent.name)
        authorized_length = 30
        text = fullpath.root
        x = len(text)
        for directory in fullpath.parts[1:]:
            # Small hack for Linux user as the root directory is already the / character. Not very important.
            separator = ""
            try:
                if text[-1] != "/":
                    separator = "/"
            except Exception:
                pass

            if len(directory) + x < authorized_length:
                text = text + separator + directory
                x += len(directory)
            else:
                # Doesn't fit on the line: put it on a newline instead
                text = text + separator + "\n" + directory
                x = len(directory)
        self.fullDatabaseNameLabel.setText(text)

    def closeChildren(self):
        """
        Close related children: this reverts Molonaviz to its initial state. This should be called when closing the database, or a study. For now, this means
            -close the current study
            -close the current lab
            -clear all models
            -close all subwindows
        This should NOT close the connection to the database.
        """
        self.mdiArea.closeAllSubWindows()
        if self.currentStudy is not None:
            self.currentStudy.close()
        self.currentStudy = None
        if self.currentLab is not None:
            self.currentLab.close()
        self.currentLab = None

        self.thermoView.subscribe_model(None)
        self.psensorView.subscribe_model(None)
        self.shaftView.subscribe_model(None)
        self.spointView.subscribe_model(None)


    def closeDatabase(self):
        """
        Close the database and revert Molonaviz to its initial state.
        """
        self.closeChildren()
        self.con.close()
        self.con = None

        self.actionCreateStudy.setEnabled(True)
        self.actionOpenStudy.setEnabled(True)
        self.actionCloseStudy.setEnabled(False)
        self.menuSPoint.setEnabled(False)
        self.actionImportSPoint.setEnabled(False)
        self.actionOpenSPoint.setEnabled(False)
        self.actionRemoveSPoint.setEnabled(False)
        self.switchToSubWindowView()

        if os.path.isfile(os.path.join(os.path.dirname(__file__),'config.txt')):
            os.remove(os.path.join(os.path.dirname(__file__),'config.txt'))

        self.openDatabase()

    def importLab(self):
        """
        Display a dialog so the user may import a laboratory from a directory. The laboratory is added to the database.
        """
        dlg = DialogImportLab()
        dlg.setWindowModality(QtCore.Qt.ApplicationModal)
        res = dlg.exec()
        if res == QtWidgets.QDialog.Accepted:
            labdir,labname = dlg.getLaboInfo()
            if labdir and labname: #Both strings are not empty
                try:
                    thermometersDF, psensorsDF, shaftsDF = extractDetectorsDF(labdir)
                    self.study_lab_manager.create_new_lab(labname, thermometersDF, psensorsDF, shaftsDF)
                except InvalidFile:
                    displayCriticalMessage("Some of the files in the laboratory do not match the API. Nothing was added to the database. Please check your files and try again.")

    def createStudy(self):
        """
        Display a dialog so the user may create a study.The study is added to the database. Then, open this study (by calling self.openStudy)
        """
        labs = self.study_lab_manager.get_lab_names()
        if len(labs) == 0:
            displayCriticalMessage("No laboratory was found in the database. Please create one first.")
        else:
            dlg = DialogCreateStudy(labs)
            dlg.setWindowModality(QtCore.Qt.ApplicationModal)
            res = dlg.exec()
            if res == QtWidgets.QDialog.Accepted:
                userLab = dlg.selectedLab()
                userStudyName = dlg.studyName()
                if self.study_lab_manager.is_study_in_database(userStudyName) or not userStudyName: #The study is already in the database, or the study name is empty
                    displayCriticalMessage("The name of the study may not be empty and must be different from the studies in the database.")
                else:
                    self.study_lab_manager.create_new_study(userStudyName, userLab)
                    self.openStudy(userStudyName)

    def chooseStudyName(self):
        """
        Display a dialog so the user may choose a study to open, or display an error message. Then, open a study (by calling self.openStudy).
        """
        studies = self.study_lab_manager.get_study_names()
        if len(studies) ==0:
            displayCriticalMessage("No study was found in the database. Please create one first.")
        else:
            dlg = DialogOpenStudy(studies)
            dlg.setWindowModality(QtCore.Qt.ApplicationModal)
            res = dlg.exec()
            if res == QtWidgets.QDialog.Accepted:
                userStudyName = dlg.selectedStudy()
                self.openStudy(userStudyName)

    def openStudy(self, studyName : str):
        """
        Given a VALID name of a study, open it.
        """
        self.currentStudy = StudyHandler(self.con, studyName)
        #Open the laboratory associated with the study.
        if self.currentLab is not None:
            self.currentLab.close()
            self.currentLab = None
        labName = self.study_lab_manager.get_lab_names(studyName)[0] #Reminder: get_lab_names returns a list.
        self.currentLab = LabHandler(self.con, labName)

        self.thermoView.subscribe_model(self.currentLab.getThermoModel())
        self.psensorView.subscribe_model(self.currentLab.getPSensorModel())
        self.shaftView.subscribe_model(self.currentLab.getShaftModel())
        self.currentLab.refreshDetectors()

        #Open sampling point manager.
        self.spointView.subscribe_model(self.currentStudy.getSPointModel())
        self.currentStudy.refreshSpoints()

        self.dockSensors.setWindowTitle(f"Current lab: {labName}")

        #Enable previously disabled actions, such as the menu used to manage points
        self.actionCreateStudy.setEnabled(False)
        self.actionOpenStudy.setEnabled(False)
        self.actionCloseStudy.setEnabled(True)
        self.menuSPoint.setEnabled(True)
        self.actionImportSPoint.setEnabled(True)
        self.actionOpenSPoint.setEnabled(True)
        self.actionRemoveSPoint.setEnabled(True)

    def closeStudy(self):
        """
        Close the current study and revert the app to the initial state.
        """
        self.closeChildren()

        self.dockSensors.setWindowTitle(f"Current lab:")

        #Enable and disable actions so as to go back to go back to the initial state (no study opened)
        self.actionCreateStudy.setEnabled(True)
        self.actionOpenStudy.setEnabled(True)
        self.actionCloseStudy.setEnabled(False)
        self.menuSPoint.setEnabled(False)
        self.actionImportSPoint.setEnabled(False)
        self.actionOpenSPoint.setEnabled(False)
        self.actionRemoveSPoint.setEnabled(False)

    def importSPoint(self):
        """
        Display a dialog so that the user may import and add to the database a point.
        This function may only be called if a study and its lab are opened, ie if self.currentStudy is not None and self.currentLab is not None.
        """
        dlg = DialogImportSPoint(self.currentStudy, self.currentLab)
        dlg.setWindowModality(QtCore.Qt.ApplicationModal)
        res = dlg.exec()
        if res == QtWidgets.QDialog.Accepted:
            name, psensor, shaft, infofile, noticefile, configfile, prawfile, trawfile = dlg.getSPointInfo()
            self.currentStudy.importSPoint(name, psensor, shaft, infofile, noticefile, configfile, prawfile, trawfile)

    def openSPointFromAction(self):
        """
        This happens when the user clicks the "Open Point" action. Display a dialog so the user may choose a point to open, or display an error message. Then, open the corresponding point.
        This function may only be called if a study is opened.
        """
        spointsNames = self.currentStudy.getSPointsNames()

        if len(spointsNames) ==0:
            displayCriticalMessage("No point was found in this study. Please import one first.")
        else:
            dlg = DialogOpenSPoint(spointsNames)
            dlg.setWindowModality(QtCore.Qt.ApplicationModal)
            res = dlg.exec()
            if res == QtWidgets.QDialog.Accepted:
                spointName = dlg.selectedSPoint()
                widgetviewer = self.currentStudy.openSPoint(spointName)

                subwindow = SubWindow(widgetviewer)
                self.mdiArea.addSubWindow(subwindow)
                subwindow.show()

                self.switchToSubWindowView()

    def openSPointFromDock(self):
        """
        This happens when the user double cliks a point from the dock. Open it.
        This function may only be called if a study is opened, ie if self.currentStudy is not None.
        """
        #Get the information with the flag "UserRole": this information is the name of the point (as defined in MoloTreeViewModels).
        spointName = self.treeViewDataSPoints.selectedIndexes()[0].data(QtCore.Qt.UserRole)
        if spointName is None:
            #The user clicked on one of the sub-items instead (shaft, pressure sensor...). Get the information from the parent widget.
            spointName = self.treeViewDataSPoints.selectedIndexes()[0].parent().data(QtCore.Qt.UserRole)

        widgetviewer = self.currentStudy.openSPoint(spointName)
        subwindow = SubWindow(widgetviewer)
        self.mdiArea.addSubWindow(subwindow)
        subwindow.show()

        self.switchToSubWindowView()

    def switchToTabbedView(self):
        """
        Rearrange the subwindows to display them as tabs.
        """
        self.mdiArea.setViewMode(QtWidgets.QMdiArea.TabbedView)
        self.actionSwitchToTabbedView.setEnabled(False) #Disable this action to show the user it is the display mode currently being used.
        self.actionSwitchToSubWindowView.setEnabled(True)
        self.actionSwitchToCascadeView.setEnabled(True)

    def switchToSubWindowView(self):
        """
        Rearrange the subwindows to display them in a tile pattern.
        """
        self.mdiArea.setViewMode(QtWidgets.QMdiArea.SubWindowView)
        self.mdiArea.tileSubWindows()
        self.actionSwitchToTabbedView.setEnabled(True)
        self.actionSwitchToSubWindowView.setEnabled(False) #Disable this action to show the user it is the display mode currently being used.
        self.actionSwitchToCascadeView.setEnabled(True)

    def switchToCascadeView(self):
        """
        Rearrange the subwindows to display them in a cascade.
        """
        self.mdiArea.setViewMode(QtWidgets.QMdiArea.SubWindowView)
        self.mdiArea.cascadeSubWindows()
        self.actionSwitchToTabbedView.setEnabled(True)
        self.actionSwitchToSubWindowView.setEnabled(True)
        self.actionSwitchToCascadeView.setEnabled(False) #Disable this action to show the user it is the display mode currently being used.

    def changeDockSPointsStatus(self):
        """
        Hide or show the dock displaying the sampling points.
        """
        if self.actionHideShowSPoints.isChecked():
            self.dockDataSPoints.show()
        else :
            self.dockDataSPoints.hide()

    def changeDockSensorsStatus(self):
        """
        Hide or show the dock displaying the sensors.
        """
        if self.actionHideShowSensors.isChecked():
            self.dockSensors.show()
        else :
            self.dockSensors.hide()

    def changeDockAppMessagesStatus(self):
        """
        Hide or show the dock displaying the application messages.
        """
        if self.actionHideShowAppMessages.isChecked():
            self.dockAppMessages.show()
        else :
            self.dockAppMessages.hide()

    def printApplicationMessage(self, text : str):
        """
        Show in the corresponding dock a message which needs to be displayed. This means that the program called the print() method somewhere.
        """
        self.textEditApplicationMessages.moveCursor(QtGui.QTextCursor.End)
        self.textEditApplicationMessages.insertPlainText(text)

    def clearText(self):
        self.textEditApplicationMessages.clear()

    def aboutUs(self):
        """
        Display a small dialog about the app.
        """
        dlg = DialogAboutUs()
        dlg.exec()

    def closeEvent(self, event):
        """
        Close the database when user quits the app.
        """
        try:
            self.closeChildren()
            self.con.close()
            self.con = None
        except Exception as e:
            pass
        super().close()

    def openUserGuideFR(self):
        """
        Display the French user guide in a new window.
        """
        userguidepath = get_docs("UserguideFR.pdf")
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(userguidepath))

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(get_imgs("MolonavizIcon.png")))
    mainWin = MainWindow()
    mainWin.showMaximized()

    # Create thread that will be used to display application messages.
    messageThread = QtCore.QThread()
    my_receiver = Receiver(mainWin.messageQueue)
    my_receiver.printMessage.connect(mainWin.printApplicationMessage)
    my_receiver.moveToThread(messageThread)
    messageThread.started.connect(my_receiver.run)
    messageThread.start()

    sys.exit(app.exec())