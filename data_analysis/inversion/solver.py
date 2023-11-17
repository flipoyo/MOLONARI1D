# -*- coding: utf-8 -*-
from numba import njit
from numpy import ones, zeros, float32


@njit
def solver(a, b, c, d):
    """
    Solves the system AX = B where :
        - A is tridiagonal, with a, b and c as diagonals (from bottom to top)
        - B is a vector represented by d
    """
    nf = len(d)

    ac = a.astype(float32)
    bc = b.astype(float32)
    cc = c.astype(float32)
    dc = d.astype(float32)

    for it in range(1, nf):
        mc = ac[it - 1] / bc[it - 1]
        bc[it] = bc[it] - mc * cc[it - 1]
        dc[it] = dc[it] - mc * dc[it - 1]

    xc = bc
    xc[-1] = dc[-1] / bc[-1]

    for il in range(nf - 2, -1, -1):
        xc[il] = (dc[il] - cc[il] * xc[il + 1]) / bc[il]

    return xc


@njit
def tri_product(a, b, c, d):
    """
    Computes AB where :
        - A is tridiagonal, with a, b and c as diagonals (from bottom to top)
        - B is a vector represented by d
    """
    n = len(d)
    res = zeros(n, dtype=float32)

    ac = a.astype(float32)
    bc = b.astype(float32)
    cc = c.astype(float32)
    dc = d.astype(float32)

    res[0] = dc[0] * bc[0] + dc[1] * cc[0]
    res[n - 1] = dc[n - 1] * bc[n - 1] + dc[n - 2] * ac[n - 2]

    for ix in range(1, n - 1):
        res[ix] = ac[ix - 1] * dc[ix - 1] + \
            bc[ix] * dc[ix] + cc[ix] * dc[ix + 1]

    return res


# Pour forcer la compilation à l'init
solver(0.1 * ones(1), ones(2), -ones(1), ones(2))
tri_product(ones(1), ones(2), ones(1), ones(2))
