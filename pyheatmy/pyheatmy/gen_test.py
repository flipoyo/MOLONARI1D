from datetime import datetime, timedelta
from pyheatmy.params import Param, ParamsPriors, Prior, PARAM_LIST
from pyheatmy.checker import checker
from pyheatmy.core import Column
from pyheatmy import (
    DEFAULT_dH,
    DEFAULT_T_riv,
    DEFAULT_T_aq,
    DEFAULT_time_step,
    CODE_Temp,
    CODE_list_sensors,
    CODE_scalar,
)
from scipy.interpolate import interp1d  # lagrange

import numpy as np
from numpy.random import normal


class Time_series:  # on simule un tableau de mesures
    def __init__(
        self,
        offset: float = CODE_scalar,
        depth_sensors: list = CODE_list_sensors,
        param_time_dates: list = [
            None,
            None,
            DEFAULT_time_step,
        ],  # liste [date début, date fin, pas de temps (constant)], format des dates tuple datetime ou none
        param_dH_signal: list = DEFAULT_dH,  # liste [t_début (s), t_fin (s), valeur (m)] pour un variation échelon pentu
        param_T_riv_signal: list = DEFAULT_T_riv,  # liste [amplitude (°C), période (en seconde), offset (°C)] pour un variation sinusoïdale
        param_T_aq_signal: list = DEFAULT_T_aq,  # liste [amplitude (°C), période (en seconde), offset (°C)] pour un variation sinusoïdale
        sigma_meas_P: float = None,  # (m) écart type de l'incertitude sur les valeurs de pression capteur
        sigma_meas_T: float = None,  # (°C) écart type de l'incertitude sur les valeurs de température capteur
    ):
        # on définit les attribut paramètres
        self._param_dates = param_time_dates
        self._param_dH = param_dH_signal
        self._param_T_riv = param_T_riv_signal
        self._param_T_aq = param_T_aq_signal
        self._sigma_P = sigma_meas_P
        self._sigma_T = sigma_meas_T
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
        self._T_riv_dH_measures = None
        self._T_riv_dH_measures_perturb = None
        # récupère la liste de température observée de l'aquifère (au cours du temps)
        self._T_aq = np.array([None])
        self._T_aq_perturb = np.array([None])  # avec perturbation
        # le tableau d'observation des températures utilisable dans colonne
        self._T_Shaft = np.array([None])
        self._T_Shaft_perturb = np.array([None])  # avec perturbation

        self._T_Shaft_measures = None
        self._T_Shaft_perturb_measures = None  # avec perturbation

    @classmethod
    def from_dict(cls, time_series_dict):
        return cls(**time_series_dict)

    def _generate_dates_series(self, n_len_times=2000, t_step=DEFAULT_time_step):
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
            )
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

    def _generate_dH_series(self):
        t_range = np.arange(len(self._dates)) * self._param_dates[2]
        coeff = 2 * self._param_dH[2] / (self._param_dH[1] - self._param_dH[0])
        deb = self._param_dH[0] * len(t_range) / t_range[-1]
        end = self._param_dH[1] * len(t_range) / t_range[-1]
        self._dH = np.zeros(len(t_range))
        self._dH[: int(deb)] = -self._param_dH[2]
        self._dH[int(deb) : int(end)] = (
            coeff * (t_range[int(deb) : int(end)] - self._param_dH[0])
            - self._param_dH[2]
        )
        self._dH[int(end) :] = self._param_dH[2]
        # self._dH = self._param_dH[0]*np.sin(2*np.pi*t_range/self._param_dH[1]) + self._param_dH[2]

    def _generate_Temp_riv_series(
        self,
    ):  # renvoie un signal sinusoïdal de temperature rivière
        if self._dates.any() == None:
            self._generate_dates_series()

        t_range = np.arange(len(self._dates)) * self._param_dates[2]
        self._T_riv = (
            self._param_T_riv[0] * np.sin(2 * np.pi * t_range / self._param_T_riv[1])
            + self._param_T_riv[2]
        )

    def _generate_Temp_aq_series(
        self,
    ):  # renvoie un signal sinusoïdal de temperature aquifère
        if self._dates.any() == None:
            self._generate_dates_series()

        t_range = np.arange(len(self._dates)) * self._param_dates[2]
        self._T_aq = (
            self._param_T_aq[0] * np.sin(2 * np.pi * t_range / self._param_T_aq[1])
            + self._param_T_aq[2]
        )

    def _generate_T_riv_dH_series(
        self,
    ):  # renvoie un signal sinusoïdal de différence de charge
        if self._dates.any() == None:
            self._generate_dates_series()

        if self._dH.any() == None:
            self._generate_dH_series()

        if self._T_riv.any() == None:
            self._generate_Temp_riv_series()

        self._T_riv_dH_measures = list(
            zip(self._dates, list(zip(self._dH, self._T_riv)))
        )

    def _generate_Shaft_Temp_series(
        self,
    ):  # en argument n_sens_vir le nb de capteur (2 aux frontières et 3 inutiles à 0)
        # initialisation
        n_sens_vir = len(self._depth_sensors)
        if self._dates.any() == None:
            self._generate_dates_series()

        if self._T_aq.any() == None:
            self._generate_Temp_aq_series()

        if self._T_Shaft.any() == None:
            self._T_Shaft = (
                np.ones((len(self._dates), n_sens_vir)) * CODE_Temp
            )  # le tableau qui accueille des données de températures de forçage
            self._T_Shaft[:, n_sens_vir - 1] = self._T_aq

            f = interp1d(
                [self._real_z[0], self._real_z[-1]], [self._T_riv[0], self._T_aq[0]]
            )
            self._T_Shaft[0] = f(self._depth_sensors)
        # T_init*np.ones(n_sens_vir-1) # pour les conditions initiales au niveau des capteurs T1, T2, T3, ... avant Taq
        # si T_shaft existe déjà (mais si maj) alors on maj seulement T_shaft_measure
        self._T_Shaft_measures = list(zip(self._dates, self._T_Shaft))

    def _generate_perturb_Shaft_Temp_series(self):
        n_sens_vir = len(self._depth_sensors)
        if self._dates.any() == None:
            self._generate_dates_series()
        n_t = len(self._dates)

        if self._T_Shaft.any() == None:
            self._generate_Shaft_Temp_series()

        self._T_Shaft_perturb = np.zeros((n_t, n_sens_vir))
        self._T_Shaft_perturb = self._T_Shaft + normal(
            0, self._sigma_T, (n_t, n_sens_vir)
        )  # perturbe toutes les températures
        self._T_Shaft_perturb_measures = list(
            zip(self._dates, self._T_Shaft_perturb)
        )  # peut renvoyer un format T_measure pour un objet colonne

    def _generate_perturb_T_riv_dH_series(self):
        if self._dates.any() == None:
            self._generate_dates_series()
        n_t = len(self._dates)

        if self._T_riv.any() == None or self._dH.any() == None:
            self._generate_T_riv_dH_series()
        # perturbation des données générées
        self._T_riv_perturb = self._T_riv + normal(0, self._sigma_T, n_t)
        self._dH_perturb = self._dH + normal(0, self._sigma_P, n_t)

        self._T_riv_dH_measures_perturb = list(
            zip(self._dates, list(zip(self._dH_perturb, self._T_riv_perturb)))
        )

    def _measures_column_one_layer(self, column, layer_list, nb_cell):
        column.compute_solve_transi(layer_list, nb_cell)
        id_sensors = column.get_id_sensors()
        for i in range(len(id_sensors)):
            self._T_Shaft[1:, i] = column._temps[
                id_sensors[i], 1:
            ]  # maj les températures émulée des capteurs à partir de t>0 (ie t=1)
            if i < len(id_sensors):
                column._T_measures[:, i] = column._temps[id_sensors[i], :]
        self._generate_Shaft_Temp_series()
