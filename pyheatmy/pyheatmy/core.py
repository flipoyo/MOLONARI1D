import traceback
from typing import List, Sequence, Union
from random import random, choice
from operator import attrgetter
from numbers import Number
from datetime import datetime
import sys
import psutil
import types

import numpy as np
import copy
import matplotlib.pyplot as plt
from tqdm import trange
from scipy.interpolate import interp1d
from matplotlib.colors import LinearSegmentedColormap

from pyheatmy.lagrange import Lagrange
from pyheatmy.params import Param, Prior, PARAM_LIST, calc_K
from pyheatmy.state import State
from pyheatmy.checker import checker
from pyheatmy.config import *
from pyheatmy.linear_system import *

from pyheatmy.utils import *
from pyheatmy.layers import Layer, getListParameters


# Column is a monolithic class and pyheatmy is executable from there. Calculation, retrieval and plots are methods from the column class
class Column:  # colonne de sédiments verticale entre le lit de la rivière et l'aquifère
    def __init__(
        self,
        river_bed: float,  # profondeur de la colonne en mètres
        # profondeur des capteurs de températures en mètres
        depth_sensors: Sequence[float],
        offset: float,  # correspond au décalage du capteur de température par rapport au lit de la rivière
        # liste contenant un tuple avec la date, la charge et la température au sommet de la colonne
        dH_measures: list,
        T_measures: list,  # liste contenant un tuple avec la date et la température aux points de mesure de longueur le nombre de temps mesuré
        sigma_meas_P: float = None,  # écart type de l'incertitude sur les valeurs de pression capteur
        sigma_meas_T: float = None,  # écart type de l'incertitude sur les valeurs de température capteur
        all_layers: list[Layer] = [],  # liste des couches de la colonne
        inter_mode: str = "linear",  # mode d'interpolation du profil de température initial : 'lagrange' ou 'linear'
        eps=EPSILON,
        nb_cells=NB_CELLS,
        rac="~/OUTPUT_MOLONARI1D/generated_data",  # printing directory by default,
        verbose=False,
    ):
        self._dir_print = create_dir(
            rac, verbose=verbose
        )  # once validated verbose=False

        self._classType = ClassType.COLUMN

        # ! Pour l'instant on suppose que les temps matchent
        self._times = [t for t, _ in dH_measures]
        # récupère la liste des charges de la riviière (au cours du temps)
        self._dH = np.array([d for _, (d, _) in dH_measures])
        # récupère la liste de température de la rivière (au cours du temps)
        self._T_riv = np.array([t for _, (_, t) in dH_measures])
        # récupère la liste de température de l'aquifère (au cours du temps)
        self._T_aq = np.array([t[-1] for _, t in T_measures])
        # récupère la liste de températures des capteurs (au cours du temps)
        self._T_measures = np.array([t[:-1] for _, t in T_measures])

        # décale d'un offset les positions des capteurs de température (aussi riviere)
        self._real_z = np.array([0] + depth_sensors) + offset
        # enlève l'offset sur la mesure de température rivière car cette mesure est prise dans le capteur pression
        self._real_z[0] -= offset

        self.depth_sensors = depth_sensors
        self.offset = offset

        self.zbed = river_bed  # profondeur du lit de la rivière

        self.set_layers(all_layers)  # liste des couches de la colonne

        self._z_solve = (
            None  # le tableau contenant la profondeur du milieu des cellules
        )
        self._id_sensors = None
        # le tableau contenant les températures à tout temps et à toute profondeur (lignes : températures) (colonnes : temps)
        self._temperatures = None

        # le tableau contenant les charges à tout temps et à toute profondeur (lignes : charges) (colonnes : temps)
        self._H_res = None
        # le tableau contenant le débit spécifique à tout temps et à toute profondeur (lignes : débit) (colonnes : temps)
        self._flows = None
        # le tableau contenant le flux advectif latéral (pseudo2D) à tout temps et à toute profondeur (lignes : flux) (colonnes : temps)
        self._lateral_advec_heat_flux = None

        # liste contenant des objets de classe état et de longueur le nombre d'états acceptés par la MCMC (<=nb_iter), passe à un moment par une longueur de 1000 pendant l'initialisation de MCMC
        self._states = list()
        self._acceptances = None
        # dictionnaire indexé par les quantiles (0.05,0.5,0.95) à qui on a associe un array de deux dimensions : dimension 1 les profondeurs, dimension 2 : liste des valeurs de températures associées au quantile, de longueur les temps de mesure
        self._quantiles_temperatures = None
        # dictionnaire indexé par les quantiles (0.05,0.5,0.95) à qui on a associe un array de deux dimensions : dimension 1 les profondeurs, dimension 2 : liste des valeurs de débits spécifiques associés au quantile, de longueur les temps de mesure
        self._quantiles_flows = None
        self.lagr = Lagrange(
            np.array(self._real_z),
            np.array([self._T_riv[0], *self._T_measures[0], self._T_aq[0]]),
        )  # crée le polynome interpolateur de lagrange faisant coincider les températures connues à la profondeur réelle
        self.linear = interp1d(
            self._real_z, [self._T_riv[0], *self._T_measures[0], self._T_aq[0]]
        )
        # crée la fonction affine par morceaux faisant coincider les températures connues à la profondeur réelle
        self.inter_mode = inter_mode
        self.eps = eps
        self.tests()  # teste que les conditions nécessaires à l'analyse sont remplies
        if verbose:
            print("Column created with success")
            print(f"Number of time steps: {self.get_timelength()}")
            print(f"Time step in days: {self.get_dt_in_days()}")
            print(f"T_riv: {self._T_riv}")
            print(f"T_aq: {self._T_aq}")
            print(f"dH : {self._dH}")
            print(f"list of dates   : {self._times}")
        self.initialization(nb_cells)

    def set_layers(
        self, layer: Union[Layer, List[Layer]]
    ):  # instancie une couche ou une liste de couches à la colonne, en s'assurant de bien ordonner les couches
        self.all_layers = []  # On vide la liste des couches avant d'en ajouter de nouvelles
        if isinstance(layer, Layer):
            self.all_layers.append(layer)
        elif isinstance(layer, list) and all(isinstance(l, Layer) for l in layer):
            self.all_layers.extend(layer)
        else:
            raise ValueError(
                "You must provide a Layer object or a list of Layer objects."
            )

        self.all_layers = sorted(
            self.all_layers, key=lambda x: x.zLow
        )  # we're sorting the layerlist by increasing zLow

    def initialization(self, nb_cells):
        self._nb_cells = nb_cells
        self.initialize_q_s_list()

    def initialization_nb_cells(self, nb_cells):
        self._nb_cells = nb_cells

    def initialize_q_s_list(self):
        # Initialisation d'une matrice vide pour stocker les sources de chaleur si nécessaire en post-traitement
        self._q_s_list = np.zeros((self._nb_cells, len(self._times)))

    def tests(self):
        # teste que les données sont aux bons formats
        if np.shape(self._dH) != np.shape(self._T_aq) or (
            np.shape(self._dH) != np.shape(self._T_riv)
            # or (np.shape(self._T_measures[1]) != (3,))
        ):
            raise NameError("Problème dans la taille des donées")

        # teste qu'il ne manque pas de données pour les conditions aux limites
        if np.isnan(np.sum(self._T_aq)):
            raise NameError("Donnée(s) manquante(s) pour la température aquifère")

        if np.isnan(np.sum(self._T_riv)):
            raise NameError("Donnée(s) manquante(s) pour la température rivière")

        if np.isnan(np.sum(self._dH)):
            raise NameError("Donnée(s) manquante(s) pour la pression")

    @classmethod
    def from_dict(cls, col_dict, verbose=False):
        """
        Class method to create an instance of Column from a dictionnary.
        """
        return cls(**col_dict, verbose=verbose)

    ##########################################################################################"
    #
    #   Time management of the simulation
    #
    # #######################################################################################"

    def get_timelength(self):
        return len(self._times)

    def get_dt(self):
        nt = self.get_timelength()
        # print(f"number of time steps =  {nt}")
        dt = (self._times[-1] - self._times[0]).total_seconds()
        dt /= nt
        # print(f"time step in seconds =  {dt}")
        return dt

    def get_dt_in_days(self):
        dt = self.get_dt()
        return dt / NSECINDAY

    def create_time_in_day(self):
        nd = self.get_dt_in_days()
        return np.array([i * nd for i in range(self.get_timelength())])

    ##########################################################################################"
    #
    #   Computation function
    #
    # #######################################################################################"

    @checker
    def compute_solve_transi(self, verbose=True):
        try:
            layersList = self.all_layers
            nb_cells = self._nb_cells

            if len(layersList) == 1:
                layer = layersList[0]  # Cas homogène
                dz = self._real_z[-1] / nb_cells
                self._z_solve = dz / 2 + np.array([k * dz for k in range(nb_cells)])
                self._id_sensors = [
                    np.argmin(np.abs(z - self._z_solve)) for z in self._real_z[1:-1]
                ]

                all_dt = np.array(
                    [
                        (self._times[j + 1] - self._times[j]).total_seconds()
                        for j in range(len(self._times) - 1)
                    ]
                )
                isdtconstant = np.all(all_dt == all_dt[0])

                H_init = self._dH[0] - self._dH[0] * self._z_solve / self._real_z[-1]
                H_aq = np.zeros(len(self._times))
                H_riv = self._dH

                if self.inter_mode == "lagrange":
                    T_init = np.array([self.lagr(z) for z in self._z_solve])
                elif self.inter_mode == "linear":
                    T_init = self.linear(self._z_solve)

                T_riv = self._T_riv
                T_aq = self._T_aq

                
                IntrinK, n, lambda_s, rhos_cs, q_s = layer.get_physical_params()
               
                if verbose:
                    print(
                        "--- Compute Solve Transi ---",
                        f"One layer : IntrinK = {IntrinK}, n = {n}, lambda_s = {lambda_s}, rhos_cs = {rhos_cs}, q_s = {q_s}",
                        sep="\n",
                    )

                heigth = abs(self._real_z[-1] - self._real_z[0])
                Ss = n / heigth

                
                array_IntrinK = np.array([IntrinK, IntrinK])
                array_K = (RHO_W * G * array_IntrinK) * 1.0 / MU
               
                array_q_s = np.array([q_s, q_s])
                array_Ss = np.array([Ss, Ss])
                list_zLow = np.array([0.2])
                inter_cara = np.array([[nb_cells // 2, 0]])
                z_solve = self._z_solve.copy()
               
                
                IntrinK_list, n_list, lambda_s_list, rhos_cs_list, q_s_list = (
                    getListParameters(layersList, nb_cells)
                )
                Ss_list = n_list / heigth

                H_strat = H_stratified(
                    Ss_list,
                    IntrinK_list, 
                    n_list,
                    lambda_s_list,
                    rhos_cs_list,
                    all_dt,
                    q_s_list, 
                    dz,
                    H_init,
                    H_riv,
                    H_aq,
                    T_init,
                    array_K,
                    array_Ss,
                    list_zLow,
                    z_solve,
                    inter_cara,
                    isdtconstant,
                    alpha=ALPHA,
                )
                H_res = H_strat.compute_H_stratified()

                nablaH = H_strat.nablaH()

                T_strat = T_stratified(
                    nablaH,
                    Ss_list,
                    IntrinK_list, 
                    n_list,
                    lambda_s_list,
                    rhos_cs_list,
                    all_dt,
                    q_s_list, 
                    dz,
                    H_init,
                    H_riv,
                    H_aq,
                    T_init,
                    T_riv,
                    T_aq,
                    alpha=ALPHA,
                    N_update_Mu=N_UPDATE_MU,
                )
                T_res = T_strat.compute_T_stratified()

                
                if hasattr(T_strat, "source_heat_flux"):
                    self._lateral_advec_heat_flux = T_strat.source_heat_flux * dz

                self._temperatures = T_res
                self._H_res = H_res

                K = calc_K(IntrinK) 
               
                if verbose:
                    print(
                        f"Solving the flow with intrinsec permeability {IntrinK}, and permeability {K}"
                    )
                self._flows = -K * nablaH

                if verbose:
                    print("Done.")

            else:  # Case multiple layers
                dz = self._real_z[-1] / nb_cells
                self._z_solve = dz / 2 + np.array([k * dz for k in range(nb_cells)])

                self._id_sensors = [
                    np.argmin(np.abs(z - self._z_solve)) for z in self._real_z[1:-1]
                ]

                all_dt = np.array(
                    [
                        (self._times[j + 1] - self._times[j]).total_seconds()
                        for j in range(len(self._times) - 1)
                    ]
                )
                isdtconstant = np.all(all_dt == all_dt[0])

                H_init = (
                    self._dH[0] - self._dH[0] * self._z_solve / self._real_z[-1]
                )
                H_aq = np.zeros(len(self._times))
                H_riv = self._dH

                if self.inter_mode == "lagrange":
                    T_init = np.array([self.lagr(z) for z in self._z_solve])
                elif self.inter_mode == "linear":
                    T_init = self.linear(self._z_solve)

                T_riv = self._T_riv
                T_aq = self._T_aq

               
                IntrinK_list, n_list, lambda_s_list, rhos_cs_list, q_s_list = (
                    getListParameters(layersList, nb_cells)
                )

                array_IntrinK = np.array(
                    [float(layer.get_physical_params().IntrinK) for layer in self.all_layers]
                )
                
                array_k = array_IntrinK
                array_K = calc_K(array_k)
               
                heigth = abs(self._real_z[-1] - self._real_z[0])
                array_Ss = (
                    np.array([float(x.get_physical_params().n) for x in layersList])
                    / heigth
                )
               
                # Calculs pour H_stratified (array_eps, array_Hinter, etc.)
                array_eps = np.zeros(len(layersList))
                array_eps[0] = layersList[0].zLow

                for idx in range(1, len(layersList)):
                    array_eps[idx] = layersList[idx].zLow - layersList[idx - 1].zLow
                array_Hinter = np.zeros(len(layersList) + 1)
                array_Hinter[0] = self._dH[0]
                array_Hinter[-1] = 0.0
                N = len(array_Hinter) - 1
               
                # calculate Hinter
                H_gauche = np.zeros((N - 1, N - 1))
                H_droite = np.zeros((N - 1, N - 1))
                scalar_gauche = np.zeros(N - 1)
                scalar_droite = np.zeros(N - 1)
                scalar_gauche[0] = array_K[0] * array_Hinter[0] / array_eps[0]
                scalar_droite[-1] = -array_K[-1] * array_Hinter[-1] / array_eps[-1]
                H_gauche[0, 0] = -array_K[0] / array_eps[0]
                for diag in range(1, N - 1):
                    H_gauche[diag, diag - 1] = array_K[diag] / array_eps[diag]
                    H_gauche[diag, diag] = -array_K[diag] / array_eps[diag]

                H_droite[N - 2, N - 2] = array_K[-1] / array_eps[-1]
                for diag in range(0, N - 2):
                    H_droite[diag, diag + 1] = -array_K[diag + 1] / array_eps[diag + 1]
                    H_droite[diag, diag] = array_K[diag + 1] / array_eps[diag + 1]

                Matrix_b = scalar_gauche - scalar_droite
                Matrix_A = H_droite - H_gauche
                H_sol = np.linalg.solve(Matrix_A, Matrix_b)
                for idx in range(len(H_sol)):
                    array_Hinter[idx + 1] = H_sol[idx]

                list_array_L = []
                cnt = 0
                for idx in range(len(layersList) - 1):
                    cnt_start = cnt
                    while cnt < len(self._z_solve):
                        if (
                            self._z_solve[cnt] <= layersList[idx].zLow
                            and self._z_solve[cnt + 1] > layersList[idx].zLow
                        ):
                            list_array_L.append(self._z_solve[cnt_start : cnt + 1])
                            cnt += 1
                            break
                        else:
                            cnt += 1
                list_array_L.append(self._z_solve[cnt:])

                list_array_H = []
                for idx in range(len(list_array_L)):
                    if idx > 0:
                        list_array_H.append(
                            array_Hinter[idx]
                            - (array_Hinter[idx] - array_Hinter[idx + 1])
                            / array_eps[idx]
                            * (list_array_L[idx] - layersList[idx - 1].zLow)
                        )
                    else:
                        list_array_H.append(
                            array_Hinter[idx]
                            - (array_Hinter[idx] - array_Hinter[idx + 1])
                            / array_eps[idx]
                            * (list_array_L[idx] - 0)
                        )
                H_init = list_array_H[0]
                for idx in range(1, len(list_array_H)):
                    H_init = np.concatenate((H_init, list_array_H[idx]))

                Ss_list = n_list / heigth

                list_zLow = []
                for layer in layersList:
                    list_zLow.append(layer.zLow)
                list_zLow.pop()
                list_zLow = np.array(list_zLow)
                z_solve = self._z_solve.copy()

                inter_cara = np.zeros((len(list_zLow), 2))
                for zlow_idx in range(len(list_zLow)):
                    for z_idx in range(len(z_solve) - 1):
                        if (
                            z_solve[z_idx] <= list_zLow[zlow_idx]
                            and z_solve[z_idx + 1] > list_zLow[zlow_idx]
                        ):
                            if abs(z_solve[z_idx] - list_zLow[zlow_idx]) < EPSILON:
                                inter_cara[zlow_idx, 0] = z_idx
                            elif abs(z_solve[z_idx + 1] - list_zLow[zlow_idx]) < EPSILON:
                                inter_cara[zlow_idx, 0] = z_idx + 1
                            else:
                                inter_cara[zlow_idx, 0] = z_idx
                                inter_cara[zlow_idx, 1] = z_idx + 1

                H_strat = H_stratified(
                    Ss_list,
                    IntrinK_list, 
                    n_list,
                    lambda_s_list,
                    rhos_cs_list,
                    all_dt,
                    q_s_list, 
                    dz,
                    H_init,
                    H_riv,
                    H_aq,
                    T_init,
                    array_K,
                    array_Ss,
                    list_zLow,
                    z_solve,
                    inter_cara,
                    isdtconstant,
                    alpha=ALPHA,
                )
                H_res = H_strat.compute_H_stratified()
                self._H_res = H_res

                
                K_list = calc_K(IntrinK_list)
                nablaH = H_strat.nablaH()
                flows = np.zeros((nb_cells, len(self._times)), np.float32)

                for i in range(nb_cells):
                    flows[i, :] = -K_list[i] * nablaH[i, :]

                
                for elem_idx in range(len(inter_cara)):
                    try:
                        if inter_cara[elem_idx][1] == 0:
                            current_idx = int(inter_cara[elem_idx][0])
                            # Vérifications de continuité
                            if (
                                K_list[current_idx]
                                == K_list[current_idx + 1]
                            ):
                                nablaH[current_idx, :] = nablaH[
                                    current_idx + 1, :
                                ]
                            if (
                                current_idx > 0
                                and K_list[current_idx]
                                == K_list[current_idx - 1]
                            ):
                                nablaH[current_idx, :] = nablaH[
                                    current_idx - 1, :
                                ]

                            flows[current_idx, :] = (
                                -K_list[current_idx]
                                * nablaH[current_idx, :]
                            )
                        else:
                            idx0 = int(inter_cara[elem_idx][0])
                            idx1 = int(inter_cara[elem_idx][1])
                           
                            nablaH[idx0, :] = (
                                H_res[idx0 + 1, :]
                                - H_res[idx0, :]
                            ) / dz
                            nablaH[idx1, :] = (
                                H_res[idx1, :]
                                - H_res[idx1 - 1, :]
                            ) / dz
                           
                            x = (
                                list_zLow[elem_idx] - z_solve[idx0]
                            ) / (
                                z_solve[idx1]
                                - z_solve[idx0]
                            )
                            # Moyenne harmonique
                            k_eff = 1 / (
                                x / K_list[idx0]
                                + (1 - x) / K_list[idx1]
                            )
                            # On met à jour K_list localement pour le calcul de flux (optionnel selon logique)
                            # K_list[idx0] = k_eff
                           
                            flows[idx0, :] = -k_eff * nablaH[idx0, :]
                            flows[idx1, :] = -k_eff * nablaH[idx1, :]

                    except IndexError as e:
                         print(f"Erreur correction flux: {e}")
                         raise e

                T_strat = T_stratified(
                    nablaH,
                    Ss_list,
                    IntrinK_list,
                    n_list,
                    lambda_s_list,
                    rhos_cs_list,
                    all_dt,
                    q_s_list, 
                    dz,
                    H_init,
                    H_riv,
                    H_aq,
                    T_init,
                    T_riv,
                    T_aq,
                    alpha=ALPHA,
                    N_update_Mu=N_UPDATE_MU,
                )
                T_res = T_strat.compute_T_stratified()
               
                
                if hasattr(T_strat, "source_heat_flux"):
                    self._lateral_advec_heat_flux = T_strat.source_heat_flux * dz
               
                self._temperatures = T_res
                self._flows = flows
               
                if verbose:
                    print("Done.")

                if np.isnan(self._temperatures).any() or np.isnan(self._flows).any():
                    print(
                        f"Issue for the following parameters : {self.get_list_current_params()}"
                    )
                    print(
                        f"Issue for the follwing number of layers : {len(self.all_layers)}"
                    )
                    raise ValueError("NaN values in compute_solve_transi")
       
        except Exception as e:
            print("\n--- RAPPORT DE BUG DÉFINITIF ---")
            print(f"Une erreur inattendue s'est produite : {e}")
            traceback.print_exc()
            raise e

    @compute_solve_transi.needed
    def get_id_sensors(self):
        return self._id_sensors

    @compute_solve_transi.needed
    def get_RMSE(self):
        nb_sensors = len(self._T_measures[0])
        nb_times = len(self._T_measures)
        list_RMSE = np.array(
            [
                np.sqrt(
                    np.nansum(
                        (self.get_temperatures_solve()[id, :] - temperatures_obs) ** 2
                    )
                    / nb_times
                )
                for id, temperatures_obs in zip(
                    self.get_id_sensors(), self._T_measures.T
                )
            ]
        )
        total_RMSE = np.sqrt(np.nansum(list_RMSE**2) / nb_sensors)
        return np.append(list_RMSE, total_RMSE)

    @compute_solve_transi.needed
    def print_RMSE_at_sensor(self):
        rmse = self.get_RMSE()
        for i in range(len(rmse) - 1):
            print(f"RMSE at sensor {i} : {rmse[i]}")
        print(f"Total RMSE : {rmse[-1]}")

    @compute_solve_transi.needed
    def get_depths_solve(self):
        return self._z_solve

    depths_solve = property(get_depths_solve)

    def get_times_solve(self):
        return self._times

    times_solve = property(get_times_solve)

    @compute_solve_transi.needed
    def get_temperatures_solve(self, z=None):
        if z is None:
            return self._temperatures
        z_ind = np.argmin(np.abs(self.depths_solve - z))
        return self._temperatures[z_ind, :]

    temperatures_solve = property(get_temperatures_solve)

    @compute_solve_transi.needed
    def get_vertical_advec_flows_solve(self):
        return RHO_W * C_W * self._flows * (self.temperatures_solve - ZERO_CELSIUS)

    vertical_advec_flows_solve = property(get_vertical_advec_flows_solve)

    def get_lateral_advec_heat_flux_solve(self, z=None):
        if z is None:
            return self._lateral_advec_heat_flux
        z_ind = np.argmin(np.abs(self.depths_solve - z))
        return self._lateral_advec_heat_flux[z_ind, :]

    lateral_advec_heat_flux_solve = property(get_lateral_advec_heat_flux_solve)

    @compute_solve_transi.needed
    def get_conduc_flows_solve(self):
        dz = self._z_solve[1] - self._z_solve[0]
        nb_cells = len(self._z_solve)
        _, n_list, lambda_s_list, _, _ = getListParameters(self.all_layers, nb_cells)
        lambda_m_list = (
            n_list * (LAMBDA_W) ** 0.5 + (1.0 - n_list) * (lambda_s_list) ** 0.5
        ) ** 2
        nablaT = np.zeros((nb_cells, len(self._times)), np.float32)

        for i in range(1, nb_cells - 1):
            nablaT[i, :] = (
                self._temperatures[i + 1, :] - self._temperatures[i - 1, :]
            ) / (2 * dz)
        nablaT[0, :] = nablaT[1, :]
        nablaT[nb_cells - 1, :] = nablaT[nb_cells - 2, :]

        conduc_flows = np.zeros((nb_cells, len(self._times)), np.float32)
        for i in range(nb_cells):
            conduc_flows[i, :] = lambda_m_list[i] * nablaT[i, :]

        return conduc_flows

    conduc_flows_solve = property(get_conduc_flows_solve)

    @compute_solve_transi.needed
    def get_flows_solve(self, z=None):
        if z is None:
            return self._flows
        z_ind = np.argmin(np.abs(self.depths_solve - z))
        return self._flows[z_ind, :]

    flows_solve = property(get_flows_solve)

    def perturbation_DREAM(
        self,
        nb_chain,
        nb_layer,
        nb_param,
        X,
        id_layer,
        j,
        delta,
        ncr,
        c,
        c_star,
        cr_vec,
        pcr,
        ranges,
        is_param_fixed,
    ):
        X_proposal = np.zeros((nb_layer, nb_param), np.float32)
        dX = np.zeros((nb_layer, nb_param), np.float32)

        for l in range(nb_layer):
            variable_indices = np.where(is_param_fixed[l] == False)[0]
            n_variable_params = len(variable_indices)

            if n_variable_params == 0:
                X_proposal[l] = X[j, l]
                continue

            id_layer[l] = np.random.choice(ncr, p=pcr[l])
            z = np.random.uniform(0, 1, n_variable_params)
            A_variable = z <= cr_vec[id_layer[l]]
            d_star = np.sum(A_variable)

            if d_star == 0:
                A_variable[np.argmin(z)] = True
                d_star = 1

            A = np.zeros(nb_param, dtype=bool)
            jump_indices = variable_indices[A_variable]
            A[jump_indices] = True

            lambd = np.random.uniform(-c, c, d_star)
            zeta = np.random.normal(0, c_star, d_star)

            available_indices = np.delete(np.arange(nb_chain), j)
            a = np.random.choice(available_indices, delta, replace=False)
            remaining_indices = np.setdiff1d(available_indices, a)
            b = np.random.choice(remaining_indices, delta, replace=False)
            gamma = 2.38 / np.sqrt(2 * d_star * delta)
            gamma = np.random.choice([gamma, 1], 1, [0.8, 0.2])

            dX[l][A] = zeta + (1 + lambd) * gamma * np.sum(
                X[a, l][:, A] - X[b, l][:, A], axis=0
            )

            X_proposal[l] = X[j, l] + dX[l]

            width = ranges[l][:, 1] - ranges[l][:, 0]
            variable_mask = width > 0
            X_proposal[l][variable_mask] = ranges[l][variable_mask, 0] + np.mod(
                X_proposal[l][variable_mask] - ranges[l][variable_mask, 0],
                width[variable_mask],
            )

        return (X_proposal, dX, id_layer)

    @checker
    def compute_mcmc(
        self,
        quantile: Union[float, Sequence[float]] = (QUANTILE_MIN, MEDIANE, QUANTILE_MAX),
        verbose=False,
        typealgo="no sigma",
        sigma2=1.0,
        nb_iter=NITMCMC,
        nb_chain=NBCHAINS,
        nitmaxburning=NBBURNING,
        delta=3,
        n_CR=3,
        c=0.1,
        c_star=1e-12,
        n_sous_ech_time=1,
        n_sous_ech_space=1,
        threshold=GELMANRCRITERIA,
    ):
        if verbose:
            print(
                "--- Compute MCMC ---",
                "Priors :",
                *(
                    f"    {prior}"
                    for prior in [layer.Prior_list for layer in self.all_layers]
                ),
                f"Number of cells : {self._nb_cells}",
                f"Number of iterations : {nb_iter}",
                f"Number of chains : {nb_chain}",
                "--------------------",
                sep="\n",
            )

        n_sous_ech_iter = max(1, int(np.ceil(nb_chain * nb_iter / NSAMPLEMIN)))
        sizesubsampling = max(int(np.ceil(nb_iter / n_sous_ech_iter)), 1)

        process = psutil.Process()

        if typealgo == "no sigma":
            sigma2_temp_prior = Prior((sigma2, sigma2), 0, lambda x: 1)
            sigma2_distrib = sigma2_temp_prior.density
        else:
            sigma2_temp_prior = Prior(
                (SIGMA2_MIN_T, SIGMA2_MAX_T), RANDOMWALKSIGMAT, lambda x: 1 / x
            )
            sigma2_distrib = sigma2_temp_prior.density

        if isinstance(quantile, Number):
            quantile = [quantile]

        dz = self._real_z[-1] / self._nb_cells
        _z_solve = dz / 2 + np.array([k * dz for k in range(self._nb_cells)])
        ind_ref = [np.argmin(np.abs(z - _z_solve)) for z in self._real_z[1:-1]]
        temp_ref = self._T_measures[:, :].T
        self._states = list()

        nb_layer = len(self.all_layers)
        nb_param = N_PARAM_MCMC
        nb_accepted = 0
        nb_burn_in_iter = 0

        # Gestion paramètres fixes 
        is_param_fixed = np.zeros((nb_layer, nb_param), dtype=bool)
        for l, layer in enumerate(self.all_layers):
            for p, prior in enumerate(layer.Prior_list):
                # Si le prior a un attribut is_fixed, on l'utilise, sinon on suppose False
                if hasattr(prior, "is_fixed") and prior.is_fixed:
                    is_param_fixed[l, p] = True

        temp_proposal = np.zeros((self._nb_cells, len(self._times)), np.float32)
        nb_cells_sous_ech = int(np.floor(self._nb_cells / n_sous_ech_space))
        nb_times_sous_ech = int(np.floor(len(self._times) / n_sous_ech_time))

        if nb_chain > 1:
            _temp_iter_chain = np.zeros(
                (nb_chain, self._nb_cells, len(self._times)), np.float32
            )
            _flow_iter_chain = np.zeros(
                (nb_chain, self._nb_cells, len(self._times)), np.float32
            )

            _temp = np.zeros(
                (sizesubsampling, nb_chain, nb_cells_sous_ech, nb_times_sous_ech),
                np.float32,
            )
            _flows = np.zeros(
                (sizesubsampling, nb_chain, nb_cells_sous_ech, nb_times_sous_ech),
                np.float32,
            )

            ranges = np.empty((nb_layer, nb_param, 2))
            for l in range(nb_layer):
                for p in range(nb_param):
                    # Utilisation de mcmc_range si disponible, sinon range standard
                    if hasattr(self.all_layers[l].Prior_list[p], "mcmc_range"):
                        lower_bound, upper_bound = self.all_layers[l].Prior_list[p].mcmc_range
                    else:
                        lower_bound, upper_bound = self.all_layers[l].Prior_list[p].range
                    ranges[l, p] = [lower_bound, upper_bound]

            cr_vec = np.arange(1, n_CR + 1) / n_CR
            n_id = np.zeros((nb_layer, n_CR), np.float32)
            J = np.zeros((nb_layer, n_CR), np.float32)
            pcr = np.ones((nb_layer, n_CR)) / n_CR
            id_layer = np.zeros(nb_layer, np.int32)

            multi_chain = [copy.deepcopy(self) for _ in range(nb_chain)]

            for column in multi_chain:
                column.compute_solve_transi = types.MethodType(
                    Column.compute_solve_transi, column
                )

            self._states = list()
            X = np.zeros((nb_chain, nb_layer, nb_param), np.float32)
            Energy = np.zeros((nb_chain), np.float32)

            for j, column in enumerate(multi_chain):
                column.sample_params_from_priors()
                X[j] = column._get_list_mcmc_params()
                Energy[j] = compute_energy(
                    _temp_iter_chain[j][ind_ref], temp_ref, sigma2, sigma2_distrib
                )

                column.compute_solve_transi(verbose=False)
                _temp_iter_chain[j] = column.get_temperatures_solve()
                _flow_iter_chain[j] = column.get_flows_solve()
                self._states.append(
                    State(
                        layers=X[j],
                        energy=Energy[j],
                        ratio_accept=1,
                        sigma2_temp=sigma2_temp_prior.sample(),
                    )
                )

            XBurnIn = np.zeros(
                (nitmaxburning + 1, nb_chain, nb_layer, nb_param), np.float32
            )
            XBurnIn[0] = X

            print(
                f"Initialisation - Utilisation de la mémoire (en Mo) : {process.memory_info().rss / 1e6}"
            )

            if verbose:
                print("--- Begin Burn in phase ---")

            for i in trange(nitmaxburning, desc="Burn in phase"):
                std_X = np.std(X, axis=0)
                std_X[std_X == 0] = 1.0

                for j, column in enumerate(multi_chain):
                    X_proposal, dX, id_layer = self.perturbation_DREAM(
                        nb_chain,
                        nb_layer,
                        nb_param,
                        X,
                        id_layer,
                        j,
                        delta,
                        n_CR,
                        c,
                        c_star,
                        cr_vec,
                        pcr,
                        ranges,
                        is_param_fixed,
                    )
                    sigma2_temp_proposal = sigma2_temp_prior.perturb(
                        self._states[j].sigma2_temp
                    )

                    for l, layer in enumerate(column.all_layers):
                        layer.mcmc_params = Param(*X_proposal[l])

                    column.compute_solve_transi(verbose=False)
                    temp_proposal = column._temperatures
                    Energy_Proposal = compute_energy(
                        temp_proposal[ind_ref],
                        temp_ref,
                        sigma2_temp_proposal,
                        sigma2_distrib,
                    )
                    log_ratio_accept = Energy[j] - Energy_Proposal

                    if np.log(np.random.uniform(0, 1)) < log_ratio_accept:
                        X[j] = X_proposal
                        Energy[j] = Energy_Proposal
                        _temp_iter_chain[j] = temp_proposal
                    else:
                        dX = np.zeros((nb_layer, nb_param))
                        for l, layer in enumerate(column.all_layers):
                            layer.mcmc_params = Param(*X[j][l])

                    for l in range(nb_layer):
                        J[l, id_layer[l]] += np.sum((dX[l] / std_X[l]) ** 2)
                        n_id[l, id_layer[l]] += 1

                for l in range(nb_layer):
                    pcr[l][n_id[l] != 0] = J[l][n_id[l] != 0] / n_id[l][n_id[l] != 0]
                    if np.sum(pcr[l]) == 0:
                        pcr[l][:] = 1.0 / n_CR
                    else:
                        pcr[l] = pcr[l] / np.sum(pcr[l])

                XBurnIn[i + 1] = X

                if gelman_rubin(
                    i + 2, nb_param, nb_layer, XBurnIn[: i + 2], threshold=threshold
                ):
                    if verbose:
                        print(f"Burn-in finished after : {nb_burn_in_iter} iterations")
                    break
                nb_burn_in_iter += 1

            self.nb_burn_in_iter = nb_burn_in_iter
            self._acceptance = np.zeros(nb_chain, np.float32)
            del XBurnIn

            print(
                f"Initialisation post burn-in - Utilisation de la mémoire (en Mo) : {process.memory_info().rss / 1e6}"
            )

            for i in trange(nb_iter, desc="DREAM MCMC Computation", file=sys.stdout):
                std_X = np.std(X, axis=0)
                std_X[std_X == 0] = 1.0

                for j, column in enumerate(multi_chain):
                    X_proposal, dX, id_layer = self.perturbation_DREAM(
                        nb_chain,
                        nb_layer,
                        nb_param,
                        X,
                        id_layer,
                        j,
                        delta,
                        n_CR,
                        c,
                        c_star,
                        cr_vec,
                        pcr,
                        ranges,
                        is_param_fixed,
                    )
                    sigma2_temp_proposal = sigma2_temp_prior.perturb(
                        self._states[j].sigma2_temp
                    )

                    for l, layer in enumerate(column.all_layers):
                        layer.mcmc_params = Param(*X_proposal[l])

                    column.compute_solve_transi(verbose=False)
                    temp_proposal = column.get_temperatures_solve()
                    _temp_iter_chain[j] = temp_proposal
                    _flow_iter_chain[j] = column.get_flows_solve()

                    Energy_Proposal = compute_energy(
                        temp_proposal[ind_ref],
                        temp_ref,
                        sigma2_temp_proposal,
                        sigma2_distrib,
                    )
                    log_ratio_accept = compute_log_acceptance(
                        Energy_Proposal, Energy[j]
                    )

                    if np.log(np.random.uniform(0, 1)) < log_ratio_accept:
                        X[j] = X_proposal
                        Energy[j] = Energy_Proposal
                        self._acceptance[j] += 1
                        self._states.append(
                            State(
                                layers=X[j],
                                energy=Energy[j],
                                ratio_accept=1,
                                sigma2_temp=sigma2_temp_proposal,
                            )
                        )
                    else:
                        dX = np.zeros((nb_layer, nb_param), np.float32)
                        self._states.append(self._states[-nb_chain])
                        for l, layer in enumerate(column.all_layers):
                            layer.mcmc_params = Param(*X[j][l])

                if i % n_sous_ech_iter == 0:
                    k = i // n_sous_ech_iter
                    for j in range(nb_chain):
                        if np.isnan(
                            _temp_iter_chain[j, ::n_sous_ech_space, ::n_sous_ech_time]
                        ).any():
                            _temp[k, j] = _temp[(k - 1), j]
                            _flows[k, j] = _flows[(k - 1), j]
                        else:
                            _temp[k, j] = _temp_iter_chain[
                                j, ::n_sous_ech_space, ::n_sous_ech_time
                            ]
                            _flows[k, j] = _flow_iter_chain[
                                j, ::n_sous_ech_space, ::n_sous_ech_time
                            ]

            for j in range(nb_chain):
                self._acceptance[j] /= nb_iter

            if verbose == True:
                print(f"Acceptance rate : {self._acceptance}")

            _temp = _temp.reshape(
                sizesubsampling * nb_chain, nb_cells_sous_ech, nb_times_sous_ech
            )
            _flows = _flows.reshape(
                sizesubsampling * nb_chain, nb_cells_sous_ech, nb_times_sous_ech
            )

        else:  # Cas single chain
            _temp_iter = np.zeros(
                (self._nb_cells, len(self._times)), np.float32
            )
            _flow_iter = np.zeros(
                (self._nb_cells, len(self._times)), np.float32
            )
            _temp = np.zeros(
                (sizesubsampling, self._nb_cells, len(self._times)), np.float32
            )
            _flows = np.zeros(
                (sizesubsampling, self._nb_cells, len(self._times)), np.float32
            )
            self._acceptance = 0

            if isinstance(quantile, Number):
                quantile = [quantile]

            for i in trange(nitmaxburning, desc="Init Mcmc ", file=sys.stdout):
                self.sample_params_from_priors()
                init_sigma2_temp = sigma2_temp_prior.sample()

                self.compute_solve_transi(verbose=False)
                self._states.append(
                    State(
                        layers=self.get_list_current_params(),
                        energy=compute_energy(
                            self.temperatures_solve[ind_ref, :],
                            temp_ref,
                            sigma2=init_sigma2_temp,
                            sigma2_distrib=sigma2_distrib,
                        ),
                        ratio_accept=1,
                        sigma2_temp=init_sigma2_temp,
                    )
                )

            self._states = [min(self._states, key=attrgetter("energy"))]

            for l, layer in enumerate(self.all_layers):
                layer.mcmc_params = Param(*self._states[0].layers[l])

            self._acceptance = np.zeros(nb_iter)

            _temp_iter = self.get_temperatures_solve()
            _flow_iter = self.get_flows_solve()

            nb_accepted = 0

            for i in trange(nb_iter, desc="Mcmc Computation", file=sys.stdout):
                X = self._get_list_mcmc_params()
                self.perturb_params()
                sigma2_temp_proposal = sigma2_temp_prior.perturb(
                    self._states[-1].sigma2_temp
                )

                self.compute_solve_transi(verbose=False)
                _temp_iter = self.get_temperatures_solve()
                _flow_iter = self.get_flows_solve()

                Energy_Proposal = compute_energy(
                    self.temperatures_solve[ind_ref, :],
                    temp_ref,
                    sigma2_temp_proposal,
                    sigma2_distrib=sigma2_temp_prior.density,
                )

                log_ratio_accept = compute_log_acceptance(
                    Energy_Proposal, self._states[-1].energy
                )

                if np.log(random()) < log_ratio_accept:
                    nb_accepted += 1
                    self._states.append(
                        State(
                            layers=self.get_list_current_params(),
                            energy=Energy_Proposal,
                            ratio_accept=nb_accepted / (i + 1),
                            sigma2_temp=sigma2_temp_proposal,
                        )
                    )
                else:
                    self._states.append(self._states[-1])
                    for l, layer in enumerate(self.all_layers):
                        layer.mcmc_params = Param(*X[l])

                if i % n_sous_ech_iter == 0:
                    k = i // n_sous_ech_iter
                    _temp[k] = _temp_iter[::n_sous_ech_space, ::n_sous_ech_time]
                    _flows[k] = _flow_iter[::n_sous_ech_space, ::n_sous_ech_time]

            self._acceptance = nb_accepted / (nb_iter + 1)

            if verbose == True:
                print(f"Acceptance rate : {self._acceptance}")
                print(
                    f"Fin itérations MCMC, avant le calcul des quantiles - Utilisation de la mémoire (en Mo) : {process.memory_info().rss / 1e6}"
                )

        self._quantiles_temperatures = {
            quant: res
            for quant, res in zip(quantile, np.quantile(_temp, quantile, axis=0))
        }

        self._quantiles_flows = {
            quant: res
            for quant, res in zip(quantile, np.quantile(_flows, quantile, axis=0))
        }

        self._acceptance = self._acceptance / nb_iter

        if verbose == True:
            print("Quantiles computed")

    @compute_mcmc.needed
    def get_depths_mcmc(self):
        return self._z_solve

    depths_mcmc = property(get_depths_mcmc)

    @compute_mcmc.needed
    def get_times_mcmc(self):
        return self._times

    times_mcmc = property(get_times_mcmc)

    @compute_mcmc.needed
    def sample_param(self):
        return choice(
            [[layer.mcmc_params for layer in state.layers] for state in self._states]
        )

    @compute_mcmc.needed
    def get_best_param(self):
        return [
            layer.mcmc_params
            for layer in min(self._states, key=attrgetter("energy")).layers
        ]

    @compute_mcmc.needed
    def get_best_sigma2(self):
        return min(self._states, key=attrgetter("energy")).sigma2_temp

    @compute_mcmc.needed
    def get_best_layers(self):
        best_layers = min(self._states, key=attrgetter("energy")).layers
        for l, layer in enumerate(self.all_layers):
            layer.mcmc_params = Param(*best_layers[l])

    def get_all_params(self):
        all_physical_params_history = []
        layers_with_priors = self.all_layers

        for state in self._states:
            mcmc_params_for_state = state.layers
            physical_state_params = []

            for l, layer_obj in enumerate(layers_with_priors):
                mcmc_params_for_layer = mcmc_params_for_state[l]
                physical_vals = [
                    prior.mcmc_to_physical(val) if prior is not None else val
                    for prior, val in zip(layer_obj.Prior_list, mcmc_params_for_layer)
                ]
                physical_state_params.append(Param(*physical_vals))

            all_physical_params_history.append(physical_state_params)
        return all_physical_params_history

 
    def get_all_IntrinK(self):
        all_params = self.get_all_params()
        return [[p.IntrinK for p in state_params] for state_params in all_params]

    def get_all_n(self):
        all_params = self.get_all_params()
        return [[p.n for p in state_params] for state_params in all_params]

    def get_all_lambda_s(self):
        all_params = self.get_all_params()
        return [[p.lambda_s for p in state_params] for state_params in all_params]

    def get_all_rhos_cs(self):
        all_params = self.get_all_params()
        return [[p.rhos_cs for p in state_params] for state_params in all_params]

    def get_all_q_s(self):
        all_params = self.get_all_params()
        return [[p.q_s for p in state_params] for state_params in all_params]

    all_IntrinK = property(get_all_IntrinK)
    all_n = property(get_all_n)
    all_lambda_s = property(get_all_lambda_s)
    all_rhos_cs = property(get_all_rhos_cs)
    all_q_s = property(get_all_q_s)

    @compute_mcmc.needed
    def get_all_sigma2(self):
        return [state.sigma2_temp for state in self._states]

    all_sigma = property(get_all_sigma2)

    @compute_mcmc.needed
    def get_all_energy(self):
        return self._initial_energies + [state.energy for state in self._states]

    all_energy = property(get_all_energy)

    @compute_mcmc.needed
    def get_all_acceptance_ratio(self):
        return self._acceptance

    all_acceptance_ratio = property(get_all_acceptance_ratio)

    @compute_mcmc.needed
    def get_quantiles(self):
        return self._quantiles_temperatures.keys()

    @compute_mcmc.needed
    def get_temperatures_quantile(self, quantile):
        return self._quantiles_temperatures[quantile]

    @compute_mcmc.needed
    def get_flows_quantile(self, quantile):
        return self._quantiles_flows[quantile]

    @compute_mcmc.needed
    def get_RMSE_quantile(self, quantile):
        nb_sensors = len(self._T_measures[0])
        nb_times = len(self._T_measures)

        list_RMSE = np.array(
            [
                np.sqrt(
                    np.nansum(
                        (
                            self.get_temperatures_quantile(quantile)[id, :]
                            - temperatures_obs
                        )
                        ** 2
                    )
                    / nb_times
                )
                for id, temperatures_obs in zip(
                    self.get_id_sensors(), self._T_measures.T
                )
            ]
        )
        total_RMSE = np.sqrt(np.sum(list_RMSE**2) / nb_sensors)
        return np.append(list_RMSE, total_RMSE)

    @compute_solve_transi.needed
    def get_temperature_at_sensors(self, zero=0, verbose=False):
        ids = self.get_id_sensors()
        if verbose:
            print(f"{len(ids)} Sensors\n")
        temperatures = np.zeros(
            (len(ids) + 2, self.get_timelength())
        )
        temperatures[0] = self._T_riv - zero
        temperatures[len(ids) + 1] = self._T_aq - zero
        for id in range(len(ids)):
            temperatures[id + 1] = self.get_temperatures_solve()[ids[id]] - zero
        return temperatures

    @compute_solve_transi.needed
    def plot_it_Zt(
        self,
        plotIt,
        title="TBD",
        cbarUnits="TBD",
        distBot=1.0,
        distLeft=0.5,
        fontsize=15,
    ):
        zoomSize = 2
        titleSize = fontsize + zoomSize
        reducedSize = fontsize - 2 * zoomSize
        nd = self.get_dt_in_days()
        temps_en_jours = self.create_time_in_day()
        fig, ax = plt.subplots(figsize=(10, 5), facecolor="w")

        im = ax.imshow(
            plotIt,
            aspect="auto",
            extent=[
                temps_en_jours[0],
                temps_en_jours[-1],
                self.depths_solve[-1],
                self.depths_solve[0],
            ],
            cmap="Spectral_r",
        )

        ax.set_xlabel("time in days", fontsize=fontsize)
        ax.set_ylabel("depth in m", fontsize=fontsize)
        ax.xaxis.tick_bottom()
        ax.xaxis.set_label_position("bottom")
        cbar = plt.colorbar(im, ax=ax, shrink=1, location="right")

        cbarSize = ax.xaxis.get_ticklabels()[0].get_fontsize()
        cbar.ax.tick_params(labelsize=cbarSize)
        cbar.ax.xaxis.set_label_position("top")
        cbar.ax.xaxis.label.set_rotation(0)
        cbar.ax.text(
            distLeft,
            distBot,
            cbarUnits,
            ha="center",
            va="bottom",
            transform=cbar.ax.transAxes,
            fontsize=fontsize,
        )

        ax.set_title(title, fontsize=titleSize)
        plt.show()

    @compute_solve_transi.needed
    def plot_temperature_at_sensors(
        self, title="Temperatures", verbose=False, fontsize=15
    ):
        zoomSize = 2
        titleSize = fontsize + zoomSize
        fig, ax = plt.subplots(figsize=(10, 5), facecolor="w")

        temps_en_jours = self.create_time_in_day()
        ids = self.get_id_sensors()
        temperatures = self.get_temperature_at_sensors(verbose=verbose)

        for i in range(len(ids) + 2):
            if verbose:
                print(f"Plotting Sensor {i}\n")
            if i == 0:
                label = "T_riv"
            elif i == len(ids) + 1:
                label = "T_aq"
            else:
                label = f"T{i}"

            ax.plot(temps_en_jours, temperatures[i], label=label)

        ax.set_xlabel("time in days", fontsize=fontsize)
        ax.set_ylabel("temperature", fontsize=fontsize)
        ax.set_title(title, fontsize=titleSize)
        ax.legend(
            loc="center left", bbox_to_anchor=(1, 0.5), fontsize=fontsize - zoomSize
        )
        plt.show()

    def set_zeroT(self, tunits="K"):
        if tunits == "K":
            zeroT = 0
        else:
            zeroT = ZERO_CELSIUS
        return zeroT

    @compute_solve_transi.needed
    def plot_compare_temperatures_sensors(self, tunits="K", fontsize=15):
        zeroT = self.set_zeroT(tunits)
        temps_en_jours = self.create_time_in_day()
        ids = self.get_id_sensors()
        temperatures = self.get_temperature_at_sensors() - zeroT
        nsensors = len(ids)
        fig, axes = plt.subplots(1, nsensors, figsize=(20, 5), sharey=True)
        axes[0].set_ylabel(f"Temperature in {tunits}")

        for i in range(nsensors):
            axes[i].set_xlabel("time in days", fontsize=fontsize)
            axes[i].plot(
                temps_en_jours,
                self._T_measures[:, i] - zeroT,
                label="Measurement",
            )
            axes[i].plot(temps_en_jours, temperatures[i + 1], label="Simulated")
            axes[i].legend()
            axes[i].set_title(f"Sensor {i + 1}")

        plt.subplots_adjust(wspace=0.05)

    @compute_mcmc.needed
    def plot_quantile_temperatures_sensors(self, tunits="K", fontsize=15):
        zeroT = self.set_zeroT(tunits)
        temps_en_jours = self.create_time_in_day()

        fig, axes = plt.subplots(1, 3, figsize=(20, 5), sharey=True)
        axes[0].set_ylabel(f"Temperature in {tunits}")

        for i, id in enumerate(self.get_id_sensors()):
            axes[i].set_xlabel("Time in days")
            axes[i].plot(
                temps_en_jours,
                self._T_measures[:, i] - zeroT,
                label="Measurement",
            )
            for q_s in self.get_quantiles():
                axes[i].plot(
                    temps_en_jours,
                    self.get_temperatures_quantile(q_s)[id] - zeroT,
                    label=f"Quantile {q_s}",
                )
            axes[i].legend()
            axes[i].set_title(f"Sensor {i + 1}")

        plt.subplots_adjust(wspace=0.05)

    @compute_solve_transi.needed
    def plot_temperatures_umbrella(self, dplot=1, K_offset=0, fontsize=15):
        K_offset = ZERO_CELSIUS
        fig, ax = plt.subplots(figsize=(10, 5), facecolor="w")
        nt = len(self._times)
        colors = [(1, 0.8, 0.6), (0.4, 0.2, 0)]
        n_bins = nt // dplot
        cmap_name = "orange_brown"
        colormap = LinearSegmentedColormap.from_list(cmap_name, colors, N=n_bins)
        colors = [colormap(i / (nt // dplot)) for i in range(nt // dplot)]
        line_styles = ["-", "--", "-.", ":", (0, (3, 1, 1, 1)), (0, (5, 10))]

        for idx, i in enumerate(range(0, nt, dplot)):
            color = colors[idx % len(colors)]
            linestyle = line_styles[idx % len(line_styles)]
            ax.plot(
                self._temperatures[:nt, i] - K_offset,
                -self._z_solve,
                label=f"T@{i * self.get_dt_in_days():.3f}d",
                color=color,
                linestyle=linestyle,
            )

        ax.legend(loc="center left", bbox_to_anchor=(1, 0.5), fontsize=fontsize)
        ax.set_ylabel("Depth (m)", fontsize=fontsize)
        ax.set_xlabel("T (°C)", fontsize=fontsize)
        ax.grid()
        ax.set_title("Temperature profiles over time", fontsize=fontsize, pad=20)
        plt.tight_layout()
        plt.show()

    @compute_solve_transi.needed
    def plot_CALC_results(self, fontsize=15):
        print(
            f"Plotting Température in column. time series have nrecords =  {len(self._times)}"
        )
        nt = len(self._times)
        K_offset = ZERO_CELSIUS
        n_sens = len(self.depth_sensors) - 1

        def min2jour(x):
            return x * self.get_dt_in_days()

        def jour2min(x):
            return x / self.get_dt_in_days()

        fig, ax = plt.subplots(3, 3, sharey=False, figsize=(22, 21))
        plt.subplots_adjust(wspace=0.3, hspace=0.4)
        fig.suptitle("Résultats calcul : simulateur de données", fontsize=fontsize + 6)

        ax[0, 0].plot(self._T_riv[:nt][:nt] - K_offset, label="Triv")
        for i in range(n_sens):
            ax[0, 0].plot(
                self._T_measures[:nt, i] - K_offset, label="T{}".format(i + 1)
            )
        ax[0, 0].plot(self._T_aq[:nt] - K_offset, label="Taq")
        ax[0, 0].legend(fontsize=fontsize)
        ax[0, 0].grid()
        ax[0, 0].xaxis.tick_top()
        ax[0, 0].set_xlabel("n*dt (15min)", fontsize=fontsize)
        ax[0, 0].xaxis.set_label_position("top")
        ax[0, 0].set_ylabel("T (°C)", fontsize=fontsize)
        ax[0, 0].secax = ax[0, 0].secondary_xaxis(
            "bottom", functions=(min2jour, jour2min)
        )
        ax[0, 0].secax.set_xlabel("t (jour)", fontsize=fontsize)
        ax[0, 0].set_title("Température mesurées", fontsize=fontsize, pad=20)

        for i in range(nt):
            ax[0, 1].plot(self._temperatures[:nt, i] - K_offset, -self._z_solve)
        ax[0, 1].set_ylabel("Depth (m)", fontsize=fontsize)
        ax[0, 1].set_xlabel("T (°C)", fontsize=fontsize)
        ax[0, 1].grid()
        ax[0, 1].set_title(
            "Evolution du profil de température", fontsize=fontsize, pad=20
        )

        ax[0, 2].axis("off")

        im0 = ax[1, 0].imshow(
            self._temperatures[:, :nt] - K_offset, aspect="auto", cmap="Spectral_r"
        )
        ax[1, 0].set_xlabel("t (15min)", fontsize=fontsize)
        ax[1, 0].set_ylabel("z (m)", fontsize=fontsize)
        ax[1, 0].xaxis.tick_top()
        ax[1, 0].xaxis.set_label_position("top")
        ax[1, 0].secax = ax[1, 0].secondary_xaxis(
            "bottom", functions=(min2jour, jour2min)
        )
        ax[1, 0].secax.set_xlabel("t (jour)", fontsize=fontsize)
        cbar0 = fig.colorbar(im0, ax=ax[1, 0], shrink=1, location="right")
        cbar0.set_label("Température (°C)", fontsize=fontsize)
        ax[1, 0].set_title("Frise température MD", fontsize=fontsize, pad=20)

        im3 = ax[1, 1].imshow(
            self.get_flows_solve()[:, :nt], aspect="auto", cmap="Spectral_r"
        )
        ax[1, 1].set_xlabel("t (15min)", fontsize=fontsize)
        ax[1, 1].set_ylabel("z (m)", fontsize=fontsize)
        ax[1, 1].xaxis.tick_top()
        ax[1, 1].xaxis.set_label_position("top")
        ax[1, 1].secax = ax[1, 1].secondary_xaxis(
            "bottom", functions=(min2jour, jour2min)
        )
        ax[1, 1].secax.set_xlabel("t (jour)", fontsize=fontsize)
        cbar3 = fig.colorbar(im3, ax=ax[1, 1], shrink=1, location="right")
        cbar3.set_label("Water flow (m/s)", fontsize=fontsize)
        ax[1, 1].set_title("Frise Flux d'eau MD", fontsize=fontsize, pad=20)

        ax[1, 2].axis("off")

        im1 = ax[2, 0].imshow(
            self.get_conduc_flows_solve()[:, :nt], aspect="auto", cmap="Spectral_r"
        )
        ax[2, 0].set_xlabel("t (15min)", fontsize=fontsize)
        ax[2, 0].set_ylabel("z (m)", fontsize=fontsize)
        ax[2, 0].xaxis.tick_top()
        ax[2, 0].xaxis.set_label_position("top")
        ax[2, 0].secax = ax[2, 0].secondary_xaxis(
            "bottom", functions=(min2jour, jour2min)
        )
        ax[2, 0].secax.set_xlabel("t (jour)", fontsize=fontsize)
        cbar1 = fig.colorbar(im1, ax=ax[2, 0], shrink=1, location="right")
        cbar1.set_label("Flux conductif (W/m²)", fontsize=fontsize)
        ax[2, 0].set_title("Frise Flux conductif MD", fontsize=fontsize, pad=20)

        im2 = ax[2, 1].imshow(
            self.get_vertical_advec_flows_solve()[:, :nt],
            aspect="auto",
            cmap="Spectral_r",
        )
        ax[2, 1].set_xlabel("t (15min)", fontsize=fontsize)
        ax[2, 1].set_ylabel("z (m)", fontsize=fontsize)
        ax[2, 1].xaxis.tick_top()
        ax[2, 1].xaxis.set_label_position("top")
        ax[2, 1].secax = ax[2, 1].secondary_xaxis(
            "bottom", functions=(min2jour, jour2min)
        )
        ax[2, 1].secax.set_xlabel("t (jour)", fontsize=fontsize)
        cbar2 = fig.colorbar(im2, ax=ax[2, 1], shrink=1, location="right")
        cbar2.set_label("Vertical Advective Flux (W/m²)", fontsize=fontsize)
        ax[2, 1].set_title("Frise Flux advectif vertical MD", fontsize=fontsize, pad=20)

        if self._lateral_advec_heat_flux is not None:
            im4 = ax[2, 2].imshow(
                self.get_lateral_advec_heat_flux_solve()[:, :nt],
                aspect="auto",
                cmap="Spectral_r",
            )
            ax[2, 2].set_xlabel("t (15min)", fontsize=fontsize)
            ax[2, 2].set_ylabel("z (m)", fontsize=fontsize)
            ax[2, 2].xaxis.tick_top()
            ax[2, 2].xaxis.set_label_position("top")
            ax[2, 2].secax = ax[2, 2].secondary_xaxis(
                "bottom", functions=(min2jour, jour2min)
            )
            ax[2, 2].secax.set_xlabel("t (jour)", fontsize=fontsize)
            cbar4 = fig.colorbar(im4, ax=ax[2, 2], shrink=1, location="right")
            cbar4.set_label("Lateral Advective Flux (W/m²)", fontsize=fontsize)
            ax[2, 2].set_title(
                "Frise Flux advectif latéral MD", fontsize=fontsize, pad=20
            )
        else:
            ax[2, 2].axis("off")

    @compute_solve_transi.needed
    def plot_all_results(self):
        self.print_RMSE_at_sensor()
        self.plot_compare_temperatures_sensors()
        self.plot_temperature_at_sensors()

        nt = len(self._temperatures[0, :])
        dplot = 15
        self.plot_temperatures_umbrella(round(nt / dplot))

        flows = self.get_flows_solve()
        unitLeg = "m/s"
        title = "Darcy velocity"
        self.plot_it_Zt(flows, title, unitLeg, 1.04, 2)

        temperatures = self.get_temperatures_solve()
        unitLeg = "K"
        title = "Temperatures"
        self.plot_it_Zt(temperatures, title, unitLeg)

        flux_advectifs_verticaux = self.get_vertical_advec_flows_solve()
        unitLeg = "W/m2"
        title = "Vertical Advective heat flux"
        self.plot_it_Zt(flux_advectifs_verticaux, title, unitLeg, 1.04, 2)

        flux_conductifs = self.get_conduc_flows_solve()
        unitLeg = "W/m2"
        title = "Conductive heat flux"
        self.plot_it_Zt(flux_conductifs, title, unitLeg, 1.04, 2)

        if self._lateral_advec_heat_flux is not None:
            flux_advectif_lateral = self.get_lateral_advec_heat_flux_solve()
            unitLeg = "W/m2"
            title = "Lateral Advective Heat Flux"
            self.plot_it_Zt(flux_advectif_lateral, title, unitLeg, 1.04, 2)

        self.plot_CALC_results()

    @compute_mcmc.needed
    def plot_all_param_pdf(self):
        nb_layers = len(self.all_layers)
        nb_params = len(PARAM_LIST)

        all_params_history_list = self.get_all_params()

        if not all_params_history_list:
            print("Aucune donnée MCMC à afficher.")
            return

        all_params_array = np.array(all_params_history_list)

        fig, axes = plt.subplots(
            nrows=nb_layers,
            ncols=nb_params,
            figsize=(15, 3 * nb_layers if nb_layers > 1 else 5),
            squeeze=False,
        )
        fig.suptitle("Distribution a posteriori des paramètres (PDF)", fontsize=16)

        for id_l in range(nb_layers):
            layer_distribs = all_params_array[:, id_l, :]

            axes[id_l, 0].hist(layer_distribs[:, 0])
            axes[id_l, 0].set_title(f"Couche {id_l + 1} : IntrinK")

            axes[id_l, 1].hist(layer_distribs[:, 1])
            axes[id_l, 1].set_title(f"Couche {id_l + 1} : n")

            axes[id_l, 2].hist(layer_distribs[:, 2])
            axes[id_l, 2].set_title(f"Couche {id_l + 1} : lambda_s")

            axes[id_l, 3].hist(layer_distribs[:, 3])
            axes[id_l, 3].set_title(f"Couche {id_l + 1} : rhos_cs")

            axes[id_l, 4].hist(layer_distribs[:, 4])
            axes[id_l, 4].set_title(f"Couche {id_l + 1} : q_s")

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.show()

    def plot_darcy_flow_quantile(self):
        temps_en_jours = self.create_time_in_day()

        fig, axes = plt.subplots(
            1, 3, figsize=(20, 10), sharex="col", sharey="row", constrained_layout=True
        )
        axes[0].set_ylabel("Débit en m/s")

        im_list = []
        for i, q in enumerate(self.get_quantiles()):
            im = axes[i].imshow(
                self.get_flows_quantile(q),
                aspect="auto",
                cmap="Spectral_r",
                extent=[0, temps_en_jours[-1], self._real_z[-1], self._real_z[0]],
            )
            axes[i].set_title(f"Darcy flow quantile : {100 * q} %")
            axes[i].set_xlabel("Time in days)")
            im_list.append(im)

        cbar = fig.colorbar(
            im_list[0], ax=axes, orientation="vertical", fraction=0.02, pad=0.04
        )
        cbar.set_label("Flow Rate (m/s)")
        plt.show()

    def print_sensor_file(self, fp, senType, senName):
        print(f"Printing Sensor file {senType}")
        if senType == SensorType.pressure_sensors.value:
            fp.write(f"P_Sensor_Name,{senName}\n")
            fp.write(f"Datalogger,MOLONARI1D_by_arduino\n")
            fp.write(f"Calibration_Date,{ABSURD_DATE}\n")
            fp.write(f"Intercept,0.\n")
            fp.write(f"dU_dH,1\n")
            fp.write(f"dU_dT,0.0\n")
            fp.write(f"Sigma_Meas_P,0.01\n")
            fp.write(
                f"Thermometer name,{SENSOR_FILE_NAMES[SensorType.temperature_sensors]}\n"
            )
        elif senType == SensorType.shafts.value:
            fp.write(f"Shaft_Name,{senName}\n")
            fp.write(f"Datalogger,Hobo\n")
            fp.write(
                f"T_Sensor_Name,{SENSOR_FILE_NAMES[SensorType.temperature_sensors]}\n"
            )
            fp.write(f'Sensors_Depth,"{self.depth_sensors}"\n')
        else:
            fp.write(f"Cons_Name,Mines\n")
            fp.write(f"Cons_Ref,Corefge\n")
            fp.write(f"T_Sensor_Name,{senName}\n")
            fp.write(f"Sigma_Meas_T,0.03\n")

    def print_sampling_point_info(
        self,
        fp,
        spname="VirtualPoint",
        psenname="Pvirtual",
        shaftname="Svirtual",
        tname="Tvirtual",
    ):
        fp.write(f"Point_Name,{spname}\n")
        fp.write(f"P_Sensor_Name,{psenname}\n")
        fp.write(f"Shaft_Name,{shaftname}\n")
        fp.write(f"Implantation_Date,{self._times[0]}\n")
        fp.write(f"Meas_Date,{self._times[-1]}\n")
        fp.write(f"River_Bed,{self.zbed}\n")
        fp.write(f"Delta_h,{self.offset}\n")

    @compute_solve_transi.needed
    def print_in_file_processed_MOLONARI_dataset(
        self, zeroT=ZERO_CELSIUS, spname="VirtualPoint", lname="VirtualLabo"
    ):
        spDirName = f"{self._dir_print}/{spname}"
        pointDir = create_dir(spDirName)

        labDirName = f"{self._dir_print}/{lname}"
        labDir = create_dir(labDirName)

        ids = self.get_id_sensors()
        temperatures = self.get_temperature_at_sensors()

        fpressure = open_printable_file(
            rac=pointDir,
            dataType=DeviceType.PRESSURE,
            classType=self._classType,
            spname=spname,
        )
        fthermal = open_printable_file(
            rac=pointDir,
            dataType=DeviceType.TEMPERATURE,
            classType=self._classType,
            spname=spname,
        )

        for i in range(len(self._times)):
            formatted_time = self._times[i].strftime("%m/%d/%y %I:%M:%S %p")
            fpressure.write(
                f"{formatted_time},{self._dH[i]:.4f},{temperatures[0][i] - zeroT:.4f}\n"
            )
            temp_values = [f"{formatted_time}"]
            for id in range(len(ids) + 1):
                temp_values.append(f"{temperatures[id + 1][i] - zeroT:.4f}")
            temp_string = ",".join(temp_values)
            fthermal.write(f"{temp_string}\n")

        finfo = open_printable_file(rac=pointDir, fname=f"{spname}_info")
        self.print_sampling_point_info(finfo, spname)

        close_printable_file(fpressure)
        close_printable_file(fthermal)
        close_printable_file(finfo)

        for sensor in SensorType:
            senDir = create_dir(f"{labDir}/{sensor.name}")
            fname = SENSOR_FILE_NAMES[sensor]
            fp = open_printable_file(rac=senDir, fname=fname)
            self.print_sensor_file(fp, sensor.value, SENSOR_FILE_NAMES[sensor])
            close_printable_file(fp)

    def sample_params_from_priors(self):
        for layer in self.all_layers:
            layer.sample()

    def _get_list_mcmc_params(self):
        return [layer.mcmc_params for layer in self.all_layers]

    def get_list_current_params(self):
        return [layer.get_physical_params() for layer in self.all_layers]

    def perturb_params(self):
        for layer in self.all_layers:
            layer.perturb(layer.mcmc_params)


def compute_energy(temp_simul, temp_ref, sigma2, sigma2_distrib):
    norm2 = np.linalg.norm(temp_ref - temp_simul) ** 2
    return (
        (np.size(temp_ref) * np.log(sigma2))
        + norm2 / (2 * sigma2)
        - np.log(sigma2_distrib(sigma2))
    )


def compute_log_acceptance(current_energy: float, prev_energy: float):
    return prev_energy - current_energy

