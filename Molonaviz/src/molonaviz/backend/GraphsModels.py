import numpy as np
from ..interactions.MoloModel import MoloModel
from ..utils.general import build_picture, databaseDateToDatetime

"""
This file regroups different models used to display graphs in the window showing the sampling point results.
"""

class PressureDataModel(MoloModel):
    """
    A model to display the pressure as given by the captors (raw or cleaned data).
    """
    def __init__(self, queries):
        super().__init__(queries)
        self.array_data = []

    def update_data(self):
        try:
            while self.queries[0].next():
                self.array_data.append([self.queries[0].value(0),self.queries[0].value(1)]) #Date, Pressure
            self.array_data = np.array(self.array_data)
        except Exception:
            #Empty query or invalid query: then revert any changes done. The model is empty: nothing will be displayed.
            self.reset_data()

    def get_pressure(self):
        try:
            return self.array_data[:,1]
        except Exception:
            return np.array([])

    def get_dates(self):
        try:
            return databaseDateToDatetime(self.array_data[:,0])
        except Exception:
            return np.array([])

    def reset_data(self):
        self.array_data = []

class TemperatureDataModel(MoloModel):
    """
    A model to display the presure as given by the captors (raw or cleaned data).
    """
    def __init__(self, queries):
        super().__init__(queries)
        self.array_data = []

    def update_data(self):
        try:
            while self.queries[0].next():
                self.array_data.append([self.queries[0].value(0),self.queries[0].value(1),self.queries[0].value(2),self.queries[0].value(3),self.queries[0].value(4),self.queries[0].value(5)]) #Date, Temp1 to 4, TempBed
            self.array_data = np.array(self.array_data)
        except Exception:
            #Empty query or invalid query: then revert any changes done. The model is empty: nothing will be displayed.
            self.reset_data()

    def get_temperatures(self):
        try:
            return [self.array_data[:, i] for i in range(1,6)]
        except Exception:
            return np.array([])

    def get_dates(self):
        try:
            return databaseDateToDatetime(self.array_data[:,0])
        except Exception:
            return np.array([])

    def reset_data(self):
        self.array_data = []

class WaterFluxModel(MoloModel):
    """
    A model to display the water fluxes.
    """
    def __init__(self, queries):
        super().__init__(queries)
        self.flows = {}
        self.dates=[]

    def update_data(self):
        try:
            #Initialize data structures
            self.queries[0].next()
            if self.queries[0].value(0) is not None and self.queries[0].value(2) is not None:
                #There is at least a valid query so the model should not be empty
                self.dates.append(self.queries[0].value(0))
                self.flows[self.queries[0].value(2)] = [self.queries[0].value(1)]
                while self.queries[0].next():
                    self.dates.append(self.queries[0].value(0)) #Dates
                    self.flows[self.queries[0].value(2)].append(self.queries[0].value(1)) #Flow
                for i in range(1,len(self.queries)):
                    self.queries[i].next()
                    self.flows[self.queries[i].value(2)] = [self.queries[i].value(1)]
                    #Add the other flows for the different quantiles if they exist
                    while self.queries[i].next():
                        self.flows[self.queries[i].value(2)].append(self.queries[i].value(1))
        except Exception:
            #Empty query or invalid query: then revert any changes done. The model is empty: nothing will be displayed.
            self.reset_data()

    def get_water_flow(self):
        """
        Return a dictionnary with keys beings the quantiles and values being the arrays of associated flows.
        """
        try :
            return self.flows[0], {key:np.array(value) for index, (key,value) in enumerate(self.flows.items()) if key !=0}
        except Exception:
            # Quantile 0 (direct model) doesn't exists
            return np.array([]), {}

    def get_dates(self):
        return databaseDateToDatetime(np.array(self.dates))

    def reset_data(self):
        self.flows = {}
        self.dates=[]

class SolvedTemperatureModel(MoloModel):
    """
    A model to representing the temperature, depth and time. Can be used for umbrellas, temperature heat map or temperature per depth.
    """
    def __init__(self, queries):
        super().__init__(queries)
        self.dates = []
        self.data = {}
        self.depths = []

    def update_data(self):
        try:
            while self.queries[0].next():
                self.dates.append(self.queries[0].value(0))
            self.dates = np.array(self.dates)
            while self.queries[1].next():
                self.depths.append(np.float64(self.queries[1].value(0)))
            self.depths = np.array(self.depths)

            for i in range(2,len(self.queries)):
                query = self.queries[i]
                query.next()
                array_data = [np.float64(query.value(0))]
                quantile = query.value(1)
                while query.next():
                    array_data.append(np.float64(query.value(0)))
                array_data = build_picture(np.array(array_data), nb_cells= len(self.depths))
                self.data[quantile] = array_data
        except Exception:
            #Empty query or invalid query: then revert any changes done. The model is empty: nothing will be displayed.
            self.reset_data()


    def get_temperatures_cmap(self,quantile):
        """
        Given a quantile, return the associated heat map.
        """
        try:
            return self.data[quantile]
        except Exception:
            return np.array([[]])

    def get_depths(self):
        return np.array(self.depths)

    def get_dates(self):
        return databaseDateToDatetime(np.array(self.dates))

    def get_depth_by_temp(self, nb_dates):
        """
        Return a list and a dictionnary:
        -the list corresponds to the depths array
        -the dictionnary has as many keys as nb_dates: these are equally spaced dates. The values are the temperature values.
        """
        try:
            n = self.dates.shape[0]
            step = n // nb_dates
            result = {}
            for i in range(nb_dates):
                date = self.dates[i*step]
                result[date] = self.data[0][:,np.where(self.dates==date)[0][0]]
            return self.depths,result
        except Exception:
            return np.array([]), {}

    def get_temp_by_date(self,depth,quantile):
        """
        Return the temperatures for a given depth and quantile.
        """
        try:
            return self.data[quantile][np.where(self.depths==depth)[0][0],:]
        except Exception:
            return np.array([])

    def reset_data(self):
        self.dates = []
        self.data = {}
        self.depths = []

class HeatFluxesModel(MoloModel):
    """
    A model to display the three heat fluxes (advective, conductive, total)
    """
    def __init__(self, queries):
        super().__init__(queries)
        self.dates = []
        self.array_data = []
        self.depths = []

    def update_data(self):
        try:
            while self.queries[0].next():
                self.dates.append(self.queries[0].value(0))
            self.dates = np.array(self.dates)
            while self.queries[1].next():
                self.depths.append(np.float64(self.queries[1].value(0)))
            self.depths = np.array(self.depths)

            while self.queries[2].next():
                self.array_data.append([np.float64(self.queries[2].value(1)),np.float64(self.queries[2].value(2)),np.float64(self.queries[2].value(3))]) #Advective, conductive, total
            self.array_data = np.array(self.array_data)

            self.advective = build_picture(self.array_data[:,0],nb_cells =len(self.depths))
            self.conductive = build_picture(self.array_data[:,1],nb_cells =len(self.depths))
            self.total = build_picture(self.array_data[:,2],nb_cells =len(self.depths))
        except Exception:
            #Empty query or invalid query: then revert any changes done. The model is empty: nothing will be displayed.
            self.reset_data()

    def get_depths(self):
        return np.array(self.depths)

    def get_dates(self):
        return databaseDateToDatetime(np.array(self.dates))

    def get_advective_flow(self):
        if len(self.advective) ==0:
            #The model is empty!
            return np.array([[]])
        return self.advective

    def get_conductive_flow(self):
        if len(self.conductive)==0:
            #The model is empty!
            return np.array([[]])
        return self.conductive

    def get_total_flow(self):
        if len(self.total)==0:
            #The model is empty!
            return np.array([[]])
        return self.total

    def reset_data(self):
        self.dates = []
        self.array_data = []
        self.depths = []
        self.advective = []
        self.conductive = []
        self.total = []

class ParamsDistributionModel(MoloModel):
    """
    A model to display the information about the parameters distribution.
    """
    def __init__(self, queries):
        super().__init__(queries)
        self.log10k = []
        self.porosity = []
        self.conductivity = []
        self.capacity = []

    def update_data(self):
        try:
            while self.queries[0].next():
                self.log10k.append(self.queries[0].value(0))
                self.conductivity.append(self.queries[0].value(1))
                self.porosity.append(self.queries[0].value(2))
                self.capacity.append(self.queries[0].value(3))
            self.log10k = np.array(self.log10k)
            self.conductivity = np.array(self.conductivity)
            self.porosity = np.array(self.porosity)
            self.capacity = np.array(self.capacity)
        except Exception:
            #Empty query or invalid query: then revert any changes done. The model is empty: nothing will be displayed.
            self.reset_data()

    def get_log10k(self):
        return np.array(self.log10k)

    def get_conductivity(self):
        return np.array(self.conductivity)

    def get_porosity(self):
        return np.array(self.porosity)

    def get_capacity(self):
        return np.array(self.capacity)

    def reset_data(self):
        self.log10k = []
        self.porosity = []
        self.conductivity = []
        self.capacity = []