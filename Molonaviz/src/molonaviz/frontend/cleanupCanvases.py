import pandas as pd

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from matplotlib.widgets import RectangleSelector

import matplotlib.dates as mdates


def createEmptyDf():
        """
        Return an empty dataframe with the correct fields.
        WARNING: if the fields do not have the correct type, the merges may fail, especially for the dates! Pandas can't merge a Timestamp and a Series of type object, even if it is empty!
        """
        df = pd.DataFrame({"Date" : pd.Series(dtype='datetime64[ns]'),
                            "Temp1" : pd.Series(dtype='float64'),
                            "Temp2" : pd.Series(dtype='float64'),
                            "Temp3" : pd.Series(dtype='float64'),
                            "Temp4" : pd.Series(dtype='float64'),
                            "TempBed" : pd.Series(dtype='float64'),
                            "Pressure" : pd.Series(dtype='float64')})
        return df

class CompareCanvas(FigureCanvasQTAgg):
    """
    A small class to select some points which should be removed.
    For now, three things are plots on the same curve:
        - the reference data is the background, which correponds to the raw data
        - the cleaned data is immutable, and corresponds to the pre-processing using outliers methods. It cannot be changed
        - the selected data, which is a subset of the elements in reference_data no in cleaned data.
    """
    def __init__(self, reference_data : pd.DataFrame):
        self.fig = Figure()
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.reference_data = reference_data
        self.cleaned_data = createEmptyDf()
        self.selected_data = createEmptyDf()

    def setReferenceData(self, data):
        """
        Set the given dataframe as the reference data.
        """
        self.reference_data = data

    def set_cleaned_data(self, data):
        self.cleaned_data = data

    def set_selected_data(self, data):
        self.selected_data = data

    def plotData(self, field):
        """
        Plot given field (Pressure, Temp1, Temp2, Temp3, Temp4 or TempBed).
        """
        self.axes.clear()
        # Ok, so what is happening here? We have three dataframes:
        # - reference_data is the full dataframe (= raw measures)
        # - cleaned_data is the dataframe of points picked out by the outliers methods
        # - selected_data is the dataframe of points hand picked by the user
        # So formally, we have:
        # - All
        # - {cleaned}
        # - {selected_points}
        # And we want
        # - {cleaned}
        # - {selected_points} \ {cleaned}
        # - All \ ({cleaned} u {selected_points})
        # The goal is to make merges on the dataframes to reflect these changes. BUT, it's not simple because of the Timestamps. I hate pandas!

        # {cleaned}
        self.cleaned_data.plot.scatter(x ="Date", y = field, c = '#FF6D6D', s = 1, ax = self.axes)

        # {selected_points} \ {cleaned}
        modified_u_selected = self.cleaned_data.merge(self.selected_data, on=["Date", "Temp1","Temp2", "Temp3", "Temp4", "TempBed", "Pressure"], how = 'outer', indicator = True)
        selected_only = modified_u_selected[modified_u_selected["_merge"] == 'right_only']

        selected_only.plot.scatter(x ="Date", y = field, c = '#E52EA8', s = 1, ax = self.axes)

        # All \ ({cleaned} u {selected_points})
        modified_u_selected.drop(labels="_merge", axis = 1, inplace = True)
        all_but_modified_and_selected = self.reference_data.merge(modified_u_selected, on=["Date", "Temp1","Temp2", "Temp3", "Temp4", "TempBed", "Pressure"], how = 'left', indicator = True)
        untouched = all_but_modified_and_selected[all_but_modified_and_selected["_merge"] == "left_only"]

        untouched.plot.scatter(x ="Date", y = field, c = 'b', s = 1, ax = self.axes)

        self.format_xaxis()
        self.fig.canvas.draw()

    def format_xaxis(self):
        formatter = mdates.DateFormatter("%y/%m/%d %H:%M")
        self.axes.xaxis.set_major_formatter(formatter)
        self.axes.xaxis.set_major_locator(MaxNLocator(4))

class SelectCanvas(CompareCanvas):
    """
    An interactive matplolib allowing the user to select points. Since it inherits from CompareCanvas, it can plot 3 types of curves, and follows the almost the same rules. Although SelectCanvas holds the dataframes with all columns, it can only show one of these columns on the y axis.

    SelectCanvas holds the last selection made by the user in self.last_selection. Not that this is not the same as CompareCanvas.selected_data: if the user selects some points in variable A, then move on to variable B, we should both:
        - display the points manually selected in A
        - display the last selection done on A
    These should be of the same color.
    """
    def __init__(self, reference_data: pd.DataFrame, field):
        super().__init__(reference_data)

        self.field = field# The only field which will be shown
        self.x = self.reference_data["Date"]
        self.y = self.reference_data[self.field]
        self.last_selection = createEmptyDf()

        self.selector = RectangleSelector(self.axes, self.selectPoints, useblit=True)

    def selectPoints(self, event1, event2):
        var_plotted = self.reference_data.copy(deep = True)
        mask = self.inside(event1, event2)
        self.last_selection = var_plotted[mask]
        self.plotData(self.field)

    def inside(self, event1, event2):
        """
        Return a boolean mask of the points inside the rectangle defined by event1 and event2.
        """
        # Get the 4 corners of the rectangle selected.
        x0, x1 = sorted([event1.xdata, event2.xdata])
        y0, y1 = sorted([event1.ydata, event2.ydata])
        x0 = mdates.num2date(x0)
        x1 = mdates.num2date(x1)

        # self.x is a pandas dataframe with TIMESTAMPS and not datetime objects. Calling self.x.dt.date convert it to a dataframe with datetime.date objects and not datetime.datetime objects (which also have the hour, minutes and seconds)
        # After some research, it seems a panda dataframe can only hold datetime.date objects and not datetime.datetime objects (with hours and so on). So we have to convert x0 et and x1 to timestamps.
        # BUT! It's not done! self.x is a list of Timestamps without any timezone! However, x0 and x1 use the default timezone (utc).
        # When trying to compare x0 and self.x, pandas will fallback to the default implementation of the Timestamps, which is np.datetime64, which bugs as it tries to compare an timezone unaware date and a timezone specific one. And you still wonder why I hate pandas?
        x0 = x0.replace(tzinfo = None)
        x1 = x1.replace(tzinfo = None)
        x0 = pd.Timestamp(x0)
        x1 = pd.Timestamp(x1)
        mask = ((self.x > x0) & (self.x < x1) &
                (self.y > y0) & (self.y < y1))
        return mask

    def plotData(self, field):
        save_selected_points = self.selected_data.copy(deep = True)
        self.selected_data = pd.concat([self.selected_data, self.last_selection], axis = 0)
        self.selected_data.drop_duplicates(inplace = True)
        self.selected_data.dropna(inplace = True) # For sanity purposes
        super().plotData(field)
        self.selected_data = save_selected_points

    def reset(self):
        self.last_selection = self.createEmptyDf()

    def getSelectedPoints(self):
        return self.last_selection
