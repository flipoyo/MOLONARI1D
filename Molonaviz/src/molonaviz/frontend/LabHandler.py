from PyQt5.QtSql import QSqlDatabase #Used only for type hints
from ..backend.LabEquipementManager import LabEquipementManager

class LabHandler:
    """
    A high-level concrete frontend class to handle the user's actions regarding a laboratory.
    For now, this class doesn't do much, but it can be enhanced to handle a virtual laboratory.
    An instance of this class is always linked to a laboratory.
    """
    def __init__(self, con : QSqlDatabase, labName : str):
        self.labManager = LabEquipementManager(con, labName)

    def getThermoModel(self):
        """
        Return the thermometers backend model.
        """
        return self.labManager.get_thermo_model()

    def getPSensorModel(self):
        """
        Return the thermometers pressure sensor model.
        """
        return self.labManager.get_psensor_model()

    def getShaftModel(self):
        """
        Return the shaft pressure sensor model.
        """
        return self.labManager.get_shaft_model()

    def refreshDetectors(self):
        """
        Refresh the detectors data
        """
        self.labManager.refresh_detectors()

    def getPSensorsNames(self):
        """
        Return the list of the names of the pressure sensors.
        """
        return self.labManager.get_psensors_names()

    def getShaftsNames(self):
        """
        Return the list of the names of the shafts.
        """
        return self.labManager.get_shafts_names()

    def close(self):
        pass