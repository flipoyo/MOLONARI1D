import numpy as np
import matplotlib.pyplot as plt
from pyheatmy.synthetic_MOLONARI import *
from pyheatmy.config import *
from pyheatmy.utils import create_periodic_signal
import scipy as sp


# à mettre dans utils (?)
def two_column_array(a1, a2):
    assert len(a1) == len(a2), "t and T must have the same length"
    if len(a2.shape) == 1:
        a = np.zeros((len(a1), 2))
        a[:, 0] = a1
        a[:, 1] = a2
        return a
    else:
        a = np.zeros((len(a1), int(1 + a2.shape[1])))
        a[:, 0] = a1
        a[:, 1:] = a2
        return a


class time_series_multiperiodic:
    def __init__(self, type):
        assert type in [
            "ts",
            "multi_periodic",
        ], "type must be either ts or multi_periodic"
        self.type = type

    def values_time_series(self, dates, T, dt, depth_sensors):
        if self.type == "ts":
            self.time_series = two_column_array(dates, T)
            self.dt = dt
            self.nb_sensors = len(T[0, :])
            self.depth_sensors = depth_sensors
        else:
            return "This is not a time series"

    def create_multiperiodic_signal(
        self, amplitude, periods, dates, dt, offset=DEFAULT_T_riv_offset, verbose=True
    ):
        if self.type == "multi_periodic":
            self.dt = dt
            assert len(amplitude) == len(
                periods
            ), "amplitude and periods must have the same length"
            if verbose:
                print(
                    "Creating a multi-periodic signal, with the following period:",
                    periods,
                    "and the following amplitude:",
                    amplitude,
                )
            for i in range(len(periods)):
                periods[i] = convert_period_in_second(periods[i][0], periods[i][1])
                if verbose :
                    print("periods :", periods)
            T = create_periodic_signal(
                dates,
                dt,
                [amplitude[0], periods[0], offset],
                signal_name="TBD",
                verbose=False,
            )

            for i in range(1, len(amplitude)):
                T += create_periodic_signal(
                    dates,
                    dt,
                    [amplitude[i], periods[i], 0],
                    signal_name="TBD",
                    verbose=False,
                )
            self.multi_periodic = two_column_array(dates, T)
        else:
            return "This is not a multi-periodic type"

    def plot_temp_river(self, time_unit="s"):
        assert type(time_unit) == str, "time_unit must be of type str"
        if self.type == "multi_periodic":
            a = self.multi_periodic #ok, as we have a multi-periodic signal (which already is a n*2 matrix, corresponding of the river temperature at a given time)
            plt.plot(a[:, 0], a[:, 1])
            plt.title("Temperature profile")
            plt.xlabel("date")
            plt.ylabel("temperature : °C")
            plt.show()
        if self.type == "ts":
            a = self.time_series
            plt.plot(a[:, 0], a[:, 1]) #corresponding at the first sensor temperature, ie river temperature at a given time
            plt.title("Temperature profile")
            plt.xlabel("date")
            plt.ylabel("temperature : °C")
            plt.show()

    def nb_per_day(self, Verbose = True): #method to get the number of points per day
        if Verbose:
            print('dt must be in seconds')
        return(int(NSECINDAY/self.dt))
    
    def nb_days_in_period(self): #method to get the number of days in the period
        if self.type == "multi_periodic":
            return int(self.multi_periodic.shape[0]/self.nb_per_day())
        elif self.type == "ts":
            return int(self.time_series.shape[0]/self.nb_per_day())
        
    def create_matrix(self):
        if self.type == "ts":
            matrix = np.zeros(self.time_series.shape[0], self.nb_sensors)
            for i in range(self.time_series.shape[0]):
                matrix[i,:] = self.time_series[i,1:]
            self.matrix = matrix
        elif self.type == 'multi_periodic':
            return 0 # to be implemented, must compute an analytical resolution of temperature diffusion problem to get the matrix...
    
    def amplitude(self, day):
        amplitude_list = []
        n_dt_in_day = self.nb_per_day(Verbose=False)
        if self.type == "multi_periodic":
            return "To be implemented..."
        elif self.type == "ts":
            self.create_matrix()
            T = self.matrix
        else : 
            return "You can not compute the method before creating a time series or a multi-periodic signal"
        for j in range(len(T[0,:])):
            T_max = max(T[day:day + n_dt_in_day,j])
            T_min = min(T[day: day + n_dt_in_day,j])
            A = (T_max - T_min) / 2
            amplitude_list.append(A)
        return amplitude_list
    def ln_amp(self, day):
        amplitude_list = self.amplitude(self, day)
        amplitude_array = np.array(amplitude_list)
        ln_rapport_amplitude = np.log( amplitude_array / amplitude_array[0] )
        return ln_rapport_amplitude

    def get_pearson_coef(self):
        n_dt_in_day = self.nb_per_day(Verbose=False)
        n_days = self.nb_days_in_period()
        pearson_coef = np.zeros(n_days)
        for i in range(n_days):
            ln_amp_i = self.ln_amp(i*n_dt_in_day)
            Lr = sp.stats.linregress(self.depths, ln_amp_i)
            pearson_coef[i] = Lr.rvalue
        return pearson_coef
    
    def plot_pearson_coef(self):
        pearson_coef = self.get_pearson_coef()
        n_days = self.nb_days_in_period()
        n_days = np.arange(n_days)
        plt.scatter(n_days, pearson_coef)
        plt.xlabel('Jours')
        plt.ylabel('Coefficient de Pearson')
        plt.ylim(-1, 1)
        plt.title('Evolution du coefficient de Pearson en fonction du temps')
        plt.show()

# testing
if __name__ == "__main__":
    from datetime import datetime, timedelta

    timestamp = 1485714600
    date_0 = datetime.fromtimestamp(timestamp)
    step = timedelta(days=2, hours=3)
    dates = [date_0 + i * step for i in range(1000)]

    mp_ts = time_series_multiperiodic("multi_periodic")
    mp_ts.create_multiperiodic_signal(
        [10, 5, 3], [[1, "y"], [2, "m"], [21, "d"]], dates, dt=2 * NSECINDAY + 3 * NSECINHOUR
    )
    mp_ts.plot()
