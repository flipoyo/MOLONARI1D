from collections import namedtuple
from copy import deepcopy
from dataclasses import dataclass
from random import uniform, gauss
from numpy import inf
from typing import Callable, Sequence
from pyheatmy.config import *
from numbers import Number # Pour vérifier si une variable est un nombre (int, float)

PARAM_LIST = ["moinslog10IntrinK", "n", "lambda_s", "rhos_cs", "q_s"]

Param = namedtuple("Param", PARAM_LIST)

def cst(x):
    return 1.0  # fonction de densité par défaut

# On modifie la classe Prior pour gérer les paramètres fixes (q_s=0 dans le cas 1D)
@dataclass
class Prior:
    range_val: object  # Peut être un tuple (min, max) ou un simple nombre
    sigma: float
    density: Callable[[float], float] = cst

    def __post_init__(self):
        """
        Cette fonction est automatiquement appelée après l'initialisation.
        C'est ici qu'on va vérifier si le paramètre est fixe ou variable.
        """
        # On regarde si on nous a donné un simple nombre ou un intervalle (tuple)
        if isinstance(self.range_val, Number):
            # CAS 1 : C'est un nombre, le paramètre est donc FIXE.
            self.is_fixed = True
            self.fixed_value = float(self.range_val) # On stocke cette valeur
            self.range = (self.fixed_value, self.fixed_value) # On met à jour self.range par cohérence
        else:
            # CAS 2 : C'est un intervalle, le paramètre est VARIABLE (comportement habituel).
            self.is_fixed = False
            self.range = self.range_val # On assigne la valeur à self.range comme avant

    def perturb(self, val):
        """
        Cette fonction perturbe la valeur du paramètre pour l'itération MCMC suivante.
        Si le paramètre est fixé, il ne bouge pas.
        """
        # Si le paramètre est fixé, on retourne simplement sa valeur. La "perturbation" est nulle.
        if self.is_fixed:
            return self.fixed_value
        
        # Sinon, on applique la marche aléatoire comme avant.
        new_val = val + gauss(0, self.sigma)
        lower_bound, upper_bound = self.range

        # Gestion des bords par "rebond" (plus stable pour la MCMC).
        if new_val < lower_bound:
            # Si on dépasse par le bas, on rebondit vers l'intérieur.
            new_val = 2 * lower_bound - new_val
        if new_val > upper_bound:
            # Si on dépasse par le haut, on rebondit aussi vers l'intérieur.
            new_val = 2 * upper_bound - new_val
        return new_val
    
    # --- ANCIENNE VERSION DE LA MÉTHODE PERTURB (pour comparaison) ---
    # def perturb(self, val):
    #     # Perturbe la valeur d'un paramètre en respectant le prior.
    #     new_val = val + gauss(0, self.sigma)
    #     lower_bound, upper_bound = self.range
    #     range_span = upper_bound - lower_bound
    #     # Cette gestion des bords ("modulo") pouvait causer des sauts non physiques.
    #     if range_span != 0:
    #         new_val = (new_val - lower_bound) % range_span + lower_bound
    #     else:
    #         new_val = val
    #     return new_val
    # -----------------------------------------------------------------

    def sample(self):
        """
        Cette fonction tire une valeur initiale pour le paramètre.
        Si le paramètre est fixé, c'est toujours la même valeur.
        """
        # Si le paramètre est fixé, on retourne toujours sa valeur.
        if self.is_fixed:
            return self.fixed_value
        
        # Sinon, on tire une valeur au hasard dans l'intervalle.
        lower_bound, upper_bound = self.range
        return uniform(lower_bound, upper_bound)

    def __repr__(self) -> str:
        """
        Pour qu'on voie clairement ce que fait le Prior quand on l'affiche.
        """
        if self.is_fixed:
            return f"Prior avec une valeur fixe : {self.fixed_value}"
        else:
            return f"Prior sur une valeur qui évolue entre {self.range[0]} et {self.range[1]} avec un écart type de {self.sigma}"

    def reciprocal(x):
        return 1 / x

    priors = {
        "moinslog10IntrinK": ((11, 15), 0.01),  # (intervalle, sigma)
        "n": ((0.01, 0.25), 0.01),
        "lambda_s": ((1, 5), 0.1),
        "rhos_cs": ((1e6, 1e7), 1e5),
        "q_s": ((0, 1), 1e2)
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