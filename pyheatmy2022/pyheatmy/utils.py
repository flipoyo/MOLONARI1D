from numpy import float32, full, zeros, indices
from numpy.linalg import solve
from numba import njit

from .solver import solver, tri_product

#LAMBDA_W = 0 # test du cas purement advectif
LAMBDA_W = 0.6071
RHO_W = 1000
C_W = 4185
ALPHA = 0.4


@njit
def compute_T(
    moinslog10K, n, lambda_s, rhos_cs, all_dt, dz, H_res, H_riv, H_aq, T_init, T_riv, T_aq, alpha=ALPHA
):
    """ Computes T(z, t) by solving the heat equation : dT/dt = ke Delta T + ae nabla H nabla T, for an homogeneous column.

    Parameters
    ----------
    moinslog10K : float
        value of -log10(K), where K = permeability.
    n : float
        porosity.
    lambda_s : float
        thermal conductivity.
    rho_cs : float
        density.
    all_dt : float array
        array of temporal discretization steps.
    dz : float
        spatial discretization step.
    H_res : float array
        bidimensional array of H(z, t). Usually computed by compute_H.
    H_riv : float array
        boundary condition H(z = z_riv, t).
    H_aq : float array
        boundary condition H(z = z_aq, t).
    T_init : float array
        boundary condition T(z, t=0).
    T_riv : float array
        boundary condition T(z = z_riv, t).
    T_aq : float array
        boundary condition T(z = z_aq, t).
    alpha : float, default: 0.3
        parameter of the semi-implicit scheme. Can cause instability if too big.

    Returns
    -------
    T_res : float array
        bidimensional array of T(z, t).
    """
    rho_mc_m = n * RHO_W * C_W + (1 - n) * rhos_cs
    K = 10.0 ** -moinslog10K
    lambda_m = (n * (LAMBDA_W) ** 0.5 + (1.0 - n) * (lambda_s) ** 0.5) ** 2

    ke = lambda_m / rho_mc_m
    ae = RHO_W * C_W * K / rho_mc_m

    n_cell = len(T_init)
    n_times = len(all_dt) + 1

    # First we need to compute the gradient of H(z, t)

    nablaH = zeros((n_cell, n_times), float32)

    nablaH[0, :] = 2*(H_res[1, :] - H_riv)/(3*dz)

    for i in range(1, n_cell - 1):
        nablaH[i, :] = (H_res[i+1, :] - H_res[i-1, :])/(2*dz)

    nablaH[n_cell - 1, :] = 2*(H_aq - H_res[n_cell - 2, :])/(3*dz)

    # Now we can compute T(z, t)

    T_res = zeros((n_cell, n_times), float32)
    T_res[:, 0] = T_init

    for j, dt in enumerate(all_dt):
        # Compute T at time times[j+1]

        # Defining the 3 diagonals of B
        lower_diagonal = (ke*alpha/dz ** 2) - (alpha*ae/(2*dz)) * nablaH[1:, j]
        lower_diagonal[-1] = 4*ke*alpha / \
            (3*dz**2) - (2*alpha*ae/(3*dz)) * nablaH[n_cell - 1, j]

        diagonal = full(n_cell, 1/dt - 2*ke*alpha/dz**2, float32)
        diagonal[0] = 1/dt - 4*ke*alpha/dz**2
        diagonal[-1] = 1/dt - 4*ke*alpha/dz**2

        upper_diagonal = (ke*alpha/dz ** 2) + \
            (alpha*ae/(2*dz)) * nablaH[:-1, j]
        upper_diagonal[0] = 4*ke*alpha / \
            (3*dz**2) + (2*alpha*ae/(3*dz)) * nablaH[0, j]

        # Defining c
        c = zeros(n_cell, float32)
        c[0] = (8*ke*(1-alpha) / (3*dz**2) - 2*(1-alpha)*ae*nablaH[0, j]/(3*dz)) * \
            T_riv[j+1] + (8*ke*alpha / (3*dz**2) - 2*alpha *
                          ae*nablaH[0, j]/(3*dz)) * T_riv[j]
        c[-1] = (8*ke*(1-alpha) / (3*dz**2) + 2*(1-alpha)*ae*nablaH[n_cell - 1, j]/(3*dz)) * \
            T_aq[j+1] + (8*ke*alpha / (3*dz**2) + 2*alpha *
                         ae*nablaH[n_cell - 1, j]/(3*dz)) * T_aq[j]

        B_fois_T_plus_c = tri_product(
            lower_diagonal, diagonal, upper_diagonal, T_res[:, j]) + c

        # Defining the 3 diagonals of A
        lower_diagonal = - (ke*(1-alpha)/dz ** 2) + \
            ((1-alpha)*ae/(2*dz)) * nablaH[1:, j]
        lower_diagonal[-1] = - 4*ke*(1-alpha)/(3*dz**2) + \
            (2*(1-alpha)*ae/(3*dz)) * nablaH[n_cell - 1, j]

        diagonal = full(n_cell, 1/dt + 2*ke*(1-alpha)/dz**2, float32)
        diagonal[0] = 1/dt + 4*ke*(1-alpha)/dz**2
        diagonal[-1] = 1/dt + 4*ke*(1-alpha)/dz**2

        upper_diagonal = - (ke*(1-alpha)/dz ** 2) - \
            ((1-alpha)*ae/(2*dz)) * nablaH[:-1, j]
        upper_diagonal[0] = - 4*ke*(1-alpha)/(3*dz**2) - \
            (2*(1-alpha)*ae/(3*dz)) * nablaH[0, j]

        try:
            T_res[:, j+1] = solver(lower_diagonal, diagonal,
                                   upper_diagonal, B_fois_T_plus_c)
        except Exception:
            A = zeros((n_cell, n_cell), float32)
            A[0, 0] = diagonal[0]
            A[0, 1] = upper_diagonal[0]
            for i in range(1, n_cell - 1):
                A[i, i-1] = lower_diagonal[i-1]
                A[i, i] = diagonal[i]
                A[i, i+1] = upper_diagonal[i]
            A[n_cell - 1, n_cell - 1] = diagonal[n_cell - 1]
            A[n_cell - 1, n_cell - 2] = lower_diagonal[n_cell - 2]
            T_res[:, j+1] = solve(A, B_fois_T_plus_c)

    return T_res


@njit
def compute_H(moinslog10K, Ss, all_dt, isdtconstant, dz, H_init, H_riv, H_aq, alpha=ALPHA):
    """ Computes H(z, t) by solving the diffusion equation : Ss dH/dT = K Delta H, for  an homogeneous column.

    Parameters
    ----------
    moinslog10K : float
        value of -log10(K) where K = permeability.
    Ss : float
        specific emmagasinement.
    all_dt : float array
        array temporal discretization steps.
    isdtconstant : bool
        True iff the temporal discretization step is constant.
    dz : float
        spatial discretization step.
    H_init : float array
        boundary condition H(z, t = 0).
    H_riv : float array
        boundary condition H(z = z_riv, t).
    H_aq : float array
        boundary condition H(z = z_aquifer, t).
    alpha : float, default: 0.3
        parameter of the semi-implicit scheme. Can cause instability if too big.

    Returns
    -------
    H_res : float array
        bidimensional array of H(z, t).
    """
    n_cell = len(H_init)
    n_times = len(all_dt) + 1

    H_res = zeros((n_cell, n_times), float32)
    H_res[:, 0] = H_init

    K = 10.0 ** -moinslog10K
    KsurSs = K/Ss

    # Check if dt is constant :
    if isdtconstant:  # dt is constant so A and B are constant
        dt = all_dt[0]

        # Defining the 3 diagonals of B
        lower_diagonal_B = full(n_cell - 1, KsurSs*alpha/dz**2, float32)
        lower_diagonal_B[-1] = 4*KsurSs*alpha/(3*dz**2)

        diagonal_B = full(n_cell, 1/dt - 2*KsurSs*alpha/dz**2, float32)
        diagonal_B[0] = 1/dt - 4*KsurSs*alpha/dz**2
        diagonal_B[-1] = 1/dt - 4*KsurSs*alpha/dz**2

        upper_diagonal_B = full(n_cell - 1, KsurSs*alpha/dz**2, float32)
        upper_diagonal_B[0] = 4*KsurSs*alpha/(3*dz**2)

        # Defining the 3 diagonals of A
        lower_diagonal_A = full(
            n_cell - 1, - KsurSs*(1-alpha)/dz**2, float32)
        lower_diagonal_A[-1] = - 4*KsurSs*(1-alpha)/(3*dz**2)

        diagonal_A = full(n_cell, 1/dt + 2*KsurSs*(1-alpha)/dz**2, float32)
        diagonal_A[0] = 1/dt + 4*KsurSs*(1-alpha)/dz**2
        diagonal_A[-1] = 1/dt + 4*KsurSs*(1-alpha)/dz**2

        upper_diagonal_A = full(
            n_cell - 1, - KsurSs*(1-alpha)/dz**2, float32)
        upper_diagonal_A[0] = - 4*KsurSs*(1-alpha)/(3*dz**2)

        for j in range(n_times - 1):
            # Compute H at time times[j+1]

            # Defining c
            c = zeros(n_cell, float32)
            c[0] = (8*KsurSs / (3*dz**2)) * \
                ((1-alpha)*H_riv[j+1] + alpha*H_riv[j])
            c[-1] = (8*KsurSs / (3*dz**2)) * \
                ((1-alpha)*H_aq[j+1] + alpha*H_aq[j])

            B_fois_H_plus_c = tri_product(
                lower_diagonal_B, diagonal_B, upper_diagonal_B, H_res[:, j]) + c

            H_res[:, j+1] = solver(lower_diagonal_A, diagonal_A,
                                   upper_diagonal_A, B_fois_H_plus_c)
    else:  # dt is not constant so A and B and not constant
        for j, dt in enumerate(all_dt):
            # Compute H at time times[j+1]

            # Defining the 3 diagonals of B
            lower_diagonal = full(n_cell - 1, KsurSs*alpha/dz**2, float32)
            lower_diagonal[-1] = 4*KsurSs*alpha/(3*dz**2)

            diagonal = full(n_cell, 1/dt - 2*KsurSs*alpha/dz**2, float32)
            diagonal[0] = 1/dt - 4*KsurSs*alpha/dz**2
            diagonal[-1] = 1/dt - 4*KsurSs*alpha/dz**2

            upper_diagonal = full(n_cell - 1, KsurSs*alpha/dz**2, float32)
            upper_diagonal[0] = 4*KsurSs*alpha/(3*dz**2)

            # Defining c
            c = zeros(n_cell, float32)
            c[0] = (8*KsurSs / (3*dz**2)) * \
                ((1-alpha)*H_riv[j+1] + alpha*H_riv[j])
            c[-1] = (8*KsurSs / (3*dz**2)) * \
                ((1-alpha)*H_aq[j+1] + alpha*H_aq[j])

            B_fois_H_plus_c = tri_product(
                lower_diagonal, diagonal, upper_diagonal, H_res[:, j]) + c

            # Defining the 3 diagonals of A
            lower_diagonal = full(
                n_cell - 1, - KsurSs*(1-alpha)/dz**2, float32)
            lower_diagonal[-1] = - 4*KsurSs*(1-alpha)/(3*dz**2)

            diagonal = full(n_cell, 1/dt + 2*KsurSs*(1-alpha)/dz**2, float32)
            diagonal[0] = 1/dt + 4*KsurSs*(1-alpha)/dz**2
            diagonal[-1] = 1/dt + 4*KsurSs*(1-alpha)/dz**2

            upper_diagonal = full(
                n_cell - 1, - KsurSs*(1-alpha)/dz**2, float32)
            upper_diagonal[0] = - 4*KsurSs*(1-alpha)/(3*dz**2)

            H_res[:, j+1] = solver(lower_diagonal, diagonal,
                                   upper_diagonal, B_fois_H_plus_c)

    return H_res


@njit
def compute_T_stratified(
    moinslog10K_list, n_list, lambda_s_list, rhos_cs_list, all_dt, dz, H_res, H_riv, H_aq, nablaH, T_init, T_riv, T_aq, alpha=ALPHA
):
    """ Computes T(z, t) by solving the heat equation : dT/dt = ke Delta T + ae nabla H nabla T, for an heterogeneous column.

    Parameters
    ----------
    moinslog10K_list : float array
        values of -log10(K) for each cell of the column, where K = permeability.
    n_list : float array
        porosity for each cell of the column.
    lambda_s_list : float array
        thermal conductivity for each cell of the column.
    rho_cs_list : float array
        density for each cell of the column.
    all_dt : float array
        array of temporal discretization steps.
    dz : float
        spatial discretization step.
    H_res : float array
        bidimensional array of H(z, t). Usually computed by compute_H_stratified.
    H_riv : float array
        boundary condition H(z = z_riv, t).
    H_aq : float array
        boundary condition H(z = z_aq, t).
    T_init : float array
        boundary condition T(z, t=0).
    T_riv : float array
        boundary condition T(z = z_riv, t).
    T_aq : float array
        boundary condition T(z = z_aq, t).
    alpha : float, default: 0.3
        parameter of the semi-implicit scheme. Can cause instability if too big.

    Returns
    -------
    T_res : float array
        bidimensional array of T(z, t).
    """
    rho_mc_m_list = n_list * RHO_W * C_W + (1 - n_list) * rhos_cs_list
    K_list = 10.0 ** -moinslog10K_list
    lambda_m_list = (n_list * (LAMBDA_W) ** 0.5 +
                     (1.0 - n_list) * (lambda_s_list) ** 0.5) ** 2

    ke_list = lambda_m_list / rho_mc_m_list
    ae_list = RHO_W * C_W * K_list / rho_mc_m_list

    n_cell = len(T_init)
    n_times = len(all_dt) + 1

    # First we need to compute the gradient of H(z, t)

    nablaH = zeros((n_cell, n_times), float32)

    nablaH[0, :] = 2*(H_res[1, :] - H_riv)/(3*dz)

    for i in range(1, n_cell - 1):
        nablaH[i, :] = (H_res[i+1, :] - H_res[i-1, :])/(2*dz)

    nablaH[n_cell - 1, :] = 2*(H_aq - H_res[n_cell - 2, :])/(3*dz)

    # Now we can compute T(z, t)

    T_res = zeros((n_cell, n_times), float32)
    T_res[:, 0] = T_init

    for j, dt in enumerate(all_dt):
        # Compute T at time times[j+1]

        # Defining the 3 diagonals of B
        lower_diagonal = (ke_list[1:]*alpha/dz ** 2) - \
            (alpha*ae_list[1:]/(2*dz)) * nablaH[1:, j]
        lower_diagonal[-1] = 4*ke_list[n_cell - 1]*alpha / \
            (3*dz**2) - (2*alpha*ae_list[n_cell -
                                         1]/(3*dz)) * nablaH[n_cell - 1, j]

        diagonal = 1/dt - 2*ke_list*alpha/dz**2
        diagonal[0] = 1/dt - 4*ke_list[0]*alpha/dz**2
        diagonal[-1] = 1/dt - 4*ke_list[n_cell - 1]*alpha/dz**2

        upper_diagonal = (ke_list[:-1]*alpha/dz ** 2) + \
            (alpha*ae_list[:-1]/(2*dz)) * nablaH[:-1, j]
        upper_diagonal[0] = 4*ke_list[0]*alpha / \
            (3*dz**2) + (2*alpha*ae_list[0]/(3*dz)) * nablaH[0, j]

        # Defining c
        c = zeros(n_cell, float32)
        c[0] = (8*ke_list[0]*(1-alpha) / (3*dz**2) - 2*(1-alpha)*ae_list[0]*nablaH[0, j]/(3*dz)) * \
            T_riv[j+1] + (8*ke_list[0]*alpha / (3*dz**2) - 2*alpha *
                          ae_list[0]*nablaH[0, j]/(3*dz)) * T_riv[j]
        c[-1] = (8*ke_list[n_cell - 1]*(1-alpha) / (3*dz**2) + 2*(1-alpha)*ae_list[n_cell - 1]*nablaH[n_cell - 1, j]/(3*dz)) * \
            T_aq[j+1] + (8*ke_list[n_cell - 1]*alpha / (3*dz**2) + 2*alpha *
                         ae_list[n_cell - 1]*nablaH[n_cell - 1, j]/(3*dz)) * T_aq[j]

        B_fois_T_plus_c = tri_product(
            lower_diagonal, diagonal, upper_diagonal, T_res[:, j]) + c

        # Defining the 3 diagonals of A
        lower_diagonal = - (ke_list[1:]*(1-alpha)/dz ** 2) + \
            ((1-alpha)*ae_list[1:]/(2*dz)) * nablaH[1:, j]
        lower_diagonal[-1] = - 4*ke_list[n_cell - 1]*(1-alpha)/(3*dz**2) + \
            (2*(1-alpha)*ae_list[n_cell - 1]/(3*dz)) * nablaH[n_cell - 1, j]

        diagonal = 1/dt + 2*ke_list*(1-alpha)/dz**2
        diagonal[0] = 1/dt + 4*ke_list[0]*(1-alpha)/dz**2
        diagonal[-1] = 1/dt + 4*ke_list[n_cell - 1]*(1-alpha)/dz**2

        upper_diagonal = - (ke_list[:-1]*(1-alpha)/dz ** 2) - \
            ((1-alpha)*ae_list[:-1]/(2*dz)) * nablaH[:-1, j]
        upper_diagonal[0] = - 4*ke_list[0]*(1-alpha)/(3*dz**2) - \
            (2*(1-alpha)*ae_list[0]/(3*dz)) * nablaH[0, j]

        try:
            T_res[:, j+1] = solver(lower_diagonal, diagonal,
                                   upper_diagonal, B_fois_T_plus_c)
        except Exception:
            A = zeros((n_cell, n_cell), float32)
            A[0, 0] = diagonal[0]
            A[0, 1] = upper_diagonal[0]
            for i in range(1, n_cell - 1):
                A[i, i-1] = lower_diagonal[i-1]
                A[i, i] = diagonal[i]
                A[i, i+1] = upper_diagonal[i]
            A[n_cell - 1, n_cell - 1] = diagonal[n_cell - 1]
            A[n_cell - 1, n_cell - 2] = lower_diagonal[n_cell - 2]
            T_res[:, j+1] = solve(A, B_fois_T_plus_c)

    return T_res


@njit
def compute_H_stratified(moinslog10K_list, Ss_list, all_dt, isdtconstant, dz, H_init, H_riv, H_aq, alpha=ALPHA):
    """ Computes H(z, t) by solving the diffusion equation : Ss dH/dT = K Delta H, for an heterogeneous column.

    Parameters
    ----------
    moinslog10K_list : float array
        values of -log10(K) for each cell of the column, where K = permeability.
    Ss_list : float array
        specific emmagasinement for each cell of the column.
    all_dt : float array
        array temporal discretization steps.
    isdtconstant : bool
        True iff the temporal discretization step is constant.
    dz : float
        spatial discretization step.
    H_init : float array
        boundary condition H(z, t = 0).
    H_riv : float array
        boundary condition H(z = z_riv, t).
    H_aq : float array
        boundary condition H(z = z_aquifer, t).
    alpha : float, default: 0.3
        parameter of the semi-implicit scheme. Can cause instability if too big.

    Returns
    -------
    H_res : float array
        bidimensional array of H(z, t).
    """
    n_cell = len(H_init)
    n_times = len(all_dt) + 1

    H_res = zeros((n_cell, n_times), float32)
    H_res[:, 0] = H_init

    K_list = 10.0 ** -moinslog10K_list
    KsurSs_list = K_list/Ss_list

    # Check if dt is constant :
    if isdtconstant:  # dt is constant so A and B are constant
        dt = all_dt[0]

        # Defining the 3 diagonals of B
        lower_diagonal_B = KsurSs_list[1:]*alpha/dz**2
        lower_diagonal_B[-1] = 4*KsurSs_list[n_cell - 1]*alpha/(3*dz**2)

        diagonal_B = 1/dt - 2*KsurSs_list*alpha/dz**2
        diagonal_B[0] = 1/dt - 4*KsurSs_list[0]*alpha/dz**2
        diagonal_B[-1] = 1/dt - 4*KsurSs_list[n_cell - 1]*alpha/dz**2

        upper_diagonal_B = KsurSs_list[:-1]*alpha/dz**2
        upper_diagonal_B[0] = 4*KsurSs_list[0]*alpha/(3*dz**2)

        # Defining the 3 diagonals of A
        lower_diagonal_A = - KsurSs_list[1:]*(1-alpha)/dz**2
        lower_diagonal_A[-1] = - 4*KsurSs_list[n_cell - 1]*(1-alpha)/(3*dz**2)

        diagonal_A = 1/dt + 2*KsurSs_list*(1-alpha)/dz**2
        diagonal_A[0] = 1/dt + 4*KsurSs_list[0]*(1-alpha)/dz**2
        diagonal_A[-1] = 1/dt + 4*KsurSs_list[n_cell - 1]*(1-alpha)/dz**2

        upper_diagonal_A = - KsurSs_list[:-1]*(1-alpha)/dz**2
        upper_diagonal_A[0] = - 4*KsurSs_list[0]*(1-alpha)/(3*dz**2)

        for j in range(n_times - 1):
            # Compute H at time times[j+1]

            # Defining c
            c = zeros(n_cell, float32)
            c[0] = (8*KsurSs_list[0] / (3*dz**2)) * \
                ((1-alpha)*H_riv[j+1] + alpha*H_riv[j])
            c[-1] = (8*KsurSs_list[n_cell - 1] / (3*dz**2)) * \
                ((1-alpha)*H_aq[j+1] + alpha*H_aq[j])

            B_fois_H_plus_c = tri_product(
                lower_diagonal_B, diagonal_B, upper_diagonal_B, H_res[:, j]) + c

            H_res[:, j+1] = solver(lower_diagonal_A, diagonal_A,
                                   upper_diagonal_A, B_fois_H_plus_c)
    else:  # dt is not constant so A and B and not constant
        for j, dt in enumerate(all_dt):
            # Compute H at time times[j+1]

            # Defining the 3 diagonals of B
            lower_diagonal = KsurSs_list[1:]*alpha/dz**2
            lower_diagonal[-1] = 4*KsurSs_list[n_cell - 1]*alpha/(3*dz**2)

            diagonal = 1/dt - 2*KsurSs_list*alpha/dz**2
            diagonal[0] = 1/dt - 4*KsurSs_list[0]*alpha/dz**2
            diagonal[-1] = 1/dt - 4*KsurSs_list[n_cell - 1]*alpha/dz**2

            upper_diagonal = KsurSs_list[:-1]*alpha/dz**2
            upper_diagonal[0] = 4*KsurSs_list[0]*alpha/(3*dz**2)

            # Defining c
            c = zeros(n_cell, float32)
            c[0] = (8*KsurSs_list[0] / (3*dz**2)) * \
                ((1-alpha)*H_riv[j+1] + alpha*H_riv[j])
            c[-1] = (8*KsurSs_list[n_cell - 1] / (3*dz**2)) * \
                ((1-alpha)*H_aq[j+1] + alpha*H_aq[j])

            B_fois_H_plus_c = tri_product(
                lower_diagonal, diagonal, upper_diagonal, H_res[:, j]) + c

            # Defining the 3 diagonals of A
            lower_diagonal = - KsurSs_list[1:]*(1-alpha)/dz**2
            lower_diagonal[-1] = - 4 * \
                KsurSs_list[n_cell - 1]*(1-alpha)/(3*dz**2)

            diagonal = 1/dt + 2*KsurSs_list*(1-alpha)/dz**2
            diagonal[0] = 1/dt + 4*KsurSs_list[0]*(1-alpha)/dz**2
            diagonal[-1] = 1/dt + 4*KsurSs_list[n_cell - 1]*(1-alpha)/dz**2

            upper_diagonal = - KsurSs_list[:-1]*(1-alpha)/dz**2
            upper_diagonal[0] = - 4*KsurSs_list[0]*(1-alpha)/(3*dz**2)

            H_res[:, j+1] = solver(lower_diagonal, diagonal,
                                   upper_diagonal, B_fois_H_plus_c)

    return H_res
