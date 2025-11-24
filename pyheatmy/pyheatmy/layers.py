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
        IntrinK: float = INTRINK_DEFAULT, 
        n: float = N_DEFAULT,
        lambda_s: float = LAMBDA_S_DEFAULT,
        rhos_cs: float = RHOS_CS_DEFAULT,
        q_s: float = Q_S_DEFAULT, 
        Prior_IntrinK: Prior = None, 
        Prior_n: Prior = None,
        Prior_lambda_s: Prior = None,
        Prior_rhos_cs: Prior = None,
        Prior_q_s: Prior = None, 
    ):
        self.name = name
        self.zLow = zLow
       
        # On stocke les priors
        self.Prior_IntrinK = Prior_IntrinK
        self.Prior_n = Prior_n
        self.Prior_lambda_s = Prior_lambda_s
        self.Prior_rhos_cs = Prior_rhos_cs
        self.Prior_q_s = Prior_q_s
        self.Prior_list = [Prior_IntrinK, Prior_n, Prior_lambda_s, Prior_rhos_cs, Prior_q_s]

        # On crée un tuple de paramètres physiques initiaux (VALEURS BRUTES)
        # Cela permet de stocker l'état initial physique voulu par l'utilisateur
        self._initial_physical_params = Param(IntrinK, n, lambda_s, rhos_cs, q_s)
       

        mcmc_vals = [
            prior.physical_to_mcmc(val) if prior is not None else val
            for prior, val in zip(self.Prior_list, self._initial_physical_params)
        ]
        self.mcmc_params = Param(*mcmc_vals)

    def sample(self):
        """Met à jour mcmc_params avec des valeurs initiales tirées des priors."""
        sampled_vals = [prior.sample() for prior in self.Prior_list]
        self.mcmc_params = Param(*sampled_vals)
   
    def perturb(self, param):
        """Met à jour mcmc_params en appliquant une perturbation à chaque valeur."""
        perturbed_vals = [
            prior.perturb(val)
            for prior, val in zip(self.Prior_list, param)
        ]
        self.mcmc_params = Param(*perturbed_vals)
       
    def __repr__(self) -> str:
        # On affiche les paramètres physiques pour la lisibilité
        return self.name + f" : ends at {self.zLow} m. Params Physiques: " + self.get_physical_params().__repr__()
   
    
    def set_priors_from_dict(self, priors_dict):
        """Assigne les priors depuis un dictionnaire."""
        
        
       
        # On tente de récupérer avec les nouveaux noms, sinon on fallback sur les anciens si nécessaire
        self.Prior_IntrinK = Prior(*priors_dict.get('Prior_IntrinK', priors_dict.get('Prior_moinslog10IntrinK')))
        self.Prior_n = Prior(*priors_dict['Prior_n'])
        self.Prior_lambda_s = Prior(*priors_dict['Prior_lambda_s'])
        self.Prior_rhos_cs = Prior(*priors_dict['Prior_rhos_cs'])
        self.Prior_q_s = Prior(*priors_dict.get('Prior_q_s', priors_dict.get('Prior_q')))
       
        self.Prior_list = [self.Prior_IntrinK, self.Prior_n, self.Prior_lambda_s, self.Prior_rhos_cs, self.Prior_q_s]
       

        mcmc_vals = [
            prior.physical_to_mcmc(val) if prior is not None else val
            for prior, val in zip(self.Prior_list, self._initial_physical_params)
        ]
        self.mcmc_params = Param(*mcmc_vals)
   
    @classmethod
    def from_dict(cls, monolayer_dict):
        return cls(**monolayer_dict)

    def get_physical_params(self, mcmc_params=None):
        """
        Retourne les paramètres en valeurs PHYSIQUES.
        C'est cette fonction qui est appelée par le simulateur (core.py).
        Elle traduit les paramètres de travail (MCMC) en paramètres réels.
        """
        if mcmc_params is None:
            mcmc_params = self.mcmc_params

        physical_vals = [
            # Si un prior existe, on l'utilise pour traduire la valeur (ex: 10**x).
            prior.mcmc_to_physical(val) if prior is not None else val
            # Sinon, on considère que la valeur est déjà physique.
            for prior, val in zip(self.Prior_list, mcmc_params)
        ]
        return Param(*physical_vals)


def getListParameters(layersList, nbCells: int):
    """
    Renvoie les profils des paramètres physiques dans la colonne discrétisée.
    Utilise get_physical_params() pour assurer que Core reçoit des valeurs physiques (ex: K linéaire).
    """
    dz = layersList[-1].zLow / nbCells
    cell_centers = np.linspace(dz / 2, layersList[-1].zLow - dz / 2, nbCells)
   
    # 5 paramètres : IntrinK, n, lambda_s, rhos_cs, q_s
    listParameters = np.zeros((nbCells, 5))
   
    zLow_prev = 0
    for layer in layersList:
        # On demande à la couche ses paramètres en format PHYSIQUE.
        physical_params = layer.get_physical_params()
       
        mask = (cell_centers > zLow_prev) & (cell_centers <= layer.zLow)
       
        # On assigne directement le tuple de valeurs physiques.
        listParameters[mask, :] = physical_params
       
        zLow_prev = layer.zLow
       
    return (
        listParameters[:, 0], # IntrinK
        listParameters[:, 1], # n
        listParameters[:, 2], # lambda_s
        listParameters[:, 3], # rhos_cs
        listParameters[:, 4], # q_s
    )

# Fonction utilitaire du prof conservée
def layersListCreator(layers_spec):
    """
    Construct and return a list of Layer instances.
    Accepts iterable of tuples or dicts.
    """
    layers = []
    for spec in layers_spec:
        if isinstance(spec, dict):
            layer = Layer.from_dict(spec)
        else:
            layer = Layer(*spec)
        layers.append(layer)
    return layers