from PyQt5 import QtGui, QtCore

from ..interactions.MoloView import MoloView
from ..interactions.MoloModel import MoloModel #Used only for type hints


class ThermometerTreeView(QtGui.QStandardItemModel, MoloView):
    """
    Concrete class for the model used for to display the thermometers in a tree view in the main window.
    """
    def __init__(self, molomodel: MoloModel | None):
        QtGui.QStandardItemModel.__init__(self)
        MoloView.__init__(self, molomodel)

    def onUpdate(self):
        self.clear()# QStandardItemModel method to visually remove everything from the TreeView
        thermos = self.model.get_all_thermometers()
        for thermometer in thermos:
            item = QtGui.QStandardItem(thermometer.name)
            self.appendRow(item)
            item.appendRow(QtGui.QStandardItem(f"Manufacturer name : {thermometer.manuName}"))
            item.appendRow(QtGui.QStandardItem(f"Manufacturer reference : {thermometer.manuRef}"))
            item.appendRow(QtGui.QStandardItem(f"Error (°C) : {thermometer.error}"))

    def resetData(self):
        self.clear()

class PSensorTreeViewModel(QtGui.QStandardItemModel, MoloView):
    """
    Concrete class for the model used for to display the pressure sensors in a tree view in the main window.
    """
    def __init__(self, molomodel: MoloModel | None):
        QtGui.QStandardItemModel.__init__(self)
        MoloView.__init__(self, molomodel)

    def onUpdate(self):
        self.clear()# QStandardItemModel method to visually remove everything from the TreeView
        psensors = self.model.get_all_psensors()
        for ps in psensors:
            item = QtGui.QStandardItem(ps.name)
            self.appendRow(item)
            item.appendRow(QtGui.QStandardItem(f"Datalogger : {ps.datalogger}"))
            item.appendRow(QtGui.QStandardItem(f"Calibration date : {ps.calibrationDate}"))
            item.appendRow(QtGui.QStandardItem(f"Intercept : {ps.intercept:.3f}"))
            item.appendRow(QtGui.QStandardItem(f"Du/Dh : {ps.dudh:.3f}"))
            item.appendRow(QtGui.QStandardItem(f"Du/Dt : {ps.dudt:.3f}"))
            item.appendRow(QtGui.QStandardItem(f"Error : {ps.error:.2f}"))

    def resetData(self):
        self.clear()

class ShaftTreeView(QtGui.QStandardItemModel, MoloView):
    """
    Concrete class for the model used for to display the shafts in a tree view in the main window.
    """
    def __init__(self, molomodel: MoloModel | None):
        QtGui.QStandardItemModel.__init__(self)
        MoloView.__init__(self, molomodel)

    def onUpdate(self):
        self.clear()# QStandardItemModel method to visually remove everything from the TreeView
        shafts = self.model.get_all_shafts()
        for shaft in shafts:
            item = QtGui.QStandardItem(shaft.name)
            self.appendRow(item)
            item.appendRow(QtGui.QStandardItem(f"Datalogger : {shaft.datalogger}"))
            item.appendRow(QtGui.QStandardItem(f"Thermometer type : {shaft.thermoType}"))
            item.appendRow(QtGui.QStandardItem(f"Thermometer depths (m) : {shaft.depths}"))

    def resetData(self):
        self.clear()

class SamplingPointTreeView(QtGui.QStandardItemModel, MoloView):
    """
    Concrete class for the model used for to display the points associated to a study in a tree view in the main window.
    """
    def __init__(self, molomodel: MoloModel | None):
        QtGui.QStandardItemModel.__init__(self)
        MoloView.__init__(self, molomodel)

    def onUpdate(self):
        self.clear()# QStandardItemModel method to visually remove everything from the TreeView
        samplingPoints = self.model.get_all_sampling_points()
        for spoint in samplingPoints:
            item = QtGui.QStandardItem(spoint.name)
            item.setData(spoint.name, QtCore.Qt.UserRole) #Flag the name of the point as an information (in fact the only information) which the user will be able to retrieve.
            self.appendRow(item)
            item.appendRow(QtGui.QStandardItem(f"Pressure sensor : {spoint.psensor}"))
            item.appendRow(QtGui.QStandardItem(f"Shaft : {spoint.shaft}"))
            item.appendRow(QtGui.QStandardItem(f"River bed = {spoint.rivBed}"))
            item.appendRow(QtGui.QStandardItem(f"Offset = {spoint.offset}"))

    def resetData(self):
        self.clear()

