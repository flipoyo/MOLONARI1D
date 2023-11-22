from timeit import timeit
import numpy as np
import timeit
from numba import njit, guvectorize
from scipy.interpolate import interp1d, lagrange, BarycentricInterpolator


"""implémentation numba de l'interpolation de Lagrange Barycentrique, 
    voir https://people.maths.ox.ac.uk/trefethen/barycentric.pdf, formule 4.2"""


@njit
def n_barycentric(x):
    """calcul les poids barycentriques w_i du polynome interpolateur de Lagrange (qui dépendent seulement des abscisses interpollées """
    n = len(x)
    diff = np.array([[x[i]-x[j] for j in range(n)] for i in range(n)])
    for i in range(n):
        diff[i, i] = 1
    w = np.array([1/np.prod(diff[i, :]) for i in range(n)])
    return w

# @guvectorize(["void(float64[:], float64[:], float64[:], float64[:])"],
#             "(n),(n),(n),(m)->(m)")


@njit
def n_evaluate(x, w, y, point):
    """évalue le polynome interpollateur au point P, les poids w_i précedemment calculés sont nécessaires"""
    poids = w/(point-x)
    return np.dot(poids, y)/np.sum(poids)


class Lagrange():
    """encapsule ces fonctions dans un objet Lagrange similaire aux interpollateurs scipy
    Pour plus de lisibilité (similarité aux interpollateurs scipy) les ordonées de la fonction à interpoller sont donnés dès l'initialisation même si elles sont inutiles"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.n = len(x)
        self.w = n_barycentric(x)

    def new_y(self, y):
        """permet d'interpoler une autre fonction aux mêmes abscisses, 
        plus rapide que de recréer l'objet et recalculer les mêmes poids w_i"""
        self.y = y

    def call(self, point):
        return n_evaluate(self.x, self.w, self.y, point)

    def __call__(self, point):
        index = np.where(self.x == point)
        if len(index[0]) == 0:
            return n_evaluate(self.x, self.w, self.y, point)
        else:
            return self.y[index[0][0]]


if __name__ == '__main__':
    x = np.array([1, 2, 3])
    y = np.array([0, 5, 1.1])
    L = Lagrange(x, y)
    # print(L(1))
    print(y[np.where(x == 2)[0][0]])
    print("Initialisation Numba")
    print(timeit.timeit("Lagrange(x,y)", globals=globals()))
    print("Evaluation Numba")
    print(timeit.timeit("L(1.2)", globals=globals()))

    print("Initialisation interp1d")
    print(timeit.timeit("interp1d(x,y)", globals=globals()))
    i = interp1d(x, y)
    print("Evaluation")
    print(timeit.timeit("i(1.2)", globals=globals()))
    print("Initialisation Lagrange")
    print(timeit.timeit("lagrange(x,y)", globals=globals()))
    l = lagrange(x, y)
    print("Evaluation")
    print(timeit.timeit("l(1.2)", globals=globals()))

    print("Initialisation Barycentric")
    print(timeit.timeit("BarycentricInterpolator(x,y)", globals=globals()))
    b = BarycentricInterpolator(x, y)
    print("Evaluation")
    print(timeit.timeit("b(1.2)", globals=globals()))
