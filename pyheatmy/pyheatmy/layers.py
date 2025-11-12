import numpy as np
from copy import deepcopy
from typing import Sequence, Callable
from random import uniform, gauss
from collections import namedtuple
from dataclasses import dataclass
from random import uniform, gauss
from numpy import inf
from pyheatmy.config import *

from pyheatmy.params import Param, Prior


class Layer:
    def __init__(
        self,
        name: str,
        zLow: float,  # profondeur en m du bas de la couche (>0)
        moinslog10IntrinK: float = MOINSLOG10INTRINK_DEFAULT,
        n: float = N_DEFAULT,
        lambda_s: float = LAMBDA_S_DEFAULT,
        rhos_cs: float = RHOS_CS_DEFAULT,
        q: float = Q_DEFAULT,
        Prior_moinslog10IntrinK: Prior = None,  # Prior sur moinslog10IntrinK, c'est un tuple ex: (range=(9, 15), sigma= 0.1)
        Prior_n: Prior = None,
        Prior_lambda_s: Prior = None,
        Prior_rhos_cs: Prior = None,
        Prior_q: Prior = None,
    ):
        # Voir si tout ça ne peut pas être simplifié avec un @dataclass

        self.name = name
        self.zLow = zLow
        self.params = Param(moinslog10IntrinK, n, lambda_s, rhos_cs, q)
        self.Prior_moinslog10IntrinK = Prior_moinslog10IntrinK
        self.Prior_n = Prior_n
        self.Prior_lambda_s = Prior_lambda_s
        self.Prior_rhos_cs = Prior_rhos_cs
        self.Prior_q = Prior_q
        self.Prior_list = [
            Prior_moinslog10IntrinK,
            Prior_n,
            Prior_lambda_s,
            Prior_rhos_cs,
            Prior_q,
        ]

    def sample(self):
        return Param(*(prior.sample() for prior in self.Prior_list))

    def perturb(self, param):
        return Param(
            *(prior.perturb(val) for prior, val in zip(self.Prior_list, param))
        )

    def __repr__(self) -> str:
        return self.name + f" : ends at {self.zLow} m. " + self.params.__repr__()

    def set_priors_from_dict(self, priors_dict):
        # a method that expect an input similar to
        # priors = {
        #   "Prior_moinslog10IntrinK": ((10, 15), .01),
        #   "Prior_n": ((.01, .25), .01),
        #   "Prior_lambda_s": ((1, 10), .1),
        #   "Prior_rhos_cs": ((1e6,1e7), 1e5)
        # }

        self.Prior_moinslog10IntrinK = Prior(*priors_dict["Prior_moinslog10IntrinK"])
        self.Prior_n = Prior(*priors_dict["Prior_n"])
        self.Prior_lambda_s = Prior(*priors_dict["Prior_lambda_s"])
        self.Prior_rhos_cs = Prior(*priors_dict["Prior_rhos_cs"])
        self.Prior_q = Prior(*priors_dict["Prior_q"])
        self.Prior_list = [
            self.Prior_moinslog10IntrinK,
            self.Prior_n,
            self.Prior_lambda_s,
            self.Prior_rhos_cs,
            self.Prior_q,
        ]

    @classmethod
    def from_dict(cls, monolayer_dict):
        return cls(**monolayer_dict)


# Dans le fichier pyheatmy/layers.py


def getListParameters(layersList, nb_cells):
    """
    Crée des listes de paramètres physiques pour chaque cellule de la colonne.
    Cette version corrigée gère correctement le cas multi-couches.
    """
    # Initialise des listes vides pour chaque paramètre
    moinslog10IntrinK_list = np.zeros(nb_cells)
    n_list = np.zeros(nb_cells)
    lambda_s_list = np.zeros(nb_cells)
    rhos_cs_list = np.zeros(nb_cells)
    q_list = np.zeros(nb_cells)

    # Calcule la profondeur de chaque cellule
    dz = layersList[-1].zLow / nb_cells
    z_centers = dz / 2 + np.arange(nb_cells) * dz

    # Parcourt chaque couche et assigne ses paramètres aux bonnes cellules
    current_z = 0.0
    for layer in layersList:
        # Détermine les indices des cellules appartenant à cette couche
        indices = np.where((z_centers > current_z) & (z_centers <= layer.zLow))

        # Récupère les paramètres de la couche
        moinslog10IntrinK, n, lambda_s, rhos_cs, q = layer.params

        # Assigne les paramètres à ces cellules
        moinslog10IntrinK_list[indices] = moinslog10IntrinK
        n_list[indices] = n
        lambda_s_list[indices] = lambda_s
        rhos_cs_list[indices] = rhos_cs
        q_list[indices] = q

        # Met à jour la profondeur de départ pour la couche suivante
        current_z = layer.zLow

    return moinslog10IntrinK_list, n_list, lambda_s_list, rhos_cs_list, q_list
