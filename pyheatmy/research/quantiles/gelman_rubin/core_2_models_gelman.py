"""
    author: Nicolas Matte
    session: MOLONARI 2023
"""
from typing import List, Sequence, Union
from random import random, choice
from operator import attrgetter
from numbers import Number
import sys
import psutil

import numpy as np
import matplotlib.pyplot as plt
from tqdm import trange
from scipy.interpolate import interp1d

from lagrange import Lagrange
from params import Param, ParamsPriors, Prior, PARAM_LIST
from state import State
from checker import checker

from utils_2_models_gelman import *
# (
#         C_W,
#     RHO_W,
#     LAMBDA_W,
#     compute_H_stratified,
#     compute_T_stratified,
#     conv,
#     compute_energy,
#     compute_log_acceptance,
#     convert_to_layer,
#     check_range,
#     gelman_rubin,
#     interface_transition,
# )
#from utils import C_W, RHO_W, LAMBDA_W, compute_H, compute_T, compute_H_stratified, compute_T_stratified, EPSILON
from layers import Layer, getListParameters, sortLayersList, AllPriors, LayerPriors


class Column:  # colonne de sédiments verticale entre le lit de la rivière et l'aquifère
    def __init__(
        self,
        river_bed: float,  # profondeur de la colonne en mètres
        # profondeur des capteurs de températures en mètres
        depth_sensors: Sequence[float],
        offset: float,  # correspond au décalage du capteur de température par rapport au lit de la rivière
        # liste contenant un tuple avec la date, la charge et la température au sommet de la colonne
        dH_measures: list,
        T_measures: list,  # liste contenant un tuple avec la date et la température aux points de mesure de longueur le nombre de temperatures mesuré
        sigma_meas_P: float,  # écart type de l'incertitude sur les valeurs de pression capteur
        sigma_meas_T: float,  # écart type de l'incertitude sur les valeurs de température capteur
        # mode d'interpolation du profil de température initial : 'lagrange' ou 'linear'
        inter_mode: str = "linear",
    ):
        # ! Pour l'instant on suppose que les temperatures matchent
        self._times = [t for t, _ in dH_measures]
        # récupère la liste des charges de la riviière (au cours du temperatures)
        self._dH = np.array([d for _, (d, _) in dH_measures])
        # récupère la liste de température de la rivière (au cours du temperatures)
        self._T_riv = np.array([t for _, (_, t) in dH_measures])
        # récupère la liste de température de l'aquifère (au cours du temperatures)
        self._T_aq = np.array([t[-1] for _, t in T_measures])
        # récupère la liste de températures des capteurs (au cours du temperatures)
        self._T_measures = np.array([t[:-1] for _, t in T_measures])

        # décale d'un offset les positions des capteurs de température (aussi riviere)
        self._real_z = np.array([0] + depth_sensors) + offset
        # enlève l'offset sur la mesure de température rivière car cette mesure est prise dans le capteur pression
        self._real_z[0] -= offset

        self.depth_sensors = depth_sensors
        self.offset = offset

        self._layersList = None

        self._z_solve = (
            None  # le tableau contenant la profondeur du milieu des cellules
        )
        self._id_sensors = None
        # le tableau contenant les températures à tout temperatures et à toute profondeur (lignes : températures) (colonnes : temperatures)
        self._temperatures = None
        # le tableau contenant les charges à tout temperatures et à toute profondeur (lignes : charges) (colonnes : temperatures)
        self._H_res = None
        # le tableau contenant le débit spécifique à tout temperatures et à toute profondeur (lignes : débit) (colonnes : temperatures)
        self._flows = None

        # liste contenant des objets de classe état et de longueur le nombre d'états acceptés par la MCMC (<=nb_iter), passe à un moment par une longueur de 1000 pendant l'initialisation de MCMC
        self._states = None
        self._initial_energies = None
        self._acceptances = None
        # dictionnaire indexé par les quantiles (0.05,0.5,0.95) à qui on a associe un array de deux dimensions : dimension 1 les profondeurs, dimension 2 : liste des valeurs de températures associées au quantile, de longueur les temperatures de mesure
        self._quantiles_temperatures = None
        # dictionnaire indexé par les quantiles (0.05,0.5,0.95) à qui on a associe un array de deux dimensions : dimension 1 les profondeurs, dimension 2 : liste des valeurs de débits spécifiques associés au quantile, de longueur les temperatures de mesure
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
        self.tests()  # teste que les conditions nécessaires à l'analyse sont remplies

    def tests(self):
        # teste que les données sont aux bons formats
        if np.shape(self._dH) != np.shape(self._T_aq) or (
            np.shape(self._dH) != np.shape(self._T_riv)
            or (np.shape(self._T_measures[1]) != (3,))
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
    def from_dict(cls, col_dict):
        """
        Class method to create an instance of Column from a dictionnary.
        """
        return cls(**col_dict)

    def _check_layers(self, layersList):
        """
        Initializes the _layersList attribute with layersList sorted by zLow.
        Checks the last layer's zLow matches the end of the column.
        """
        self._layersList = sortLayersList(layersList)

        if len(self._layersList) == 0:
            raise ValueError("Your list of layers is empty.")

        if self._layersList[-1].zLow != self._real_z[-1]:
            self._layersList[-1].zLow = self._real_z[-1]
            # raise ValueError(
            #     "Last layer does not match the end of the column.")

    def _compute_solve_transi_multiple_layers(self, layersList, nb_cells, verbose):
        dz = self._real_z[-1] / nb_cells  # profondeur d'une cellule
        self._z_solve = dz / 2 + np.array([k * dz for k in range(nb_cells)])

        self._id_sensors = [
            np.argmin(np.abs(z - self._z_solve)) for z in self._real_z[1:-1]
        ]

        all_dt = np.array(
            [
                (self._times[j + 1] - self._times[j]).total_seconds()
                for j in range(len(self._times) - 1)
            ]
        )  # le tableau des pas de temperatures (dépend des données d'entrée)
        isdtconstant = np.all(all_dt == all_dt[0])

        H_init = self._dH[0] - self._dH[0] * self._z_solve / self._real_z[-1]
        # fixe toutes les charges de l'aquifère à 0 (à tout temperatures)
        H_aq = np.zeros(len(self._times))
        H_riv = (
            self._dH
        )  # self.dH contient déjà les charges de la rivière à tout temperatures, stocke juste dans une variable locale
        # crée les températures initiales (t=0) sur toutes les profondeurs (milieu des cellules)

        if self.inter_mode == "lagrange":
            T_init = np.array([self.lagr(z) for z in self._z_solve])
        elif self.inter_mode == "linear":
            T_init = self.linear(self._z_solve)
        T_riv = self._T_riv
        T_aq = self._T_aq

        moinslog10IntrinK_list, n_list, lambda_s_list, rhos_cs_list = getListParameters(
            layersList, nb_cells
        )

         ## zhan: ici H_init a causé un problème sous le cas stratifié
        
        array_moinslog10IntrinK = np.array([float(x.params.moinslog10IntrinK) for x in layersList])
        array_K = 10 ** (-array_moinslog10IntrinK)
        heigth = abs(self._real_z[-1] - self._real_z[0])
        array_Ss = np.array([float(x.params.n) for x in layersList]) / heigth
        array_eps = np.zeros(len(layersList)) # eps de chaque couche
        array_eps[0] = layersList[0].zLow
        
        for idx in range(1, len(layersList)):
            array_eps[idx] = layersList[idx].zLow - layersList[idx - 1].zLow
        array_Hinter = np.zeros(len(layersList) + 1) # charge hydraulique de chaque interface
        array_Hinter[0] = self._dH[0]
        array_Hinter[-1] = 0.0
        N = len(array_Hinter) - 1
        # calculate Hinter
        H_gauche = np.zeros((N-1, N-1))
        H_droite = np.zeros((N-1, N-1))
        scalar_gauche = np.zeros(N-1)
        scalar_droite = np.zeros(N-1)
        #print('scalar_gauche = ',scalar_gauche)
        #print('N = ', N)
        #print('array_Hinter = ',array_Hinter)
        #print('layersList = ', layersList)
        scalar_gauche[0] = array_K[0] * array_Hinter[0] / array_eps[0]
        scalar_droite[-1] = -array_K[-1] * array_Hinter[-1] / array_eps[-1]
        H_gauche[0,0] = -array_K[0] / array_eps[0]
        for diag in range(1, N-1):
            H_gauche[diag, diag - 1] = array_K[diag] / array_eps[diag]
            H_gauche[diag, diag] = -array_K[diag] / array_eps[diag]

        H_droite[N-2, N-2] = array_K[-1] / array_eps[-1]
        for diag in range(0, N-2):
            H_droite[diag, diag + 1] = -array_K[diag + 1] / array_eps[diag + 1]
            H_droite[diag, diag] = array_K[diag + 1] / array_eps[diag + 1]
        
        Matrix_b = scalar_gauche - scalar_droite
        Matrix_A = H_droite - H_gauche
        H_sol = np.linalg.solve(Matrix_A, Matrix_b)
        for idx in range(len(H_sol)):
            array_Hinter[idx + 1] = H_sol[idx]
        #
        # list_array_L: couper le profondeur selon l'épaisseur de chaque couche
        list_array_L = []
        cnt = 0
        for idx in range(len(layersList) - 1):
            cnt_start = cnt
            while cnt < len(self._z_solve):
                if self._z_solve[cnt] <= layersList[idx].zLow and self._z_solve[cnt + 1] > layersList[idx].zLow:
                    list_array_L.append(self._z_solve[cnt_start:cnt + 1])
                    cnt += 1
                    break
                else:
                    cnt += 1
        list_array_L.append(self._z_solve[cnt:])
        #
        # calculer H de chaque couche

        list_array_H = []
        for idx in range(len(list_array_L)):
            if idx > 0: 
                list_array_H.append(array_Hinter[idx] - (array_Hinter[idx] - array_Hinter[idx + 1]) / array_eps[idx] * (list_array_L[idx] - layersList[idx-1].zLow))
            else:
                list_array_H.append(array_Hinter[idx] - (array_Hinter[idx] - array_Hinter[idx + 1]) / array_eps[idx] * (list_array_L[idx] - 0))
        if verbose:
            print("charge hydraulique sur chaque interface", array_Hinter)
            for idx in range(len(list_array_L)):
                plt.plot(list_array_H[idx], list_array_L[idx], label = 'couche ' + str(idx + 1))
            plt.plot(H_init, self._z_solve, linestyle = '--', label = 'solution originale')
            plt.legend()
            plt.title("charge hydraulique stratifiée initialisé")
            plt.xlabel('la charge hydraulique (m)')
            plt.ylabel('le profondeur (m)')
            plt.show()

        '''print('list_array_H shape',len(list_array_H))'''
        H_init = list_array_H[0]
        for idx in range(1, len(list_array_H)):
            H_init = np.concatenate((H_init, list_array_H[idx]))
        
        #print('H_inti shape init:',H_init.shape)
        
        ## zhan : end

        
        Ss_list = n_list / heigth  # l'emmagasinement spécifique = porosité sur la hauteur

        if verbose:
            print("--- Compute Solve Transi ---")
            for layer in layersList:
                print(layer)

        #H_riv = np.array([H_init[0] for _ in H_riv])
        # H_aq = np.array([H_init[-1] for _ in H_riv])
        if verbose:
            print("conditions aux limites")
            print("H_riv", H_riv)
            print("H_aq", H_aq)
        ##
        list_zLow = []
        for layer in layersList:
            list_zLow.append(layer.zLow)
        list_zLow.pop()
        z_solve = self._z_solve.copy()

        ## zhan Nov8: Classification according to Klist on symmetry of interfaces
        inter_cara = np.zeros((len(list_zLow), 2))
        for zlow_idx in range(len(list_zLow)):
            for z_idx in range(len(z_solve) - 1):
                if z_solve[z_idx] <= list_zLow[zlow_idx] and z_solve[z_idx + 1] > list_zLow[zlow_idx]:
                    if abs(z_solve[z_idx] - list_zLow[zlow_idx]) < EPSILON:
                        inter_cara[zlow_idx,0] = z_idx
                    elif abs(z_solve[z_idx + 1] - list_zLow[zlow_idx]) < EPSILON:
                        inter_cara[zlow_idx,0] = z_idx + 1
                    else:
                        inter_cara[zlow_idx,0] = z_idx
                        inter_cara[zlow_idx,1] = z_idx + 1
        ## end
        '''print("array_K shape:", array_K.shape)
        print("array_Ss shape:", array_Ss.shape)
        print("list_zLow shape:", len(list_zLow))
        print("z_solve shape:", len(z_solve))
        print("inter_cara shape:", inter_cara.shape)
        print("moinslog10IntrinK_list shape:", moinslog10IntrinK_list.shape)
        print("Ss_list shape:", Ss_list.shape)
        print("all_dt shape:", all_dt.shape)
        print("dz shape:", dz.shape)
        print("H_init shape:", H_init.shape)
        print("H_riv shape:", H_riv.shape)
        print("H_aq shape:", H_aq.shape)'''




        H_res = compute_H_stratified(
            array_K, array_Ss, list_zLow, z_solve, inter_cara, moinslog10IntrinK_list, Ss_list, all_dt, isdtconstant, dz, H_init, H_riv, H_aq)

        self._H_res = H_res  # stocke les résultats

        # création d'un tableau du gradient de la charge selon la profondeur, calculé à tout temperatures
        K_list = 10 ** - moinslog10IntrinK_list
        nablaH = np.zeros((nb_cells, len(self._times)), np.float32)

        nablaH[0, :] = 2 * (H_res[1, :] - H_riv) / (3 * dz)

        ## zhan Nov8: calculation de la derivation
        for i in range(1, nb_cells - 1):
            nablaH[i, :] = (H_res[i+1, :] - H_res[i-1, :])/(2*dz)
        flows = np.zeros((nb_cells, len(self._times)), np.float32)

        for i in range(nb_cells):
            flows[i, :] = - K_list[i]*nablaH[i, :]
        if verbose:
            plt.plot(z_solve, flows[:,0], linestyle = '--', label = "before derivation fix")
        for elem_idx in range(len(inter_cara)):
            if inter_cara[elem_idx][1] == 0:
                if K_list[int(inter_cara[elem_idx][0])] == K_list[int(inter_cara[elem_idx][0])+1]:
                    nablaH[int(inter_cara[elem_idx][0]), :] = nablaH[int(inter_cara[elem_idx][0])+1, :]  ## +1
                if K_list[int(inter_cara[elem_idx][0])] == K_list[int(inter_cara[elem_idx][0])-1]:
                    nablaH[int(inter_cara[elem_idx][0]), :] = nablaH[int(inter_cara[elem_idx][0])-1, :]  ## +1
                flows[int(inter_cara[elem_idx][0]), :] = - K_list[int(inter_cara[elem_idx][0])]*nablaH[int(inter_cara[elem_idx][0]), :]
            else:
                nablaH[int(inter_cara[elem_idx][0]), :] = (H_res[int(inter_cara[elem_idx][0])+1, :] - H_res[int(inter_cara[elem_idx][0]), :])/ dz
                nablaH[int(inter_cara[elem_idx][1]), :] = (H_res[int(inter_cara[elem_idx][1]), :] - H_res[int(inter_cara[elem_idx][1]) - 1, :])/ dz
                x = (list_zLow[elem_idx] - z_solve[int(inter_cara[elem_idx][0])]) / (z_solve[int(inter_cara[elem_idx][1])] - z_solve[int(inter_cara[elem_idx][0])])
                K_list[int(inter_cara[elem_idx][0])] = 1 / (x / K_list[int(inter_cara[elem_idx][0])] + (1-x) / K_list[int(inter_cara[elem_idx][0])+1])
                flows[int(inter_cara[elem_idx][0]), :] = - K_list[int(inter_cara[elem_idx][0])]*nablaH[int(inter_cara[elem_idx][0]), :]
                flows[int(inter_cara[elem_idx][1]), :] = - K_list[int(inter_cara[elem_idx][0])]*nablaH[int(inter_cara[elem_idx][1]), :]

        if verbose:
            plt.plot(z_solve, flows[:,0], label = "after derivation fix")
            plt.legend()
            plt.title("flow")
            plt.show()
        
        ## zhan Nov8
    
        nablaH[nb_cells - 1, :] = 2*(H_aq - H_res[nb_cells - 2, :])/(3*dz)

        T_res = compute_T_stratified(Ss_list, moinslog10IntrinK_list, n_list, lambda_s_list,
                                     rhos_cs_list, all_dt, dz, H_res, H_riv, H_aq, nablaH, T_init, T_riv, T_aq)

        self._temperatures = T_res

        self._flows = flows  # calcul du débit spécifique
        if verbose:
            print("Done.")

    @checker
    def compute_solve_transi(
        self, layersList: Union[tuple, Sequence[Layer]], nb_cells: int, verbose=True
    ):
        """
        Computes H, T and flow for each time and depth of the discretization of the column.
        """
        #print('layersList = ',layersList)
        
        if isinstance(layersList, tuple):
            #print('layersList is a tuple')
            layer = [
                Layer(
                    "Layer 1",
                    self._real_z[-1],
                    layersList[0],
                    layersList[1],
                    layersList[2],
                    layersList[3],
                )
            ]
            self.compute_solve_transi(layer, nb_cells, verbose)

        else:
            # Checking the layers are well defined
            #print('layersList is not a tuple')
            self._check_layers(layersList)
            self._compute_solve_transi_multiple_layers(
                self._layersList, nb_cells, verbose
            )

    @compute_solve_transi.needed
    def get_id_sensors(self):
        """
        Returns
        -------
        self._id_sensors : int list
            list of the 3 indices of the cells where the non boundary sensors are.
        """
        return self._id_sensors

    @compute_solve_transi.needed
    def get_RMSE(self):
        """
        Returns
        -------
        res : float array
            array with 4 elements which contains the RMSE for the non boundary sensors, and the total RMSE
        """

        # Number of sensors (except boundary conditions : river and aquifer)
        nb_sensors = len(self._T_measures[0])

        # Number of times for which we have measures
        nb_times = len(self._T_measures)

        # Array of RMSE for each sensor
        list_RMSE = np.array(
            [
                np.sqrt(
                    np.nansum((self.get_temperatures_solve()[id, :] - temperatures_obs) ** 2)
                    / nb_times
                )
                for id, temperatures_obs in zip(self.get_id_sensors(), self._T_measures.T)
            ]
        )

        # Total RMSE
        total_RMSE = np.sqrt(np.nansum(list_RMSE**2) / nb_sensors)

        return np.append(list_RMSE, total_RMSE)

    # erreur si pas déjà éxécuté compute_solve_transi, sinon l'attribut pas encore affecté à une valeur
    @compute_solve_transi.needed
    def get_depths_solve(self):
        """
        Returns
        -------
        self._z_solve : float array
            array of the depths of the middle of each cell.
        """
        return self._z_solve

    depths_solve = property(get_depths_solve)
    # récupération de l'attribut _z_solve

    def get_times_solve(self):
        """
        Returns
        -------
        self._times : datetime list
            list of the times at which the temperatures are computed.
        """
        return self._times

    times_solve = property(get_times_solve)
    # récupération de l'attribut _times

    # erreur si pas déjà éxécuté compute_solve_transi, sinon l'attribut pas encore affecté à une valeur
    @compute_solve_transi.needed
    def get_temperatures_solve(self, z=None):
        if z is None:
            return self._temperatures
        z_ind = np.argmin(np.abs(self.depths_solve - z))
        return self._temperatures[z_ind, :]

    temperatures_solve = property(get_temperatures_solve)
    # récupération des températures au cours du temps à toutes les profondeurs (par défaut) ou bien à une profondeur donnée

    # erreur si pas déjà éxécuté compute_solve_transi, sinon l'attribut pas encore affecté à une valeur
    @compute_solve_transi.needed
    def get_advec_flows_solve(self):
        return RHO_W * C_W * self._flows * (self.temperatures_solve - 273.15)

    advec_flows_solve = property(get_advec_flows_solve)
    # récupération des flux advectifs = masse volumnique*capacité calorifique*débit spécifique*température

    # erreur si pas déjà éxécuté compute_solve_transi, sinon l'attribut pas encore affecté à une valeur
    @compute_solve_transi.needed
    def get_conduc_flows_solve(self):
        dz = self._z_solve[1] - self._z_solve[0]  # pas en profondeur
        nb_cells = len(self._z_solve)

        _, n_list, lambda_s_list, _ = getListParameters(self._layersList, nb_cells)

        lambda_m_list = (
            n_list * (LAMBDA_W) ** 0.5 + (1.0 - n_list) * (lambda_s_list) ** 0.5
        ) ** 2  # conductivité thermique du milieu poreux équivalent
        
        # création du gradient de température
        nablaT = np.zeros((nb_cells, len(self._times)), np.float32)

        nablaT[0, :] = 2 * (self._temperatures[1, :] - self._T_riv) / (3 * dz)

        for i in range(1, nb_cells - 1):
            nablaT[i, :] = (self._temperatures[i + 1, :] - self._temperatures[i - 1, :]) / (2 * dz)

        nablaT[nb_cells - 1, :] = (
            2 * (self._T_aq - self._temperatures[nb_cells - 2, :]) / (3 * dz)
        )

        conduc_flows = np.zeros((nb_cells, len(self._times)), np.float32)
        
        for i in range(nb_cells):
            conduc_flows[i, :] = lambda_m_list[i] * nablaT[i, :]

        return conduc_flows

    conduc_flows_solve = property(get_conduc_flows_solve)
    # récupération des flux conductifs = conductivité*gradient(T)

    # erreur si pas déjà éxécuté compute_solve_transi, sinon l'attribut pas encore affecté à une valeur
    @compute_solve_transi.needed
    def get_flows_solve(self, z=None):
        if z is None:
            return self._flows  # par défaut, retourne le tableau des débits spécifiques
        z_ind = np.argmin(np.abs(self.depths_solve - z))
        # sinon ne les retourne que pour la profondeur choisie
        return self._flows[z_ind, :]

    flows_solve = property(get_flows_solve)
    # récupération des débits spécifiques au cours du temps à toutes les profondeurs (par défaut) ou bien à une profondeur donnée

    def compute_mcmc_without_sigma2(
        self,
        nb_iter: int,
        all_priors: Union[
            AllPriors,
            Sequence[
                Union[
                    LayerPriors,
                    Sequence[Union[str, float, Sequence[Union[Prior, dict]]]],
                ]
            ],
        ],
        nb_cells: int,
        quantile: Union[float, Sequence[float]] = (0.05, 0.5, 0.95),
        verbose=True,
        sigma2=1.0,
    ):
        if isinstance(quantile, Number):
            quantile = [quantile]

        def conv(layer):
            name, prof, priors = layer
            if isinstance(priors, dict):
                return (
                    name,
                    prof,
                    [Prior(*args) for args in (priors[lbl] for lbl in PARAM_LIST)],
                )
            else:
                return layer

        if not isinstance(all_priors, AllPriors):
            all_priors = AllPriors([LayerPriors(*conv(layer)) for layer in all_priors])

        dz = self._real_z[-1] / nb_cells
        _z_solve = dz / 2 + np.array([k * dz for k in range(nb_cells)])
        ind_ref = [np.argmin(np.abs(z - _z_solve)) for z in self._real_z[1:-1]]
        temp_ref = self._T_measures[:, :].T

        def compute_energy(temp: np.array):
            norm2 = np.nansum((temp - temp_ref) ** 2)
            return 0.5 * norm2 / sigma2

        def compute_log_acceptance(actual_energy: float, prev_energy: float):
            return prev_energy - actual_energy

        if verbose:
            print(
                "--- Compute Mcmc ---",
                "Priors :",
                *(f"    {prior}" for prior in all_priors),
                f"Number of cells : {nb_cells}",
                f"Number of iterations : {nb_iter}",
                "Launch Mcmc",
                sep="\n",
            )

        self._states = list()
        _temperatures = np.zeros((nb_iter + 1, nb_cells, len(self._times)), np.float32)
        _flows = np.zeros((nb_iter + 1, nb_cells, len(self._times)), np.float32)

        for _ in trange(1000, desc="Init Mcmc ", file=sys.stdout):
            init_layers = all_priors.sample()
            self.compute_solve_transi(init_layers, nb_cells, verbose=False)
            self._states.append(
                State(
                    layers=init_layers,
                    energy=compute_energy(self.temperatures_solve[ind_ref, :]),
                    ratio_accept=1,
                    sigma2_temp=sigma2,
                )
            )

        self._initial_energies = [state.energy for state in self._states]
        self._states = [min(self._states, key=attrgetter("energy"))]
        self._acceptance = np.zeros(nb_iter)

        _temperatures[0] = self.get_temperatures_solve()
        _flows[0] = self.get_flows_solve()

        nb_accepted = 0

        for i in trange(nb_iter, desc="Mcmc Computation ", file=sys.stdout):
            current_layers = all_priors.perturb(self._states[-1].layers)
            self.compute_solve_transi(current_layers, nb_cells, verbose=False)
            energy = compute_energy(self.temperatures_solve[ind_ref, :])
            log_ratio_accept = compute_log_acceptance(energy, self._states[-1].energy)
            if np.log(random()) < log_ratio_accept:
                nb_accepted += 1
                self._states.append(
                    State(
                        layers=current_layers,
                        energy=energy,
                        ratio_accept=nb_accepted / (i + 1),
                        sigma2_temp=sigma2,
                    )
                )
            else:
                self._states.append(self._states[-1])

            _temperatures[i] = self.get_temperatures_solve()
            _flows[i] = self.get_flows_solve()
            self._acceptance[i] = nb_accepted / (i + 1)

        # self.compute_solve_transi.reset()

        self._quantiles_temperatures = {
            quant: res
            for quant, res in zip(quantile, np.quantile(_temperatures, quantile, axis=0))
        }
        self._quantiles_flows = {
            quant: res
            for quant, res in zip(quantile, np.quantile(_flows, quantile, axis=0))
        }
        if verbose:
            print("Quantiles Done.")

    def compute_mcmc_with_sigma2(
        self,
        nb_iter: int,
        all_priors: Union[
            AllPriors,
            Sequence[
                Union[
                    LayerPriors,
                    Sequence[Union[str, float, Sequence[Union[Prior, dict]]]],
                ]
            ],
        ],
        nb_cells: int,
        quantile: Union[float, Sequence[float]] = (0.05, 0.5, 0.95),
        verbose=True,
        sigma2_temp_prior: Prior = Prior((0.01, np.inf), 1, lambda x: 1 / x),
    ):
        if isinstance(quantile, Number):
            quantile = [quantile]

        if not isinstance(all_priors, AllPriors):
            all_priors = AllPriors([LayerPriors(*conv(layer)) for layer in all_priors])

        dz = self._real_z[-1] / nb_cells
        _z_solve = dz / 2 + np.array([k * dz for k in range(nb_cells)])
        ind_ref = [np.argmin(np.abs(z - _z_solve)) for z in self._real_z[1:-1]]
        temp_ref = self._T_measures[:, :].T

        def compute_energy(temp: np.array, sigma2, sigma2_distrib):
            norm2 = np.nansum((temp - temp_ref) ** 2)
            return (
                0.5 * norm2 / sigma2
                + np.size(self._T_measures) * np.log(sigma2) / 2
                - np.log(sigma2_distrib(sigma2))
            )

        def compute_log_acceptance(actual_energy: float, prev_energy: float):
            return prev_energy - actual_energy

        if verbose:
            print(
                "--- Compute Mcmc ---",
                "Priors :",
                *(f"    {prior}" for prior in all_priors),
                f"Number of cells : {nb_cells}",
                f"Number of iterations : {nb_iter}",
                "Launch Mcmc",
                sep="\n",
            )

        self._states = list()
        _temperatures = np.zeros((nb_iter + 1, nb_cells, len(self._times)), np.float32)
        _flows = np.zeros((nb_iter + 1, nb_cells, len(self._times)), np.float32)

        for _ in trange(1000, desc="Init Mcmc ", file=sys.stdout):
            init_layers = all_priors.sample()
            init_sigma2_temp = sigma2_temp_prior.sample()
            self.compute_solve_transi(init_layers, nb_cells, verbose=False)
            self._states.append(
                State(
                    layers=init_layers,
                    energy=compute_energy(
                        self.temperatures_solve[ind_ref, :],
                        sigma2=init_sigma2_temp,
                        sigma2_distrib=sigma2_temp_prior.density,
                    ),
                    ratio_accept=1,
                    sigma2_temp=init_sigma2_temp,
                )
            )

        self._initial_energies = [state.energy for state in self._states]
        self._states = [min(self._states, key=attrgetter("energy"))]
        self._acceptance = np.zeros(nb_iter)

        _temperatures[0] = self.get_temperatures_solve()
        _flows[0] = self.get_flows_solve()

        nb_accepted = 0

        for i in trange(nb_iter, desc="Mcmc Computation ", file=sys.stdout):
            current_layers = all_priors.perturb(self._states[-1].layers)
            current_sigma2_temp = sigma2_temp_prior.perturb(
                self._states[-1].sigma2_temp
            )
            self.compute_solve_transi(current_layers, nb_cells, verbose=False)
            energy = compute_energy(
                self.temperatures_solve[ind_ref, :],
                sigma2=current_sigma2_temp,
                sigma2_distrib=sigma2_temp_prior.density,
            )
            log_ratio_accept = compute_log_acceptance(energy, self._states[-1].energy)
            if np.log(random()) < log_ratio_accept:
                nb_accepted += 1
                self._states.append(
                    State(
                        layers=current_layers,
                        energy=energy,
                        ratio_accept=nb_accepted / (i + 1),
                        sigma2_temp=current_sigma2_temp,
                    )
                )
            else:
                self._states.append(self._states[-1])

            _temperatures[i] = self.get_temperatures_solve()
            _flows[i] = self.get_flows_solve()
            self._acceptance[i] = nb_accepted / (i + 1)

        # self.compute_solve_transi.reset()

        self._quantiles_temperatures = {
            quant: res
            for quant, res in zip(quantile, np.quantile(_temperatures, quantile, axis=0))
        }
        self._quantiles_flows = {
            quant: res
            for quant, res in zip(quantile, np.quantile(_flows, quantile, axis=0))
        }
        if verbose:
            print("Quantiles Done.")

    def compute_dream_mcmc_without_sigma2(
        self,
        nb_iter: int,
        all_priors: Union[
            AllPriors,
            Sequence[
                Union[
                    LayerPriors,
                    Sequence[Union[str, float, Sequence[Union[Prior, dict]]]],
                ]
            ],
        ],
        nb_cells: int,
        quantile: Union[float, Sequence[float]] = (0.05, 0.5, 0.95),
        verbose=False,
        sigma2=1.0,
        nb_chain=10,
        delta=3,
        ncr=3,
        c=0.1,
        c_star=1e-6,
        n_sous_ech_iter=10,
        n_sous_ech_space=1,
        n_sous_ech_time=1,
        threshold=1.1
    ):

        process = psutil.Process()

        # vérification des types des arguments
        if isinstance(quantile, Number):
            quantile = [quantile]

        if not isinstance(all_priors, AllPriors):
            all_priors = AllPriors([LayerPriors(*conv(layer)) for layer in all_priors])

        # définition des paramètres de la simulation
        dz = self._real_z[-1] / nb_cells
        _z_solve = dz / 2 + np.array([k * dz for k in range(nb_cells)])
        ind_ref = [np.argmin(np.abs(z - _z_solve)) for z in self._real_z[1:-1]]
        temp_ref = self._T_measures[:, :].T

        # quantités des différents paramètres
        nb_layer = len(all_priors)  # nombre de couches
        nb_param = 4  # nombre de paramètres à estimer par couche
        nb_accepted = 0  # nombre de propositions acceptées
        nb_burn_in_iter = 0  # nombre d'itération de burn-in
        nb_burn_in_iter_modi = 0
        R_list = []
        R_list_modi = []
        printed_b_message = False  
        printed_b_message2 = False
        nb_burnin_list1 = []
        nb_burnin_list2 = []

        # création des bornes des paramètres
        ranges = np.empty((nb_layer, nb_param, 2))
        for l in range(nb_layer):
            for p in range(nb_param):
                ranges[l, p] = all_priors[l][p].range

        # propriétés des couches
        name_layer = [all_priors.sample()[i].name for i in range(nb_layer)]
        z_low = [all_priors.sample()[i].zLow for i in range(nb_layer)]

        _temp_act = np.zeros(
            (nb_chain, nb_cells, len(self._times)), np.float32
        )

        _energy = np.zeros(nb_chain, np.float32)

        # variables pour l'état courant
        temp_new = np.zeros(
            (nb_cells, len(self._times)), np.float32
                            )
        energy_new = 0
        X = np.array([np.array(all_priors.sample()) for _ in range(nb_chain)])
        X = np.array(
            [
                np.array([X[c][l].params for l in range(nb_layer)])
                for c in range(nb_chain)
            ]
        )  # stockage des paramètres pour l'itération en cours

        # stockage des résultats
        self._states = list()  # stockage des états à chaque itération
        self._acceptance = np.zeros(
            (nb_iter, nb_chain), np.float32
        )  # stockage des taux d'acceptation

        _params = np.zeros(
            (nb_iter + 1, nb_chain, nb_layer, nb_param), np.float32
        )  # stockage des paramètres
        _params[0] = X  # initialisation des paramètres

        # objets liés à DREAM
        cr_vec = np.arange(1, ncr + 1) / ncr
        n_id = np.zeros((nb_layer, ncr))
        J = np.zeros((nb_layer, ncr))
        pcr = np.ones((nb_layer, ncr)) / ncr

        if verbose:
            print(
                "--- Compute DREAM MCMC ---",
                "Priors :",
                *(f"    {prior}" for prior in all_priors),
                f"Number of cells : {nb_cells}",
                f"Number of iterations : {nb_iter}",
                f"Number of chains : {nb_chain}",
                "--------------------",
                sep="\n",
            )

        # initialisation des chaines
        for j in range(nb_chain):
            self.compute_solve_transi(
                convert_to_layer(nb_layer, name_layer, z_low, X[j]),
                nb_cells,
                verbose=False,
            )
            _temp_act[j] = self.get_temperatures_solve()
            _energy[j] = compute_energy(
                _temp_act[j][ind_ref, :], temp_ref, sigma2
            )
        _temp_old = np.copy(_temp_act)
        _energy_old = np.copy(_energy) # Conservation du profil précédent

        print(f"Initialisation - Utilisation de la mémoire (en Mo) : {process.memory_info().rss /1e6}")

        if verbose:
            print("--- Begin Burn in phase ---")
        for i in range(nb_iter):
            # Initialisation pour les nouveaux paramètres
            x_new = np.zeros(
                (nb_layer, nb_param), np.float32
                )
            X_new = np.zeros(
                (nb_chain, nb_layer, nb_param), np.float32
                )
            std_X = np.std(X, axis=0)  # calcul des écarts types des paramètres
            for j in range(nb_chain):
                dX = np.zeros((nb_layer, nb_param))  # perturbation DREAM
                for l in range(nb_layer):
                    # actualiation des paramètres DREAM pour la couche l
                    id = np.random.choice(ncr, p=pcr[l])
                    z = np.random.uniform(0, 1, nb_param)
                    A = z <= cr_vec[id]
                    d_star = np.sum(A)
                    if d_star == 0:
                        A[np.argmin(z)] = True
                        d_star = 1
                    lambd = np.random.uniform(-c, c, d_star)
                    zeta = np.random.normal(0, c_star, d_star)
                    choose = np.delete(np.arange(nb_chain), j)
                    a = np.random.choice(choose, delta, replace=False)
                    choose = np.delete(choose, np.where(np.isin(choose, a)))
                    b = np.random.choice(choose, delta, replace=False)

                    gamma = 2.38 / np.sqrt(2 * d_star * delta)
                    dX[l][A] = zeta + (1 + lambd) * gamma * np.sum(
                        X[a, l][:, A] - X[b, l][:, A], axis=0
                    )

                    x_new[l] = X[j, l] + dX[l]  # caclul du potentiel nouveau paramètre
                    x_new[l] = check_range(
                        x_new[l], ranges[l]
                    )  # vérification des bornes et réajustement si besoin

                # Calcul du profil de température associé aux nouveaux paramètres
                self.compute_solve_transi(
                    convert_to_layer(nb_layer, name_layer, z_low, x_new),
                    nb_cells,
                    verbose=False,
                )
                temp_new = (
                    self.get_temperatures_solve()
                )  # récupération du profil de température
                energy_new = compute_energy(
                    temp_new[ind_ref, :], temp_ref, sigma2
                )  # calcul de l'énergie

                # calcul de la probabilité d'acceptation
                log_ratio_accept = compute_log_acceptance(
                    energy_new, _energy[j]
                )

                # Acceptation ou non des nouveaux paramètres
                if np.log(np.random.uniform(0, 1)) < log_ratio_accept:
                    X_new[j] = x_new  # actualisation des paramètres pour la chaine j
                    _temp_old[j] = _temp_act[j]
                    _temp_act[j] = temp_new
                    _energy_old[j] = _energy[j]
                    _energy[j] = energy_new
                else:
                    dX = np.zeros(
                        (nb_layer, nb_param), np.float32
                        )
                    X_new[j] = X[
                        j
                    ]  # conservation des anciens paramètres pour la chaine j
                    exchange_var = _temp_act[j]
                    _temp_act[j] = _temp_old[j]
                    _temp_old[j] = exchange_var
                    
                    exchange_var = _energy[j]
                    _energy[j] = _energy_old[j]
                    _energy_old[j] = exchange_var

                # Mise à jour des paramètres de la couche j pour DREAM
                for l in range(nb_layer):
                    J[l, id] += np.sum((dX[l] / std_X[l]) ** 2)
                    n_id[l, id] += 1

            # Mise à jour du pcr pour chaque couche pour DREAM
            for l in range(nb_layer):
                pcr[l][n_id[l] != 0] = J[l][n_id[l] != 0] / n_id[l][n_id[l] != 0]
                pcr[l] = pcr[l] / np.sum(pcr[l])

            # Actualisation des paramètres à la fin de l'itération
            X = X_new
            _params[i + 1] = X_new
            # Fin d'une itération, on check si on peut sortir du burn-in
            b, R = gelman_rubin(i+2, nb_param, nb_layer, _params[:i+2], threshold=threshold)
            if not b:
                R_list.append(R)
                nb_burn_in_iter += 1
            if b and not printed_b_message:
                print(f"Burn in finished after : {nb_burn_in_iter} iterations by gelman rubin")
                printed_b_message = True  
            

            b_modi,R_modi = gelman_R_chap(i+2, nb_param, nb_layer, _params[:i+2])
            if not b_modi:
                R_list_modi.append(R_modi)
                nb_burn_in_iter_modi += 1
            if b_modi and not printed_b_message2:
                print(f"Burn in finished after : {nb_burn_in_iter_modi} iterations by modified gelman rubin")
                printed_b_message2 = True

            if b and b_modi:
                print('Both 2 model reach burn in')
                break
        
        
        self.nb_burnin_list1 = nb_burnin_list1
        self.nb_burnin_list2 = nb_burnin_list2
        self.nb_burn_in_iter = nb_burn_in_iter
        self.nb_burn_in_iter_modi = nb_burn_in_iter_modi
        self.R_list = R_list
        self.R_list_modi = R_list_modi

        # Transition après le burn in
        _params = np.zeros(
            (nb_iter + 1, nb_chain, nb_layer, nb_param), np.float32
        )  # réinitialisation des paramètres
        _params[0] = X  # initialisation des paramètres

        # Préparation du sous-échantillonnage
        nb_iter_sous_ech = int( np.ceil( (nb_iter+1) / n_sous_ech_iter))
        nb_cells_sous_ech = int( np.ceil(nb_cells / n_sous_ech_space) )
        nb_times_sous_ech = int( np.ceil(len(self._times) / n_sous_ech_time) )

        # Initialisation des flux
        _flows = np.zeros(
            (nb_iter_sous_ech, nb_chain, nb_cells_sous_ech, nb_times_sous_ech), np.float32
        ) # Flux sous-échantillonnés pour le calcul des quantiles
        _flow_act = np.zeros(
            (nb_chain, nb_cells, len(self._times)), np.float32
            ) # Flux à l'itération MCMC actuelle
        for j in range(nb_chain):
            _flow_act[j] = self.get_flows_solve() # AJOUTER LES PARAMETRES QUAND LA FONCTION SERA IMPLEMENTEE !
        _flow_old = np.copy(_flow_act) # Conservation du profil précédent
        _flows[0] = _flow_act[:, ::n_sous_ech_space, ::n_sous_ech_time]

        _temp = np.zeros(
            (nb_iter_sous_ech, nb_chain, nb_cells_sous_ech, nb_times_sous_ech), np.float32
            )
        _temp[0] = _temp_act[:, ::n_sous_ech_space, ::n_sous_ech_time]  # initialisation des températures sous-échantillonnées

        # initialisation des états
        for j in range(nb_chain):
            self._states.append(
                State(
                    layers=convert_to_layer(nb_layer, name_layer, z_low, X[j]),
                    energy=_energy[j],
                    ratio_accept=1,
                    sigma2_temp=sigma2,
                )
            )

        print(f"Initialisation post burn-in - Utilisation de la mémoire (en Mo) : {process.memory_info().rss /1e6}")

        for i in trange(nb_iter, desc="DREAM MCMC Computation", file=sys.stdout):
            # Initialisation pour les nouveaux paramètres
            x_new = np.zeros(
                (nb_layer, nb_param), np.float32
                )
            X_new = np.zeros(
                (nb_chain, nb_layer, nb_param), np.float32
                )
            std_X = np.std(X, axis=0)  # calcul des écarts types des paramètres
            for j in range(nb_chain):
                dX = np.zeros(
                    (nb_layer, nb_param), np.float32
                    )  # perturbation DREAM
                for l in range(nb_layer):
                    # actualiation des paramètres DREAM pour la couche l
                    id = np.random.choice(ncr, p=pcr[l])
                    z = np.random.uniform(0, 1, nb_param)
                    A = z <= cr_vec[id]
                    d_star = np.sum(A)
                    if d_star == 0:
                        A[np.argmin(z)] = True
                        d_star = 1
                    lambd = np.random.uniform(-c, c, d_star)
                    zeta = np.random.normal(0, c_star, d_star)
                    choose = np.delete(np.arange(nb_chain), j)
                    a = np.random.choice(choose, delta, replace=False)
                    choose = np.delete(choose, np.where(np.isin(choose, a)))
                    b = np.random.choice(choose, delta, replace=False)

                    gamma = 2.38 / np.sqrt(2 * d_star * delta)
                    dX[l][A] = zeta + (1 + lambd) * gamma * np.sum(
                        X[a, l][:, A] - X[b, l][:, A], axis=0
                    )

                    x_new[l] = X[j, l] + dX[l]  # calcul du potentiel nouveau paramètre
                    x_new[l] = check_range(
                        x_new[l], ranges[l]
                    )  # vérification des bornes et réajustement si besoin

                # Calcul du profil de température associé aux nouveaux paramètres
                self.compute_solve_transi(
                    convert_to_layer(nb_layer, name_layer, z_low, x_new),
                    nb_cells,
                    verbose=False,
                )
                temp_new = (
                    self.get_temperatures_solve()
                )  # récupération du profil de température
                energy_new = compute_energy(
                    temp_new[ind_ref, :], temp_ref, sigma2
                )  # calcul de l'énergie

                # calcul de la probabilité d'acceptation
                log_ratio_accept = compute_log_acceptance(energy_new, _energy[j])

                # Acceptation ou non des nouveaux paramètres
                if np.log(np.random.uniform(0, 1)) < log_ratio_accept:
                    X_new[j] = x_new

                    _temp_old[j] = _temp_act[j]
                    _temp_act[j] = temp_new

                    _flow_old[j] = _flow_act[j]
                    _flow_act[j] = self.get_flows_solve()

                    if (i+1) % n_sous_ech_iter == 0: 
                        # Si i+1 est un multiple de n_sous_ech_iter, on stocke
                        k = (i+1) // n_sous_ech_iter
                        _temp[k, j] = temp_new[::n_sous_ech_space, ::n_sous_ech_time]
                        _flows[k, j] = _flow_act[j, ::n_sous_ech_space, ::n_sous_ech_time]

                    _energy_old[j] = _energy[j]
                    _energy[j] = energy_new
                    nb_accepted += 1
                    self._states.append(
                        State(
                            layers=convert_to_layer(nb_layer, name_layer, z_low, x_new),
                            energy=energy_new,
                            ratio_accept=nb_accepted / (i * 10 + j + 1),
                            sigma2_temp=sigma2,
                        )
                    )
                else:
                    dX = np.zeros(
                        (nb_layer, nb_param), np.float32
                        )
                    X_new[j] = X[j]
                    exchange_var = _temp_act[j] # Variable d'échange
                    _temp_act[j] = _temp_old[j]
                    _temp_old[j] = exchange_var

                    exchange_var = _flow_act[j] # Variable d'échange
                    _flow_act[j] = _flow_old[j]
                    _flow_old[j] = exchange_var

                    if (i+1) % n_sous_ech_iter == 0:
                        # Si i+1 est un multiple de n_sous_ech_iter, on stocke
                        k = (i+1) // n_sous_ech_iter
                        _temp[k, j] = _temp_act[j][::n_sous_ech_space, ::n_sous_ech_time]
                        _flows[k, j] = _flow_act[j, ::n_sous_ech_space, ::n_sous_ech_time]

                    exchange_var = _energy[j]
                    _energy[j] = _energy_old[j]
                    _energy_old[j] = exchange_var

                    self._states.append(
                        State(
                            layers=self._states[-nb_chain].layers,
                            energy=self._states[-nb_chain].energy,
                            ratio_accept=nb_accepted / (i * 10 + j + 1),
                            sigma2_temp=sigma2,
                        )
                    )  # ajout de l'état à la liste des états
                self._acceptance[i, j] = nb_accepted / (
                    i * 10 + j + 1
                )  # mise à jour des taux d'acceptation

                # Mise à jour des paramètres de la couche j pour DREAM
                for l in range(nb_layer):
                    J[l, id] += np.sum((dX[l] / std_X[l]) ** 2)
                    n_id[l, id] += 1

            # Actualisation des paramètres à la fin de l'itération
            X = X_new
            _params[i + 1] = X_new

        # Calcul des quantiles pour la température
        _temp = _temp.reshape(nb_iter_sous_ech * nb_chain, nb_cells_sous_ech, nb_times_sous_ech)
        _flows = _flows.reshape(nb_iter_sous_ech * nb_chain, nb_cells_sous_ech, nb_times_sous_ech)

        print("Occupation mémoire des températures (en Mo) : ", _temp.nbytes/1e6)
        print("Occupation mémoire des flux (en Mo) : ", _flows.nbytes/1e6)

        print(f"Fin itérations MCMC, avant le calcul des quantiles - Utilisation de la mémoire (en Mo) : {process.memory_info().rss /1e6}")

        self._quantiles_temperatures = {
            quant: res
            for quant, res in zip(quantile, np.quantile(_temp, quantile, axis=0))
        }
        
        self._quantiles_flows = {
            quant: res
            for quant, res in zip(quantile, np.quantile(_flows, quantile, axis=0))
        }

        if verbose:
            print("Quantiles computed")

        print(f"Fin de l'exécution - Utilisation de la mémoire (en Mo) : {process.memory_info().rss / 1e6}")

    @checker
    def compute_mcmc(
        self,  # la colonne
        nb_iter: int,
        all_priors: Union[
            AllPriors,
            Sequence[
                Union[
                    LayerPriors,
                    Sequence[Union[str, float, Sequence[Union[Prior, dict]]]],
                ]
            ],
        ],
        nb_cells: int,  # le nombre de cellules de la colonne
        # les quantiles pour l'affichage de stats sur les valeurs de température
        quantile: Union[float, Sequence[float]] = (0.05, 0.5, 0.95),
        nb_chain: int = 10,
        delta=2,
        ncr=3,
        c=0.1,
        cstar=1e-6,
        verbose=True,  # affiche texte explicatifs ou non
        sigma2=None,
        sigma2_temp_prior: Prior = Prior((0.01, np.inf), 1, lambda x: 1 / x),
    ):
        if nb_chain < 2:
            if sigma2 is None:
                self.compute_mcmc_with_sigma2(
                    nb_iter, all_priors, nb_cells, quantile, verbose, sigma2_temp_prior
                )
            else:
                self.compute_mcmc_without_sigma2(
                    nb_iter, all_priors, nb_cells, quantile, verbose, sigma2
                )
        else:
            self.compute_dream_mcmc_without_sigma2(
                nb_iter,
                all_priors,
                nb_cells,
                quantile,
                verbose,
                sigma2,
                nb_chain,
                delta,
                ncr,
                c,
                cstar,
            )

    # erreur si pas déjà éxécuté compute_mcmc, sinon l'attribut pas encore affecté à une valeur
    @compute_mcmc.needed
    def get_depths_mcmc(self):
        return (
            self._z_solve
        )  # NF 15/9/2022 only used in MolonaviZ where we want all cell coordinates, as stated in the API. Never used in pyheatme so no bug following the change

    depths_mcmc = property(get_depths_mcmc)

    # erreur si pas déjà éxécuté compute_mcmc, sinon l'attribut pas encore affecté à une valeur
    @compute_mcmc.needed
    def get_times_mcmc(self):
        return self._times

    times_mcmc = property(get_times_mcmc)

    # erreur si pas déjà éxécuté compute_mcmc, sinon l'attribut pas encore affecté à une valeur
    @compute_mcmc.needed
    def sample_param(self):
        # retourne aléatoirement un des couples de paramètres parlesquels est passé la MCMC
        return choice(
            [[layer.params for layer in state.layers] for state in self._states]
        )

    # erreur si pas déjà éxécuté compute_mcmc, sinon l'attribut pas encore affecté à une valeur
    @compute_mcmc.needed
    def get_best_param(self):
        """return the params that minimize the energy"""
        return [
            layer.params for layer in min(self._states, key=attrgetter("energy")).layers
        ]  # retourne le couple de paramètres minimisant l'énergie par lequels est passé la MCMC

    @compute_mcmc.needed
    def get_best_sigma2(self):
        """return the best sigma that minimizes the energy"""
        return min(self._states, key=attrgetter("energy")).sigma2_temp

    @compute_mcmc.needed
    def get_best_layers(self):
        """return the params that minimize the energy"""
        return min(self._states, key=attrgetter("energy")).layers

    # erreur si pas déjà éxécuté compute_mcmc, sinon l'attribut pas encore affecté à une valeur
    @compute_mcmc.needed
    def get_all_params(self):
        n_layers = len(self._layersList)
        n_params = len(self._layersList[0].params)
        n_states = len(self._states)
        res = np.empty((n_layers, n_states, n_params))
        for i in range(n_layers):
            for j, state in enumerate(self._states):
                res[i][j] = np.array(state.layers[i].params)
        return res

    all_params = property(get_all_params)

    # erreur si pas déjà éxécuté compute_mcmc, sinon l'attribut pas encore affecté à une valeur
    @compute_mcmc.needed
    def get_all_moinslog10IntrinK(self):
        # retourne toutes les valeurs de moinslog10IntrinK (K : perméabilité) par lesquels est passé la MCMC
        return [
            [layer.params.moinslog10IntrinK for layer in state.layers]
            for state in self._states
        ]

    all_moinslog10IntrinK = property(get_all_moinslog10IntrinK)

    # erreur si pas déjà éxécuté compute_mcmc, sinon l'attribut pas encore affecté à une valeur
    @compute_mcmc.needed
    def get_all_n(self):
        # retourne toutes les valeurs de n (n : porosité) par lesquels est passé la MCMC
        return [[layer.params.n for layer in state.layers] for state in self._states]

    all_n = property(get_all_n)

    # erreur si pas déjà éxécuté compute_mcmc, sinon l'attribut pas encore affecté à une valeur
    @compute_mcmc.needed
    def get_all_lambda_s(self):
        # retourne toutes les valeurs de lambda_s (lambda_s : conductivité thermique du solide) par lesquels est passé la MCMC
        return [
            [layer.params.lambda_s for layer in state.layers] for state in self._states
        ]

    all_lambda_s = property(get_all_lambda_s)

    # erreur si pas déjà éxécuté compute_mcmc, sinon l'attribut pas encore affecté à une valeur
    @compute_mcmc.needed
    def get_all_rhos_cs(self):
        # retourne toutes les valeurs de rho_cs (rho_cs : produite de la densité par la capacité calorifique spécifique du solide) par lesquels est passé la MCMC
        return [
            [layer.params.rhos_cs for layer in state.layers] for state in self._states
        ]

    all_rhos_cs = property(get_all_rhos_cs)

    # erreur si pas déjà éxécuté compute_mcmc, sinon l'attribut pas encore affecté à une valeur
    @compute_mcmc.needed
    def get_all_sigma2(self):
        return [state.sigma2_temp for state in self._states]

    all_sigma = property(get_all_sigma2)

    @compute_mcmc.needed
    def get_all_energy(self):
        return self._initial_energies + [state.energy for state in self._states]

    all_energy = property(get_all_energy)

    @compute_mcmc.needed
    # retourne toutes les valeurs d'acceptance empirique par lesquels est passée la MCMC
    def get_all_acceptance_ratio(self):
        return self._acceptance

    all_acceptance_ratio = property(get_all_acceptance_ratio)

    @compute_mcmc.needed
    def get_quantiles(self):
        return self._quantiles_temperatures.keys()

    # erreur si pas déjà éxécuté compute_mcmc, sinon l'attribut pas encore affecté à une valeur
    @compute_mcmc.needed
    def get_temperatures_quantile(self, quantile):
        return self._quantiles_temperatures[quantile]
        # retourne les valeurs des températures en fonction du temps selon le quantile demandé

    # erreur si pas déjà éxécuté compute_mcmc, sinon l'attribut pas encore affecté à une valeur
    @compute_mcmc.needed
    def get_flows_quantile(self, quantile):
        return self._quantiles_flows[quantile]

    @compute_mcmc.needed
    def get_RMSE_quantile(self, quantile):
        # Number of sensors (except boundary conditions : river and aquifer)
        nb_sensors = len(self._T_measures[0])

        # Number of times for which we have measures
        nb_times = len(self._T_measures)

        # Array of RMSE for each sensor
        list_RMSE = np.array(
            [
                np.sqrt(
                    np.nansum(
                        (self.get_temperatures_quantile(quantile)[id, :] - temperatures_obs) ** 2
                    )
                    / nb_times
                )
                for id, temperatures_obs in zip(self.get_id_sensors(), self._T_measures.T)
            ]
        )

        # Total RMSE
        total_RMSE = np.sqrt(np.sum(list_RMSE**2) / nb_sensors)

        return np.append(list_RMSE, total_RMSE)

    def plot_CALC_results(self, fontsize=15):
        time_array = np.array(
            [
                (self._times[j + 1] - self._times[j]).total_seconds()
                for j in range(len(self._times) - 1)
            ]
        )
        K_offset = 273.15
        nb_cells = len(self._z_solve)
        n_sens = len(self.depth_sensors) - 1
        dz = self._real_z[-1] / nb_cells

        """Changement de l'échelle de l'axe x"""

        def min2jour(x):
            return x / (4 * 24)

        def jour2min(x):
            return x * (4 * 24)

        """Plots des profils de température"""

        fig, ax = plt.subplots(2, 3, sharey=False, figsize=(22, 14))
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
        ax[0, 0].set_xlabel("t (15min)", fontsize=fontsize)
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

        """Plots des frises"""

        im0 = ax[0, 2].imshow(
            self._temperatures[:, :nt] - K_offset, aspect="auto", cmap="Spectral_r"
        )
        ax[0, 2].set_xlabel("t (15min)", fontsize=fontsize)
        ax[0, 2].set_ylabel("z (m)", fontsize=fontsize)
        ax[0, 2].xaxis.tick_top()
        ax[0, 2].xaxis.set_label_position("top")
        ax[0, 2].secax = ax[0, 2].secondary_xaxis(
            "bottom", functions=(min2jour, jour2min)
        )
        ax[0, 2].secax.set_xlabel("t (jour)", fontsize=fontsize)
        cbar0 = fig.colorbar(im0, ax=ax[0, 2], shrink=1, location="right")
        cbar0.set_label("Température (°C)", fontsize=fontsize)
        ax[0, 2].set_title("Frise température MD", fontsize=fontsize, pad=20)

        im1 = ax[1, 0].imshow(
            self.get_conduc_flows_solve()[:, :nt], aspect="auto", cmap="Spectral_r"
        )
        ax[1, 0].set_xlabel("t (15min)", fontsize=fontsize)
        ax[1, 0].set_ylabel("z (m)", fontsize=fontsize)
        ax[1, 0].xaxis.tick_top()
        ax[1, 0].xaxis.set_label_position("top")
        ax[1, 0].secax = ax[1, 0].secondary_xaxis(
            "bottom", functions=(min2jour, jour2min)
        )
        ax[1, 0].secax.set_xlabel("t (jour)", fontsize=fontsize)
        cbar1 = fig.colorbar(im1, ax=ax[1, 0], shrink=1, location="right")
        cbar1.set_label("Flux conductif (W/m²)", fontsize=fontsize)
        ax[1, 0].set_title("Frise Flux conductif MD", fontsize=fontsize, pad=20)

        im2 = ax[1, 1].imshow(
            self.get_advec_flows_solve()[:, :nt], aspect="auto", cmap="Spectral_r"
        )
        ax[1, 1].set_xlabel("t (15min)", fontsize=fontsize)
        ax[1, 1].set_ylabel("z (m)", fontsize=fontsize)
        ax[1, 1].xaxis.tick_top()
        ax[1, 1].xaxis.set_label_position("top")
        ax[1, 1].secax = ax[1, 1].secondary_xaxis(
            "bottom", functions=(min2jour, jour2min)
        )
        ax[1, 1].secax.set_xlabel("t (jour)", fontsize=fontsize)
        cbar2 = fig.colorbar(im2, ax=ax[1, 1], shrink=1, location="right")
        cbar2.set_label("Flux advectif (W/m²)", fontsize=fontsize)
        ax[1, 1].set_title("Frise Flux advectif MD", fontsize=fontsize, pad=20)

        im3 = ax[1, 2].imshow(
            self.get_flows_solve()[:, :nt], aspect="auto", cmap="Spectral_r"
        )
        ax[1, 2].set_xlabel("t (15min)", fontsize=fontsize)
        ax[1, 2].set_ylabel("z (m)", fontsize=fontsize)
        ax[1, 2].xaxis.tick_top()
        ax[1, 2].xaxis.set_label_position("top")
        ax[1, 2].secax = ax[1, 2].secondary_xaxis(
            "bottom", functions=(min2jour, jour2min)
        )
        ax[1, 2].secax.set_xlabel("t (jour)", fontsize=fontsize)
        cbar3 = fig.colorbar(im3, ax=ax[1, 2], shrink=1, location="right")
        cbar3.set_label("Water flow (m/s)", fontsize=fontsize)
        ax[1, 2].set_title("Frise Flux d'eau MD", fontsize=fontsize, pad=20)