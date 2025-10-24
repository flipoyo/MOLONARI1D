from numpy import float32, zeros

from numpy.linalg import solve

# import numpy as np
from numba import njit
import numpy as np

from pyheatmy.solver import solver, tri_product
from pyheatmy.config import *

# ATTENTION : Revoir la définition de ALPHA (schéma semi-implicite)

# ATTENTION : Pour l'instant, on définit les paramètres physiques d'adimensionnement de manière manuelle. Il faudra ensuite que le 
# système puisse les déterminer automatiquement. Par exemple, pour DH_0/DT_0, on pourrait prendre la valeur moyenne ou initiale
# entre la rivière et l'acquifère sur la durée de l'étude. On les place ici mais il faut les placer dans config.py 

# Paramètres physiques d'adimensionnement :
DH_0 = 0.01 # Différence de charge spécifique, (en m) ???
DT_0 = 10 # Différence de température caractéristique, UNITE °C ???
L_0 = 0.4 # Hauteur caractéristique de la colonne d'eau (en m)
P_0 = 24*3600 # Période caractéristique de variation du signal, (en s)



# Classe définissant et initiant les paramètres physiques des systèmes linéaires de la classe H_stratified et T_stratified
class Linear_system:
    def __init__(
        self,
        Ss_list,
        moinslog10IntrinK_list,
        n_list,
        lambda_s_list,
        rhos_cs_list,
        all_dt,
        dz,
        H_init,
        T_init,
    ):
        self.moinslog10IntrinK_list = moinslog10IntrinK_list
        self.T_init = T_init
        self.n_list = n_list
        self.rhos_cs_list = rhos_cs_list
        self.lambda_s_list = lambda_s_list
        self.H_init = H_init
        self.all_dt = all_dt
        self.dz = dz
        self.Ss_list = Ss_list
        self.calc_physical_param()

    # @njit
    def compute_Mu(self, T):
        # mu = MU_A * np.exp(MU_B * 1.0 / T + MU_C * T + MU_D * (T**2)) # Error when executing the MCMC : RuntimeWarning: overflow encountered in exp
        # mu = MU_A * np.exp(MU_B * 1.0 / T + MU_C * T + MU_D * (T**2))
        mu = DEFAULT_MU
        return mu

    # @njit
    def compute_K(self, moinslog10IntrinK_list):
        return (RHO_W * G * 10.0**-moinslog10IntrinK_list) * 1.0 / self.mu_list

    def compute_n_cell(self):
        return len(self.H_init)

    def compute_n_times(self):
        return len(self.all_dt) + 1

    def compute_rho_mc_m_list(self):
        return self.n_list * RHO_W * C_W + (1 - self.n_list) * self.rhos_cs_list

    def compute_lambda_m_list(self):
        return (
            self.n_list * (LAMBDA_W) ** 0.5
            + (1.0 - self.n_list) * (self.lambda_s_list) ** 0.5
        ) ** 2

    def compute_ke_list(self):
        return self.lambda_m_list / self.rho_mc_m_list

    def compute_ae_list(self):
        return RHO_W * C_W * self.K_list / self.rho_mc_m_list

    def compute_dK_list(self, K_list, n_cell, dz):
        list = zeros(n_cell, float32)
        list[0] = (K_list[1] - K_list[0]) / dz
        list[-1] = (K_list[-1] - K_list[-2]) / dz
        for idx in range(1, len(list) - 1):
            list[idx] = (K_list[idx + 1] - K_list[idx - 1]) / (2 * dz)
        return list

    def compute_H_res(self):
        H_res = zeros((self.n_cell, self.n_times), float32)
        H_res[:, 0] = self.H_init[:]
        return H_res

    def compute_KsurSs_list(self):
        return self.K_list / self.Ss_list
    
    def calc_physical_param(self):
        self.n_cell = self.compute_n_cell()
        self.n_times = self.compute_n_times()
        self.mu_list = self.compute_Mu(self.T_init)
        self.K_list = self.compute_K(self.moinslog10IntrinK_list)
        self.rho_mc_m_list = self.compute_rho_mc_m_list()
        self.lambda_m_list = self.compute_lambda_m_list()
        self.ke_list = self.compute_ke_list()
        self.ae_list = self.compute_ae_list()
        self.H_res = self.compute_H_res()
        self.dK_list = self.compute_dK_list(self.K_list, self.n_cell, self.dz)
        self.KsurSs_list = self.compute_KsurSs_list()


# Classe qui définit le système linéaire pour l'équation de la diffusivité
class H_stratified(Linear_system):
    def __init__(
        self,
        Ss_list,
        moinslog10IntrinK_list,
        n_list,
        lambda_s_list,
        rhos_cs_list,
        all_dt,
        q_list,
        dz,
        H_init,
        H_riv,
        H_aq,
        T_init,
        array_K,
        array_Ss,
        list_zLow,
        z_solve,
        inter_cara,
        isdtconstant,
        alpha=ALPHA,
    ):
        super().__init__(
            Ss_list,
            moinslog10IntrinK_list,
            n_list,
            lambda_s_list,
            rhos_cs_list,
            all_dt,
            dz,
            H_init,
            T_init,
        )
        self.array_K = array_K
        self.array_Ss = array_Ss
        self.list_zLow = list_zLow
        self.z_solve = z_solve
        self.T_init = T_init
        self.inter_cara = inter_cara
        self.moinslog10IntrinK_list = moinslog10IntrinK_list
        self.Ss_list = Ss_list
        self.all_dt = all_dt
        self.isdtconstant = isdtconstant
        self.dz = dz
        self.H_init = H_init
        self.H_riv = H_riv
        self.H_aq = H_aq
        self.alpha = alpha
        self.heat_source = q_list
        self.calc_param_adim()

    def compute_gamma_list(self):
        return MU_W * (L_0**2) * (self.Ss_list) / (RHO_W * (10.0**-self.moinslog10IntrinK_list) * G * P_0)
    
    def compute_H_adim_res(self):
        H_adim_res = zeros((self.n_cell, self.n_times), float32)
        H_adim_res[:, 0] = (self.H_init[:] - self.H_init[0]) / DH_0
        return H_adim_res
    
    def compute_H_res_from_H_adim_res(self):
        self.H_res = self.H_adim_res * DH_0 + self.H_init[0]
        return self.H_res

    def calc_param_adim(self):
        """Calcul des paramètres adimensionnés"""
        self.gamma = self.compute_gamma_list()
        self.dz_adim = self.dz / L_0
        self.H_adim_res = self.compute_H_adim_res()

    def compute_H_stratified(self): # OK
        if self.isdtconstant.all():
            self.compute_H_constant_dt()
        else:
            self.compute_H_variable_dt()
        return self.H_res

    def compute_H_constant_dt(self):    # OK
        dt = self.all_dt[0]
        dt_adim = dt / P_0

        lower_diagonal_B, diagonal_B, upper_diagonal_B = self.compute_B_diagonals(dt_adim)
        lower_diagonal_A, diagonal_A, upper_diagonal_A = self.compute_A_diagonals(dt_adim)

        for tup_idx in range(len(self.inter_cara)): # On boucle sur les layers
            self.correct_numerical_schema(
                tup_idx,
                lower_diagonal_B,
                diagonal_B,
                upper_diagonal_B,
                lower_diagonal_A,
                diagonal_A,
                upper_diagonal_A,
            )

        for j in range(self.n_times - 1):
            c = self.compute_c(j)
            B_fois_H_plus_c = (
                tri_product(
                    lower_diagonal_B, diagonal_B, upper_diagonal_B, self.H_adim_res[:, j]
                )
                + c
            )
            self.H_adim_res[:, j + 1] = solver(
                lower_diagonal_A, diagonal_A, upper_diagonal_A, B_fois_H_plus_c
            )

        # Re-dimensionnement H_adim_res → H_res
        self.H_res = self.compute_H_res_from_H_adim_res()

    def nablaH(self):  
        nablaH = np.zeros((self.n_cell, self.n_times), np.float32)

        nablaH[0, :] = 2 * (self.H_res[1, :] - self.H_riv) / (3 * self.dz)

        for i in range(1, self.n_cell - 1):
            nablaH[i, :] = (self.H_res[i + 1, :] - self.H_res[i - 1, :]) / (2 * self.dz)

        nablaH[self.n_cell - 1, :] = (
            2 * (self.H_aq - self.H_res[self.n_cell - 2, :]) / (3 * self.dz)
        )
        return nablaH
    
    def nablaH_adim(self):  # OK
        nablaH_adim = np.zeros((self.n_cell, self.n_times), np.float32)

        H_adim_riv = (self.H_riv - self.H_init[0]) / DH_0
        nablaH_adim[0, :] = 2 * (self.H_adim_res[1, :] - H_adim_riv) / (3 * self.dz_adim)

        for i in range(1, self.n_cell - 1):
            nablaH_adim[i, :] = (self.H_adim_res[i + 1, :] - self.H_adim_res[i - 1, :]) / (2 * self.dz_adim)

        H_adim_aq = (self.H_aq - self.H_init[0]) / DH_0
        nablaH_adim[self.n_cell - 1, :] = (
            2 * (H_adim_aq - self.H_adim_res[self.n_cell - 2, :]) / (3 * self.dz_adim)
        )
        return nablaH_adim

    def compute_H_variable_dt(self):    # OK
        for j, dt in enumerate(self.all_dt):
            dt_adim = dt / P_0
            lower_diagonal_B, diagonal_B, upper_diagonal_B = self.compute_B_diagonals(
                dt_adim
            )
            lower_diagonal_A, diagonal_A, upper_diagonal_A = self.compute_A_diagonals(
                dt_adim
            )

            for tup_idx in range(len(self.inter_cara)):
                self.correct_numerical_schema(
                    tup_idx,
                    lower_diagonal_B,
                    diagonal_B,
                    upper_diagonal_B,
                    lower_diagonal_A,
                    diagonal_A,
                    upper_diagonal_A,
                )

            c = self.compute_c(j)
            B_fois_H_plus_c = (
                tri_product(
                    lower_diagonal_B, diagonal_B, upper_diagonal_B, self.H_adim_res[:, j]
                )
                + c
            )
            self.H_adim_res[:, j + 1] = solver(
                lower_diagonal_A, diagonal_A, upper_diagonal_A, B_fois_H_plus_c
            )
        
        # Re-dimensionnement H_adim_res → H_res
        self.H_res = self.compute_H_res_from_H_adim_res()

    def compute_B_diagonals(self, dt_adim):   # OK
        lower_diagonal_B = zeros(self.n_cell - 1, float32)
        lower_diagonal_B[:] = (1- self.alpha) / self.dz_adim**2
        lower_diagonal_B[-1] = (
            4 * (1- self.alpha) / (3 * self.dz_adim**2)
        )

        diagonal_B = zeros(self.n_cell, float32)
        diagonal_B[:] = (self.gamma / dt_adim) - (2 * (1 - self.alpha) / self.dz_adim**2)
        diagonal_B[0] = (self.gamma[0] / dt_adim) - (4 * (1 - self.alpha) / self.dz_adim**2)
        diagonal_B[-1] = (self.gamma[-1] / dt_adim) - (4 * (1 - self.alpha) / self.dz_adim**2)

        upper_diagonal_B = zeros(self.n_cell - 1, float32)
        upper_diagonal_B[:] = (1- self.alpha) / self.dz_adim**2
        upper_diagonal_B[0] = 4 * (1- self.alpha) / (3 * self.dz_adim**2)

        return lower_diagonal_B, diagonal_B, upper_diagonal_B

    def compute_A_diagonals(self, dt_adim):  # OK
        lower_diagonal_A = zeros(self.n_cell - 1, float32)
        lower_diagonal_A[:] = -self.alpha / self.dz_adim**2
        lower_diagonal_A[-1] = -4 * self.alpha / (3 * self.dz_adim**2)

        diagonal_A = zeros(self.n_cell, float32)
        diagonal_A[:] = (self.gamma / dt_adim) + (2*self.alpha / self.dz_adim**2)
        diagonal_A[0] = (self.gamma[0] / dt_adim) + (4*self.alpha / self.dz_adim**2)
        diagonal_A[-1] = (self.gamma[-1] / dt_adim) + (4*self.alpha / self.dz_adim**2)

        upper_diagonal_A = zeros(self.n_cell - 1, float32)
        upper_diagonal_A[:] = -self.alpha / self.dz_adim**2
        upper_diagonal_A[0] = -4 * self.alpha / (3*self.dz_adim**2)

        return lower_diagonal_A, diagonal_A, upper_diagonal_A

    def correct_numerical_schema(   # OK
        self,
        tup_idx,
        lower_diagonal_B,
        diagonal_B,
        upper_diagonal_B,
        lower_diagonal_A,
        diagonal_A,
        upper_diagonal_A,
    ):
        K1 = self.array_K[tup_idx]
        K2 = self.array_K[tup_idx + 1]
        dt_adim = self.all_dt[0] / P_0

        if self.inter_cara[tup_idx][1] == 0:
            pos_idx = int(self.inter_cara[tup_idx][0])
            diagonal_B[pos_idx] = (
                ((self.Ss_list[pos_idx] * L_0**2 / P_0 / (K1+K2)*0.5) / dt_adim) 
                - (2 * (1 - self.alpha) / self.dz_adim**2)
            )
            # lower_diagonal_B[pos_idx - 1] = (1- self.alpha) / self.dz_adim**2     → pas de changement 
            # upper_diagonal_B[pos_idx] = (1- self.alpha) / self.dz_adim**2     → pas de changement
            diagonal_A[pos_idx] = (
                ((self.Ss_list[pos_idx] * L_0**2 / P_0 / (K1+K2)*0.5) / dt_adim) 
                + (2*self.alpha / self.dz_adim**2)
            )
            # lower_diagonal_A[pos_idx - 1] = -self.alpha / self.dz_adim**2     → pas de changement
            # upper_diagonal_A[pos_idx] = -self.alpha / self.dz_adim**2     → pas de changement
        else:
            pos_idx = int(self.inter_cara[tup_idx][0])
            x = (self.list_zLow[tup_idx] - self.z_solve[pos_idx]) / (
                self.z_solve[pos_idx + 1] - self.z_solve[pos_idx]
            )
            Keq = 1 / (x / K1 + (1 - x) / K2)
            diagonal_B[pos_idx] = (
               ((self.Ss_list[pos_idx] * L_0**2 / P_0 / (K1+Keq)*0.5) / dt_adim) 
                - (2 * (1 - self.alpha) / self.dz_adim**2)
            )
            # lower_diagonal_B[pos_idx - 1] = (1- self.alpha) / self.dz_adim**2     → pas de changement 
            # upper_diagonal_B[pos_idx] = (1- self.alpha) / self.dz_adim**2     → pas de changement
            diagonal_A[pos_idx] = (
               ((self.Ss_list[pos_idx] * L_0**2 / P_0 / (K1+Keq)*0.5) / dt_adim) 
                + (2*self.alpha / self.dz_adim**2)
            )
            # lower_diagonal_A[pos_idx - 1] = -self.alpha / self.dz_adim**2     → pas de changement
            # upper_diagonal_A[pos_idx] = -self.alpha / self.dz_adim**2     → pas de changement

            diagonal_B[pos_idx + 1] = (
                ((self.Ss_list[pos_idx] * L_0**2 / P_0 / (Keq+K2)*0.5) / dt_adim) 
                - (2 * (1 - self.alpha) / self.dz_adim**2)
            )
            # lower_diagonal_B[pos_idx] = (1- self.alpha) / self.dz_adim**2     → pas de changement 
            # upper_diagonal_B[pos_idx + 1] = (1- self.alpha) / self.dz_adim**2     → pas de changement
            diagonal_A[pos_idx + 1] = (
                ((self.Ss_list[pos_idx] * L_0**2 / P_0 / (Keq+K2)*0.5) / dt_adim) 
                + (2*self.alpha / self.dz_adim**2)
            )
            # lower_diagonal_A[pos_idx] = -self.alpha / self.dz_adim**2     → pas de changement
            # upper_diagonal_A[pos_idx + 1] = -self.alpha / self.dz_adim**2     → pas de changement

    def compute_c(self, j):  # QUID heat_source ??
        c = zeros(self.n_cell, float32)
        # Adimensionnement des charges hydrauliques aux limites
        H_riv_adim = (self.H_riv - self.H_init[0]) / DH_0
        H_aq_adim = (self.H_aq - self.H_init[0]) / DH_0
        
        c[0] = (8 / (3 * self.dz_adim**2)) * (
            (1 - self.alpha) * H_riv_adim[j] + self.alpha * H_riv_adim[j + 1]
        )
        c[-1] = (8 / (3 * self.dz_adim**2)) * (
            (1 - self.alpha) * H_aq_adim[j] + self.alpha * H_aq_adim[j + 1]
        )
        #c -= self.heat_source
        return c


# Classe qui définit le système linéaire pour l'équation de la chaleur
class T_stratified(Linear_system):
    def __init__(
        self,
        nablaH,
        Ss_list,
        moinslog10IntrinK_list,
        n_list,
        lambda_s_list,
        rhos_cs_list,
        all_dt,
        q_list,
        dz,
        H_init,
        H_riv,
        H_aq,
        T_init,
        T_riv,
        T_aq,
        alpha=ALPHA,
        N_update_Mu=N_UPDATE_MU,
    ):
        super().__init__(
            Ss_list,
            moinslog10IntrinK_list,
            n_list,
            lambda_s_list,
            rhos_cs_list,
            all_dt,
            dz,
            H_init,
            T_init,
        )
        self.Ss_list = Ss_list
        self.moinslog10IntrinK_list = moinslog10IntrinK_list
        self.n_list = n_list
        self.lambda_s_list = lambda_s_list
        self.rhos_cs_list = rhos_cs_list
        self.H_riv = H_riv
        self.H_aq = H_aq
        self.nablaH = nablaH
        self.T_init = T_init
        self.T_riv = T_riv
        self.T_aq = T_aq
        self.alpha = alpha
        self.N_update_Mu = N_update_Mu
        self.heat_source = q_list
        self.calc_param_adim()

    def compute_kappa_list(self):
        return (RHO_W**2) * C_W * (10.0**-self.moinslog10IntrinK_list) * G * DH_0 / (MU_W * LAMBDA_W)
    
    def compute_beta_list(self):
        beta_value = RHO_W * C_W * (L_0**2) / (P_0 * LAMBDA_W)
        return np.full(self.n_cell, beta_value, dtype=float32)
    
    def compute_T_adim_res(self):
        T_adim_res = zeros((self.n_cell, self.n_times), float32)
        T_adim_res[:, 0] = (self.T_init[:] - self.T_init[0]) / DT_0
        return T_adim_res

    def compute_T_res_from_T_adim_res(self):
        self.T_res = self.T_adim_res * DT_0 + self.T_init[0]
        return self.T_res
    
    def calc_param_adim(self):
        """Calcul des paramètres adimensionnés"""
        self.kappa = self.compute_kappa_list()
        self.beta = self.compute_beta_list()
        self.dz_adim = self.dz / L_0
        self.T_adim_res = self.compute_T_adim_res()
        self.nablaH_adim = L_0 * self.nablaH / DH_0

    def compute_T_stratified(self):
        self.T_res = zeros((self.n_cell, self.n_times), float32)
        self.T_res[:, 0] = self.T_init
        for j, dt in enumerate(self.all_dt):
            # Update of Mu(T) after N_update_Mu iterations:
            if j % self.N_update_Mu == 1:
                self.mu_list = self.compute_Mu(self.T_adim_res[:, j - 1]*DT_0 + self.T_init[0])

            # Compute T at time times[j+1]
            dt_adim = dt / P_0
            # Defining the 3 diagonals of B
            lower_diagonal = self._compute_lower_diagonal(j)
            diagonal = self._compute_diagonal(j, dt_adim)
            upper_diagonal = self._compute_upper_diagonal(j)

            # Defining c
            c = self._compute_c(j)

            B_fois_T_plus_c = (
                tri_product(lower_diagonal, diagonal, upper_diagonal, self.T_adim_res[:, j])
                + c
            )

            # Defining the 3 diagonals of A
            lower_diagonal_A, diagonal_A, upper_diagonal_A = self._compute_A_diagonals(
                j, dt_adim
            )

            try:
                self.T_adim_res[:, j + 1] = solver(
                    lower_diagonal_A, diagonal_A, upper_diagonal_A, B_fois_T_plus_c
                )
            except Exception:
                A = self._construct_A_matrix(
                    lower_diagonal_A, diagonal_A, upper_diagonal_A
                )
                self.T_adim_res[:, j + 1] = solve(A, B_fois_T_plus_c)

        # Re-dimensionnement T_adim_res → T_res
        self.T_res = self.compute_T_res_from_T_adim_res()

        return self.T_res

    def _compute_lower_diagonal(self, j): #OK
        lower_diagonal = zeros(self.n_cell - 1, float32)
        lower_diagonal[:] = ((1 - self.alpha) / self.dz_adim**2) - (
            (1 - self.alpha) * self.kappa[1:] / (2 * self.dz_adim)
        ) * self.nablaH_adim[1:, j]
        lower_diagonal[-1] = (4 *(1 - self.alpha) / self.dz_adim**2 /3) + (
            (1 - self.alpha) * 2 *self.kappa[-1] / (3 * self.dz_adim)
        ) * self.nablaH_adim[-1, j]
        return lower_diagonal

    def _compute_diagonal(self, j, dt_adim): #OK
        diagonal = zeros(self.n_cell, float32)
        diagonal[:] = self.beta / dt_adim - 2 * (1-self.alpha) / self.dz_adim**2
        diagonal[0] = self.beta[0] / dt_adim - 4 * (1-self.alpha) / self.dz_adim**2
        diagonal[-1] = self.beta[-1] / dt_adim - 4 * (1-self.alpha) / self.dz_adim**2
        return diagonal

    def _compute_upper_diagonal(self, j): #OK
        upper_diagonal = zeros(self.n_cell - 1, float32)
        upper_diagonal[:] = ((1 - self.alpha) / self.dz_adim**2) + (
            (1 - self.alpha) * self.kappa[:-1] / (2 * self.dz_adim)
        ) * self.nablaH_adim[:-1, j]
        upper_diagonal[0] = (4 * (1 - self.alpha) / self.dz_adim**2 /3) + (
            (1 - self.alpha) * 2 * self.kappa[0] / (3 * self.dz_adim)
        ) * self.nablaH_adim[1, j]
        return upper_diagonal

    def _compute_c(self, j): #OK
        c = np.zeros(self.n_cell, np.float32)
        # Adimensionnement des températures aux limites
        T_riv_adim = (self.T_riv - self.T_init[0]) / DT_0
        T_aq_adim = (self.T_aq - self.T_init[0]) / DT_0
        
        c[0] = (
            8 * self.alpha / (3 * self.dz_adim**2)
            - 2 * self.alpha * self.kappa[0] * self.nablaH_adim[0, j+1] / (3 * self.dz_adim)
        ) * T_riv_adim[j + 1] + (
            8 * (1 - self.alpha) / (3 * self.dz_adim**2)
            - 2 * (1 - self.alpha) * self.kappa[0] * self.nablaH_adim[0, j] / (3 * self.dz_adim)
        ) * T_riv_adim[j]
        c[-1] = (
           8 * self.alpha / (3 * self.dz_adim**2)
            + 2 * self.alpha * self.kappa[-1] * self.nablaH_adim[-1, j+1] / (3 * self.dz_adim)
        ) * T_aq_adim[j + 1] + (
            8 * (1 - self.alpha) / (3 * self.dz_adim**2)
            + 2 * (1 - self.alpha) * self.kappa[-1] * self.nablaH_adim[-1, j] / (3 * self.dz_adim)
        ) * T_aq_adim[j]

        # c += self.heat_source[:, j]
        return c

    def _compute_A_diagonals(self, j, dt_adim): #OK

        lower_diagonal = zeros(self.n_cell - 1, float32)
        lower_diagonal[:] = (
            - self.alpha / self.dz_adim**2 + self.alpha * self.kappa[:-1] * self.nablaH_adim[:-1,j+1] / (2*self.dz_adim)
        )

        lower_diagonal[-1] = (
            - 4 * self.alpha / (3 * self.dz_adim**2) + 2 * self.alpha * self.kappa[-2] * self.nablaH_adim[-2,j+1] / (3*self.dz_adim)
        )

        diagonal = zeros(self.n_cell, float32)
        diagonal[:] = (
            self.beta / dt_adim
            + 2 * self.alpha / self.dz_adim**2
        )
        diagonal[0] = (
            self.beta[0] / dt_adim
            + 4 * self.alpha / self.dz_adim**2
        )
        diagonal[-1] = (
            self.beta[-1] / dt_adim
            + 4 * self.alpha / self.dz_adim**2
        )

        upper_diagonal = zeros(self.n_cell - 1, float32)
        upper_diagonal[:] = (
            - self.alpha / self.dz_adim**2 - self.alpha * self.kappa[1:] * self.nablaH_adim[1:,j+1] / (2*self.dz_adim)      
        )
        upper_diagonal[0] = (
            - 4 * self.alpha / (3 * self.dz_adim**2) - 2 * self.alpha * self.kappa[0] * self.nablaH_adim[1,j+1] / (3*self.dz_adim)
        )

        return lower_diagonal, diagonal, upper_diagonal

    def _construct_A_matrix(self, lower_diagonal, diagonal, upper_diagonal):
        A = np.zeros((self.n_cell, self.n_cell), float32)
        A[0, 0] = diagonal[0]
        A[0, 1] = upper_diagonal[0]
        for i in range(1, self.n_cell - 1):
            A[i, i - 1] = lower_diagonal[i - 1]
            A[i, i] = diagonal[i]
            A[i, i + 1] = upper_diagonal[i]
        A[self.n_cell - 1, self.n_cell - 1] = diagonal[self.n_cell - 1]
        A[self.n_cell - 1, self.n_cell - 2] = lower_diagonal[self.n_cell - 2]
        return A



# Classe pour l'instant expérimentale pour prendre en compte le coupage HTK
# class HTK_stratified(Linear_system):
#     def __init__(
#         self,
#         lambda_s_list,
#         rhos_cs_list,
#         n_list,
#         T_init,
#         array_K,
#         array_Ss,
#         list_zLow,
#         z_solve,
#         inter_cara,
#         moinslog10IntrinK_list,
#         Ss_list,
#         all_dt,
#         isdtconstant,
#         dz,
#         H_init,
#         H_riv,
#         H_aq,
#         heatsource,
#         alpha=ALPHA,
#     ):
#         super().__init__(
#             Ss_list,
#             moinslog10IntrinK_list,
#             n_list,
#             lambda_s_list,
#             rhos_cs_list,
#             all_dt,
#             dz,
#             H_init,
#             T_init,
#         )
#         self.lambda_s_list = lambda_s_list
#         self.rhos_cs_list = rhos_cs_list
#         self.n_list = n_list
#         self.T_init = T_init
#         self.array_K = array_K
#         self.array_Ss = array_Ss
#         self.list_zLow = list_zLow
#         self.z_solve = z_solve
#         self.inter_cara = inter_cara
#         self.moinslog10IntrinK_list = moinslog10IntrinK_list
#         self.Ss_list = Ss_list
#         self.all_dt = all_dt
#         self.isdtconstant = isdtconstant
#         self.dz = dz
#         self.H_init = H_init
#         self.H_riv = H_riv
#         self.H_aq = H_aq
#         self.alpha = alpha
#         self.heat_source = heatsource
#         self.compute_HTK_stratified()

#     def compute_HTK_stratified(self):
#         if self.isdtconstant:
#             self.compute_H_constant_dt()
#         else:
#             self.compute_H_variable_dt()
#         return self.H_res

#     def compute_H_constant_dt(self):
#         dt = self.all_dt[0]

#         lower_diagonal_B, diagonal_B, upper_diagonal_B = self.compute_B_diagonals(dt)
#         lower_diagonal_A, diagonal_A, upper_diagonal_A = self.compute_A_diagonals(dt)

#         for tup_idx in range(len(self.inter_cara)):
#             self.correct_numerical_schema(
#                 tup_idx,
#                 lower_diagonal_B,
#                 diagonal_B,
#                 upper_diagonal_B,
#                 lower_diagonal_A,
#                 diagonal_A,
#                 upper_diagonal_A,
#             )

#         for j in range(self.n_times - 1):
#             c = self.compute_c(j)
#             B_fois_H_plus_c = (
#                 tri_product(
#                     lower_diagonal_B, diagonal_B, upper_diagonal_B, self.H_res[:, j]
#                 )
#                 + c
#             )
#             self.H_res[:, j + 1] = solver(
#                 lower_diagonal_A, diagonal_A, upper_diagonal_A, B_fois_H_plus_c
#             )

#     def compute_H_variable_dt(self):
#         for j, dt in enumerate(self.all_dt):
#             lower_diagonal_B, diagonal_B, upper_diagonal_B = self.compute_B_diagonals(
#                 dt
#             )
#             lower_diagonal_A, diagonal_A, upper_diagonal_A = self.compute_A_diagonals(
#                 dt
#             )

#             for tup_idx in range(len(self.inter_cara)):
#                 self.correct_numerical_schema(
#                     tup_idx,
#                     lower_diagonal_B,
#                     diagonal_B,
#                     upper_diagonal_B,
#                     lower_diagonal_A,
#                     diagonal_A,
#                     upper_diagonal_A,
#                 )

#             c = self.compute_c(j)
#             B_fois_H_plus_c = (
#                 tri_product(
#                     lower_diagonal_B, diagonal_B, upper_diagonal_B, self.H_res[:, j]
#                 )
#                 + c
#             )
#             self.H_res[:, j + 1] = solver(
#                 lower_diagonal_A, diagonal_A, upper_diagonal_A, B_fois_H_plus_c
#             )

#     def compute_B_diagonals(self, dt):
#         lower_diagonal_B = self.K_list[1:] * self.alpha / self.dz**2
#         lower_diagonal_B[-1] = (
#             4 * self.K_list[self.n_cell - 1] * self.alpha / (3 * self.dz**2)
#         )

#         diagonal_B = self.Ss_list * 1 / dt - 2 * self.K_list * self.alpha / self.dz**2
#         diagonal_B[0] = (
#             self.Ss_list[0] * 1 / dt - 4 * self.K_list[0] * self.alpha / self.dz**2
#         )
#         diagonal_B[-1] = (
#             self.Ss_list[self.n_cell - 1] * 1 / dt
#             - 4 * self.K_list[self.n_cell - 1] * self.alpha / self.dz**2
#         )

#         upper_diagonal_B = self.K_list[:-1] * self.alpha / self.dz**2
#         upper_diagonal_B[0] = 4 * self.K_list[0] * self.alpha / (3 * self.dz**2)

#         return lower_diagonal_B, diagonal_B, upper_diagonal_B

#     def compute_A_diagonals(self, dt):
#         lower_diagonal_A = -self.K_list[1:] * (1 - self.alpha) / self.dz**2
#         lower_diagonal_A[-1] = (
#             -4 * self.K_list[self.n_cell - 1] * (1 - self.alpha) / (3 * self.dz**2)
#         )

#         diagonal_A = (
#             self.Ss_list * 1 / dt + 2 * self.K_list * (1 - self.alpha) / self.dz**2
#         )
#         diagonal_A[0] = (
#             self.Ss_list[0] * 1 / dt
#             + 4 * self.K_list[0] * (1 - self.alpha) / self.dz**2
#         )
#         diagonal_A[-1] = (
#             self.Ss_list[self.n_cell - 1] * 1 / dt
#             + 4 * self.K_list[self.n_cell - 1] * (1 - self.alpha) / self.dz**2
#         )

#         upper_diagonal_A = -self.K_list[:-1] * (1 - self.alpha) / self.dz**2
#         upper_diagonal_A[0] = -4 * self.K_list[0] * (1 - self.alpha) / (3 * self.dz**2)

#         return lower_diagonal_A, diagonal_A, upper_diagonal_A

#     def correct_numerical_schema(
#         self,
#         tup_idx,
#         lower_diagonal_B,
#         diagonal_B,
#         upper_diagonal_B,
#         lower_diagonal_A,
#         diagonal_A,
#         upper_diagonal_A,
#     ):
#         K1 = self.array_K[tup_idx]
#         K2 = self.array_K[tup_idx + 1]

#         if self.inter_cara[tup_idx][1] == 0:
#             pos_idx = int(self.inter_cara[tup_idx][0])
#             diagonal_B[pos_idx] = (
#                 self.Ss_list[pos_idx] * 1 / self.all_dt[0]
#                 - (K1 + K2) * self.alpha / self.dz**2
#             )
#             lower_diagonal_B[pos_idx - 1] = K1 * self.alpha / self.dz**2
#             upper_diagonal_B[pos_idx] = K2 * self.alpha / self.dz**2
#             diagonal_A[pos_idx] = (
#                 self.Ss_list[pos_idx] * 1 / self.all_dt[0]
#                 + (K1 + K2) * (1 - self.alpha) / self.dz**2
#             )
#             lower_diagonal_A[pos_idx - 1] = -K1 * (1 - self.alpha) / self.dz**2
#             upper_diagonal_A[pos_idx] = -K2 * (1 - self.alpha) / self.dz**2
#         else:
#             pos_idx = int(self.inter_cara[tup_idx][0])
#             x = (self.list_zLow[tup_idx] - self.z_solve[pos_idx]) / (
#                 self.z_solve[pos_idx + 1] - self.z_solve[pos_idx]
#             )
#             Keq = 1 / (x / K1 + (1 - x) / K2)
#             diagonal_B[pos_idx] = (
#                 self.Ss_list[pos_idx] * 1 / self.all_dt[0]
#                 - (K1 + Keq) * self.alpha / self.dz**2
#             )
#             lower_diagonal_B[pos_idx - 1] = K1 * self.alpha / self.dz**2
#             upper_diagonal_B[pos_idx] = Keq * self.alpha / self.dz**2
#             diagonal_A[pos_idx] = (
#                 self.Ss_list[pos_idx] * 1 / self.all_dt[0]
#                 + (K1 + Keq) * (1 - self.alpha) / self.dz**2
#             )
#             lower_diagonal_A[pos_idx - 1] = -K1 * (1 - self.alpha) / self.dz**2
#             upper_diagonal_A[pos_idx] = -Keq * (1 - self.alpha) / self.dz**2

#             diagonal_B[pos_idx + 1] = (
#                 self.Ss_list[pos_idx] * 1 / self.all_dt[0]
#                 - (K2 + Keq) * self.alpha / self.dz**2
#             )
#             lower_diagonal_B[pos_idx] = Keq * self.alpha / self.dz**2
#             upper_diagonal_B[pos_idx + 1] = K2 * self.alpha / self.dz**2
#             diagonal_A[pos_idx + 1] = (
#                 self.Ss_list[pos_idx] * 1 / self.all_dt[0]
#                 + (K2 + Keq) * (1 - self.alpha) / self.dz**2
#             )
#             lower_diagonal_A[pos_idx] = -Keq * (1 - self.alpha) / self.dz**2
#             upper_diagonal_A[pos_idx + 1] = -K2 * (1 - self.alpha) / self.dz**2

#     def compute_c(self, j):
        c = zeros(self.n_cell, float32)
        c[0] = (8 * self.K_list[0] / (3 * self.dz**2)) * (
            (1 - self.alpha) * self.H_riv[j + 1] + self.alpha * self.H_riv[j]
        )
        c[-1] = (8 * self.K_list[self.n_cell - 1] / (3 * self.dz**2)) * (
            (1 - self.alpha) * self.H_aq[j + 1] + self.alpha * self.H_aq[j]
        )
        # c += self.heat_source[:, j]
        return c


if __name__ == "__main__":
    L = 0.5
    print(1)
