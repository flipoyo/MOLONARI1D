from numpy import (
    float32,
    zeros,
    nansum,
    sum,
    var,
    mean,
    isclose,
    sqrt,
    all,
    array,
    shape,
    exp,
    size,
    log
)
from numpy.linalg import solve
from numba import njit

from pyheatmy.layers import Layer
from pyheatmy.solver import solver, tri_product
from pyheatmy.params import Prior, PARAM_LIST

# LAMBDA_W = 0 # test du cas purement advectif
LAMBDA_W = 0.6071
RHO_W = 1000
C_W   = 4185
ALPHA = 0.4
G = 9.81
N_UPDATE_MU = 96
EPSILON = 1e-10
MU = 1e-3

def conv(layer):
    name, prof, priors = layer
    if isinstance(priors, dict):
        return (
            name,
            prof,
            [Prior(*args) for args in (priors[lbl] for lbl in PARAM_LIST)],
        )
    else:
        return layer


def compute_energy(temp1, temp2, sigma2: float, remanence):
    remanence_step = int(remanence * 24 * 60 / 15)
    norm2 = nansum((temp1[:,remanence_step:] - temp2[:,remanence_step:]) ** 2)
    return 0.5 * norm2 / sigma2

def compute_energy_with_distrib(temp1, temp2, sigma2, sigma2_distrib):
    norm2 = nansum((temp1 - temp2) ** 2)
    return (
        0.5 * norm2 / sigma2
        + size(temp2) * log(sigma2) / 2
        - log(sigma2_distrib(sigma2))
    )

def compute_log_acceptance(current_energy: float, prev_energy: float):
    return prev_energy - current_energy


def convert_to_layer(nb_layer, name_layer, z_low, params):
    return [Layer(name_layer[i], z_low[i], *params[i]) for i in range(nb_layer)]


def check_range(x, ranges):
    while sum(x < ranges[:, 0]) + sum(x > ranges[:, 1]) > 0:
        x = (
            (x < ranges[:, 0]) * (ranges[:, 1] - (ranges[:, 0] - x))
            + (x > ranges[:, 1]) * (ranges[:, 0] + (x - ranges[:, 1]))
            + (x >= ranges[:, 0]) * (x <= ranges[:, 1]) * x
        )
    return x


def gelman_rubin(nb_current_iter, nb_param, nb_layer, chains, threshold=1.1):
    R = zeros((nb_layer, nb_param))
    for l in range(nb_layer):
        chains_layered = chains[:, :, l, :]
        # Variances intra-chaînes des paramètres
        Var_intra = var(chains_layered, axis=0)

        # Moyenne des variances intra-chaîne
        var_intra = mean(Var_intra, axis=0)

        # Moyennes de chaque chaîne
        means_chains = mean(chains_layered, axis=0)

        # Variance entre les moyennes des chaînes, dite inter-chaînes
        var_inter = var(means_chains, axis=0)

        # Calcul de l'indicateur de Gelman-Rubin
        for j in range(nb_param):
            if isclose(var_intra[j], 0):
                R[l, j] = 2
            else:
                R[l, j] = sqrt(
                    var_inter[j]
                    / var_intra[j]
                    * (nb_current_iter - 1)
                    / nb_current_iter
                    + 1
                )

    # On considère que la phase de burn-in est terminée dès que R < threshold
    return all(R < threshold)

@njit
def compute_Mu(T):
    """ 
    Paramètres : T : Température ou Tableau de températures
    Résultat : mu : Viscosité à la température T selon l'approximation de ...
    """
    A = 1.856e-11 * 1e-3
    B = 4209
    C = 0.04527
    D = -3.376e-5
    mu = A*exp(B*1./T + C*T + D*(T**2))
    return mu

# @njit
# def compute_HTK_stratified(array_K, array_Ss, list_zLow, z_solve, inter_cara, moinslog10K_list, Ss_list, all_dt, isdtconstant, dz, H_init, H_riv, H_aq, alpha=ALPHA):
#     dt = all_dt[0]
#     # mu_list = compute_Mu(T_init)
#     # rho_mc_m_list = n_list * RHO_W * C_W + (1 - n_list) * rhos_cs_list
#     # K_list = (RHO_W * G * 10.0 ** -moinslog10k_list) * 1./mu_list # ici k et K n'est pas le meme
#     # lambda_m_list = (n_list * (LAMBDA_W) ** 0.5 +(1.0 - n_list) * (lambda_s_list) ** 0.5) ** 2
#     # ke_list = lambda_m_list / rho_mc_m_list
#     # ae_list = RHO_W * C_W * K_list / rho_mc_m_list
#     n_cell = len(H_init)
#     n_times = len(all_dt) + 1
#     # compute T0 -> K0 -> H1 -> T1 -> K1 ...
#     H_res = zeros((n_cell, n_times), float32)
#     H_res[:, 0] = H_init[:]
#     K_list = 10.0 ** -moinslog10K_list
#     dK_list = K_list
#     dK_list[0] = (K_list[1] - K_list[0]) / dz
#     dK_list[-1] = (K_list[-1] - K_list[-2]) / dz
#     for idx in range(1, len(dK_list) - 1):
#         dK_list[idx] = (dK_list[idx+1] - dK_list[idx-1]) / 2 / dz
#     lower_diagonal_B = K_list[1:]*alpha/dz**2 # + dK_list[1:] * alpha / (2*dz)
#     lower_diagonal_B[-1] = 4*K_list[n_cell - 1]*alpha/(3*dz**2) # + 4*dK_list[n_cell - 1] * alpha / (3*2*dz)

#     diagonal_B =  Ss_list * 1/dt - 2*K_list*alpha/dz**2
#     diagonal_B[0] =  Ss_list[0] * 1/dt - 4*K_list[0]*alpha/dz**2
#     diagonal_B[-1] =  Ss_list[n_cell - 1] * 1/dt - 4*K_list[n_cell - 1]*alpha/dz**2

#     upper_diagonal_B = K_list[:-1]*alpha/dz**2 # - dK_list[:-1]*alpha / (2*dz)
#     upper_diagonal_B[0] = 4*K_list[0]*alpha/(3*dz**2) # - 4*dK_list[0]*alpha / (3*2*dz)

#     lower_diagonal_A = -K_list[1:]*(1-alpha)/dz**2 # - dK_list[1:] * (1-alpha) / (2*dz)
#     lower_diagonal_A[-1] = -4*K_list[n_cell - 1]*(1-alpha)/(3*dz**2) # - 4 * dK_list[n_cell - 1] * (1-alpha) / (3*2*dz)

#     diagonal_A =  Ss_list * 1/dt + 2*K_list*(1-alpha)/dz**2
#     diagonal_A[0] =  Ss_list[0] * 1/dt + 4*K_list[0]*(1-alpha)/dz**2
#     diagonal_A[-1] =  Ss_list[n_cell - 1] * 1/dt + 4*K_list[n_cell - 1]*(1-alpha)/dz**2

#     upper_diagonal_A =  -K_list[:-1]*(1-alpha)/dz**2 # + dK_list[:-1]*(1-alpha)/(2*dz)
#     upper_diagonal_A[0] =  -4*K_list[0]*(1-alpha)/(3*dz**2) # + 4 * dK_list[0]*(1-alpha)/(3*2*dz)

#     for j in range(n_times - 1):
 
#         c = zeros(n_cell, float32)
#         c[0] = (8*K_list[0] / (3*dz**2)) * ((1-alpha)*H_riv[j+1] + alpha*H_riv[j]) # + 8/3 * (dK_list[0] * (-1) / 2 / dz) * ((1-alpha)*H_riv[j+1] + alpha*H_riv[j])
#         c[-1] = (8*K_list[n_cell - 1] / (3*dz**2)) * ((1-alpha)*H_aq[j+1] + alpha*H_aq[j]) # + 8/3 * (dK_list[n_cell - 1] * (-1) / 2 / dz) * ((1-alpha)*H_aq[j+1] + alpha*H_aq[j])

#         B_fois_H_plus_c = tri_product(
#             lower_diagonal_B, diagonal_B, upper_diagonal_B, H_res[:, j]) + c

#         H_res[:, j+1] = solver(lower_diagonal_A, diagonal_A,
#                                 upper_diagonal_A, B_fois_H_plus_c)
#         print("test", j)
#         print(H_res[:, j+1])
#     print("finition cal HTK")
#     return H_res


@njit
def compute_T_stratified(
    Ss_list, moinslog10K_list, n_list, lambda_s_list, rhos_cs_list, all_dt, dz, H_res, H_riv, H_aq, nablaH, T_init, T_riv, T_aq, alpha=ALPHA, N_update_Mu=N_UPDATE_MU
):
    """Computes T(z, t) by solving the heat equation : dT/dt = ke Delta T + ae nabla H nabla T, for an heterogeneous column.

    Parameters
    ----------
    moinslog10k_list : float array
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
        initial condition T(z, t=0).
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

    mu_list = compute_Mu(T_init)
    rho_mc_m_list = n_list * RHO_W * C_W + (1 - n_list) * rhos_cs_list
    K_list = (RHO_W * G * 10.0**-moinslog10K_list) * 1.0 / mu_list
    lambda_m_list = (
        n_list * (LAMBDA_W) ** 0.5 + (1.0 - n_list) * (lambda_s_list) ** 0.5
    ) ** 2

    ke_list = lambda_m_list / rho_mc_m_list
    ae_list = RHO_W * C_W * K_list / rho_mc_m_list

    n_cell = len(T_init)
    n_times = len(all_dt) + 1

    # Now we can compute T(z, t)

    T_res = zeros((n_cell, n_times), float32)
    T_res[:, 0] = T_init

    for j, dt in enumerate(all_dt):
        # Update of Mu(T) after N_update_Mu iterations:
        if j % N_update_Mu == 1:
            mu_list = compute_Mu(T_res[:, j - 1])

        # Compute T at time times[j+1]

        # Defining the 3 diagonals of B
        lower_diagonal = (ke_list[1:] * alpha / dz**2) - (
            alpha * ae_list[1:] / (2 * dz)
        ) * nablaH[1:, j]
        lower_diagonal[-1] = (
            4 * ke_list[n_cell - 1] * alpha / (3 * dz**2)
            - (2 * alpha * ae_list[n_cell - 1] / (3 * dz)) * nablaH[n_cell - 1, j]
        )

        diagonal = 1 / dt - 2 * ke_list * alpha / dz**2
        diagonal[0] = 1 / dt - 4 * ke_list[0] * alpha / dz**2
        diagonal[-1] = 1 / dt - 4 * ke_list[n_cell - 1] * alpha / dz**2

        upper_diagonal = (ke_list[:-1] * alpha / dz**2) + (
            alpha * ae_list[:-1] / (2 * dz)
        ) * nablaH[:-1, j]
        upper_diagonal[0] = (
            4 * ke_list[0] * alpha / (3 * dz**2)
            + (2 * alpha * ae_list[0] / (3 * dz)) * nablaH[0, j]
        )

        # Defining c
        c = zeros(n_cell, float32)
        c[0] = (
            8 * ke_list[0] * (1 - alpha) / (3 * dz**2)
            - 2 * (1 - alpha) * ae_list[0] * nablaH[0, j] / (3 * dz)
        ) * T_riv[j + 1] + (
            8 * ke_list[0] * alpha / (3 * dz**2)
            - 2 * alpha * ae_list[0] * nablaH[0, j] / (3 * dz)
        ) * T_riv[
            j
        ]
        c[-1] = (
            8 * ke_list[n_cell - 1] * (1 - alpha) / (3 * dz**2)
            + 2 * (1 - alpha) * ae_list[n_cell - 1] * nablaH[n_cell - 1, j] / (3 * dz)
        ) * T_aq[j + 1] + (
            8 * ke_list[n_cell - 1] * alpha / (3 * dz**2)
            + 2 * alpha * ae_list[n_cell - 1] * nablaH[n_cell - 1, j] / (3 * dz)
        ) * T_aq[
            j
        ]

        B_fois_T_plus_c = (
            tri_product(lower_diagonal, diagonal, upper_diagonal, T_res[:, j]) + c
        )

        # Defining the 3 diagonals of A
        lower_diagonal = (
            -(ke_list[1:] * (1 - alpha) / dz**2)
            + ((1 - alpha) * ae_list[1:] / (2 * dz)) * nablaH[1:, j]
        )
        lower_diagonal[-1] = (
            -4 * ke_list[n_cell - 1] * (1 - alpha) / (3 * dz**2)
            + (2 * (1 - alpha) * ae_list[n_cell - 1] / (3 * dz)) * nablaH[n_cell - 1, j]
        )

        diagonal = 1 / dt + 2 * ke_list * (1 - alpha) / dz**2
        diagonal[0] = 1 / dt + 4 * ke_list[0] * (1 - alpha) / dz**2
        diagonal[-1] = 1 / dt + 4 * ke_list[n_cell - 1] * (1 - alpha) / dz**2

        upper_diagonal = (
            -(ke_list[:-1] * (1 - alpha) / dz**2)
            - ((1 - alpha) * ae_list[:-1] / (2 * dz)) * nablaH[:-1, j]
        )
        upper_diagonal[0] = (
            -4 * ke_list[0] * (1 - alpha) / (3 * dz**2)
            - (2 * (1 - alpha) * ae_list[0] / (3 * dz)) * nablaH[0, j]
        )

        try:
            T_res[:, j + 1] = solver(
                lower_diagonal, diagonal, upper_diagonal, B_fois_T_plus_c
            )
        except Exception:
            A = zeros((n_cell, n_cell), float32)
            A[0, 0] = diagonal[0]
            A[0, 1] = upper_diagonal[0]
            for i in range(1, n_cell - 1):
                A[i, i - 1] = lower_diagonal[i - 1]
                A[i, i] = diagonal[i]
                A[i, i + 1] = upper_diagonal[i]
            A[n_cell - 1, n_cell - 1] = diagonal[n_cell - 1]
            A[n_cell - 1, n_cell - 2] = lower_diagonal[n_cell - 2]
            T_res[:, j + 1] = solve(A, B_fois_T_plus_c)

    return T_res 


@njit
def compute_H_stratified(array_K, array_Ss, list_zLow, z_solve, T_init, inter_cara, moinslog10K_list, Ss_list, all_dt, isdtconstant, dz, H_init, H_riv, H_aq, alpha=ALPHA):
    """ Computes H(z, t) by solving the diffusion equation : Ss dH/dT = K Delta H, for an heterogeneous column.

    Parameters
    ----------
    moinslog10k_list : float array
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
    H_res[:, 0] = H_init[:]

    ## case without div
    mu_list = compute_Mu(T_init)
    K_list = (RHO_W * G * 10.0**-moinslog10K_list) * 1.0 / mu_list
    # K_list = 10.0 ** -moinslog10K_list
    ## case without div
    KsurSs_list = K_list/Ss_list
    dK_list = zeros(n_cell, float32)
    dK_list[0] = (K_list[1] - K_list[0]) / dz
    dK_list[-1] = (K_list[-1] - K_list[-2]) / dz
    for idx in range(1, len(dK_list) - 1):
        dK_list[idx] = (K_list[idx+1] - K_list[idx-1]) / 2 / dz
    

    # Check if dt is constant :
    if isdtconstant:  # dt is constant so A and B are constant
        dt = all_dt[0]

        # Defining the 3 diagonals of B
        # on lower_diagonal and upper_diagonal we add the term of divK
        lower_diagonal_B = K_list[1:]*alpha/dz**2  
        lower_diagonal_B[-1] = 4*K_list[n_cell - 1]*alpha/(3*dz**2)  

        diagonal_B =  Ss_list * 1/dt - 2*K_list*alpha/dz**2
        diagonal_B[0] =  Ss_list[0] * 1/dt - 4*K_list[0]*alpha/dz**2
        diagonal_B[-1] =  Ss_list[n_cell - 1] * 1/dt - 4*K_list[n_cell - 1]*alpha/dz**2

        upper_diagonal_B = K_list[:-1]*alpha/dz**2 
        upper_diagonal_B[0] = 4*K_list[0]*alpha/(3*dz**2) 

        # Defining the 3 diagonals of A
        lower_diagonal_A = - K_list[1:]*(1-alpha)/dz**2  
        lower_diagonal_A[-1] = - 4*K_list[n_cell - 1]*(1-alpha)/(3*dz**2)  

        diagonal_A =  Ss_list * 1/dt + 2*K_list*(1-alpha)/dz**2
        diagonal_A[0] =  Ss_list[0] * 1/dt + 4*K_list[0]*(1-alpha)/dz**2
        diagonal_A[-1] =  Ss_list[n_cell - 1] * 1/dt + 4*K_list[n_cell - 1]*(1-alpha)/dz**2

        upper_diagonal_A = - K_list[:-1]*(1-alpha)/dz**2 
        upper_diagonal_A[0] = - 4*K_list[0]*(1-alpha)/(3*dz**2)  

        # correction of numerical schema on the interface of different layers
         
        for tup_idx in range(len(inter_cara)):
            K1 = array_K[tup_idx]
            K2 = array_K[tup_idx + 1]
            
            if inter_cara[tup_idx][1] == 0: # sampling point coincide with change of interface
                pos_idx = int(inter_cara[tup_idx][0])
                diagonal_B[pos_idx] = Ss_list[pos_idx] * 1/dt - (K1 + K2) *alpha/dz**2
                lower_diagonal_B[pos_idx - 1] = K1*alpha/dz**2
                upper_diagonal_B[pos_idx] = K2*alpha/dz**2
                diagonal_A[pos_idx] = Ss_list[pos_idx] * 1/dt + (K1 + K2) *(1-alpha)/dz**2
                lower_diagonal_A[pos_idx - 1] = - K1*(1-alpha)/dz**2
                upper_diagonal_A[pos_idx] = - K2*(1-alpha)/dz**2
                
            else: # sampling point are distributed on both sides of the interface with distance x*dz and (1-x)*dz
                pos_idx = int(inter_cara[tup_idx][0])
                x = (list_zLow[tup_idx] - z_solve[pos_idx]) / (z_solve[pos_idx+1] - z_solve[pos_idx])
                Keq = (1 / (x/K1 + (1-x)/K2))
                diagonal_B[pos_idx] = Ss_list[pos_idx]*1/dt - (K1 + Keq) *alpha/dz**2
                lower_diagonal_B[pos_idx - 1] = K1*alpha/dz**2
                upper_diagonal_B[pos_idx] = Keq*alpha/dz**2
                diagonal_A[pos_idx] = Ss_list[pos_idx]*1/dt + (K1 + Keq) *(1-alpha)/dz**2
                lower_diagonal_A[pos_idx - 1] = - K1*(1-alpha)/dz**2
                upper_diagonal_A[pos_idx] = - Keq*(1-alpha)/dz**2

                diagonal_B[pos_idx + 1] = Ss_list[pos_idx]*1/dt - (K2 + Keq) *alpha/dz**2
                lower_diagonal_B[pos_idx] = Keq*alpha/dz**2
                upper_diagonal_B[pos_idx + 1] = K2*alpha/dz**2
                diagonal_A[pos_idx + 1] = Ss_list[pos_idx]*1/dt + (K2 + Keq) *(1-alpha)/dz**2
                lower_diagonal_A[pos_idx] = - Keq*(1-alpha)/dz**2
                upper_diagonal_A[pos_idx + 1] = - K2*(1-alpha)/dz**2

        for j in range(n_times - 1):
            # Compute H at time times[j+1]

            # Defining c
            c = zeros(n_cell, float32)
            c[0] = (8*K_list[0] / (3*dz**2)) * \
                ((1-alpha)*H_riv[j+1] + alpha*H_riv[j])
            c[-1] = (8*K_list[n_cell - 1] / (3*dz**2)) * \
                ((1-alpha)*H_aq[j+1] + alpha*H_aq[j])
            B_fois_H_plus_c = tri_product(
                lower_diagonal_B, diagonal_B, upper_diagonal_B, H_res[:, j]) + c

            H_res[:, j+1] = solver(lower_diagonal_A, diagonal_A,
                                   upper_diagonal_A, B_fois_H_plus_c)
            
        
    else:  # dt is not constant so A and B and not constant
        for j, dt in enumerate(all_dt):
            # Compute H at time times[j+1]

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
            lower_diagonal_A[-1] = - 4 * \
                KsurSs_list[n_cell - 1]*(1-alpha)/(3*dz**2)

            diagonal_A = 1/dt + 2*KsurSs_list*(1-alpha)/dz**2
            diagonal_A[0] = 1/dt + 4*KsurSs_list[0]*(1-alpha)/dz**2
            diagonal_A[-1] = 1/dt + 4*KsurSs_list[n_cell - 1]*(1-alpha)/dz**2

            upper_diagonal_A = - KsurSs_list[:-1]*(1-alpha)/dz**2
            upper_diagonal_A[0] = - 4*KsurSs_list[0]*(1-alpha)/(3*dz**2)

            for tup_idx in range(len(inter_cara)):
                K1 = array_K[tup_idx]
                K2 = array_K[tup_idx + 1]
        
                if inter_cara[tup_idx][1] == 0: # sampling point coincide with change of interface
                    pos_idx = int(inter_cara[tup_idx][0])
                    diagonal_B[pos_idx] = Ss_list[pos_idx] * 1/dt - (K1 + K2) *alpha/dz**2
                    lower_diagonal_B[pos_idx - 1] = K1*alpha/dz**2
                    upper_diagonal_B[pos_idx] = K2*alpha/dz**2
                    diagonal_A[pos_idx] = Ss_list[pos_idx] * 1/dt + (K1 + K2) *(1-alpha)/dz**2
                    lower_diagonal_A[pos_idx - 1] = - K1*(1-alpha)/dz**2
                    upper_diagonal_A[pos_idx] = - K2*(1-alpha)/dz**2
            
                else: # sampling point are distributed on both sides of the interface with distance x*dz and (1-x)*dz
                    pos_idx = int(inter_cara[tup_idx][0])
                    x = (list_zLow[tup_idx] - z_solve[pos_idx]) / (z_solve[pos_idx+1] - z_solve[pos_idx])
                    Keq = (1 / (x/K1 + (1-x)/K2))
                    diagonal_B[pos_idx] = Ss_list[pos_idx]*1/dt - (K1 + Keq) *alpha/dz**2
                    lower_diagonal_B[pos_idx - 1] = K1*alpha/dz**2
                    upper_diagonal_B[pos_idx] = Keq*alpha/dz**2
                    diagonal_A[pos_idx] = Ss_list[pos_idx]*1/dt + (K1 + Keq) *(1-alpha)/dz**2
                    lower_diagonal_A[pos_idx - 1] = - K1*(1-alpha)/dz**2
                    upper_diagonal_A[pos_idx] = - Keq*(1-alpha)/dz**2

                    diagonal_B[pos_idx + 1] = Ss_list[pos_idx]*1/dt - (K2 + Keq) *alpha/dz**2
                    lower_diagonal_B[pos_idx] = Keq*alpha/dz**2
                    upper_diagonal_B[pos_idx + 1] = K2*alpha/dz**2
                    diagonal_A[pos_idx + 1] = Ss_list[pos_idx]*1/dt + (K2 + Keq) *(1-alpha)/dz**2
                    lower_diagonal_A[pos_idx] = - Keq*(1-alpha)/dz**2
                    upper_diagonal_A[pos_idx + 1] = - K2*(1-alpha)/dz**2


            # Defining c
            c = zeros(n_cell, float32)
            c[0] = (8*KsurSs_list[0] / (3*dz**2)) * \
                ((1-alpha)*H_riv[j+1] + alpha*H_riv[j])
            c[-1] = (8*KsurSs_list[n_cell - 1] / (3*dz**2)) * \
                ((1-alpha)*H_aq[j+1] + alpha*H_aq[j])

            B_fois_H_plus_c = (
                tri_product(lower_diagonal_B, diagonal_B, upper_diagonal_B, H_res[:, j])
                + c
            )


            H_res[:, j+1] = solver(lower_diagonal_A, diagonal_A,
                                   upper_diagonal_A, B_fois_H_plus_c)

    return H_res


@njit
def compute_HTK_stratified(lambda_s_list, rhos_cs_list, n_list, T_init, array_K, array_Ss, list_zLow, z_solve, inter_cara, moinslog10k_list, Ss_list, all_dt, isdtconstant, dz, H_init, H_riv, H_aq, alpha=ALPHA):
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
    H_res[:, 0] = H_init[:]
    ## case with div
    mu_list = compute_Mu(T_init)
    rho_mc_m_list = n_list * RHO_W * C_W + (1 - n_list) * rhos_cs_list
    K_list = (RHO_W * G * 10.0 ** -moinslog10k_list) * 1./mu_list # ici k et K n'est pas le meme
    lambda_m_list = (n_list * (LAMBDA_W) ** 0.5 +(1.0 - n_list) * (lambda_s_list) ** 0.5) ** 2
    ke_list = lambda_m_list / rho_mc_m_list
    ae_list = RHO_W * C_W * K_list / rho_mc_m_list
    ## case with div

    ## case without div
    # K_list = 10.0 ** -moinslog10K_list
    ## case without div
    KsurSs_list = K_list/Ss_list
    dK_list = zeros(n_cell, float32)
    dK_list[0] = (K_list[1] - K_list[0]) / dz
    dK_list[-1] = (K_list[-1] - K_list[-2]) / dz
    for idx in range(1, len(dK_list) - 1):
        dK_list[idx] = (K_list[idx+1] - K_list[idx-1]) / 2 / dz
    

    # Check if dt is constant :
    if isdtconstant:  # dt is constant so A and B are constant
        dt = all_dt[0]

        # Defining the 3 diagonals of B
        # on lower_diagonal and upper_diagonal we add the term of divK
        lower_diagonal_B = K_list[1:]*alpha/dz**2   + dK_list[1:] * alpha / (2*dz)
        lower_diagonal_B[-1] = 4*K_list[n_cell - 1]*alpha/(3*dz**2)    + 4*dK_list[n_cell - 1] * alpha / (3*2*dz)

        diagonal_B =  Ss_list * 1/dt - 2*K_list*alpha/dz**2
        diagonal_B[0] =  Ss_list[0] * 1/dt - 4*K_list[0]*alpha/dz**2
        diagonal_B[-1] =  Ss_list[n_cell - 1] * 1/dt - 4*K_list[n_cell - 1]*alpha/dz**2

        upper_diagonal_B = K_list[:-1]*alpha/dz**2   - dK_list[:-1]*alpha / (2*dz)
        upper_diagonal_B[0] = 4*K_list[0]*alpha/(3*dz**2)   - 4*dK_list[0]*alpha / (3*2*dz)

        # Defining the 3 diagonals of A
        lower_diagonal_A = - K_list[1:]*(1-alpha)/dz**2   - dK_list[1:] * (1-alpha) / (2*dz)
        lower_diagonal_A[-1] = - 4*K_list[n_cell - 1]*(1-alpha)/(3*dz**2)   - 4 * dK_list[n_cell - 1] * (1-alpha) / (3*2*dz)

        diagonal_A =  Ss_list * 1/dt + 2*K_list*(1-alpha)/dz**2
        diagonal_A[0] =  Ss_list[0] * 1/dt + 4*K_list[0]*(1-alpha)/dz**2
        diagonal_A[-1] =  Ss_list[n_cell - 1] * 1/dt + 4*K_list[n_cell - 1]*(1-alpha)/dz**2

        upper_diagonal_A = - K_list[:-1]*(1-alpha)/dz**2    + dK_list[:-1]*(1-alpha)/(2*dz)
        upper_diagonal_A[0] = - 4*K_list[0]*(1-alpha)/(3*dz**2)    + 4 * dK_list[0]*(1-alpha)/(3*2*dz)

        ## correction of numerical schema on the interface of different layers
        # for tup_idx in range(len(inter_cara)):
        #     array_KsurSs = array_K / array_Ss
        #     K1 = array_K[tup_idx]
        #     K2 = array_K[tup_idx + 1]
            
        #     if inter_cara[tup_idx][1] == 0: # sampling point coincide with change of interface
        #         pos_idx = int(inter_cara[tup_idx][0])
        #         diagonal_B[pos_idx] = Ss_list[pos_idx] * 1/dt - (K1 + K2) *alpha/dz**2
        #         lower_diagonal_B[pos_idx - 1] = K1*alpha/dz**2
        #         upper_diagonal_B[pos_idx] = K2*alpha/dz**2
        #         diagonal_A[pos_idx] = Ss_list[pos_idx] * 1/dt + (K1 + K2) *(1-alpha)/dz**2
        #         lower_diagonal_A[pos_idx - 1] = - K1*(1-alpha)/dz**2
        #         upper_diagonal_A[pos_idx] = - K2*(1-alpha)/dz**2
                
        #     else: # sampling point are distributed on both sides of the interface with distance x*dz and (1-x)*dz
        #         pos_idx = int(inter_cara[tup_idx][0])
        #         x = (list_zLow[tup_idx] - z_solve[pos_idx]) / (z_solve[pos_idx+1] - z_solve[pos_idx])
        #         Keq = (1 / (x/K1 + (1-x)/K2))
        #         diagonal_B[pos_idx] = Ss_list[pos_idx]*1/dt - (K1 + Keq) *alpha/dz**2
        #         lower_diagonal_B[pos_idx - 1] = K1*alpha/dz**2
        #         upper_diagonal_B[pos_idx] = Keq*alpha/dz**2
        #         diagonal_A[pos_idx] = Ss_list[pos_idx]*1/dt + (K1 + Keq) *(1-alpha)/dz**2
        #         lower_diagonal_A[pos_idx - 1] = - K1*(1-alpha)/dz**2
        #         upper_diagonal_A[pos_idx] = - Keq*(1-alpha)/dz**2

        #         diagonal_B[pos_idx + 1] = Ss_list[pos_idx]*1/dt - (K2 + Keq) *alpha/dz**2
        #         lower_diagonal_B[pos_idx] = Keq*alpha/dz**2
        #         upper_diagonal_B[pos_idx + 1] = K2*alpha/dz**2
        #         diagonal_A[pos_idx + 1] = Ss_list[pos_idx]*1/dt + (K2 + Keq) *(1-alpha)/dz**2
        #         lower_diagonal_A[pos_idx] = - Keq*(1-alpha)/dz**2
        #         upper_diagonal_A[pos_idx + 1] = - K2*(1-alpha)/dz**2

        for j in range(n_times - 1):
            # Compute H at time times[j+1]

            # Defining c
            c = zeros(n_cell, float32)
            c[0] = (8*K_list[0] / (3*dz**2)) * \
                ((1-alpha)*H_riv[j+1] + alpha*H_riv[j])
            c[-1] = (8*K_list[n_cell - 1] / (3*dz**2)) * \
                ((1-alpha)*H_aq[j+1] + alpha*H_aq[j])
            c = zeros(n_cell, float32)
            c[0] = (8*K_list[0] / (3*dz**2)) * ((1-alpha)*H_riv[j+1] + alpha*H_riv[j]) + 8/3 * (dK_list[0] * (-1) / 2 / dz) * ((1-alpha)*H_riv[j+1] + alpha*H_riv[j])
            c[-1] = (8*K_list[n_cell - 1] / (3*dz**2)) * ((1-alpha)*H_aq[j+1] + alpha*H_aq[j]) + 8/3 * (dK_list[n_cell - 1] * (-1) / 2 / dz) * ((1-alpha)*H_aq[j+1] + alpha*H_aq[j])

            B_fois_H_plus_c = tri_product(
                lower_diagonal_B, diagonal_B, upper_diagonal_B, H_res[:, j]) + c

            H_res[:, j+1] = solver(lower_diagonal_A, diagonal_A,
                                   upper_diagonal_A, B_fois_H_plus_c)
            
        
    else:  # dt is not constant so A and B and not constant
        for j, dt in enumerate(all_dt):
            # Compute H at time times[j+1]

            # Defining the 3 diagonals of B
            lower_diagonal = KsurSs_list[1:] * alpha / dz**2
            lower_diagonal[-1] = 4 * KsurSs_list[n_cell - 1] * alpha / (3 * dz**2)

            diagonal = 1 / dt - 2 * KsurSs_list * alpha / dz**2
            diagonal[0] = 1 / dt - 4 * KsurSs_list[0] * alpha / dz**2
            diagonal[-1] = 1 / dt - 4 * KsurSs_list[n_cell - 1] * alpha / dz**2

            upper_diagonal = KsurSs_list[:-1] * alpha / dz**2
            upper_diagonal[0] = 4 * KsurSs_list[0] * alpha / (3 * dz**2)

            # Defining c
            c = zeros(n_cell, float32)
            c[0] = (8 * KsurSs_list[0] / (3 * dz**2)) * (
                (1 - alpha) * H_riv[j + 1] + alpha * H_riv[j]
            )
            c[-1] = (8 * KsurSs_list[n_cell - 1] / (3 * dz**2)) * (
                (1 - alpha) * H_aq[j + 1] + alpha * H_aq[j]
            )

            B_fois_H_plus_c = (
                tri_product(lower_diagonal, diagonal, upper_diagonal, H_res[:, j]) + c
            )

            # Defining the 3 diagonals of A
            lower_diagonal = -KsurSs_list[1:] * (1 - alpha) / dz**2
            lower_diagonal[-1] = (
                -4 * KsurSs_list[n_cell - 1] * (1 - alpha) / (3 * dz**2)
            )

            diagonal = 1 / dt + 2 * KsurSs_list * (1 - alpha) / dz**2
            diagonal[0] = 1 / dt + 4 * KsurSs_list[0] * (1 - alpha) / dz**2
            diagonal[-1] = 1 / dt + 4 * KsurSs_list[n_cell - 1] * (1 - alpha) / dz**2

            upper_diagonal = -KsurSs_list[:-1] * (1 - alpha) / dz**2
            upper_diagonal[0] = -4 * KsurSs_list[0] * (1 - alpha) / (3 * dz**2)

            H_res[:, j + 1] = solver(
                lower_diagonal, diagonal, upper_diagonal, B_fois_H_plus_c
            )

    return H_res
