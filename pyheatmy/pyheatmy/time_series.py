from datetime import datetime, timedelta
from pyheatmy.params import Param, ParamsPriors, Prior, PARAM_LIST
from pyheatmy.checker import checker
from pyheatmy.core import Column
from pyheatmy.config import *
from pyheatmy.utils import create_periodic_signal, convert_to_timestamp, convert_list_to_timestamp


from scipy.interpolate import interp1d  # lagrange

import numpy as np
from numpy.random import normal
import matplotlib.pyplot as plt
import pandas as pd


class Time_series:  # on simule un tableau de mesures
    def __init__(
        self,
        offset: float = CODE_scalar,
        depth_sensors: list = DEFAULT_sensor_depth,
        param_time_dates: list = [
            None,
            None,
            DEFAULT_time_step,
        ],  # liste [date début, date fin, pas de temps (constant)], format des dates tuple datetime ou none
        param_dH_signal: list = DEFAULT_dH_signal,  # liste [t_début (s), t_fin (s), valeur (m)] pour un variation échelon pentu
        param_T_riv_signal: list = DEFAULT_T_riv_signal,  # liste [amplitude (°C), période (en seconde), offset (°C)] pour un variation sinusoïdale
        param_T_aq_signal: list = DEFAULT_T_aq_signal,  # liste [amplitude (°C), période (en seconde), offset (°C)] pour un variation sinusoïdale
        sigma_meas_P: float = None,  # (m) écart type de l'incertitude sur les valeurs de pression capteur
        sigma_meas_T: float = None,  # (°C) écart type de l'incertitude sur les valeurs de température capteur
    ):
                
        self._classType = ClassType.TIME_SERIES
        # on définit les attribut paramètres
        self._param_dates = param_time_dates
        self._param_dH = param_dH_signal
        self._param_T_riv = param_T_riv_signal
        self._param_T_aq = param_T_aq_signal
        self._sigma_P = sigma_meas_P
        self._sigma_T = sigma_meas_T
        print("Initializing time series")
        print("param_time_dates:", self._param_dates)
        print("param_dH_signal:", self._param_dH)
        print("param_T_riv_signal:", self._param_T_riv)
        print("param_T_aq_signal:", self._param_T_aq)
        print("sigma_meas_P:", self._sigma_P)
        print("sigma_meas_T:", self._sigma_T)

        self._depth_sensors = np.array(depth_sensors)
        self._real_z = np.array([0] + depth_sensors) + offset

        self._dates = np.array([None])
        self._time_array = np.array([None])
        # le tableau d'observation des charges utilisable dans colonne
        self._dH = np.array([None])
        self._dH_perturb = np.array([None])  # avec perturbation
        # récupère la liste de température observée de la rivière (au cours du temps)
        self._T_riv = np.array([None])
        self._T_riv_perturb = np.array([None])  # avec perturbation
        # le tableau d'observation de la pression et de la température rivière
        self._molonariP_data = None
        self._molonariP_data = None
        # récupère la liste de température observée de l'aquifère (au cours du temps)
        self._T_aq = np.array([None])
        self._T_aq_perturb = np.array([None])  # avec perturbation
        # le tableau d'observation des températures utilisable dans colonne
        self._T_Shaft = np.array([None])
        self._T_Shaft_perturb = np.array([None])  # avec perturbation

        self._T_Shaft_measures = None
        self._molonariT_data = None  # avec perturbation

    @classmethod
    def from_dict(cls, time_series_dict):
        return cls(**time_series_dict)

    def _generate_dates_series(self, n_len_times=2000, t_step=DEFAULT_time_step):#generate_dates_seemsOK
        if self._param_dates[0] == None:
            self._dates = np.array(
                [datetime.fromtimestamp(t_step * k) for k in range(n_len_times)]
            )
            self._time_array = np.array([t_step * k for k in range(n_len_times)])
        else:
            dt, end, step = (
                datetime(*self._param_dates[0]),
                datetime(*self._param_dates[1]),
                timedelta(seconds=self._param_dates[2]),
            )# dt is tini
            times_vir1 = []
            times_list = []
            S = 0
            while dt < end:
                times_vir1.append(dt)
                dt += step
                times_list.append(S)
                S += self._param_dates[2]
            self._dates = np.array(times_vir1)
            self._time_array = np.array(times_list)

        # self._dates = pd.to_datetime(self._dates)
        # print(f"initial dates : \n\t{self._dates}\n and time array : \n\t{self._time_array}")
        # data = self._dates
        # transformed_data = [(pd.Timestamp(dt), values) for dt, values in data]
        # self._dates = transformed_data
        # print(f"after conversion to timestamps dates : \n\t{self._dates}\n and time array : \n\t{self._time_array}")

    def _generate_dH_series(self,verbose=True):
        # if self._dates.any() == None:
        #     self._generate_dates_series()
        ts = create_periodic_signal(self._dates,self._param_dates[2],self._param_dH,"Hydraulic head differential",verbose=verbose)
        # self._dH = convert_list_to_timestamp(ts,self)
        self._dH = ts

    def _generate_Temp_riv_series(self,verbose=True):  # renvoie un signal sinusoïdal de temperature rivière
        # if self._dates.any() == None:
        #     self._generate_dates_series()
        ts = create_periodic_signal(self._dates,self._param_dates[2],self._param_T_riv,"T_riv",verbose=verbose)
        # self._T_riv = convert_list_to_timestamp(ts,self)
        self._T_riv = ts

    def _generate_Temp_aq_series(self,verbose=True):  # renvoie un signal sinusoïdal de temperature aquifère
        # if self._dates.any() == None:
        #     self._generate_dates_series()
        ts = create_periodic_signal(self._dates,self._param_dates[2],self._param_T_aq,"T_aq",verbose=verbose)
        # self._T_aq = [(pd.Timestamp(dt), values) for dt, values in ts]
        # self._T_aq = convert_list_to_timestamp(ts,self)
        self._T_aq = ts

    def _generate_Shaft_Temp_series(self,verbose=True):  # en argument n_sens_vir le nb de capteur (2 aux frontières et 3 inutiles à 0)
        # initialisation
        n_sens_vir = len(self._depth_sensors)
        if verbose:
            print(f"Generating Shaft with {n_sens_vir} sensors")
        if self._T_Shaft.any() == None:
            self._T_Shaft = np.ones((len(self._dates), n_sens_vir)) * CODE_Temp  # le tableau qui accueille des données de températures de forçage
            # self._T_Shaft[:, n_sens_vir - 1] = self._T_aq

            # Loop through each date and perform interpolation
            for i, date in enumerate(self._dates):
                f = interp1d(
                    [self._real_z[0], self._real_z[-1]], [self._T_riv[i], self._T_aq[i]]
                )
                self._T_Shaft[i, :] = f(self._depth_sensors)
        
            # Set the last column to _T_aq
            self._T_Shaft[:, n_sens_vir - 1] = self._T_aq
        #     self._T_Shaft[0] = f(self._depth_sensors)
        # # T_init*np.ones(n_sens_vir-1) # pour les conditions initiales au niveau des capteurs T1, T2, T3, ... avant Taq
        # # si T_shaft existe déjà (mais si maj) alors on maj seulement T_shaft_measure

        if verbose:
            print(f"{n_sens_vir} sensors in the shaft")
            for i in range(n_sens_vir):
                 print(f"Temperature of Sensor {i} : {self._T_Shaft[:,i]}")
        # self._T_Shaft_measures = list(zip(convert_to_timestamp(self._dates,self), self._T_Shaft))
        self._T_Shaft_measures = list(zip(self._dates, self._T_Shaft))



    def _perturbate(self,ts, sigma):#perturbates the time series with a normal distrib of sigma
        n_t=len(ts)
        new_ts=ts
        if sigma != None:
            new_ts=ts+normal(0,sigma,n_t)
        return new_ts
    
    @checker
    def _generate_perturb_Shaft_Temp_series(self):
        n_t = len(self._dates)
        n_sens_vir = len(self._depth_sensors)
        self._T_Shaft_perturb = np.zeros((n_t, n_sens_vir))
        for i in range(n_t):
            self._T_Shaft_perturb[i] = self._perturbate(self._T_Shaft[i], self._sigma_T)

            # self._molonariT_data = list(zip(convert_to_timestamp(self._dates,self), self._T_Shaft_perturb)) 
            self._molonariT_data = list(zip(self._dates, self._T_Shaft_perturb)) 
             #emulates what comes from a shaft of temperature sensors

    @checker
    def _generate_perturb_T_riv_dH_series(self):
        self._T_riv_perturb = self._perturbate(self._T_riv,self._sigma_T)
        self._dH_perturb = self._perturbate(self._dH ,self._sigma_P)
        self._molonariP_data = list(zip(self._dates, list(zip(self._dH_perturb, self._T_riv_perturb)))) #emulates what comes from a pressure sensor

        # self._molonariP_data = list(zip(convert_to_timestamp(self._dates,self), list(zip(self._dH_perturb, self._T_riv_perturb)))) #emulates what comes from a pressure sensor
    def _generate_all_series(self,verbose=True):
        if self._dates.any() == None:
            self._generate_dates_series()
        if self._dH.any() == None:
            self._generate_dH_series(verbose=verbose)
        if self._T_riv.any() == None:
            self._generate_Temp_riv_series(verbose=verbose)
        if self._T_aq.any() == None:
            self._generate_Temp_aq_series(verbose=verbose)
        if self._T_Shaft.any() == None:
            self._generate_Shaft_Temp_series(verbose=verbose)   

        #now generating perturbated measurments and emulating what comes from molonari devices
        self._generate_perturb_T_riv_dH_series()
        self._generate_perturb_Shaft_Temp_series()

    def _set_Shaft_Temp_series(self,temperatures,id_sensors,verbose=True):
        for i in range(len(id_sensors)+1):
            self._T_Shaft[:, i] = temperatures[i+1,:]
        #self._generate_Shaft_Temp_series()
        self._T_Shaft_measures = list(zip(self._dates, self._T_Shaft))


    def _plot_molonariT_data(self): 
        # Assuming self._molonariT_data is already populated
        # Extract dates and temperature data
        dates = [data[0] for data in self._molonariT_data]
        temperatures = np.array([data[1:] for data in self._molonariT_data])  # Extract all temperature series

        # Check if the dimensions match
        if len(dates) != temperatures.shape[0]:
            raise ValueError(f"Dates and temperatures must have the same length, but have shapes {len(dates)} and {temperatures.shape[0]}")

        nts=len(temperatures[:,])
        # Define a list of colors
        colors = plt.cm.viridis(np.linspace(0, 1, nts))

        # Plot each time series with a different color and label
        plt.figure(figsize=(10, 6))
        for i in range(nts):
            print(i)
            plt.plot(dates, temperatures[:, i], label=f'Shaft Sensor {i+1}', color=colors[i])

        # Formatting the plot
        plt.xlabel('Date')
        plt.ylabel('Temperature')
        plt.title('Temperature Perturbation Over Time')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)  # Rotate date labels for better readability

        # Show the plot
        plt.tight_layout()
        plt.show()


    def _measures_column_one_layer(self, column, layer_list, nb_cell,verbose=True):
        column.compute_solve_transi(layer_list, nb_cell,verbose=verbose)
        self._set_Shaft_Temp_series(column.get_temperature_at_sensors(verbose=verbose),column.get_id_sensors(),verbose=verbose)        
        self._generate_perturb_Shaft_Temp_series()

    @ _generate_perturb_Shaft_Temp_series.needed
    def _print_molonariDevice(self, column, type,verbose=True):


        if type == "molonariT":
            if verbose:
                print("MolonariT data")
                print(self._molonariT_data)
            self._plot_molonariT_data()
        elif type == "molonariP":
            if verbose:
                print("MolonariP data")
                print(self._molonariP_data)
        else:
            print("Type not recognized")





