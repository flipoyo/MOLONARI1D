"""
    author: Nicolas Matte
    session: MOLONARI 2023
"""

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
    full
)
from numpy.linalg import solve
from numba import njit

from layers import Layer
from solver import solver, tri_product
from params import Prior, PARAM_LIST
import numpy as np

# LAMBDA_W = 0 # test du cas purement advectif
LAMBDA_W = 0.6071
RHO_W = 1000
C_W = 4185
ALPHA = 0.4
EPSILON = 1e-9

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


def compute_energy(temp1, temp2, sigma2: float):
    norm2 = nansum((temp1 - temp2) ** 2)
    return 0.5 * norm2 / sigma2


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


'''def gelman_rubin(nb_current_iter, nb_param, nb_layer, chains, threshold=1.1):
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
    return all(R < threshold)'''

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

def gelman_R_chap(nb_current_iter, nb_param, nb_layer, chains, threshold=1.1):
    #Imput: chaînes de Markov calculées en parallèle

 
    R = zeros((nb_layer, nb_param))
    for l in range(nb_layer):  
        chains_layered = chains[:,:,l,:]
        _,n_chains,_,_ = chains.shape
        Var_intra = var(chains_layered,axis = 0)
        # Moyenne des variances intra-chaîne
        var_intra = mean(Var_intra, axis=0)

        # Moyennes de chaque chaîne
        means_chains = mean(chains_layered, axis=0)

        # Variance entre les moyennes des chaînes, dite inter-chaînes



        var_inter = var(means_chains,axis = 0)


        var_cible = (nb_current_iter - 1) / nb_current_iter * var_intra + var_inter 
        
        V_chap = var_cible + var_inter / n_chains
        
        #print('Var_intra = ',Var_intra)
        #print('means_chains = ',means_chains)
        P1 = zeros(nb_param)
        P2 = zeros(nb_param)
        P3 = zeros(nb_param)
        cov1 = zeros(nb_param)
        cov2 = zeros(nb_param)
        var_V_chap = zeros(nb_param)

        
        for j in range(nb_param):
            P1[j] = ((nb_current_iter - 1)/nb_current_iter)**2 / n_chains * var(Var_intra[:,j])
            P2[j] = (n_chains+1)**2/(n_chains*nb_current_iter)**2 * 2/(n_chains-1)*(var_inter[j]*nb_current_iter)**2
            #print('var_intra[j]',var_intra[j]) 
            #print('np.mean(means_chains,axis = 0)[j]',np.mean(means_chains,axis = 0)[j])
            cov1[j] = np.cov(Var_intra[:,j],(means_chains[:,j])**2)[0,1]
            cov2[j] = np.cov(Var_intra[:,j],means_chains[:,j])[0,1]
            #print(cov1[j].shape)
            #print(cov2[j].shape)
            P3[j] = 2*(n_chains+1)*(nb_current_iter-1)/n_chains*nb_current_iter**2 * nb_current_iter/n_chains * abs(cov1[j]- 2*np.mean(means_chains)*cov2[j])
            var_V_chap[j] = P1[j] + P2[j] + P3[j]
            #print('partie = ',cov1[j]- 2*np.mean(means_chains)*cov2[j])

            #if np.isclose(var_intra[j], 0) :
                #R[l,j] = 2
            
        df = 2 * V_chap**2 / var_V_chap 
        #var_cible += 1e-5
        R[l] =  sqrt(V_chap/var_intra) #* (df + 3) / (df + 1)
        # print('V_chap = ',V_chap)
        # print('var_V_chap ',var_V_chap )
        #print('df = ', df)
    #print("R = ", R)

    """if nb_current_iter > 20:
        return R < threshold, R
    else:
        return False, R"""

    return all(R < threshold), R


@njit
def compute_H(moinslog10IntrinK, Ss, all_dt, isdtconstant, dz, H_init, H_riv, H_aq, alpha=ALPHA):
    """ Computes H(z, t) by solving the diffusion equation : Ss dH/dT = K Delta H, for  an homogeneous column.

    Parameters
    ----------
    moinslog10IntrinK : float
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

    K = 10.0 ** -moinslog10IntrinK
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
    Ss_list, moinslog10IntrinK_list, n_list, lambda_s_list, rhos_cs_list, all_dt, dz, H_res, H_riv, H_aq, nablaH, T_init, T_riv, T_aq, alpha=ALPHA
):
    """ Computes T(z, t) by solving the heat equation : dT/dt = ke Delta T + ae nabla H nabla T, for an heterogeneous column.

    Parameters
    ----------
    moinslog10IntrinK_list : float array
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
    K_list = 10.0 ** -moinslog10IntrinK_list
    lambda_m_list = (n_list * (LAMBDA_W) ** 0.5 +
                     (1.0 - n_list) * (lambda_s_list) ** 0.5) ** 2

    ke_list = lambda_m_list / rho_mc_m_list
    ae_list = RHO_W * C_W * K_list / rho_mc_m_list

    n_cell = len(T_init)
    n_times = len(all_dt) + 1

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
def interface_transition(stratified_data, transition_semilenght=3):
    indexes = list()
    data_trans = zeros(shape(stratified_data))

    for i in range(shape(stratified_data)[0] - 1):
        eps = stratified_data[i + 1] - stratified_data[i]
        if abs(eps) >= 10 ** (-15):
            indexes.append(i)

    for i in range(shape(stratified_data)[0]):
        data_trans[i] = stratified_data[i]
    for index in indexes:
        data_inf = stratified_data[index]
        data_sup = stratified_data[index + 1]
        for j in range(transition_semilenght):
            data_trans[index - transition_semilenght + j] = data_inf + (
                data_sup - data_inf
            ) * j / (2 * transition_semilenght)

            data_trans[index + j] = data_inf + (data_sup - data_inf) * (
                j + transition_semilenght
            ) / (2 * transition_semilenght)
    return data_trans


@njit
def compute_H_stratified(array_K, array_Ss, list_zLow, z_solve, inter_cara, moinslog10IntrinK_list, Ss_list, all_dt, isdtconstant, dz, H_init, H_riv, H_aq, alpha=ALPHA):
    """ Computes H(z, t) by solving the diffusion equation : Ss dH/dT = K Delta H, for an heterogeneous column.

    Parameters
    ----------
    moinslog10IntrinK_list : float array
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
    K_list = 10.0 ** -moinslog10IntrinK_list
    KsurSs_list = K_list/Ss_list

    # Check if dt is constant :
    if isdtconstant:  # dt is constant so A and B are constant
        dt = all_dt[0]

        # Defining the 3 diagonals of B
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

        ## zhan Nov6
        for tup_idx in range(len(inter_cara)):
            array_KsurSs = array_K / array_Ss
            K1 = array_K[tup_idx]
            K2 = array_K[tup_idx + 1]
            # k1 = array_K[tup_idx] / array_Ss[tup_idx]
            # k2 = array_K[tup_idx + 1]/ array_Ss[tup_idx+1]
            if inter_cara[tup_idx][1] == 0:
                pos_idx = int(inter_cara[tup_idx][0])
                diagonal_B[pos_idx] = Ss_list[pos_idx] * 1/dt - (K1 + K2) *alpha/dz**2
                lower_diagonal_B[pos_idx - 1] = K1*alpha/dz**2
                upper_diagonal_B[pos_idx] = K2*alpha/dz**2
                diagonal_A[pos_idx] = Ss_list[pos_idx] * 1/dt + (K1 + K2) *(1-alpha)/dz**2
                lower_diagonal_A[pos_idx - 1] = - K1*(1-alpha)/dz**2
                upper_diagonal_A[pos_idx] = - K2*(1-alpha)/dz**2
                
            else:
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




        ## end

        # ## zhan: mod Nov 3 cas symetric
        # diagonal_B[len(diagonal_B) // 2] = 1/dt - (KsurSs_list[0] + KsurSs_list[-1]) *alpha/dz**2
        # lower_diagonal_B[len(diagonal_B) // 2 - 1] = KsurSs_list[0]*alpha/dz**2
        # upper_diagonal_B[len(diagonal_B) // 2] = KsurSs_list[-1]*alpha/dz**2
        # diagonal_A[len(diagonal_A) // 2] = 1/dt + (KsurSs_list[0] + KsurSs_list[-1]) *(1-alpha)/dz**2
        # lower_diagonal_A[len(diagonal_A) // 2 - 1] = - KsurSs_list[0]*(1-alpha)/dz**2
        # upper_diagonal_A[len(diagonal_A) // 2] = - KsurSs_list[-1]*(1-alpha)/dz**2
        # ##

        # ## zhan: mod Nov 6 cas asymetric
        # k1 = KsurSs_list[0]
        # k2 = KsurSs_list[-1]
        # keq = 1 / (1/k1/2 + 1/k2/2)
        # diagonal_B[len(diagonal_B) //  2 - 1] = 1/dt - (k1 + keq) *alpha/dz**2
        # lower_diagonal_B[len(diagonal_B) //  2 - 1 - 1] = k1*alpha/dz**2
        # upper_diagonal_B[len(diagonal_B) //  2 - 1] = keq*alpha/dz**2
        # diagonal_A[len(diagonal_A) //  2 - 1] = 1/dt + (k1 + keq) *(1-alpha)/dz**2
        # lower_diagonal_A[len(diagonal_A) //  2 - 1 - 1] = - k1*(1-alpha)/dz**2
        # upper_diagonal_A[len(diagonal_A) //  2 - 1] = - keq*(1-alpha)/dz**2

        # diagonal_B[len(diagonal_B) //  2] = 1/dt - (k2 + keq) *alpha/dz**2
        # lower_diagonal_B[len(diagonal_B) //  2 - 1] = keq*alpha/dz**2
        # upper_diagonal_B[len(diagonal_B) //  2] = k2*alpha/dz**2
        # diagonal_A[len(diagonal_A) //  2] = 1/dt + (k2 + keq) *(1-alpha)/dz**2
        # lower_diagonal_A[len(diagonal_A) //  2 - 1] = - keq*(1-alpha)/dz**2
        # upper_diagonal_A[len(diagonal_A) //  2] = - k2*(1-alpha)/dz**2
        # ##

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