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
        Prior_IntrinK: Prior = None, # Prior sur IntrinK, c'est un tuple ex: (range=(9, 15), sigma= 0.1)
        Prior_n: Prior = None,
        Prior_lambda_s: Prior = None,
        Prior_rhos_cs: Prior = None,
        Prior_q_s: Prior = None,
    ):
        # Voir si tout ça ne peut pas être simplifié avec un @dataclass

        self.name = name
        self.zLow = zLow
       
        # On stocke les priors
        self.Prior_IntrinK = Prior_IntrinK
        self.Prior_n = Prior_n
        self.Prior_lambda_s = Prior_lambda_s
        self.Prior_rhos_cs = Prior_rhos_cs
        self.Prior_q_s = Prior_q_s
        self.Prior_list = [Prior_IntrinK, Prior_n, Prior_lambda_s, Prior_rhos_cs, Prior_q_s]

        # On crée un tuple de paramètres physiques initiaux
        physical_params = Param(IntrinK, n, lambda_s, rhos_cs, q_s)
        
        # On crée l'attribut mcmc_params en traduisant les valeurs physiques initiales
        # vers l'espace de travail de la MCMC..
        mcmc_vals = [
            # Si un prior existe, on l'utilise pour traduire la valeur.
            prior.physical_to_mcmc(val) if prior is not None else val
            # Sinon (si prior est None), on considère que la valeur MCMC est la même que la valeur physique.
            for prior, val in zip(self.Prior_list, physical_params)
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
            for prior, val in zip(self.Prior_list, self.mcmc_params)
        ]
        self.mcmc_params = Param(*perturbed_vals)
        
    def __repr__(self) -> str:
        return self.name + f" : ends at {self.zLow} m. " + self.mcmc_params.__repr__()
    
    def set_priors_from_dict(self, priors_dict):
        """Assigne les priors depuis un dictionnaire."""
        self.Prior_IntrinK = Prior(*priors_dict['Prior_IntrinK'])
        self.Prior_n = Prior(*priors_dict['Prior_n'])
        self.Prior_lambda_s = Prior(*priors_dict['Prior_lambda_s'])
        self.Prior_rhos_cs = Prior(*priors_dict['Prior_rhos_cs'])
        self.Prior_q_s = Prior(*priors_dict['Prior_q_s'])
        self.Prior_list = [self.Prior_IntrinK, self.Prior_n, self.Prior_lambda_s, self.Prior_rhos_cs, self.Prior_q_s]
        
        # Il faut aussi mettre à jour les mcmc_params lorsque les priors sont assignés !
        physical_params = self.get_physical_params()
        mcmc_vals = [
            prior.physical_to_mcmc(val) if prior is not None else val
            for prior, val in zip(self.Prior_list, physical_params)
        ]
        self.mcmc_params = Param(*mcmc_vals)
    
    @classmethod
    def from_dict(cls, monolayer_dict):
        return cls(**monolayer_dict)

    def get_physical_params(self, mcmc_params=None):
        """
        Retourne les paramètres en valeurs PHYSIQUES.
        Cette version est maintenant tolérante à l'absence de Priors.
        """
        if mcmc_params is None:
            mcmc_params = self.mcmc_params

        # CORRECTION : On rend la traduction inverse conditionnelle.
        physical_vals = [
            # Si un prior existe, on l'utilise pour traduire la valeur.
            prior.mcmc_to_physical(val) if prior is not None else val
            # Sinon (si prior est None), on considère que la valeur est déjà physique.
            for prior, val in zip(self.Prior_list, mcmc_params)
        ]
        return Param(*physical_vals)


def getListParameters(layersList, nbCells: int):
    """
    Renvoie les profils des paramètres physiques dans la colonne discrétisée, avec les valeurs Physiques
    """
    dz = layersList[-1].zLow / nbCells
    cell_centers = np.linspace(dz / 2, layersList[-1].zLow - dz / 2, nbCells)
    listParameters = np.zeros((nbCells, 5))
    zLow_prev = 0
    for layer in layersList:
        # On demande à la couche ses paramètres en format PHYSIQUE.
        physical_params = layer.get_physical_params()
        
        mask = (cell_centers > zLow_prev) & (cell_centers <= layer.zLow)
        # On assigne directement le tuple de valeurs physiques.
        # La première colonne sera IntrinK, la dernière sera q_s.
        listParameters[mask, :] = physical_params
        
        zLow_prev = layer.zLow
        
    return (
        listParameters[:, 0], # IntrinK
        listParameters[:, 1], # n
        listParameters[:, 2], # lambda_s
        listParameters[:, 3], # rhos_cs
        listParameters[:, 4], # q_s
    )

# Add-on function to create the list of layers.
def layersListCreator(layers_spec):
    """
    Construct and return a list of Layer instances.

    Accepts:
    - layers_spec: iterable of tuples or dicts describing each layer.
      If an element is a dict, Layer.from_dict is used.
      If an element is a sequence, it is passed to Layer(*sequence).

    Expected tuple order (compatible with existing calls):
      (name, zLow, IntrinK, n, lambda_s, rhos_cs[, q_s])

    Returns:
      list of Layer
    """
    layers = []
    for spec in layers_spec:
        if isinstance(spec, dict):
            layer = Layer.from_dict(spec)
        else:
            # allow lists/tuples with the exact arguments for Layer.__init__
            layer = Layer(*spec)
        layers.append(layer)
    return layers
