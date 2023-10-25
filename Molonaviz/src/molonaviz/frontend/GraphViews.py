"""
This file regroups different view inheriting from matplotlib's canvas. They are used to display data as graphs.
"""
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import matplotlib.dates as mdates
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.gridspec import GridSpec

matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import matplotlib.cm as cm
from matplotlib.ticker import MaxNLocator
import numpy as np
from molonaviz.interactions.MoloModel import MoloModel
from molonaviz.interactions.MoloView import MoloView
from molonaviz.utils.general import dateToMdates
from molonaviz.utils.general import displayCriticalMessage, displayWarningMessage, createDatabaseDirectory

class GraphView(MoloView, FigureCanvasQTAgg):
    """
    Abstract class to implement a graph view, inheriting both from the MoloView and the matplotlib canvas.
    """
    def __init__(self, molomodel : MoloModel | None, width=5, height=5, dpi=100):
        MoloView.__init__(self, molomodel)

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        FigureCanvasQTAgg.__init__(self, self.fig)
        self.fig.tight_layout(h_pad=5, pad=5)
        self.ax = self.fig.add_subplot(111)

    def get_model(self, model):
        return MoloView.get_model(model)

class GraphView1D(GraphView):
    """
    Abstract class to represent 1D views (such the pressure and temperature plots).
    If time_dependent is true, then the x-array is expected to be an array of dates and will be displayed as such.

    There are two main attributes in this class:
        -self.x is a 1D array and will be displayed one the x-axis
        -self.y is a dictionnary of 1D array : the keys are the labels which should be displayed. This is useful to plot many graphs on the same view (quantiles for example).
    """
    def __init__(self, molomodel: MoloModel | None, time_dependent=False, title="", ylabel="", xlabel=""):
        super().__init__(molomodel)
        # Créez les axes et associez-les à self.ax
        self.ax = self.fig.add_subplot(111, sharex=self.ax, sharey=self.ax)
        #x and y correspond to the data which should be displayed on the x-axis and y-axis (ex: x=Date,y=Pressure)
        self.x = []
        self.y = {}
        self.xlabel = xlabel
        self.ylabel=ylabel
        self.title = title
        self.time_dependent = time_dependent
        self.colorbar = None
       


    def onUpdate(self):
        self.ax.clear()
        self.resetData()
        self.retrieveData()
        self.setup_x()
        self.plotData()
        self.draw()

    def setup_x(self):
        """
        This method allows to apply changes to the data on the x-axis (for example, format a date).
        """
        if self.time_dependent:
            self.x = dateToMdates(self.x)
            formatter = mdates.DateFormatter("%y/%m/%d %H:%M")
            self.ax.xaxis.set_major_formatter(formatter)
            self.ax.xaxis.set_major_locator(MaxNLocator(4))
            plt.setp(self.ax.get_xticklabels(), rotation = 15)
        else:
            pass

    def plotData(self):
        for index, (label, data) in enumerate(self.y.items()):
            if len(self.x) == len(data):
                self.ax.plot(self.x, data, label=label)
        self.ax.legend(loc='best')
        self.ax.set_ylabel(self.ylabel)

        self.ax.set_xlabel(self.xlabel)
        self.ax.set_title(self.title)
        self.ax.grid(True)

    def resetData(self):
        self.x = []
        self.y = {}
        self.ax.get_xaxis().set_visible(False)
        self.ax.get_yaxis().set_visible(False)

    def get_model(self, model):
        return super().get_model(model)

class GraphView2D(GraphView):
    """
    Abstract class to represent 2D views (such the temperature heat maps).
    There are three main attributes in this class:
        -self.x is a 1D array and will be displayed on the x-axis
        -self.y is a 1D array and will be displayed one the y-axis
        -self.cmap is a 2D array: the value self.y[i,j] is actually the value of a pixel.
    """
    def __init__(self, molomodel: MoloModel | None,time_dependent=False,title="",xlabel = "",ylabel=""):
        super().__init__(molomodel)
   
        self.time_dependent = time_dependent
        self.title = title
        self.ylabel = ylabel
        self.xlabel = xlabel
        self.cmap = []

        # créer une colorbar
        self.colorbar = None
        
        

    def onUpdate(self):
               
        self.ax.clear()
        self.resetData()
               
        #Créez les axes et associez-les à self.ax, en enlevant les échelles [0, 1]
        self.ax = self.fig.add_subplot(111, sharex=self.ax, sharey=self.ax)      

        self.retrieveData()
        self.setup_x()
        self.plotData()
        self.draw()
        

    def setup_x(self):
        """
        This method allows to apply changes to the data on the x-axis (for example, format a date).
        """
        if self.time_dependent:
            self.x = dateToMdates(self.x)
            formatter = mdates.DateFormatter("%y/%m/%d %H:%M")
            self.ax.xaxis.set_major_formatter(formatter)
            self.ax.xaxis.set_major_locator(MaxNLocator(4))
            plt.setp(self.ax.get_xticklabels(), rotation = 7.5)
            self.ax.set_xlim(self.x[0], self.x[-1])
        else:
            pass

    def plotData(self):
        
        if self.cmap.shape[1] ==len(self.x) and self.cmap.shape[0] == len(self.y):
            #View is not empty and should display something
            image = self.ax.imshow(self.cmap, cmap=cm.Spectral_r, aspect="auto", extent=[self.x[0], self.x[-1], float(self.y[-1]), float(self.y[0])], data="float")
            self.colorbar = self.fig.colorbar(image, ax=self.ax, use_gridspec=True)
                
            self.ax.xaxis_date()
            self.ax.set_title(self.title)
            self.ax.set_ylabel(self.ylabel)
            
            
    def retrieveData(self):
        self.y = self.model.get_depths()
        self.x = self.model.get_dates()

    def resetData(self):
        self.x = []
        self.y = []
        self.cmap = []
       
        # hide color bar, not remove it
        if self.colorbar is not None:
            self.colorbar.ax.set_visible(False)
            self.colorbar = None
        
        # remove scales
        self.ax.get_xaxis().set_visible(False)
        self.ax.get_yaxis().set_visible(False)

class GraphViewHisto(GraphView):
    """
    Abstract class to display histograms.
    """
    def __init__(self, molomodel: MoloModel | None, bins=60, color ='green', title="", xlabel = ""):
        super().__init__(molomodel)
        self.bins = bins
        self.data = []
        self.color = color
        self.title = title
        self.xlabel = xlabel

    def updateBins(self,bins):
        self.bins = bins

    def onUpdate(self):
        self.ax.clear()
        self.resetData()
        self.retrieveData()
        self.plotData()
        self.draw()

    def plotData(self):
        self.ax.hist(self.data, edgecolor='black', bins=self.bins, alpha=.3, density=True, color=self.color)
        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.xlabel)

    def resetData(self):
        self.data = []

class PressureView(GraphView1D):
    """
    Concrete class to display the Pressure in "Data arrays and plots" tab.
    """
    def __init__(self, molomodel: MoloModel | None, time_dependent=True, title="", ylabel="Voltage (V)", xlabel=""):
        super().__init__(molomodel, time_dependent, title, ylabel, xlabel)

    def retrieveData(self):
        self.x  = self.model.get_dates()
        self.y  = {"":np.float64(self.model.get_pressure())} #No label required for this one.

    def showVoltageLabel(self, show_voltage : bool):
        """
        Change the y-label according to show_voltage. This allows a PressureView to handle both pressure and voltage, which are two representations of the same physical quantity.
        """
        if show_voltage:
            self.ylabel = "Voltage (V)"
        else:
            self.ylabel = "Differential pressure (m)"

class TemperatureView(GraphView1D):
    """
    Concrete class to display the temperature in "Data arrays and plots" tab.
    """
    def __init__(self, molomodel: MoloModel | None, time_dependent=True, title="", ylabel="Temperature (°C)", xlabel=""):
        super().__init__(molomodel, time_dependent, title, ylabel, xlabel)

    def retrieveData(self):
        self.x  = self.model.get_dates()
        self.y  = {f"Sensor n°{i}":np.float64(temp) for i,temp in enumerate(self.model.get_temperatures())}

class UmbrellaView(GraphView1D):
    """
    Concrete class for the umbrellas plots.
    """
    def __init__(self, molomodel: MoloModel | None, time_dependent=False, title="", ylabel="Depth (m)", xlabel="Temperature (°C)", nb_dates =10):
        super().__init__(molomodel, time_dependent, title, ylabel, xlabel)
        self.nb_dates = nb_dates     

    def retrieveData(self):
        self.x,self.y = self.model.get_depth_by_temp(self.nb_dates)

    def plotData(self):
        """
        This function needs to be overloaded for the umbrellas, as the plot function must be like plot(temps, depth) with depths being fixed.
        """
        
        cmap = plt.get_cmap('Reds')
        colors = [cmap(i / len(self.y.items())) for i in range(len(self.y.items()))]
        list_labels = [label for label in self.y.keys()]

        for index, (label, data) in enumerate(self.y.items()):

            if len(self.x) == len(data):
                self.ax.plot( data,self.x, color=colors[index])
                
        # inverse the y-axis
        self.ax.set_ylim(0.55, 0)

        self.ax.legend(list_labels, loc='best')
        self.ax.set_ylabel(self.ylabel)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_title('Umbrellas plot')
        self.ax.grid(True)
                

    def resetData(self):
        self.x = []
        self.y = {}
        self.cmap = []

        # hide color bar, not remove it
        if self.colorbar is not None:
            self.colorbar.ax.set_visible(False)
            self.colorbar = None
        self.ax.clear()
        self.ax = self.fig.add_subplot(111, sharex=self.ax, sharey=self.ax)
        self.ax.get_xaxis().set_visible(False)
        self.ax.get_xaxis().set_visible(False)

    def onUpdate(self):
        self.resetData()
        self.retrieveData()
        self.plotData()
        self.draw()


class TempDepthView(GraphView1D):
    """
    Concrete class for the temperature to a given depth as a function of time.
    An important attribut for this class is option, which reflects what the user wants to display: either quantiles or depths for the thermometer. Option is a list of two elements:
        - the first one is a depth corresponding to a thermometer
        - a list of values representing the quantiles. If this list is empty, then nothing will be displayed
    The basis state is [None, []], as no quantile can be displayed, and the view can't know at which depth is the thermometer.
    options is NOT considered to be part of internal data, and will not be modified when calling resetData.
    """
    def __init__(self, sensors:MoloModel | None, molomodel: MoloModel | None, time_dependent=True, title="", ylabel="Temperature (°C)", xlabel="",options=[None,[]]):
        super().__init__(molomodel,time_dependent, title, ylabel, xlabel)
        self.options = options
        self.sensors = sensors
        self.molomodel = molomodel
    
        

    def updateOptions(self,options):
        self.options = options
        super().resetData() #Refresh the plots

    def retrieveData(self):
        if self.options[0] is not None: #A computation has been done.
            depth_thermo = self.options[0]
            self.x = self.molomodel.get_dates()
            self.y  = {f"Sensor n°{i}":np.float64(temp) for i,temp in enumerate(self.sensors.get_temperatures())}
            for quantile in self.options[1]:
                self.y[f"Temperature at depth {depth_thermo:.3f} m - quantile {quantile}"] = self.molomodel.get_temp_by_date(depth_thermo, quantile)

class WaterFluxView(GraphView1D):
    """
    Concrete class for the water flux as a function of time.
    """
    def __init__(self, molomodel: MoloModel | None, time_dependent=True, title="", ylabel="Water flow  (m/s)", xlabel=""):
        super().__init__(molomodel, time_dependent, title, ylabel, xlabel)

    def retrieveData(self):
        self.x = self.model.get_dates()
        direct_model, all_flows = self.model.get_water_flow()
        if len(direct_model) != 0:
            self.y["Direct model"] = direct_model
        if all_flows != {}:
            #The model is not empty so the view should display something
            for index, (key,value) in enumerate(all_flows.items()):
                if key!=0:
                    self.y[f"Quantile {key}"] = value

class TempMapView(GraphView2D):
    """
    Concrete class for the heat map.
    """
    def __init__(self, molomodel: MoloModel | None, time_dependent=True, title="Temperature (C)", xlabel="", ylabel="Depth (m)"):
        super().__init__(molomodel, time_dependent, title, xlabel, ylabel)

    def retrieveData(self):
        self.cmap = self.model.get_temperatures_cmap(0)
        self.x = self.model.get_dates()
        self.y = self.model.get_depths()

class AdvectiveFlowView(GraphView2D):
    """
    Concrete class for the advective flow map.
    """
    def __init__(self, molomodel: MoloModel | None, time_dependent=True, title="Advective flow (W/m²)", xlabel="", ylabel="Depth (m)"):
        super().__init__(molomodel, time_dependent, title, xlabel, ylabel)

    def retrieveData(self):
        self.cmap = self.model.get_advective_flow()
        self.x = self.model.get_dates()
        self.y = self.model.get_depths()

class ConductiveFlowView(GraphView2D):
    """
    Concrete class for the conductive flow map.
    """
    def __init__(self, molomodel: MoloModel | None, time_dependent=True, title="Convective flow (W/m²)", xlabel="", ylabel="Depth (m)"):
        super().__init__(molomodel, time_dependent, title, xlabel, ylabel)

    def retrieveData(self):
        self.cmap = self.model.get_conductive_flow()
        self.x = self.model.get_dates()
        self.y = self.model.get_depths()

class TotalFlowView(GraphView2D):
    """
    Concrete class for the total heat flow map.
    """
    def __init__(self, molomodel: MoloModel | None, time_dependent=True, title="Total energy flow (W/m²)", xlabel="", ylabel="Depth (m)"):
        super().__init__(molomodel, time_dependent, title, xlabel, ylabel)

    def retrieveData(self):
        self.cmap = self.model.get_total_flow()
        self.x = self.model.get_dates()
        self.y = self.model.get_depths()

class Log10KView(GraphViewHisto):
    """
    Concrete class to display the distribution of the -Log10K paramter
    """
    def __init__(self, molomodel: MoloModel | None, bins=60, color='green', title="A posteriori histogram of the permeability", xlabel = "-log10(K)"):
        super().__init__(molomodel, bins, color, title, xlabel)

    def retrieveData(self):
        self.data = self.model.get_log10k()

class PorosityView(GraphViewHisto):
    """
    Concrete class to display the distribution of the porosity paramter
    """
    def __init__(self, molomodel: MoloModel | None, bins=60, color='blue', title="A posteriori histogram of the porosity"):
        super().__init__(molomodel, bins, color, title)

    def retrieveData(self):
        self.data = self.model.get_porosity()

class ConductivityView(GraphViewHisto):
    """
    Concrete class to display the distribution of the conductivity paramter
    """
    def __init__(self, molomodel: MoloModel | None, bins=60, color='orange', title="A posteriori histogram of the thermal conductivity"):
        super().__init__(molomodel, bins, color, title)

    def retrieveData(self):
        self.data = self.model.get_conductivity()

class CapacityView(GraphViewHisto):
    """
    Concrete class to display the distribution of the capacity paramter
    """
    def __init__(self, molomodel: MoloModel | None, bins=60, color='pink', title="A posteriori histogram of the thermal capacity"):
        super().__init__(molomodel, bins, color, title)

    def retrieveData(self):
        self.data = self.model.get_capacity()