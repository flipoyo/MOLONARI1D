from collections import namedtuple
from copy import deepcopy
from dataclasses import dataclass
from random import uniform, gauss
from numpy import inf
from typing import Callable, Sequence
from .config import *
from numbers import Number  # Pour vérifier si une variable est un nombre (int, float)


PARAM_LIST = ["IntrinK", "n", "lambda_s", "rhos_cs", "q_s"]

Param = namedtuple("Param", PARAM_LIST)


def cst(x):
    return 1.0  # fonction de densité par défaut


# Classe Prior modifiée pour gérer les différentes échelles et les paramètres fixés
@dataclass
class Prior:
    """
    Classe Prior autonome qui choisit automatiquement la meilleure échelle (linéaire, log, asinh)
    Et gère les paramètres fixes.
    """

    user_range: (
        object  # tuple de bornes physiques ou float si la valeur physique est fixée
    )
    user_sigma: float
    density: Callable[[float], float] = cst

    def __post_init__(self):
        # 1. Gestion du paramètre fixe.
        if isinstance(self.user_range, Number):
            self.is_fixed = True
            self.scale = "fixed"
            self.mcmc_range = (float(self.user_range), float(self.user_range))
            # Pas de facteur d'échelle nécessaire pour un paramètre fixe.
            self.asinh_scale = 1.0
            return

        self.is_fixed = False
        lower_bound, upper_bound = self.user_range

        if lower_bound <= 0 and upper_bound > 0:
            # Cas où l'intervalle traverse zéro.
            max_abs_val = max(abs(lower_bound), abs(upper_bound))

            # Si la magnitude est petite, les ordres de grandeur sont importants -> symlog.
            if max_abs_val < SYMLOG_MAGNITUDE_THRESHOLD:
                self.scale = "symlog"
            else:
                # Sinon, pour un intervalle comme (-5, 5), le linéaire est suffisant.
                self.scale = "linear"

        # Cas où l'intervalle est strictement positif (inchangé).
        elif lower_bound > 0 and upper_bound / lower_bound > LOG_SCALE_THRESHOLD:
            self.scale = "log"
        else:
            # Pour tous les autres cas (positif et étroit, ou entièrement négatif).
            self.scale = "linear"

        # Pour le symlog, on définit un seuil linéaire,
        # càd une zone centrale où la transformation est linéaire (on évit la divergence au voisinage de zéro).
        if self.scale == "symlog":
            # Le seuil est 1/100ème de la plus grande borne.
            self.linthresh = (
                max(abs(lower_bound), abs(upper_bound)) / SYMLOG_LINTHRESH_RATIO
            )

        # 3. Transformation des bornes PHYSIQUES en bornes pour l'espace de travail MCMC.
        self.mcmc_range = self.physical_to_mcmc(np.array(self.user_range))

        # 4. TRADUCTION DU SIGMA PHYSIQUE EN SIGMA MCMC.
        self.mcmc_sigma = self._translate_sigma()

    def _translate_sigma(self):
        if self.scale == "linear" or self.is_fixed:
            return self.user_sigma

        lower_phys, upper_phys = self.user_range

        if self.scale == "log":
            center_point = np.sqrt(lower_phys * upper_phys)
        else:  # symlog
            center_point = (lower_phys + upper_phys) / 2.0

        step_point = center_point + self.user_sigma
        mcmc_center = self.physical_to_mcmc(center_point)
        mcmc_step = self.physical_to_mcmc(step_point)

        return abs(mcmc_step - mcmc_center)

    def physical_to_mcmc(self, physical_value):
        """Traduit une valeur physique vers l'espace de la MCMC."""
        if self.scale == "log":
            return np.log10(physical_value)
        elif self.scale == "symlog":
            # On applique la transformation logarithmique signée.
            sign = np.sign(physical_value)
            abs_val = np.abs(physical_value)
            return sign * np.where(
                abs_val > self.linthresh,
                1 + np.log10(abs_val / self.linthresh),
                abs_val / self.linthresh,
            )
        else:  # linear
            return physical_value

    def mcmc_to_physical(self, mcmc_value):
        """Traduit une valeur de l'espace MCMC vers la valeur physique."""
        if self.scale == "log":
            return 10 ** (mcmc_value)
        elif self.scale == "symlog":
            sign = np.sign(mcmc_value)
            abs_val = np.abs(mcmc_value)
            return sign * np.where(
                abs_val > 1,
                self.linthresh * (10 ** (abs_val - 1)),
                self.linthresh * abs_val,
            )
        else:  # linear
            return mcmc_value

    # sample et perturb travaillent dans l'espace MCMC déjà transformé.
    def sample(self):
        """
        Cette fonction tire une valeur initiale pour le paramètre.
        Si le paramètre est fixé, c'est toujours la même valeur.
        """
        if self.is_fixed:
            return self.mcmc_range[0]
        return uniform(self.mcmc_range[0], self.mcmc_range[1])

    def perturb(self, mcmc_val):
        """
        Perturbe la valeur avec la gestion des bords par modulo ("effet Pac-Man").
        Cette fonction perturbe la valeur du paramètre pour l'itération MCMC suivante.
        Si le paramètre est fixé, il ne bouge pas.
        """
        if self.is_fixed:
            return self.mcmc_range[0]

        # Le pas de perturbation est calculé
        new_val = mcmc_val + gauss(0, self.mcmc_sigma)
        lower_bound, upper_bound = self.mcmc_range

        # On calcule la largeur de l'intervalle dans l'espace MCMC
        range_span = upper_bound - lower_bound

        # On applique la gestion des bords par modulo.
        # Sécurité pour éviter la division par zéro si l'intervalle est de largeur nulle.
        if range_span > 0:
            # Cette formule "enroule" la valeur pour qu'elle reste dans l'intervalle.
            # Si elle sort par le haut, elle réapparaît en bas, et vice-versa.
            new_val = lower_bound + np.mod(new_val - lower_bound, range_span)
        else:
            # Si l'intervalle est nul, la valeur ne change pas.
            new_val = mcmc_val

        return new_val

    def __repr__(self) -> str:
        """Pour un affichage clair du statut du Prior."""
        # On peut afficher le facteur d'échelle pour le débogage si on le souhaite.
        scale_info = f", échelle: {self.scale}"
        if self.is_fixed:
            return f"Prior avec une valeur fixe : {self.user_range}" + scale_info
        else:
            return (
                f"Prior sur l'intervalle physique [{self.user_range[0]:.2e}, {self.user_range[1]:.2e}]"
                + scale_info
            )

    # --- ANCIENNE VERSION DE LA MÉTHODE PERTURB (pour comparaison) ---
    # def perturb(self, val):
    #     # Perturbe la valeur d'un paramètre en respectant le prior.
    #     new_val = val + gauss(0, self.user_sigma)
    #     lower_bound, upper_bound = self.range
    #     range_span = upper_bound - lower_bound
    #     # Cette gestion des bords ("modulo") pouvait causer des sauts non physiques.
    #     if range_span != 0:
    #         new_val = (new_val - lower_bound) % range_span + lower_bound
    #     else:
    #         new_val = val
    #     return new_val
    # -----------------------------------------------------------------

    def reciprocal(x):
        return 1 / x

    priors = {
        "IntrinK": ((11, 15), 0.01),  # (intervalle, user_sigma)
        "n": ((0.01, 0.25), 0.01),
        "lambda_s": ((1, 5), 0.1),
        "rhos_cs": ((1e6, 1e7), 1e5),
        "q_s": ((0, 1), 1e2),
    }

    # priors1 = ParamsPriors(
    #    [Prior(*args) for args in (priors[lbl] for lbl in PARAM_LIST)]
    # )

    # priors2 = ParamsPriors(
    #     [Prior(*args) for args in (priors[lbl] for lbl in PARAM_LIST)]
    # )

    # geom = AllPriors([priors1, priors2])


def calc_K(k):
    K = k * RHO_W * G
    K /= MU_W
    return K
