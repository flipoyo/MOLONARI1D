"""
This file regroups different models used to represent the available detectors in a virtual lab.
For now, such detectors are listed in a Tree View.
"""
from ..interactions.MoloModel import MoloModel
from ..interactions.Containers import Thermometer, PSensor, Shaft

class ThermometersModel(MoloModel):
    """
    A model to display the thermometers.
    """
    def __init__(self, queries):
        super().__init__(queries)
        self.data = [] #List of Thermometer objects

    def update_data(self):
        while self.queries[0].next():
            newTherm = Thermometer(self.queries[0].value(0), self.queries[0].value(1),self.queries[0].value(2),self.queries[0].value(3))
            self.data.append(newTherm)

    def get_all_thermometers(self):
        return self.data

    def reset_data(self):
        self.data = []

class PressureSensorsModel(MoloModel):
    """
    A model to display the pressure sensors.
    """
    def __init__(self, queries):
        super().__init__(queries)
        self.data = [] #List of PSensor objects

    def update_data(self):
        while self.queries[0].next():
            newPSensor = PSensor(self.queries[0].value(0), self.queries[0].value(1),self.queries[0].value(2),self.queries[0].value(3), self.queries[0].value(4), self.queries[0].value(5), self.queries[0].value(6))
            self.data.append(newPSensor)

    def get_all_psensors(self):
        return self.data

    def reset_data(self):
        self.data = []

class ShaftsModel(MoloModel):
    """
    A model to display the shafts.
    """
    def __init__(self, queries):
        super().__init__(queries)
        self.data = [] #List of Shaft objects

    def update_data(self):
        while self.queries[0].next():
            newShaft = Shaft(self.queries[0].value(0), self.queries[0].value(1),[self.queries[0].value(i) for i in range(2,6)], self.queries[0].value(6))
            self.data.append(newShaft)

    def get_all_shafts(self):
        return self.data

    def reset_data(self):
        self.data = []