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
        
    def create_entry_signal(self, dates):
        if self.entry_signal_type == 'linear' :
            T = np.zeros(dates.shape[0])
            T += self.T_riv_offset
            linear_increase = np.array([i * self.T_riv_day_amp / self.nb_per_day(verbose = False) for i in range(dates.shape[0])])
            T += linear_increase
            self.entry_signal = [dates, T]

    def plot_temp(self, all_depths = False):
        
        if self.type == "multi_periodic":
            dates = self.multi_periodic[0]
            if all_depths :
                T = self.matrix
            else:
                T = self.multi_periodic[1]
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
        plt.gcf().autofmt_xdate()
        plt.ylabel("temperature : °C")
        plt.show()

    def nb_per_day(self, verbose = True): #method to get the number of points per day
        if verbose:
            print('dt must be in seconds')
        return(int(NSECINDAY/(15*60)))  # return(int(NSECINDAY/self.dt)) but self.dt undefined
    
    def nb_days_in_period(self): #method to get the number of days in the period
        if self.type == "multi_periodic":
            return int(self.multi_periodic[0].shape[0]/self.nb_per_day(verbose = False))
        elif self.type == "ts":
            return int(self.time_series[0].shape[0]/self.nb_per_day(verbose = False))

    # if create river signal = True, then the multi periodic signal is auto generated
    def create_profil_temperature(self, verbose = True, create_signal = True, nb_layers = 1):
        if self.type == "ts":
            self.matrix = self.time_series[1]
        
        elif self.type == 'multi_periodic':
            # On regarde des variations de température sur une année, on définit une période journalière, et une période annuelle

            """Reprise du code de dmo_genData pour créer un objet synthetic_MOLONARI"""

            # modèle une couche
            if nb_layers == 1:
                self.layers_list = layersListCreator([(self.name, self.river_bed, self.moinslog10IntrinK, self.n, self.lambda_s, self.rhos_cs)])
            if nb_layers == 2:
                self.layers_list = layersListCreator([(self.name, self.river_bed, self.moinslog10IntrinK, self.n, self.lambda_s, self.rhos_cs), 
                                            (self.name2, self.river_bed2, self.moinslog10IntrinK2, self.n2, self.lambda_s2, self.rhos_cs2)])

            # un dictionnaire qui facilite le paramétrage avec des variables globales définies plus haut
            time_series_dict_user1 = {
                "offset":.0,
                "depth_sensors":self.depth_sensors,
            	"param_time_dates": [self.t_debut, self.t_fin, self.dt], 
                "param_dH_signal": [self.dH_amp, self.P_dh, self.dH_offset], #En vrai y aura une 4e valeur ici mais ca prendra en charge pareil
            	"param_T_riv_signal": [self.T_riv_day_amp, self.P_T_riv_day, self.T_riv_offset],
                "param_T_aq_signal": [self.T_aq_amp, self.P_T_aq, self.T_aq_offset],
                "sigma_meas_P": self.sigma_meas_P,
                "sigma_meas_T": self.sigma_meas_T, #float
                "verbose": False
            }

            self.time_series_dict_user1 = time_series_dict_user1

            #on génère un objet colonne à partir de l'objet emu_observ_test_user1
            emu_observ_test_user1 = synthetic_MOLONARI.from_dict(time_series_dict_user1)

            if create_signal:
                #On utilise le jeu de date précédent pour créer un signal de température multipériodique 
                self.create_multiperiodic_signal([self.T_riv_year_amp, self.T_riv_day_amp], [[self.P_T_riv_year, 's'], [self.P_T_riv_day, 's']], emu_observ_test_user1._dates,
                                                   offset=self.T_riv_offset, verbose = False)
            # or any signal
            else:
                self.create_entry_signal(np.array(emu_observ_test_user1._dates))
                self.multi_periodic = self.entry_signal


            #On force la variable T_riv dans l'objet emu_observ_test_user1
            emu_observ_test_user1._T_riv = self.multi_periodic[1]

            #Puis on applique les méthodes _generate_Shaft_Temp_series et _generate_perturb_Shaft_Temp_series pour changer les valeurs dépendante du nouveau T_riv
            emu_observ_test_user1._generate_Shaft_Temp_series(verbose = False)
            emu_observ_test_user1._generate_perturb_Shaft_Temp_series()
            emu_observ_test_user1._generate_perturb_T_riv_dH_series()

            col_dict = {
            	"river_bed": self.river_bed, 
                "depth_sensors": list(self.depth_sensors), #En vrai y aura une 4e valeur ici mais ca prendra en charge pareil
            	"offset": .0,
                "dH_measures": emu_observ_test_user1._molonariP_data,
                "T_measures": emu_observ_test_user1._molonariT_data,
                "sigma_meas_P": self.sigma_meas_P,
                "sigma_meas_T": self.sigma_meas_T,
            }
            self.col_dict = col_dict

            column = Column.from_dict(self.col_dict,verbose=False)

            print(self.layers_list)

            column._compute_solve_transi_multiple_layers(self.layers_list, self.nb_cells, verbose=False)

            self.matrix = np.transpose(column._temperatures)

            if verbose:
                print(f"Layers list: {self.layers_list}")
                #On vérifie que les températures ont bien été modifiées dans l'objet column (en particulier que la température à profondeur nulle est bien celle de la rivière)
                plt.plot(emu_observ_test_user1._dates, self.matrix)
                plt.show()
                print(f"La matrice de température a pour shape : {column._temperatures.shape}, abscisse = température aux 20 cellules, ordonnée = température à chaque pas de temps")


    def amplitude(self, day):
        amplitude_list = []
        n_dt_in_day = self.nb_per_day(verbose=False)
        if self.type == "multi_periodic":
            T = self.matrix
        elif self.type == "ts":
            self.create_profil_temperature()
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
    
    # Renvoie l'instance de régression linéaire des données (profondeur, ln(rapport amplitudes))
    def linear_regression(self, day, sensors_only = False):
        ln_amp_i = self.ln_amp(day)
        if sensors_only :
            depth_cells = self.depth_sensors
            ln_amp_i = [ln_amp_i[j] for j in self.depth_sensors_index_list]
        else :
            # It's a model so we should reject the last values (close to the aquifere)
            depth_cells = self.depth_cells[:self.last_cell]
            ln_amp_i = ln_amp_i[:self.last_cell]
            
        return sp.stats.linregress(depth_cells, ln_amp_i)

    # Trace l'interpolation linéaire en imprimant le coefficient d'exactitude
    def plot_linear_regression(self, day, sensors_only = False, create_signal = True, nb_layers = 1):
        # assert len(T) == len(depths), "a temperature measure must be assigned to a single depth"
        # créer l'objet matrix
        self.create_profil_temperature(verbose = False, create_signal=create_signal, nb_layers = nb_layers)
        Y = self.ln_amp(day)
        if sensors_only :
            X = np.array(self.depth_sensors).reshape(-1,1)
            Y = [Y[j] for j in self.depth_sensors_index_list]  # selecting only depth_sensors values. !!Note!! : river_bed / nb_cells must be a divisor of 0.1
            Lr = self.linear_regression(day, sensors_only = True)
        else :
            depths_cell = self.depth_cells[:self.last_cell]
            X = np.array(depths_cell).reshape(-1,1)
            Y = Y[:self.last_cell]
            Lr = self.linear_regression(day, sensors_only = False)
        Pearson_coefficient = Lr.rvalue
        slope = Lr.slope
        intercept = Lr.intercept
        plt.scatter(X, Y, color="r", marker="o", s=10)
        y_pred = slope * X + intercept
        plt.plot(X, y_pred, color="k")
        plt.xlabel("profondeur (unit)")
        plt.ylabel("ln(A_z / A_0)")
        plt.title("Régression linéaire sur le rapport des logarithmes des amplitudes")
        plt.figtext(.6, .8, "y = " + str(round(slope,2)) + "x + " + str(round(intercept,2)))
        plt.figtext(.6, .7, "Pearson coefficient : " + str(round(Pearson_coefficient,2)))
        plt.show()

    # returns the list of pearson coefficients for the amplitudes along each day 
    def get_pearson_coef(self, sensors_only = False):
        n_dt_in_day = self.nb_per_day(verbose=False)
        n_days = self.nb_days_in_period()
        pearson_coef = np.zeros(n_days)
        for i in range(n_days):
            Lr = self.linear_regression(i*n_dt_in_day, sensors_only = sensors_only)
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

    # Méthode pour tracer une mosaïque avec différentes valeurs de k (en -log(k))
    # des graphes (pearson coefficient day by day)
    # Pour avoir une vue d'ensemble
    # list_k = liste de ces valeurs)
    def plot_mosaic_pearson(self, list_k, sensors_only = False, create_signal = True, nb_layers = 1):
        # To save the values of the attributes, so that the method doesn't change them
        T = self.multi_periodic
        k = self.moinslog10IntrinK
        matrix = self.matrix

        n_rows = len(list_k)//2 + len(list_k)%2
        fig, ax = plt.subplots(n_rows, ncols=2, constrained_layout = True)
        n_days = self.nb_days_in_period()
        X = np.arange(n_days)
        for i in range(n_rows):
            for j in range(2):
                if 2*i + j < len(list_k):
                    # print(self.layers_list[0].params)
                    self.moinslog10IntrinK = list_k[2*i + j]
                    self.create_profil_temperature(verbose = False, create_signal = create_signal, nb_layers = nb_layers)
                    Y = self.get_pearson_coef(sensors_only = sensors_only)
                    ax[i][j].scatter(X, Y, color="r", marker="o", s=30)
                    ax[i][j].set_xlabel('day')
                    ax[i][j].set_ylabel('Pearson')
                    ax[i][j].set_title('Pearson par jour avec -log(k) = ' + str(list_k[2*i + j]), size = 10)   
                    ax[i][j].set_ylim(-1,1) 
        plt.show()

        self.multi_periodic = T
        self.moinslog10IntrinK = k
        self.matrix = matrix
    
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