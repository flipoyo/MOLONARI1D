import numpy as np
import matplotlib.pyplot as plt
from pyheatmy.synthetic_MOLONARI import *
from pyheatmy.config import *
from pyheatmy.utils import create_periodic_signal
from pyheatmy import *
from pyheatmy.time_series_multiperiodic import *
import scipy as sp
from datetime import datetime, timedelta
import os as os
import csv as csv 


class time_series_multiperiodic:
    def __init__(self, type, verbose = True):
        assert type in [
            "ts",
            "multi_periodic",
        ], "type must be either ts or multi_periodic"
        self.type = type

        if verbose:
            print("To use methods from 'profile_temperature' to the end of the code, you should define 3 arguments :")
            # + dates
            print("time_series_dict_user1, \n layers_list, \n and col_dict.")
            print("To check how to define those, go to :")
            print("MOLONARI1D/pyheatmy/research/Temp_ampl_ratio_diffusive_case.ipynb")
            print("It will show you how to use this class, in general")
            # + if ts

    def values_time_series(self, dates, T, depth_sensors):
        if self.type == "ts":
            self.time_series = [dates, T]
            self.nb_sensors = len(T[0, :])
            self.depth_sensors = depth_sensors
        else:
            return "This is not a time series"

    def create_multiperiodic_signal(
        self, amplitudes, periods, dates, offset=DEFAULT_T_riv_offset, verbose=True
    ):
        if self.type == "multi_periodic":
            assert len(amplitudes) == len(
                periods
            ), "amplitudes and periods must have the same length"
            if verbose:
                print(
                    "Creating a multi-periodic signal, with the following period:",
                    periods,
                    "and the respective following amplitude:",
                    amplitudes,
                )
            for i in range(len(periods)):
                periods[i] = convert_period_in_second(periods[i][0], periods[i][1])
            T = create_periodic_signal(
                dates,
                [amplitudes[0], periods[0], offset],
                signal_name="TBD",
                verbose=False,
            )

            for i in range(1, len(amplitudes)):
                T += create_periodic_signal(
                    dates,
                    [amplitudes[i], periods[i], 0],
                    signal_name="TBD",
                    verbose=False,
                )
            self.multi_periodic = [dates, T]
            if verbose:
                self.plot_temp()
        else:
            return "This is not a multi-periodic type"

    def plot_temp(self):
        
        if self.type == "multi_periodic":
            a = self.multi_periodic #ok, as we have a multi-periodic signal (which already is a n*2 matrix, corresponding of the river temperature at a given time)
        if self.type == "ts":
            a = self.time_series #corresponding at the first sensor temperature, ie river temperature at a given time

        dates = a[0]
        T = a[1]

        assert dates.shape[0] == T.shape[0], 'there should be as many dates as temperature mesures for one depth'
        # assert dates.dtype == datetime or dates.dtype == np.datetime64, "dates should be of type datetime.datetime and or of type" + str(dates.dtype)

        plt.title("Temperature profile")
        plt.plot(dates, T) 
        plt.xlabel("date")
        plt.tight_layout()
        plt.ylabel("temperature : °C")
        plt.show()

    def nb_per_day(self, verbose = True): #method to get the number of points per day
        if verbose:
            print('dt must be in seconds')
        return(int(NSECINDAY/15*60))  # return(int(NSECINDAY/self.dt)) but self.dt undefined
    
    def nb_days_in_period(self): #method to get the number of days in the period
        if self.type == "multi_periodic":
            return int(self.multi_periodic[0].shape[0]/self.nb_per_day())
        elif self.type == "ts":
            return int(self.time_series[0].shape[0]/self.nb_per_day())
        
    def profil_temperature(self, verbose = True):
        if self.type == "ts":
            matrix = np.zeros((self.time_series[0].shape[0], self.nb_sensors))
            for i in range(self.time_series[0].shape[0]):
                matrix[i,:] = self.time_series[i,1:]
            self.matrix = matrix
        
        elif self.type == 'multi_periodic':
            # instanciation du simulateur de données
            emu_observ_test_user1 = synthetic_MOLONARI.from_dict(self.time_series_dict_user1)

            #On force la variable T_riv dans l'objet emu_observ_test_user1
            emu_observ_test_user1._T_riv = self.multi_periodic[1][:]

            #Puis on applique les méthodes _generate_Shaft_Temp_series et _generate_perturb_Shaft_Temp_series pour changer les valeurs dépendante du nouveau T_riv
            emu_observ_test_user1._generate_Shaft_Temp_series(verbose = False)
            emu_observ_test_user1._generate_perturb_Shaft_Temp_series()
            emu_observ_test_user1._generate_perturb_T_riv_dH_series()

            col = Column.from_dict(self.col_dict,verbose=False)
            col._compute_solve_transi_multiple_layers(self.layers_list, self.nb_cells, verbose=False)

            if verbose:
                print(f"Layers list: {self.layers_list}")
                #On vérifie que les températures ont bien été modifiées dans l'objet column (en particulier que la température à profondeur nulle est bien celle de la rivière)
                plt.plot(emu_observ_test_user1._dates, col._temperatures[0,:])
                plt.show()
                print(f"La matrice de température a pour shape : {col._temperatures.shape}, abscisse = température aux 20 cellules, ordonnée = température à chaque pas de temps")

            return col._temperatures
    
    def amplitude(self, day):
        amplitude_list = []
        n_dt_in_day = self.nb_per_day(Verbose=False)
        if self.type == "multi_periodic":
            return "To be implemented..."
        elif self.type == "ts":
            self.profil_temperature()
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
        amplitude_list = self.amplitude(day)
        amplitude_array = np.array(amplitude_list)
        ln_rapport_amplitude = np.log( amplitude_array / amplitude_array[0] )
        return ln_rapport_amplitude

    # returns the list of pearson coefficients for the amplitudes along each day 
    def get_pearson_coef(self):
        n_dt_in_day = self.nb_per_day(verbose=False)
        n_days = self.nb_days_in_period()
        pearson_coef = np.zeros(n_days)
        for i in range(n_days):
            ln_amp_i = self.ln_amp(i*n_dt_in_day)
            Lr = sp.stats.linregress(self.depth_sensors, ln_amp_i)
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

    # Méthode pour tracer une mosaïque avec différentes valeurs de k
    # des graphes (pearson coefficient day by day)
    # Pour avoir une vue d'ensemble
    # list_k = liste de ces valeurs)
    def plot_mosaic_pearson(self, list_k):
        # To save the values of the attributes, so that the method doesn't change them
        T = self.multi_periodic
        k = self.layers_list[0].moinslog10K

        n_rows = len(list_k)//2 + len(list_k)%2
        fig, ax = plt.subplots(n_rows, ncols=2, constrained_layout = True)
        n_days = self.nb_days_in_period(self)
        X = np.arange(n_days)
        for i in range(n_rows):
            for j in range(2):
                if 2*i + j < len(list_k):
                    self.layers_list[0].moinslog10K = list_k[2*i+j]  # considering only one layer
                    self.multi_periodic = self.profil_temperature(self, verbose = False)
                    Y = self.get_pearson_coef(self)
                    ax[i][j].scatter(X, Y, color="r", marker="o", s=30)
                    ax[i][j].set_xlabel('day')
                    ax[i][j].set_ylabel('Pearson coefficient')
                    ax[i][j].set_title('Pearson par jour avec -log(k) = ' + str(list_k[2*i + j]), size = 10)   
                    ax[i][j].set_ylim(-1,1) 
        plt.show()

        self.multi_periodic = T
        self.layers_list[0].moinslog10K = k
    
    # Real data analysis methods

    #Function to convert the dates
    def convertDates(self, df: pd.DataFrame):
        """
        Convert dates from a list of strings by testing several different input formats
        Try all date formats already encountered in data points
        If none of them is OK, try the generic way (None)
        If the generic way doesn't work, this method fails
        (in that case, you should add the new format to the list)

        This function works directly on the giving Pandas dataframe (in place)
        This function assumes that the first column of the given Pandas dataframe
        contains the dates as characters string type

        For datetime conversion performance, see:
        See https://stackoverflow.com/questions/40881876/python-pandas-convert-datetime-to-timestamp-effectively-through-dt-accessor
        """
        formats = ("%m/%d/%y %H:%M:%S", "%m/%d/%y %I:%M:%S %p",
                   "%d/%m/%y %H:%M",    "%d/%m/%y %I:%M %p",
                   "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %I:%M:%S %p", 
                   "%d/%m/%Y %H:%M",    "%d/%m/%Y %I:%M %p",
                   "%y/%m/%d %H:%M:%S", "%y/%m/%d %I:%M:%S %p", 
                   "%y/%m/%d %H:%M",    "%y/%m/%d %I:%M %p",
                   "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %I:%M:%S %p", 
                   "%Y/%m/%d %H:%M",    "%Y/%m/%d %I:%M %p",
                   "%d-%m-%Y %H:%M",  "%m-%d-%Y %H:%M",

                   None)
        times = df[df.columns[0]]
        for f in formats:
            try:
                # Convert strings to datetime objects
                new_times = pd.to_datetime(times, format=f)
                # Convert datetime series to numpy array of integers (timestamps)
                new_ts = new_times.values.astype(np.int64)
                # If times are not ordered, this is not the appropriate format
                test = np.sort(new_ts) - new_ts
                if np.sum(abs(test)) != 0 :
                    #print("Order is not the same")
                    raise ValueError()
                # Else, the conversion is a success
                #print("Found format ", f)
                df[df.columns[0]] = new_times
                return

            except ValueError:
                #print("Format ", f, " not valid")
                continue
            
        # None of the known format are valid
        raise ValueError("Cannot convert dates: No known formats match your data!")


    #function to read and format the data
    def read_csv(self, point_number):
        root_path = os.getcwd()
        file_path = os.path.join(root_path, '..', '..', 'dataAnalysis', 'data_traite', 'point' + str(point_number) + '_temperature_traité.csv')
        df = pd.read_csv(file_path)
        df.columns = ['Date_heure', 'T_Sensor0', 'T_Sensor1', 'T_Sensor2', 'T_Sensor3']
        self.convertDates(df)
        return df

    def plot_data(point_number, verbose = True):
        url = 'dataAnalysis\data_traite\point' + str(point_number) + '_temperature_traité.csv'
        df = pd.read_csv(url)
        df.columns = ['Date_heure', 'T_Sensor0', 'T_Sensor1', 'T_Sensor2', 'T_Sensor3']
        df['Date_heure'] = pd.to_datetime(df['Date_heure'], dayfirst = True)

        # Tracer toutes les colonnes sauf 'Date_heure' en fonction de 'Date_heure'
        df.set_index('Date_heure').plot(figsize=(10, 6), grid=True, title="Graphique des valeurs en fonction des dates")
        plt.xlabel("Date")
        plt.ylabel("Température (°C)")
        plt.title("signal de température pour le capteur " + str(point_number))
        plt.show()

        

# testing
if __name__ == "__main__":
    mp_ts = time_series_multiperiodic("multi_periodic")

    timestamp = 1485714600
    date_0 = datetime.fromtimestamp(timestamp)
    step = timedelta(minutes=15)
    dates = [date_0 + i * step for i in range(4*24*30*6)]  # 6 months
    dates = np.array(dates)  # dates must be an array

    mp_ts.create_multiperiodic_signal(
        [10, 5, 3], [[1, "y"], [2, "m"], [21, "d"]], dates, verbose = True)