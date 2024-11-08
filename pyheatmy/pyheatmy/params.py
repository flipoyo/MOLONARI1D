from collections import namedtuple
from dataclasses import dataclass
from random import uniform, gauss
from numpy import inf
from typing import Callable, Sequence
from pyheatmy.config import *

PARAM_LIST = ("moinslog10IntrinK", "n", "lambda_s", "rhos_cs", "q")

Param = namedtuple("Parametres", PARAM_LIST)

def cst(x):
    return 1.0  # fonction de densité par défaut


@dataclass
class Prior:
    range: tuple
    sigma: float
    # Callable est un type de fonction, [float] est la liste des arguments que prend la fonction et float est le type de la sortie de la fonction
    density: Callable[[float], float] = cst

    def perturb(self, val):  # perturbe la valeur d'un paramètre en respectant le prior
        new_val = val + gauss(0, self.sigma)
        lower_bound, upper_bound = self.range
        range_span = upper_bound - lower_bound
        new_val = (new_val - lower_bound) % range_span + lower_bound
        return new_val

    def sample(self):  # retourne de manière uniforme un nombre de l'intervalle
        lower_bound, upper_bound = self.range
        return uniform(lower_bound, upper_bound)

    def __repr__(self) -> str:
        return (
            f"Prior sur une valeure qui évolue entre {self.range[RangeType.MIN.value]} et {self.range[RangeType.MAX.value]} avec un écart type de {self.sigma}"
        )




# The repr() function returns a printable representational string of the given object.

if __name__ == "__main__":
    import numpy as np

    def reciprocal(x):
        return 1 / x

    priors = {
        "moinslog10IntrinK": ((11, 15), 0.01),  # (intervalle, sigma)
        "n": ((0.01, 0.25), 0.01),
        "lambda_s": ((1, 5), 0.1),
        "rhos_cs": ((1e6, 1e7), 1e5),
        "q": ((0, 1), 1e2)
    }

    #priors1 = ParamsPriors(
    #    [Prior(*args) for args in (priors[lbl] for lbl in PARAM_LIST)]
    #)

    # priors2 = ParamsPriors(
    #     [Prior(*args) for args in (priors[lbl] for lbl in PARAM_LIST)]
    # )

    # geom = AllPriors([priors1, priors2])

def calc_K(k):
    K=k*RHO_W*G
    K/=MU_W
    return K