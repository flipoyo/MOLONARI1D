from numpy import float32, zeros
from numpy.linalg import solve
from numba import njit
import numpy as np
from pyheatmy.solver import solver, tri_product
from pyheatmy.config import *


# Première classe qui définit et initie les paramètres physiques communs des systèmes linéaires de la classe H_stratified et T_stratified
class Linear_system:
    def __init__(
        self,
        Ss_list,
        IntrinK_list,
        n_list,
        lambda_s_list,
        rhos_cs_list,
        all_dt,
        dz,
        H_init,
        T_init,
    ):
        self.IntrinK_list = IntrinK_list
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
        # mu = MU_A * np.exp(MU_B * 1.0 / T + MU_C * T + MU_D * (T**2)) 
        mu = DEFAULT_MU
        return mu

    # @njit
    def compute_K(self, IntrinK_list):
        return (RHO_W * G * IntrinK_list) * 1.0 / self.mu_list

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
        self.K_list = self.compute_K(self.IntrinK_list)
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
        IntrinK_list,
        n_list,
        lambda_s_list,
        rhos_cs_list,
        all_dt,
        q_s_list, 
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
            IntrinK_list,
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
        self.IntrinK_list = IntrinK_list
        self.Ss_list = Ss_list
        self.all_dt = all_dt
        self.isdtconstant = isdtconstant
        self.dz = dz
        self.H_init = H_init
        self.H_riv = H_riv
        self.H_aq = H_aq
        self.alpha = alpha
        self.q_s_list = q_s_list # MODIF

    def compute_H_stratified(self):
        if self.isdtconstant.all():
            self.compute_H_constant_dt()
        else:
            self.compute_H_variable_dt()
        return self.H_res

    def compute_H_constant_dt(self):
        dt = self.all_dt[0]

        lower_diagonal_B, diagonal_B, upper_diagonal_B = self.compute_B_diagonals(dt)
        lower_diagonal_A, diagonal_A, upper_diagonal_A = self.compute_A_diagonals(dt)

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

        for j in range(self.n_times - 1):
            c = self.compute_c(j)
            B_fois_H_plus_c = (
                tri_product(
                    lower_diagonal_B, diagonal_B, upper_diagonal_B, self.H_res[:, j]
                )
                + c
            )
            self.H_res[:, j + 1] = solver(
                lower_diagonal_A, diagonal_A, upper_diagonal_A, B_fois_H_plus_c
            )

    def nablaH(self):
        nablaH = np.zeros((self.n_cell, self.n_times), np.float32)

        nablaH[0, :] = 2 * (self.H_res[1, :] - self.H_riv) / (3 * self.dz)

        for i in range(1, self.n_cell - 1):
            nablaH[i, :] = (self.H_res[i + 1, :] - self.H_res[i - 1, :]) / (2 * self.dz)

        nablaH[self.n_cell - 1, :] = (
            2 * (self.H_aq - self.H_res[self.n_cell - 2, :]) / (3 * self.dz)
        )
        return nablaH

    def compute_H_variable_dt(self):
        for j, dt in enumerate(self.all_dt):
            lower_diagonal_B, diagonal_B, upper_diagonal_B = self.compute_B_diagonals(
                dt
            )
            lower_diagonal_A, diagonal_A, upper_diagonal_A = self.compute_A_diagonals(
                dt
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
                    lower_diagonal_B, diagonal_B, upper_diagonal_B, self.H_res[:, j]
                )
                + c
            )
            self.H_res[:, j + 1] = solver(
                lower_diagonal_A, diagonal_A, upper_diagonal_A, B_fois_H_plus_c
            )

    def compute_B_diagonals(self, dt):
        lower_diagonal_B = self.K_list[1:] * (1 - self.alpha) / self.dz**2
        lower_diagonal_B[-1] = (
            4 * self.K_list[self.n_cell - 1] * (1 - self.alpha) / (3 * self.dz**2)
        )

        diagonal_B = self.Ss_list * 1 / dt - 2 * self.K_list * (1 - self.alpha) / self.dz**2
        diagonal_B[0] = (
            self.Ss_list[0] * 1 / dt - 4 * self.K_list[0] * (1 - self.alpha) / self.dz**2
        )
        diagonal_B[-1] = (
            self.Ss_list[self.n_cell - 1] * 1 / dt
            - 4 * self.K_list[self.n_cell - 1] * (1 - self.alpha) / self.dz**2
        )

        upper_diagonal_B = self.K_list[:-1] * (1 - self.alpha) / self.dz**2
        upper_diagonal_B[0] = 4 * self.K_list[0] * (1 - self.alpha) / (3 * self.dz**2)

        return lower_diagonal_B, diagonal_B, upper_diagonal_B

    def compute_A_diagonals(self, dt):
        lower_diagonal_A = -self.K_list[1:] * self.alpha / self.dz**2
        lower_diagonal_A[-1] = (
            -4 * self.K_list[self.n_cell - 1] * self.alpha / (3 * self.dz**2)
        )

        diagonal_A = (
            self.Ss_list * 1 / dt + 2 * self.K_list * self.alpha / self.dz**2
        )
        diagonal_A[0] = (
            self.Ss_list[0] * 1 / dt
            + 4 * self.K_list[0] * self.alpha / self.dz**2
        )
        diagonal_A[-1] = (
            self.Ss_list[self.n_cell - 1] * 1 / dt
            + 4 * self.K_list[self.n_cell - 1] * self.alpha / self.dz**2
        )

        upper_diagonal_A = -self.K_list[:-1] * self.alpha / self.dz**2
        upper_diagonal_A[0] = -4 * self.K_list[0] * self.alpha / (3 * self.dz**2)

        return lower_diagonal_A, diagonal_A, upper_diagonal_A

    def correct_numerical_schema(
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

        if self.inter_cara[tup_idx][1] == 0:
            pos_idx = int(self.inter_cara[tup_idx][0])
            diagonal_B[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                - (K1 + K2) * (1 - self.alpha) / self.dz**2
            )
            lower_diagonal_B[pos_idx - 1] = K1 * (1 - self.alpha) / self.dz**2
            upper_diagonal_B[pos_idx] = K2 * (1 - self.alpha) / self.dz**2
            diagonal_A[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                + (K1 + K2) * self.alpha / self.dz**2
            )
            lower_diagonal_A[pos_idx - 1] = -K1 * self.alpha / self.dz**2
            upper_diagonal_A[pos_idx] = -K2 * self.alpha / self.dz**2
        else:
            pos_idx = int(self.inter_cara[tup_idx][0])
            x = (self.list_zLow[tup_idx] - self.z_solve[pos_idx]) / (
                self.z_solve[pos_idx + 1] - self.z_solve[pos_idx]
            )
            Keq = 1 / (x / K1 + (1 - x) / K2)
            diagonal_B[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                - (K1 + Keq) * (1 - self.alpha) / self.dz**2
            )
            lower_diagonal_B[pos_idx - 1] = K1 * (1 - self.alpha) / self.dz**2
            upper_diagonal_B[pos_idx] = Keq * (1 - self.alpha) / self.dz**2
            diagonal_A[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                + (K1 + Keq) * self.alpha / self.dz**2
            )
            lower_diagonal_A[pos_idx - 1] = -K1 * self.alpha / self.dz**2
            upper_diagonal_A[pos_idx] = -Keq * self.alpha / self.dz**2

            diagonal_B[pos_idx + 1] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                - (K2 + Keq) * (1 - self.alpha) / self.dz**2
            )
            lower_diagonal_B[pos_idx] = Keq * (1 - self.alpha) / self.dz**2
            upper_diagonal_B[pos_idx + 1] = K2 * (1 - self.alpha) / self.dz**2
            diagonal_A[pos_idx + 1] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                + (K2 + Keq) * self.alpha / self.dz**2
            )
            lower_diagonal_A[pos_idx] = -Keq * self.alpha / self.dz**2
            upper_diagonal_A[pos_idx + 1] = -K2 * self.alpha / self.dz**2

    def compute_c(self, j):
        c = zeros(self.n_cell, float32)
        c[0] = (8 * self.K_list[0] / (3 * self.dz**2)) * (
            self.alpha * self.H_riv[j + 1] + (1 - self.alpha) * self.H_riv[j]
        )
        c[-1] = (8 * self.K_list[self.n_cell - 1] / (3 * self.dz**2)) * (
            self.alpha * self.H_aq[j + 1] + (1 - self.alpha) * self.H_aq[j]
        )
        c += self.q_s_list
        return c


# Classe qui définit le système linéaire pour l'équation de la chaleur
class T_stratified(Linear_system):
    def __init__(
        self,
        nablaH,
        Ss_list,
        IntrinK_list, 
        n_list,
        lambda_s_list,
        rhos_cs_list,
        all_dt,
        q_s_list, 
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
            IntrinK_list,
            n_list,
            lambda_s_list,
            rhos_cs_list,
            all_dt,
            dz,
            H_init,
            T_init,
        )
        self.Ss_list = Ss_list
        self.IntrinK_list = IntrinK_list
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
        self.q_s_list = q_s_list 

    def compute_T_stratified(self):
        self.T_res = np.zeros((self.n_cell, self.n_times), np.float32)
        self.source_heat_flux = np.zeros((self.n_cell, self.n_times), np.float32)

        self.T_res[:, 0] = self.T_init
        # Calcul du flux au temps initial
        self.source_heat_flux[:, 0] = self.q_s_list * RHO_W * C_W * (self.T_res[:, 0] - ZERO_CELSIUS)

        for j, dt in enumerate(self.all_dt):
            # Update of Mu(T) after N_update_Mu iterations:
            if j % self.N_update_Mu == 1:
                self.mu_list = self.compute_Mu(self.T_res[:, j - 1])

            # Compute T at time times[j+1]

            # Defining the 3 diagonals of B
            lower_diagonal = self._compute_lower_diagonal(j)
            diagonal = self._compute_diagonal(j, dt)
            upper_diagonal = self._compute_upper_diagonal(j)

            # Defining c
            c = self._compute_c(j)

            B_fois_T_plus_c = (
                tri_product(lower_diagonal, diagonal, upper_diagonal, self.T_res[:, j])
                + c
            )

            # Defining the 3 diagonals of A
            lower_diagonal_A, diagonal_A, upper_diagonal_A = self._compute_A_diagonals(
                j, dt
            )

            try:
                self.T_res[:, j + 1] = solver(
                    lower_diagonal_A, diagonal_A, upper_diagonal_A, B_fois_T_plus_c
                )
            except Exception:
                A = self._construct_A_matrix(
                    lower_diagonal_A, diagonal_A, upper_diagonal_A
                )
                self.T_res[:, j + 1] = solve(A, B_fois_T_plus_c)
            
            T_semi_implicite = (1 - self.alpha) * self.T_res[:, j] + self.alpha * self.T_res[:, j + 1]
            self.source_heat_flux[:, j + 1] = self.q_s_list * RHO_W * C_W * (T_semi_implicite - ZERO_CELSIUS)

        return self.T_res

    def _compute_lower_diagonal(self, j):
        lower_diagonal = (self.ke_list[1:] * (1 - self.alpha) / self.dz**2) - (
            (1 - self.alpha) * self.ae_list[1:] / (2 * self.dz)
        ) * self.nablaH[1:, j]
        lower_diagonal[-1] = (
            4 * self.ke_list[self.n_cell - 1] * (1 - self.alpha) / (3 * self.dz**2)
            - (2 * (1 - self.alpha) * self.ae_list[self.n_cell - 1] / (3 * self.dz))
            * self.nablaH[self.n_cell - 1, j]
        )
        return lower_diagonal

    def _compute_diagonal(self, j, dt):
        heat_source = (self.q_s_list * RHO_W * C_W ) / self.rho_mc_m_list

        diagonal = 1 / dt - 2 * self.ke_list * (1 - self.alpha) / self.dz**2 + (1 - self.alpha) * heat_source
        diagonal[0] = 1 / dt - 4 * self.ke_list[0] * (1 - self.alpha) / self.dz**2 + (1 - self.alpha) * heat_source[0]
        diagonal[-1] = (
            1 / dt - 4 * self.ke_list[self.n_cell - 1] * (1 - self.alpha) / self.dz**2
            + (1 - self.alpha) * heat_source[-1]
        )
        return diagonal

    def _compute_upper_diagonal(self, j):
        upper_diagonal = (self.ke_list[:-1] * (1 - self.alpha) / self.dz**2) + (
            (1 - self.alpha) * self.ae_list[:-1] / (2 * self.dz)
        ) * self.nablaH[:-1, j]
        upper_diagonal[0] = (
            4 * self.ke_list[0] * (1 - self.alpha) / (3 * self.dz**2)
            + (2 * (1 - self.alpha) * self.ae_list[0] / (3 * self.dz)) * self.nablaH[0, j]
        )
        return upper_diagonal

    def _compute_c(self, j):
        c = np.zeros(self.n_cell, np.float32)
        c[0] = (
            8 * self.ke_list[0] * self.alpha / (3 * self.dz**2)
            - 2 * self.alpha * self.ae_list[0] * self.nablaH[0, j] / (3 * self.dz)
        ) * self.T_riv[j + 1] + (
            8 * self.ke_list[0] * (1 - self.alpha) / (3 * self.dz**2)
            - 2 * (1 - self.alpha) * self.ae_list[0] * self.nablaH[0, j] / (3 * self.dz)
        ) * self.T_riv[
            j
        ]
        c[-1] = (
            8 * self.ke_list[self.n_cell - 1] * self.alpha / (3 * self.dz**2)
            + 2
            * self.alpha
            * self.ae_list[self.n_cell - 1]
            * self.nablaH[self.n_cell - 1, j]
            / (3 * self.dz)
        ) * self.T_aq[j + 1] + (
            8 * self.ke_list[self.n_cell - 1] * (1 - self.alpha) / (3 * self.dz**2)
            + 2
            * (1 - self.alpha)
            * self.ae_list[self.n_cell - 1]
            * self.nablaH[self.n_cell - 1, j]
            / (3 * self.dz)
        ) * self.T_aq[
            j
        ]
        return c

    def _compute_A_diagonals(self, j, dt):
        heat_source = (self.q_s_list * RHO_W * C_W ) / self.rho_mc_m_list

        lower_diagonal = (
            -(self.ke_list[1:] * self.alpha / self.dz**2)
            + (self.alpha * self.ae_list[1:] / (2 * self.dz)) * self.nablaH[1:, j]
        )

        lower_diagonal[-1] = (
            -4 * self.ke_list[self.n_cell - 1] * self.alpha / (3 * self.dz**2)
            + (2 * self.alpha * self.ae_list[self.n_cell - 1] / (3 * self.dz))
            * self.nablaH[self.n_cell - 1, j]
        )

        diagonal = (
            1 / dt
            + 2 * self.ke_list * self.alpha / self.dz**2
              - self.alpha * heat_source #NOTE : signe négatif car on est de l'autre côté de l'équation
        )
        diagonal[0] = (
            1 / dt
            + 4 * self.ke_list[0] * self.alpha / self.dz**2
            - self.alpha * heat_source[0]
        )
        diagonal[-1] = (
            1 / dt
            + 4 * self.ke_list[self.n_cell - 1] * self.alpha / self.dz**2
            - self.alpha * heat_source[-1]
        )

        upper_diagonal = (
            -(self.ke_list[:-1] * self.alpha / self.dz**2)
            - (self.alpha * self.ae_list[:-1] / (2 * self.dz))
            * self.nablaH[:-1, j]
        )
        upper_diagonal[0] = (
            -4 * self.ke_list[0] * self.alpha / (3 * self.dz**2)
            - (2 * self.alpha * self.ae_list[0] / (3 * self.dz))
            * self.nablaH[0, j]
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


class HTK_stratified(Linear_system):
    def __init__(
        self,
        lambda_s_list,
        rhos_cs_list,
        n_list,
        T_init,
        array_K,
        array_Ss,
        list_zLow,
        z_solve,
        inter_cara,
        IntrinK_list,
        Ss_list,
        all_dt,
        isdtconstant,
        dz,
        H_init,
        H_riv,
        H_aq,
        q_s_list, 
        alpha=ALPHA,
    ):
        super().__init__(
            Ss_list,
            IntrinK_list,
            n_list,
            lambda_s_list,
            rhos_cs_list,
            all_dt,
            dz,
            H_init,
            T_init,
        )
        self.lambda_s_list = lambda_s_list
        self.rhos_cs_list = rhos_cs_list
        self.n_list = n_list
        self.T_init = T_init
        self.array_K = array_K
        self.array_Ss = array_Ss
        self.list_zLow = list_zLow
        self.z_solve = z_solve
        self.inter_cara = inter_cara
        self.IntrinK_list = IntrinK_list
        self.Ss_list = Ss_list
        self.all_dt = all_dt
        self.isdtconstant = isdtconstant
        self.dz = dz
        self.H_init = H_init
        self.H_riv = H_riv
        self.H_aq = H_aq
        self.alpha = alpha
        self.q_s_list = q_s_list
        self.compute_HTK_stratified()

    def compute_HTK_stratified(self):
        if self.isdtconstant:
            self.compute_H_constant_dt()
        else:
            self.compute_H_variable_dt()
        return self.H_res

    def compute_H_constant_dt(self):
        dt = self.all_dt[0]

        lower_diagonal_B, diagonal_B, upper_diagonal_B = self.compute_B_diagonals(dt)
        lower_diagonal_A, diagonal_A, upper_diagonal_A = self.compute_A_diagonals(dt)

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

        for j in range(self.n_times - 1):
            # Calcul des diagonales B (implicite) et A (explicite)
            lower_diagonal_B, diagonal_B, upper_diagonal_B = self.compute_B_diagonals(
                dt
            )
            lower_diagonal_A, diagonal_A, upper_diagonal_A = self.compute_A_diagonals(
                dt
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

            indices_temps_a_afficher = np.linspace(
                0, self.n_times - 2, 5, dtype=int
            )  # n_times-2 car j va de 0 à n_times-2

            # Vérifier si l'indice actuel j est l'un de ceux qu'on veut afficher
            if j in indices_temps_a_afficher:
                print(
                    f"\n--- Matrices Intermédiaires (Diagonales) au pas de temps j={j} ---"
                )
                np.set_printoptions(precision=6, suppress=True, linewidth=120)

                print("\nDiagonales de B (partie implicite, temps t):")
                # print des diagonales B

                print("\nDiagonales de A (partie explicite, temps t+dt):")
                # print des diagonales A

                c = self.compute_c(j)
                print(f"\nVecteur c (conditions aux limites et sources):")
                print(f"  c      : {c}")

                print(
                    "-----------------------------------------------------------------\n"
                )

                np.set_printoptions(precision=6, suppress=True, linewidth=120)

                print("\nDiagonales de B (partie implicite, temps t):")
                print(f"  Lower B: {lower_diagonal_B}")
                print(f"  Diag B : {diagonal_B}")
                print(f"  Upper B: {upper_diagonal_B}")

                print("\nDiagonales de A (partie explicite, temps t+dt):")
                print(f"  Lower A: {lower_diagonal_A}")
                print(f"  Diag A : {diagonal_A}")
                print(f"  Upper A: {upper_diagonal_A}")

                c = self.compute_c(j)  # Calculer c pour l'afficher
                print(f"\nVecteur c (conditions aux limites et sources):")
                print(f"  c      : {c}")

                print(
                    "-----------------------------------------------------------------\n"
                )

            c = self.compute_c(j)
            B_fois_H_plus_c = (
                tri_product(
                    lower_diagonal_B, diagonal_B, upper_diagonal_B, self.H_res[:, j]
                )
                + c
            )
            self.H_res[:, j + 1] = solver(
                lower_diagonal_A, diagonal_A, upper_diagonal_A, B_fois_H_plus_c
            )

    def compute_H_variable_dt(self):
        for j, dt in enumerate(self.all_dt):
            lower_diagonal_B, diagonal_B, upper_diagonal_B = self.compute_B_diagonals(
                dt
            )
            lower_diagonal_A, diagonal_A, upper_diagonal_A = self.compute_A_diagonals(
                dt
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
                    lower_diagonal_B, diagonal_B, upper_diagonal_B, self.H_res[:, j]
                )
                + c
            )
            self.H_res[:, j + 1] = solver(
                lower_diagonal_A, diagonal_A, upper_diagonal_A, B_fois_H_plus_c
            )

    def compute_B_diagonals(self, dt):
        lower_diagonal_B = self.K_list[1:] * (1 - self.alpha) / self.dz**2
        lower_diagonal_B[-1] = (
            4 * self.K_list[self.n_cell - 1] * (1 - self.alpha) / (3 * self.dz**2)
        )

        diagonal_B = self.Ss_list * 1 / dt - 2 * self.K_list * (1 - self.alpha) / self.dz**2
        diagonal_B[0] = (
            self.Ss_list[0] * 1 / dt - 4 * self.K_list[0] * (1 - self.alpha) / self.dz**2
        )
        diagonal_B[-1] = (
            self.Ss_list[self.n_cell - 1] * 1 / dt
            - 4 * self.K_list[self.n_cell - 1] * (1 - self.alpha) / self.dz**2
        )

        upper_diagonal_B = self.K_list[:-1] * (1 - self.alpha) / self.dz**2
        upper_diagonal_B[0] = 4 * self.K_list[0] * (1 - self.alpha) / (3 * self.dz**2)

        return lower_diagonal_B, diagonal_B, upper_diagonal_B

    def compute_A_diagonals(self, dt):
        lower_diagonal_A = -self.K_list[1:] * self.alpha / self.dz**2
        lower_diagonal_A[-1] = (
            -4 * self.K_list[self.n_cell - 1] * self.alpha / (3 * self.dz**2)
        )

        diagonal_A = (
            self.Ss_list * 1 / dt + 2 * self.K_list * self.alpha / self.dz**2
        )
        diagonal_A[0] = (
            self.Ss_list[0] * 1 / dt
            + 4 * self.K_list[0] * self.alpha / self.dz**2
        )
        diagonal_A[-1] = (
            self.Ss_list[self.n_cell - 1] * 1 / dt
            + 4 * self.K_list[self.n_cell - 1] * self.alpha / self.dz**2
        )

        upper_diagonal_A = -self.K_list[:-1] * self.alpha / self.dz**2
        upper_diagonal_A[0] = -4 * self.K_list[0] * self.alpha / (3 * self.dz**2)

        return lower_diagonal_A, diagonal_A, upper_diagonal_A

    def correct_numerical_schema(
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
        if self.inter_cara[tup_idx][1] == 0:
            pos_idx = int(self.inter_cara[tup_idx][0])
            diagonal_B[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                - (K1 + K2) * (1 - self.alpha) / self.dz**2
            )
            lower_diagonal_B[pos_idx - 1] = K1 * (1 - self.alpha) / self.dz**2
            upper_diagonal_B[pos_idx] = K2 * (1 - self.alpha) / self.dz**2
            diagonal_A[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                + (K1 + K2) * self.alpha / self.dz**2
            )
            lower_diagonal_A[pos_idx - 1] = -K1 * self.alpha / self.dz**2
            upper_diagonal_A[pos_idx] = -K2 * self.alpha / self.dz**2
        else:
            pos_idx = int(self.inter_cara[tup_idx][0])
            x = (self.list_zLow[tup_idx] - self.z_solve[pos_idx]) / (
                self.z_solve[pos_idx + 1] - self.z_solve[pos_idx]
            )
            Keq = 1 / (x / K1 + (1 - x) / K2)
            diagonal_B[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                - (K1 + Keq) * (1 - self.alpha) / self.dz**2
            )
            lower_diagonal_B[pos_idx - 1] = K1 * (1 - self.alpha) / self.dz**2
            upper_diagonal_B[pos_idx] = Keq * (1 - self.alpha) / self.dz**2
            diagonal_A[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                + (K1 + Keq) * self.alpha / self.dz**2
            )
            lower_diagonal_A[pos_idx - 1] = -K1 * self.alpha / self.dz**2
            upper_diagonal_A[pos_idx] = -Keq * self.alpha / self.dz**2

            diagonal_B[pos_idx + 1] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                - (K2 + Keq) * (1 - self.alpha) / self.dz**2
            )
            lower_diagonal_B[pos_idx] = Keq * (1 - self.alpha) / self.dz**2
            upper_diagonal_B[pos_idx + 1] = K2 * (1 - self.alpha) / self.dz**2
            diagonal_A[pos_idx + 1] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                + (K2 + Keq) * self.alpha / self.dz**2
            )
            lower_diagonal_A[pos_idx] = -Keq * self.alpha / self.dz**2
            upper_diagonal_A[pos_idx + 1] = -K2 * self.alpha / self.dz**2

    def compute_c(self, j):
        c = zeros(self.n_cell, float32)
        c[0] = (8 * self.K_list[0] / (3 * self.dz**2)) * (
            self.alpha * self.H_riv[j + 1] + (1 - self.alpha) * self.H_riv[j]
        )
        c[-1] = (8 * self.K_list[self.n_cell - 1] / (3 * self.dz**2)) * (
            self.alpha * self.H_aq[j + 1] + (1 - self.alpha) * self.H_aq[j]
        )
        c += self.q_s_list 
        return c


if __name__ == "__main__":
    L = 0.5
    print(1)