import numpy as np
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
        moinslog10IntrinK: float = None,
        n: float = None,
        lambda_s: float = None,
        rhos_cs: float = None,
        Prior_moinslog10IntrinK: Prior = None, # Prior sur moinslog10IntrinK, c'est un tuple ex: (range=(9, 15), sigma= 0.1)
        Prior_n: Prior = None,
        Prior_lambda_s: Prior = None,
        Prior_rhos_cs: Prior = None,
    ):
        # Voir si tout ça ne peut pas être simplifié avec un @dataclass

        self.name = name
        self.zLow = zLow
        self.params = Param(moinslog10IntrinK, n, lambda_s, rhos_cs)
        self.Prior_moinslog10IntrinK = Prior_moinslog10IntrinK
        self.Prior_n = Prior_n
        self.Prior_lambda_s = Prior_lambda_s
        self.Prior_rhos_cs = Prior_rhos_cs
        self.Prior_list = [Prior_moinslog10IntrinK, Prior_n, Prior_lambda_s, Prior_rhos_cs]

    


    def sample(self):
        return Param(*(prior.sample() for prior in self.Prior_list))
    
    def perturb(self, param):
        return Param(*(prior.perturb(val) for prior, val in zip(self.Prior_list, param)))

    def __repr__(self) -> str:
        return self.name + f" : ends at {self.zLow} m. " + self.params.__repr__()
    
    def set_priors_from_dict(self, priors_dict):    
        # a method that expect an input similar to 
        # priors = {
        #   "Prior_moinslog10IntrinK": ((10, 15), .01), 
        #   "Prior_n": ((.01, .25), .01),  
        #   "Prior_lambda_s": ((1, 10), .1), 
        #   "Prior_rhos_cs": ((1e6,1e7), 1e5)
        #}

        self.Prior_moinslog10IntrinK = Prior(*priors_dict['Prior_moinslog10IntrinK'])
        self.Prior_n = Prior(*priors_dict['Prior_n'])
        self.Prior_lambda_s = Prior(*priors_dict['Prior_lambda_s'])
        self.Prior_rhos_cs = Prior(*priors_dict['Prior_rhos_cs'])
        self.Prior_list = [self.Prior_moinslog10IntrinK, self.Prior_n, self.Prior_lambda_s, self.Prior_rhos_cs]
    

    @classmethod
    def from_dict(cls, monolayer_dict):
        return cls(**monolayer_dict)
    
def allPriors(layersList):  # Inutile ? Normalement déjà présent dans column
    """
    Return a list of all priors in layersList
    """
    return [layer.Prior_list for layer in layersList]


def layersListCreator(layersListInput): # Inutile
    layersList = list()
    for name, zLow, moinslog10IntrinK, n, lambda_s, rhos_cs in layersListInput:
        layersList.append(Layer(name, zLow, moinslog10IntrinK, n, lambda_s, rhos_cs))
    return layersList


def sortLayersList(layersList): # Inutile
    """
    Return a sorted list of layers (sorted by zLow)
    """
    return sorted(layersList, key=lambda x: x.zLow)


def getListParameters(layersList, nbCells: int):    # Inutile
    dz = layersList[-1].zLow / nbCells
    currentAltitude = dz / 2
    listParameters = list()
    for layer in layersList:
        while currentAltitude < layer.zLow:
            listParameters.append(
                [
                    layer.params.moinslog10IntrinK,
                    layer.params.n,
                    layer.params.lambda_s,
                    layer.params.rhos_cs,
                ]
            )
            currentAltitude += dz
    listParameters = np.array(listParameters)
    return (
        listParameters[:, 0],
        listParameters[:, 1],
        listParameters[:, 2],
        listParameters[:, 3],
    )

