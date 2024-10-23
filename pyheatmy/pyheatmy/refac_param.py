from collections import namedtuple
from dataclasses import dataclass
from random import uniform, gauss
from numpy import inf
from typing import Callable, Sequence
from pyheatmy.config import *


         
def cst(x):
    return 1.0  # fonction de densité par défaut


@dataclass
class Prior:
    range: tuple
    sigma: float
    # Callable est un type de fonction, [float] est la liste des arguments que prend la fonction et float est le type de la sortie de la fonction
    density: Callable[[float], float] = cst

    def perturb(self, val):  # perturbe la valeur d'un paramètre en respectant le prior
        # perturbation dans le  cadre d'une mcmc classique
        new_val = val + gauss(0, self.sigma)
        while new_val > self.range[RangeType.MAX.value]:
            new_val = self.range[RangeType.MIN.value] + (new_val - self.range[1]) % (
                self.range[RangeType.MAX.value] - self.range[RangeType.MIN.value]
            )
        while new_val < self.range[RangeType.MIN.value]:
            new_val = self.range[RangeType.MAX.value] - (self.range[RangeType.MIN.value] - new_val) % (
                self.range[RangeType.MAX.value] - self.range[RangeType.MIN.value]
            )
        return new_val

    def sample(self):  # retourne de manière uniforme un nombre de l'intervalle
        if self.range[RangeType.MIN.value] > -inf and self.range[RangeType.MAX.value] < inf:
            return uniform(*self.range)
        elif self.range[RangeType.MIN.value] > -inf:
            # better choices possible : arctan(uniform)
            return 1 / uniform(self.range[RangeType.MIN.value], PARAMBOUND)
        elif self.range[RangeType.MAX.value] < inf:
            return 1 / uniform(-PARAMBOUND, self.range[RangeType.MAX.value])
        else:
            1 / uniform(-PARAMBOUND, PARAMBOUND)

    def __repr__(self) -> str:
        return (
            f"Prior sur une valeure qui évolue entre {self.range[RangeType.MIN.value]} et {self.range[1]}"
        )


# The repr() function returns a printable representational string of the given object.


@dataclass
class Param:
    def __init__(self,name,Pdf,empiricalDistb):#empiricalDistrib est un vecteur de taille niter/subsamplingStep
        self.name=name
        self.Prior=Pdf
        self.Posterior=np.zeros(len(empiricalDistb))
        self.value=CODE_scalar

    def sample(self):
        return self.Prior.sample()

    def draw_param_value(self):
        self.value=self.sample()


    def perturb(self, valini):
        return self.Prior.perturb(valini)
    
    def random_walk(self,valini):
        self.value=self.perturb(valini)


class ParamsPriors:
    def __init__(self, priors: Sequence[Prior]):
        self.prior_list = priors



    def __iter__(self):
        return self.prior_list.__iter__()

    def __getitem__(self, key):
        return self.prior_list[key]

    def __repr__(self):
        return self.prior_list.__repr__()

    def __len__(self):
        return self.prior_list.__len__()


if __name__ == "__main__":
    import numpy as np

    def reciprocal(x):
        return 1 / x

    priors = {
        "moinslog10IntrinK": (MOINSLOG10INTRINK_INTERVAL, MOINSLOG10INTRINK_SIGMA),  # (intervalle, sigma)
        "n": (N_INTERVAL, N_SIGMA),
        "lambda_s": (LAMBDA_S_INTERVAL, LAMBDA_S_SIGMA),
        "rhos_cs": (RHOS_CS_INTERVAL, RHOS_CS_SIGMA),
    }

    priors1 = ParamsPriors(
        [Prior(*args) for args in (priors[lbl] for lbl in PARAM_LIST)]
    )

    # priors2 = ParamsPriors(
    #     [Prior(*args) for args in (priors[lbl] for lbl in PARAM_LIST)]
    # )

    # geom = AllPriors([priors1, priors2])

    class Layer:
        def __init__(
            self,
            name: str,
            zLow: float,
            moinslog10IntrinK: float,
            n: float,
            lambda_s: float,
            rhos_cs: float,
        ):
            self.name = name
            self.zLow = zLow
            self.params = Param(moinslog10IntrinK, n, lambda_s, rhos_cs)

        # The repr() function returns a printable representational string of the given object.
        # def __repr__(self) -> str:
        #     return self.name + f" : ends at {self.zLow} m. " + self.params.__repr__()

    def layersListCreator(layersListInput):
        layersList = list()
        for name, zLow, moinslog10IntrinK, n, lambda_s, rhos_cs in layersListInput:
            layersList.append(Layer(name, zLow, moinslog10IntrinK, n, lambda_s, rhos_cs))
        return layersList

def calc_K(k):
    K=k*RHO_W*G
    K/=MU_W
    return K