from numpy import float32, zeros

from numpy.linalg import solve

# import numpy as np
from numba import njit
import numpy as np

from pyheatmy.solver import solver, tri_product
from pyheatmy.config import *
from pyheatmy.utils import *


class Initialization:
    def __init__(
        self,
        a,
        Ss_list,
        moinslog10IntrinK_list,
        n_list,
        lambda_s_list,
        rhos_cs_list,
        all_dt,
        dz,
        H_init,
        H_riv,
        H_aq,
        T_init,
        T_riv,
        T_aq,
        array_K,
        array_Ss,
        list_zLow,
        z_solve,
        inter_cara,
        isdtconstant,
        heatsource,
        alpha=ALPHA,
        N_update_Mu=N_UPDATE_MU,
    ):

        self.H_stratified = H_stratified(
            array_K,
            array_Ss,
            list_zLow,
            z_solve,
            T_init,
            inter_cara,
            moinslog10IntrinK_list,
            Ss_list,
            all_dt,
            isdtconstant,
            dz,
            H_init,
            H_riv,
            H_aq,
            heatsource,
            alpha=ALPHA,
        )
        self.nablaH = self.H_stratified.nablaH

        # self.T_stratified = T_stratified(a,
        #     Ss_list,
        #     moinslog10IntrinK_list,
        #     n_list,
        #     lambda_s_list,
        #     rhos_cs_list,
        #     all_dt,
        #     dz,
        #     H_init,
        #     H_riv,
        #     H_aq,
        #     self.nablaH,
        #     T_init,
        #     T_riv,
        #     T_aq,
        #     heatsource,
        #     alpha,
        #     N_update_Mu)
        # )
        # self.HTK_stratified = HTKStratified(
        #     lambda_s_list,
        #     rhos_cs_list,
        #     n_list,
        #     T_init,
        #     a,
        #     Ss_list,
        #     all_dt,
        #     dz,
        #     H_init,
        #     H_riv,
        #     H_aq,
        #     heatsource
        #     alpha,
        # )

    def get_T(self):
        return self.T_stratified.T_res

    def get_H(self):
        return self.H_stratified.H_res

    def get_HTK(self):
        return self.HTK_stratified.H_res


L = 0.5
rho_w = 1000
c_w = 4182
lambda_w = 0.598


class T_stratified:
    def __init__(
        self,
        a,
        Ss_list,
        moinslog10IntrinK_list,
        n_list,
        lambda_s_list,
        rhos_cs_list,
        all_dt,
        dz,
        H_res,
        H_riv,
        H_aq,
        nablaH,
        T_init,
        T_riv,
        T_aq,
        heatsource,
        alpha=ALPHA,
        N_update_Mu=N_UPDATE_MU,
    ):
        self.a = a
        self.Ss_list = Ss_list
        self.moinslog10IntrinK_list = moinslog10IntrinK_list
        self.n_list = n_list
        self.lambda_s_list = lambda_s_list
        self.rhos_cs_list = rhos_cs_list
        self.all_dt = all_dt
        self.dz = dz
        self.H_res = H_res
        self.H_riv = H_riv
        self.H_aq = H_aq
        self.nablaH = nablaH
        self.T_init = T_init
        self.T_riv = T_riv
        self.T_aq = T_aq
        self.alpha = alpha
        self.N_update_Mu = N_update_Mu
        self.heat_source = heatsource
        self.mu_list = compute_Mu(self.T_init)
        self.rho_mc_m_list = (
            self.n_list * RHO_W * C_W + (1 - self.n_list) * self.rhos_cs_list
        )
        self.K_list = (
            (RHO_W * G * 10.0**-self.moinslog10IntrinK_list) * 1.0 / self.mu_list
        )
        self.lambda_m_list = (
            self.n_list * (LAMBDA_W) ** 0.5
            + (1.0 - self.n_list) * (self.lambda_s_list) ** 0.5
        ) ** 2
        self.ke_list = self.lambda_m_list / self.rho_mc_m_list
        self.ae_list = RHO_W * C_W * self.K_list / self.rho_mc_m_list
        self.n_cell = len(self.T_init)
        self.n_times = len(self.all_dt) + 1
        self.T_res = np.zeros((self.n_cell, self.n_times), np.float32)
        self.T_res[:, 0] = self.T_init
        self.compute_T_stratified()

    def compute_T_stratified(self):
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
            lower_diagonal_A, diagonal_A, upper_diagonal_A = self._compute_A_diagonals()

            try:
                self.T_res[:, j + 1] = solver(
                    lower_diagonal_A, diagonal_A, upper_diagonal_A, B_fois_T_plus_c
                )
            except Exception:
                A = self._construct_A_matrix(
                    lower_diagonal_A, diagonal_A, upper_diagonal_A
                )
                self.T_res[:, j + 1] = solve(A, B_fois_T_plus_c)

        return self.T_res

    def _compute_lower_diagonal(self, j):
        lower_diagonal = (self.ke_list[1:] * self.alpha / self.dz**2) - (
            self.alpha * self.ae_list[1:] / (2 * self.dz)
        ) * self.nablaH[1:, j]
        lower_diagonal[-1] = (
            4 * self.ke_list[self.n_cell - 1] * self.alpha / (3 * self.dz**2)
            - (2 * self.alpha * self.ae_list[self.n_cell - 1] / (3 * self.dz))
            * self.nablaH[self.n_cell - 1, j]
        )
        return lower_diagonal

    def _compute_diagonal(self, j, dt):
        diagonal = 1 / dt - 2 * self.ke_list * self.alpha / self.dz**2
        diagonal[0] = 1 / dt - 4 * self.ke_list[0] * self.alpha / self.dz**2
        diagonal[-1] = (
            1 / dt - 4 * self.ke_list[self.n_cell - 1] * self.alpha / self.dz**2
        )
        return diagonal

    def _compute_upper_diagonal(self, j):
        upper_diagonal = (self.ke_list[:-1] * self.alpha / self.dz**2) + (
            self.alpha * self.ae_list[:-1] / (2 * self.dz)
        ) * self.nablaH[:-1, j]
        upper_diagonal[0] = (
            4 * self.ke_list[0] * self.alpha / (3 * self.dz**2)
            + (2 * self.alpha * self.ae_list[0] / (3 * self.dz)) * self.nablaH[0, j]
        )
        return upper_diagonal

    def _compute_c(self, j):
        c = np.zeros(self.n_cell, np.float32)
        c[0] = (
            8 * self.ke_list[0] * (1 - self.alpha) / (3 * self.dz**2)
            - 2 * (1 - self.alpha) * self.ae_list[0] * self.nablaH[0, j] / (3 * self.dz)
        ) * self.T_riv[j + 1] + (
            8 * self.ke_list[0] * self.alpha / (3 * self.dz**2)
            - 2 * self.alpha * self.ae_list[0] * self.nablaH[0, j] / (3 * self.dz)
        ) * self.T_riv[
            j
        ]
        c[-1] = (
            8 * self.ke_list[self.n_cell - 1] * (1 - self.alpha) / (3 * self.dz**2)
            + 2
            * (1 - self.alpha)
            * self.ae_list[self.n_cell - 1]
            * self.nablaH[self.n_cell - 1, j]
            / (3 * self.dz)
            * self.T_aq[j + 1]
            + (
                8 * self.ke_list[self.n_cell - 1] * self.alpha / (3 * self.dz**2)
                + 2
                * self.alpha
                * self.ae_list[self.n_cell - 1]
                * self.nablaH[self.n_cell - 1, j]
                / (3 * self.dz)
            )
            * self.T_aq[j]
        )
        c += self.heat_source[:, j]
        return c

    def _compute_A_diagonals(self):
        lambda_w = 0.598
        lambda_m = (
            self.n_list * np.sqrt(lambda_w)
            + (1 - self.n_list) * np.sqrt(self.lambda_s_list)
        ) ** 2
        lower_diagonal = -c_w * rho_w * self.moinslog10IntrinK_list * self.nablaH / (
            self.dz
        ) - lambda_m / (self.dz**2)
        lower_diagonal[-1] = -2 * self.moinslog10IntrinK_list * self.nablaH[
            L - self.dz
        ] * rho_w * c_w / (3 * self.dz) - 4 * lambda_m / (3 * (self.dz**2))

        diagonal = (
            4 * lambda_m / (self.dz**2) + self.moinslog10IntrinK_list * self.a / 2
        )
        diagonal[0] = (
            4 * lambda_m / (self.dz**2) + self.moinslog10IntrinK_list * self.a / 2
        )
        diagonal[-1] = (
            4 * lambda_m / (self.dz**2) + self.moinslog10IntrinK_list * self.a / 2
        )

        upper_diagonal = c_w * rho_w * self.moinslog10IntrinK_list * self.nablaH / (
            self.dz
        ) - lambda_m / (self.dz**2)
        upper_diagonal[0] = -self.moinslog10IntrinK_list * self.nablaH[
            self.dz
        ] * 2 * rho_w * c_w / (3 * self.dz) - 4 * lambda_m / (3 * (self.dz**2))
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


class H_stratified:
    def __init__(
        self,
        array_K,
        array_Ss,
        list_zLow,
        z_solve,
        T_init,
        inter_cara,
        moinslog10IntrinK_list,
        Ss_list,
        all_dt,
        isdtconstant,
        dz,
        H_init,
        H_riv,
        H_aq,
        heat_source,
        alpha=ALPHA,
    ):
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
        self.heat_source = heat_source
        self.n_cell = len(H_init)
        self.n_times = len(all_dt) + 1
        self.H_res = zeros((self.n_cell, self.n_times), float32)
        self.H_res[:, 0] = H_init[:]
        self.mu_list = compute_Mu(T_init)
        self.K_list = (RHO_W * G * 10.0**-moinslog10IntrinK_list) * 1.0 / self.mu_list
        self.KsurSs_list = self.K_list / Ss_list
        self.dK_list = self.compute_dK_list()
        self.compute_H_stratified()

    def compute_dK_list(self):
        dK_list = zeros(self.n_cell, float32)
        dK_list[0] = (self.K_list[1] - self.K_list[0]) / self.dz
        dK_list[-1] = (self.K_list[-1] - self.K_list[-2]) / self.dz
        for idx in range(1, len(dK_list) - 1):
            dK_list[idx] = (self.K_list[idx + 1] - self.K_list[idx - 1]) / 2 / self.dz
        return dK_list

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

        nablaH[0, :] = 2 * (self.H_res[1, :] - self.H_riv) / (3 * dz)

        for i in range(1, self.n_cell - 1):
            nablaH[i, :] = (self.H_res[i + 1, :] - self.H_res[i - 1, :]) / (2 * dz)

        nablaH[self.n_cell - 1, :] = (
            2 * (H_aq - self.H_res[self.n_cell - 2, :]) / (3 * dz)
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
        lower_diagonal_B = self.K_list[1:] * self.alpha / self.dz**2
        lower_diagonal_B[-1] = (
            4 * self.K_list[self.n_cell - 1] * self.alpha / (3 * self.dz**2)
        )

        diagonal_B = self.Ss_list * 1 / dt - 2 * self.K_list * self.alpha / self.dz**2
        diagonal_B[0] = (
            self.Ss_list[0] * 1 / dt - 4 * self.K_list[0] * self.alpha / self.dz**2
        )
        diagonal_B[-1] = (
            self.Ss_list[self.n_cell - 1] * 1 / dt
            - 4 * self.K_list[self.n_cell - 1] * self.alpha / self.dz**2
        )

        upper_diagonal_B = self.K_list[:-1] * self.alpha / self.dz**2
        upper_diagonal_B[0] = 4 * self.K_list[0] * self.alpha / (3 * self.dz**2)

        return lower_diagonal_B, diagonal_B, upper_diagonal_B

    def compute_A_diagonals(self, dt):
        lower_diagonal_A = -self.K_list[1:] * (1 - self.alpha) / self.dz**2
        lower_diagonal_A[-1] = (
            -4 * self.K_list[self.n_cell - 1] * (1 - self.alpha) / (3 * self.dz**2)
        )

        diagonal_A = (
            self.Ss_list * 1 / dt + 2 * self.K_list * (1 - self.alpha) / self.dz**2
        )
        diagonal_A[0] = (
            self.Ss_list[0] * 1 / dt
            + 4 * self.K_list[0] * (1 - self.alpha) / self.dz**2
        )
        diagonal_A[-1] = (
            self.Ss_list[self.n_cell - 1] * 1 / dt
            + 4 * self.K_list[self.n_cell - 1] * (1 - self.alpha) / self.dz**2
        )

        upper_diagonal_A = -self.K_list[:-1] * (1 - self.alpha) / self.dz**2
        upper_diagonal_A[0] = -4 * self.K_list[0] * (1 - self.alpha) / (3 * self.dz**2)

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
                - (K1 + K2) * self.alpha / self.dz**2
            )
            lower_diagonal_B[pos_idx - 1] = K1 * self.alpha / self.dz**2
            upper_diagonal_B[pos_idx] = K2 * self.alpha / self.dz**2
            diagonal_A[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                + (K1 + K2) * (1 - self.alpha) / self.dz**2
            )
            lower_diagonal_A[pos_idx - 1] = -K1 * (1 - self.alpha) / self.dz**2
            upper_diagonal_A[pos_idx] = -K2 * (1 - self.alpha) / self.dz**2
        else:
            pos_idx = int(self.inter_cara[tup_idx][0])
            x = (self.list_zLow[tup_idx] - self.z_solve[pos_idx]) / (
                self.z_solve[pos_idx + 1] - self.z_solve[pos_idx]
            )
            Keq = 1 / (x / K1 + (1 - x) / K2)
            diagonal_B[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                - (K1 + Keq) * self.alpha / self.dz**2
            )
            lower_diagonal_B[pos_idx - 1] = K1 * self.alpha / self.dz**2
            upper_diagonal_B[pos_idx] = Keq * self.alpha / self.dz**2
            diagonal_A[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                + (K1 + Keq) * (1 - self.alpha) / self.dz**2
            )
            lower_diagonal_A[pos_idx - 1] = -K1 * (1 - self.alpha) / self.dz**2
            upper_diagonal_A[pos_idx] = -Keq * (1 - self.alpha) / self.dz**2

            diagonal_B[pos_idx + 1] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                - (K2 + Keq) * self.alpha / self.dz**2
            )
            lower_diagonal_B[pos_idx] = Keq * self.alpha / self.dz**2
            upper_diagonal_B[pos_idx + 1] = K2 * self.alpha / self.dz**2
            diagonal_A[pos_idx + 1] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                + (K2 + Keq) * (1 - self.alpha) / self.dz**2
            )
            lower_diagonal_A[pos_idx] = -Keq * (1 - self.alpha) / self.dz**2
            upper_diagonal_A[pos_idx + 1] = -K2 * (1 - self.alpha) / self.dz**2

    def compute_c(self, j):
        c = zeros(self.n_cell, float32)
        c[0] = (8 * self.K_list[0] / (3 * self.dz**2)) * (
            (1 - self.alpha) * self.H_riv[j + 1] + self.alpha * self.H_riv[j]
        )
        c[-1] = (8 * self.K_list[self.n_cell - 1] / (3 * self.dz**2)) * (
            (1 - self.alpha) * self.H_aq[j + 1] + self.alpha * self.H_aq[j]
        )
        c += self.heat_source[:, j]
        return c


class HTKStratified:
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
        moinslog10IntrinK_list,
        Ss_list,
        all_dt,
        isdtconstant,
        dz,
        H_init,
        H_riv,
        H_aq,
        heatsource,
        alpha=ALPHA,
    ):
        self.lambda_s_list = lambda_s_list
        self.rhos_cs_list = rhos_cs_list
        self.n_list = n_list
        self.T_init = T_init
        self.array_K = array_K
        self.array_Ss = array_Ss
        self.list_zLow = list_zLow
        self.z_solve = z_solve
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
        self.heat_source = heatsource
        self.n_cell = len(H_init)
        self.n_times = len(all_dt) + 1
        self.H_res = zeros((self.n_cell, self.n_times), float32)
        self.H_res[:, 0] = H_init[:]
        self.mu_list = compute_Mu(T_init)
        self.rho_mc_m_list = n_list * RHO_W * C_W + (1 - n_list) * rhos_cs_list
        self.K_list = (RHO_W * G * 10.0**-moinslog10IntrinK_list) * 1.0 / self.mu_list
        self.lambda_m_list = (
            n_list * (LAMBDA_W) ** 0.5 + (1.0 - n_list) * (lambda_s_list) ** 0.5
        ) ** 2
        self.ke_list = self.lambda_m_list / self.rho_mc_m_list
        self.ae_list = RHO_W * C_W * self.K_list / self.rho_mc_m_list
        self.KsurSs_list = self.K_list / Ss_list
        self.dK_list = self.compute_dK_list()
        self.compute_HTK_stratified()

    def compute_dK_list(self):
        dK_list = zeros(self.n_cell, float32)
        dK_list[0] = (self.K_list[1] - self.K_list[0]) / self.dz
        dK_list[-1] = (self.K_list[-1] - self.K_list[-2]) / self.dz
        for idx in range(1, len(dK_list) - 1):
            dK_list[idx] = (self.K_list[idx + 1] - self.K_list[idx - 1]) / 2 / self.dz
        return dK_list

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
        lower_diagonal_B = self.K_list[1:] * self.alpha / self.dz**2
        lower_diagonal_B[-1] = (
            4 * self.K_list[self.n_cell - 1] * self.alpha / (3 * self.dz**2)
        )

        diagonal_B = self.Ss_list * 1 / dt - 2 * self.K_list * self.alpha / self.dz**2
        diagonal_B[0] = (
            self.Ss_list[0] * 1 / dt - 4 * self.K_list[0] * self.alpha / self.dz**2
        )
        diagonal_B[-1] = (
            self.Ss_list[self.n_cell - 1] * 1 / dt
            - 4 * self.K_list[self.n_cell - 1] * self.alpha / self.dz**2
        )

        upper_diagonal_B = self.K_list[:-1] * self.alpha / self.dz**2
        upper_diagonal_B[0] = 4 * self.K_list[0] * self.alpha / (3 * self.dz**2)

        return lower_diagonal_B, diagonal_B, upper_diagonal_B

    def compute_A_diagonals(self, dt):
        lower_diagonal_A = -self.K_list[1:] * (1 - self.alpha) / self.dz**2
        lower_diagonal_A[-1] = (
            -4 * self.K_list[self.n_cell - 1] * (1 - self.alpha) / (3 * self.dz**2)
        )

        diagonal_A = (
            self.Ss_list * 1 / dt + 2 * self.K_list * (1 - self.alpha) / self.dz**2
        )
        diagonal_A[0] = (
            self.Ss_list[0] * 1 / dt
            + 4 * self.K_list[0] * (1 - self.alpha) / self.dz**2
        )
        diagonal_A[-1] = (
            self.Ss_list[self.n_cell - 1] * 1 / dt
            + 4 * self.K_list[self.n_cell - 1] * (1 - self.alpha) / self.dz**2
        )

        upper_diagonal_A = -self.K_list[:-1] * (1 - self.alpha) / self.dz**2
        upper_diagonal_A[0] = -4 * self.K_list[0] * (1 - self.alpha) / (3 * self.dz**2)

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
                - (K1 + K2) * self.alpha / self.dz**2
            )
            lower_diagonal_B[pos_idx - 1] = K1 * self.alpha / self.dz**2
            upper_diagonal_B[pos_idx] = K2 * self.alpha / self.dz**2
            diagonal_A[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                + (K1 + K2) * (1 - self.alpha) / self.dz**2
            )
            lower_diagonal_A[pos_idx - 1] = -K1 * (1 - self.alpha) / self.dz**2
            upper_diagonal_A[pos_idx] = -K2 * (1 - self.alpha) / self.dz**2
        else:
            pos_idx = int(self.inter_cara[tup_idx][0])
            x = (self.list_zLow[tup_idx] - self.z_solve[pos_idx]) / (
                self.z_solve[pos_idx + 1] - self.z_solve[pos_idx]
            )
            Keq = 1 / (x / K1 + (1 - x) / K2)
            diagonal_B[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                - (K1 + Keq) * self.alpha / self.dz**2
            )
            lower_diagonal_B[pos_idx - 1] = K1 * self.alpha / self.dz**2
            upper_diagonal_B[pos_idx] = Keq * self.alpha / self.dz**2
            diagonal_A[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                + (K1 + Keq) * (1 - self.alpha) / self.dz**2
            )
            lower_diagonal_A[pos_idx - 1] = -K1 * (1 - self.alpha) / self.dz**2
            upper_diagonal_A[pos_idx] = -Keq * (1 - self.alpha) / self.dz**2

            diagonal_B[pos_idx + 1] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                - (K2 + Keq) * self.alpha / self.dz**2
            )
            lower_diagonal_B[pos_idx] = Keq * self.alpha / self.dz**2
            upper_diagonal_B[pos_idx + 1] = K2 * self.alpha / self.dz**2
            diagonal_A[pos_idx + 1] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                + (K2 + Keq) * (1 - self.alpha) / self.dz**2
            )
            lower_diagonal_A[pos_idx] = -Keq * (1 - self.alpha) / self.dz**2
            upper_diagonal_A[pos_idx + 1] = -K2 * (1 - self.alpha) / self.dz**2

    def compute_c(self, j):
        c = zeros(self.n_cell, float32)
        c[0] = (8 * self.K_list[0] / (3 * self.dz**2)) * (
            (1 - self.alpha) * self.H_riv[j + 1] + self.alpha * self.H_riv[j]
        )
        c[-1] = (8 * self.K_list[self.n_cell - 1] / (3 * self.dz**2)) * (
            (1 - self.alpha) * self.H_aq[j + 1] + self.alpha * self.H_aq[j]
        )
        c += self.heat_source[:, j]
        return c
