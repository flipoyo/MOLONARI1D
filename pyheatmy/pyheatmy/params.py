from collections import namedtuple
from dataclasses import dataclass
from random import uniform, gauss
from numpy import inf
from typing import Callable, Sequence

PARAM_LIST = ("moinslog10K", "n", "lambda_s", "rhos_cs")

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
        # perturbation dans le  cadre d'une mcmc classique
        new_val = val + gauss(0, self.sigma)
        while new_val > self.range[1]:
            new_val = self.range[0] + (new_val - self.range[1]) % (
                self.range[1] - self.range[0]
            )
        while new_val < self.range[0]:
            new_val = self.range[1] - (self.range[0] - new_val) % (
                self.range[1] - self.range[0]
            )
        return new_val

    def sample(self):  # retourne de manière uniforme un nombre de l'intervalle
        if self.range[0] > -inf and self.range[1] < inf:
            return uniform(*self.range)
        elif self.range[0] > -inf:
            # better choices possible : arctan(uniform)
            return 1 / uniform(self.range[0], 1e7)
        elif self.range[1] < inf:
            return 1 / uniform(-1e7, self.range[1])
        else:
            1 / uniform(-1e7, 1e7)

    def __repr__(self) -> str:
        return (
            f"Prior sur une valeure qui évolue entre {self.range[0]} et {self.range[1]}"
        )


# The repr() function returns a printable representational string of the given object.


class ParamsPriors:
    def __init__(self, priors: Sequence[Prior]):
        self.prior_list = priors

    def sample(self):
        return Param(*(prior.sample() for prior in self.prior_list))

    def perturb(self, param):
        return Param(
            *(prior.perturb(val) for prior, val in zip(self.prior_list, param))
        )

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
        "moinslog10K": ((11, 15), 0.01),  # (intervalle, sigma)
        "n": ((0.01, 0.25), 0.01),
        "lambda_s": ((1, 5), 0.1),
        "rhos_cs": ((1e6, 1e7), 1e5),
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
            moinslog10K: float,
            n: float,
            lambda_s: float,
            rhos_cs: float,
        ):
            self.name = name
            self.zLow = zLow
            self.params = Param(moinslog10K, n, lambda_s, rhos_cs)

        # The repr() function returns a printable representational string of the given object.
        # def __repr__(self) -> str:
        #     return self.name + f" : ends at {self.zLow} m. " + self.params.__repr__()

    def layersListCreator(layersListInput):
        layersList = list()
        for name, zLow, moinslog10K, n, lambda_s, rhos_cs in layersListInput:
            layersList.append(Layer(name, zLow, moinslog10K, n, lambda_s, rhos_cs))
        return layersList

    # init_param = geom.sample()
    # print(init_param)
    # print(geom.perturb(init_param))
    # print(
    #     layersListCreator(
    #         [
    #             a + b
    #             for a, b in zip(
    #                 [("couche1", 10), ("couche2", 20)], geom.perturb(init_param)
    #             )
    #         ]
    #     )
    # )
    # print(geom[0])
    # print(Layer("couche", 1, *geom[0].sample()))
