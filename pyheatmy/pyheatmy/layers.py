import numpy as np
from typing import Sequence

from pyheatmy.params import Param, Prior, ParamsPriors


class Layer:
    def __init__(
        self,
        name: str,
        zLow: float,
        moinslog10K: float,
        n: float,
        lambda_s: float,
        rhos_cs: float,
    ):
        self.name = name
        self.zLow = zLow
        self.params = Param(moinslog10K, n, lambda_s, rhos_cs)

    def __repr__(self) -> str:
        return self.name + f" : ends at {self.zLow} m. " + self.params.__repr__()

    @classmethod
    def from_dict(cls, monolayer_dict):
        return cls(**monolayer_dict)


class LayerPriors(ParamsPriors):
    """Rassemble tout les priors relatfifs aux params d'une couche"""

    def __init__(self, name: str, z_low: float, priors: Sequence[Prior]):
        ParamsPriors.__init__(self, priors)
        self.name = name
        self.z_low = z_low

    def perturb(self, layer):
        return Layer(self.name, self.z_low, *ParamsPriors.perturb(self, layer.params))

    def sample(self):
        return Layer(self.name, self.z_low, *ParamsPriors.sample(self))


class AllPriors:
    def __init__(self, all_priors: Sequence[LayerPriors]):
        self.layered_prior_list = all_priors

    def sample(self):
        return [prior.sample() for prior in self.layered_prior_list]

    def perturb(self, param):
        return [
            prior.perturb(val) for prior, val in zip(self.layered_prior_list, param)
        ]

    def __iter__(self):
        return self.layered_prior_list.__iter__()

    def __getitem__(self, key):
        return self.layered_prior_list[key]

    def __repr__(self):
        return self.layered_prior_list.__repr__()

    def __len__(self):
        return self.layered_prior_list.__len__()


def layersListCreator(layersListInput):
    layersList = list()
    for name, zLow, moinslog10K, n, lambda_s, rhos_cs in layersListInput:
        layersList.append(Layer(name, zLow, moinslog10K, n, lambda_s, rhos_cs))
    return layersList


def sortLayersList(layersList):
    """
    Return a sorted list of layers (sorted by zLow)
    """
    return sorted(layersList, key=lambda x: x.zLow)


def getListParameters(layersList, nbCells: int):
    dz = layersList[-1].zLow / nbCells
    currentAltitude = dz / 2
    listParameters = list()
    for layer in layersList:
        while currentAltitude < layer.zLow:
            listParameters.append(
                [
                    layer.params.moinslog10K,
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
