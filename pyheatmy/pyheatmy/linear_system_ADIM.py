"""
---------------------------------
Numerical implementations of linear systems
used to solve pseudo-2D (and 1D) transient equations for
hydraulic head (H) and temperature (T) in a
stratified column.

File purpose:
- provide a class (`Linear_system`) that computes derived
    physical parameters (K, rho*c, lambda_m, ...),
- assemble and solve tridiagonal systems for H (class
    `H_stratified`) and for T (class `T_stratified`) using a
    semi-implicit scheme described in the project README,
- perform computations in non-dimensional variables for
    numerical stability and re-dimensionalize the results for output.
---------------------------------
"""

from numpy import float32, zeros

from numpy.linalg import solve

# import numpy as np
from numba import njit
import numpy as np

from pyheatmy.solver import solver, tri_product
from pyheatmy.config import *

# Classe définissant et initiant les paramètres physiques des systèmes linéaires de la classe H_stratified et T_stratified
class Linear_system:
    """A class that does not directly solve the equations but centralizes
    the logic for building derived physical quantities required by the
    H_stratified and T_stratified solvers.

    The `compute_*` methods return NumPy arrays (dtype float32) ready to be
    consumed by tridiagonal matrix constructors.
    """
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
        # mu = MU_A * np.exp(MU_B * 1.0 / T + MU_C * T + MU_D * (T**2)) # Error when executing the MCMC : RuntimeWarning: overflow encountered in exp
        # mu = MU_A * np.exp(MU_B * 1.0 / T + MU_C * T + MU_D * (T**2))
        mu = DEFAULT_MU
        return mu

    # @njit
    def compute_K(self, IntrinK_list):
        # IntrinK_list actually holds the physical intrinsic permeability (m2)
        # in the higher-level code (Layer.get_physical_params returns IntrinK as a physical value).
        # Therefore compute hydraulic conductivity K from intrinsic permeability directly.
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
    
    def compute_H_res(self):
        H_res = zeros((self.n_cell, self.n_times), float32)
        H_res[:, 0] = self.H_init[:]
        return H_res
    
    def calc_physical_param(self):
        self.n_cell = self.compute_n_cell()
        self.n_times = self.compute_n_times()
        self.mu_list = self.compute_Mu(self.T_init)
        self.K_list = self.compute_K(self.IntrinK_list)
        self.rho_mc_m_list = self.compute_rho_mc_m_list()
        self.lambda_m_list = self.compute_lambda_m_list()
        self.H_res = self.compute_H_res()


# Class that defines the linear system for the diffusivity equation
class H_stratified(Linear_system):
    """Solver for the hydraulic head equation (H) in a stratified column.
    This class computes the non-dimensional coefficients (gamma, zeta),
    assembles a non-dimensional tridiagonal system for hydraulic
    diffusivity in a stratified column, and applies a semi-implicit
    (alpha) time-stepping scheme.
    """
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
        self.q_s_list = q_s_list
        self.calc_param_adim()

    def compute_gamma_list(self):
        # Use the physical intrinsic permeability (not -log10) when computing gamma
        return MU_W * (self.L_0**2) * (self.Ss_list) / (RHO_W * (self.IntrinK_list) * G * self.P_0)
    
    def compute_H_adim_res(self):
        H_adim_res = zeros((self.n_cell, self.n_times), float32)
        H_adim_res[:, 0] = (self.H_init[:] - self.H_init[-1]) / self.DH_0
        return H_adim_res
    
    def compute_H_res_from_H_adim_res(self):
        self.H_res = self.H_adim_res * self.DH_0 + self.H_init[-1]
        return self.H_res

    def calc_param_adim(self):
        """Compute non-dimensional parameters"""
        self.DH_0 = self.H_init[0] - self.H_init[-1]
        self.P_0 = self.all_dt.sum()
        self.L_0 = self.dz * (self.n_cell - 1)
        self.H_adim_res = self.compute_H_adim_res()
        self.gamma = self.compute_gamma_list()
        self.dz_adim = self.dz / self.L_0


    def compute_H_stratified(self): 
        """Solve the time-stepping for H.

        Depending on whether the timestep is constant or variable, this
        method delegates to `compute_H_constant_dt` or
        `compute_H_variable_dt` respectively.

        Main steps for each timestep j:
        - periodically update temperature-dependent viscosity mu
        - build diagonals of B (explicit terms) and A (implicit terms)
        - assemble the RHS vector c including boundary conditions and sources
        - solve the tridiagonal system via `solver`

        The returned result is `H_res` in physical units (re-dimensionalized
        before being returned).
        """
        if self.isdtconstant.all():
            self.compute_H_constant_dt()
        else:
            self.compute_H_variable_dt()
        return self.H_res

    def compute_H_constant_dt(self):    
        dt = self.all_dt[0]
        dt_adim = dt / self.P_0

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

        # Re-dimension H_adim_res → H_res
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
    
    def nablaH_adim(self):  
        nablaH_adim = np.zeros((self.n_cell, self.n_times), np.float32)

        H_adim_riv = (self.H_riv - self.H_init[-1]) / self.DH_0
        nablaH_adim[0, :] = 2 * (self.H_adim_res[1, :] - H_adim_riv) / (3 * self.dz_adim)

        for i in range(1, self.n_cell - 1):
            nablaH_adim[i, :] = (self.H_adim_res[i + 1, :] - self.H_adim_res[i - 1, :]) / (2 * self.dz_adim)

        H_adim_aq = (self.H_aq - self.H_init[-1]) / self.DH_0
        nablaH_adim[self.n_cell - 1, :] = (
            2 * (H_adim_aq - self.H_adim_res[self.n_cell - 2, :]) / (3 * self.dz_adim)
        )
        return nablaH_adim

    def compute_H_variable_dt(self):    
        for j, dt in enumerate(self.all_dt):
            dt_adim = dt / self.P_0
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
        
        # Re-dimension H_adim_res → H_res
        self.H_res = self.compute_H_res_from_H_adim_res()

    def compute_B_diagonals(self, dt_adim):   
        lower_diagonal_B = zeros(self.n_cell - 1, float32)
        lower_diagonal_B[:] = (1 - self.alpha) / self.dz_adim**2
        lower_diagonal_B[-1] = (
            4 * (1 - self.alpha) / (3 * self.dz_adim**2)
        )

        diagonal_B = zeros(self.n_cell, float32)
        diagonal_B[:] = (self.gamma / dt_adim) - (2 * (1 - self.alpha) / self.dz_adim**2)
        diagonal_B[0] = (self.gamma[0] / dt_adim) - (4 * (1 - self.alpha) / self.dz_adim**2)
        diagonal_B[-1] = (self.gamma[-1] / dt_adim) - (4 * (1 - self.alpha) / self.dz_adim**2)

        upper_diagonal_B = zeros(self.n_cell - 1, float32)
        upper_diagonal_B[:] = (1 - self.alpha) / self.dz_adim**2
        upper_diagonal_B[0] = 4 * (1 - self.alpha) / (3 * self.dz_adim**2)

        return lower_diagonal_B, diagonal_B, upper_diagonal_B

    def compute_A_diagonals(self, dt_adim):  
        lower_diagonal_A = zeros(self.n_cell - 1, float32)
        lower_diagonal_A[:] = -(self.alpha) / self.dz_adim**2
        lower_diagonal_A[-1] = -4 * (self.alpha) / (3 * self.dz_adim**2)

        diagonal_A = zeros(self.n_cell, float32)
        diagonal_A[:] = (self.gamma / dt_adim) + (2*(self.alpha) / self.dz_adim**2)
        diagonal_A[0] = (self.gamma[0] / dt_adim) + (4*(self.alpha) / self.dz_adim**2)
        diagonal_A[-1] = (self.gamma[-1] / dt_adim) + (4*(self.alpha) / self.dz_adim**2)

        upper_diagonal_A = zeros(self.n_cell - 1, float32)
        upper_diagonal_A[:] = -(self.alpha) / self.dz_adim**2
        upper_diagonal_A[0] = -4 * (self.alpha) / (3*self.dz_adim**2)

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
        """Apply a local numerical correction to the diagonals around
        an interface between layers (tup_idx).

        In a stratified column, an interface between two layers
        (with properties K1, K2, ...) can lie exactly on a mesh node
        or inside a cell (fractional case). To preserve numerical
        accuracy and conservation (flux & storage) we locally replace
        diagonal coefficients with "equivalent" values that incorporate
        effective permeability and porosity (Ss).

        - If self.inter_cara[tup_idx][1] == 0: the interface coincides
          with a discretization node. We compute an equivalent term
          using the average (K1+K2)/2 and replace the diagonal value
          at the affected index. This modifies the apparent storage
          term (Ss/P_0) in diagonals B and A to account for connectivity
          across the layers.
        - Otherwise (interface inside a cell):
          - pos_idx identifies the lower cell affected by the interface
          - x is the fractional position of the interface between nodes
            z_solve[pos_idx] and z_solve[pos_idx+1]
          - Keq is an equivalent permeability (weighted harmonic mean)
            computed as 1/(x/K1 + (1-x)/K2) — corresponding to series
            conductance across sub-portions of the cell
          - The diagonals for cells pos_idx and pos_idx+1 are adjusted
            using Keq combined with the adjacent K to form averaged
            terms (e.g. (K1+Keq)/2 and (Keq+K2)/2).
        """
        K1 = self.array_K[tup_idx]
        K2 = self.array_K[tup_idx + 1]
        dt_adim = self.all_dt[0] / self.P_0

        # Case: interface exactly coincides with a mesh node
        if self.inter_cara[tup_idx][1] == 0:
            pos_idx = int(self.inter_cara[tup_idx][0])  # index of the affected cell
            # Local replacement of the diagonal by a term including
            # storage (Ss) and an average conductivity (K1+K2)/2.
            diagonal_B[pos_idx] = (
                ((self.Ss_list[pos_idx] * self.L_0**2 / self.P_0 / (K1+K2)*0.5) / dt_adim) 
                - (2 * (1 - self.alpha) / self.dz_adim**2)
            )
            diagonal_A[pos_idx] = (
                ((self.Ss_list[pos_idx] * self.L_0**2 / self.P_0 / (K1+K2)*0.5) / dt_adim) 
                + (2*(self.alpha) / self.dz_adim**2)
            )
        # Case: interface inside a cell 
        else: 
            # calculation of an equivalent permeability Keq by series combination.
            pos_idx = int(self.inter_cara[tup_idx][0])
            x = (self.list_zLow[tup_idx] - self.z_solve[pos_idx]) / (
                self.z_solve[pos_idx + 1] - self.z_solve[pos_idx]
            )
            # Keq: equivalent permeability of the fractional portion
            Keq = 1 / (x / K1 + (1 - x) / K2)
            # Adjust the diagonal of the cell containing the lower portion
            # (pos_idx) using an average between K1 and Keq
            diagonal_B[pos_idx] = (
               ((self.Ss_list[pos_idx] * self.L_0**2 / self.P_0 / (K1+Keq)*0.5) / dt_adim) 
                - (2 * (1 - self.alpha) / self.dz_adim**2)
            )
            diagonal_A[pos_idx] = (
               ((self.Ss_list[pos_idx] * self.L_0**2 / self.P_0 / (K1+Keq)*0.5) / dt_adim) 
                + (2*(self.alpha) / self.dz_adim**2)
            )

            # Also adjust the upper cell (pos_idx+1) containing
            # the upper portion of the interface; combine Keq and K2.
            diagonal_B[pos_idx + 1] = (
                ((self.Ss_list[pos_idx] * self.L_0**2 / self.P_0 / (Keq+K2)*0.5) / dt_adim) 
                - (2 * (1 - self.alpha) / self.dz_adim**2)
            )
            diagonal_A[pos_idx + 1] = (
                ((self.Ss_list[pos_idx] * self.L_0**2 / self.P_0 / (Keq+K2)*0.5) / dt_adim) 
                + (2*(self.alpha) / self.dz_adim**2)
            )

    def compute_c(self, j):
        """Assemble the right-hand side vector c for step j.
        The vector `c` incorporates contributions from boundary
        conditions (river / aquifer) in non-dimensional form as well as the
        water source q_s_list.
        """
        c = zeros(self.n_cell, float32)
        # Non-dimensionalization of hydraulic heads at boundaries
        H_riv_adim = (self.H_riv - self.H_init[-1]) / self.DH_0
        H_aq_adim = (self.H_aq - self.H_init[-1]) / self.DH_0
        
        c[0] = (8 / (3 * self.dz_adim**2)) * (
            (1 - self.alpha) * H_riv_adim[j] + (self.alpha) * H_riv_adim[j + 1]
        )
        c[-1] = (8 / (3 * self.dz_adim**2)) * (
            (1 - self.alpha) * H_aq_adim[j] + (self.alpha) * H_aq_adim[j + 1]
        )
        # Addition of the non-dimensional number zeta
        # A positive q_s corresponds to a water source  
        c += self.q_s_list * MU_W * self.L_0 ** 2 / (
            (self.IntrinK_list) * self.DH_0 * G * RHO_W
        )
        return c


# Class defining the linear system for the heat equation
class T_stratified(Linear_system):
    """Solver for the heat equation (T) on a stratified column.
    Uses the hydraulic gradient `nablaH` calculated by H_stratified to
    include heat advection. Constructs the non-dimensional coefficients
    (kappa, beta, phi) and assembles then solves the tri-diagonal systems
    for the time stepping in T.
    """
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
        self.calc_param_adim()

    def compute_kappa_list(self):
        return (RHO_W**2) * C_W * (self.IntrinK_list) * G * self.DH_0 / (MU_W * self.lambda_m_list)

    def compute_phi_list(self):
        return RHO_W * C_W * self.q_s_list * self.L_0 **2 / (MU_W * self.lambda_m_list)

    def compute_beta_list(self):
        beta_value = RHO_W * C_W * (self.L_0**2) / (self.P_0 * self.lambda_m_list)
        return np.full(self.n_cell, beta_value, dtype=float32)
    
    def compute_T_adim_res(self):
        T_adim_res = zeros((self.n_cell, self.n_times), float32)
        T_adim_res[:, 0] = (self.T_init[:] - self.T_init[0]) / self.DT_0
        return T_adim_res

    def compute_T_res_from_T_adim_res(self):
        self.T_res = self.T_adim_res * self.DT_0 + self.T_init[0]
        return self.T_res
    
    def calc_param_adim(self):
        """Compute non-dimensional parameters"""
        self.DH_0 = self.H_init[0] - self.H_init[-1]
        self.DT_0 = self.T_init[0] - self.T_init[-1]
        self.P_0 = self.all_dt.sum()
        self.L_0 = self.dz * (self.n_cell - 1)
        self.kappa = self.compute_kappa_list()
        self.beta = self.compute_beta_list()
        self.phi = self.compute_phi_list()
        self.dz_adim = self.dz / self.L_0
        self.T_adim_res = self.compute_T_adim_res()
        self.nablaH_adim = self.L_0 * self.nablaH / self.DH_0

    def compute_T_stratified(self):
        """Solve the time stepping for temperature T.
        Main steps for each time step j:
        - periodic update of temperature-dependent viscosity (mu)
        - construction of the diagonals of B (explicit terms) and A
          (implicit terms)
        - assembly of the right-hand side vector c which incorporates
          temperature boundary conditions and sources
        - solving the tri-diagonal system via `solver`
        The returned result is `T_res` in physical units.
        """
        self.T_res = zeros((self.n_cell, self.n_times), float32)
        self.T_res[:, 0] = self.T_init
        for j, dt in enumerate(self.all_dt):
            # Update of Mu(T) after N_update_Mu iterations:
            if j % self.N_update_Mu == 1:
                self.mu_list = self.compute_Mu(self.T_adim_res[:, j - 1]*self.DT_0 + self.T_init[0])

            # Compute T at time times[j+1]
            dt_adim = dt / self.P_0
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

    def _compute_lower_diagonal(self, j): 
        lower_diagonal = zeros(self.n_cell - 1, float32)
        lower_diagonal[:] = ((1 - self.alpha) / self.dz_adim**2) - (
            (1 - self.alpha) * self.kappa[1:] / (2 * self.dz_adim)
        ) * self.nablaH_adim[1:, j]
        lower_diagonal[-1] = (4 *(1 - self.alpha) / (3*self.dz_adim**2)) + (
            (1 - self.alpha) * 2 *self.kappa[-1] / (3 * self.dz_adim)
        ) * self.nablaH_adim[-1, j]
        return lower_diagonal

    def _compute_diagonal(self, j, dt_adim):
        diagonal = zeros(self.n_cell, float32)
        diagonal[:] = self.beta / dt_adim - 2 * (1 - self.alpha) / self.dz_adim**2 + self.phi * (1 - self.alpha)
        diagonal[0] = self.beta[0] / dt_adim - 4 * (1 - self.alpha) / self.dz_adim**2
        diagonal[-1] = self.beta[-1] / dt_adim - 4 * (1 - self.alpha) / self.dz_adim**2
        return diagonal

    def _compute_upper_diagonal(self, j): 
        upper_diagonal = zeros(self.n_cell - 1, float32)
        upper_diagonal[:] = ((1 - self.alpha) / self.dz_adim**2) + (
            (1 - self.alpha) * self.kappa[:-1] / (2 * self.dz_adim)
        ) * self.nablaH_adim[:-1, j]
        upper_diagonal[0] = (4 * (1 - self.alpha) / (3 * self.dz_adim**2)) + (
            (1 - self.alpha) * 2 * self.kappa[0] / (3 * self.dz_adim)
        ) * self.nablaH_adim[0, j]
        return upper_diagonal

    def _compute_c(self, j): 
        c = np.zeros(self.n_cell, np.float32)
        # Non-dimensionalization of boundary temperatures
        T_riv_adim = (self.T_riv - self.T_init[0]) / self.DT_0
        T_aq_adim = (self.T_aq - self.T_init[0]) / self.DT_0
        
        c[0] = (
            8 * (self.alpha) / (3 * self.dz_adim**2)
            - 2 * (self.alpha) * self.kappa[0] * self.nablaH_adim[0, j+1] / (3 * self.dz_adim)
        ) * T_riv_adim[j + 1] + (
            8 * (1 - self.alpha) / (3 * self.dz_adim**2)
            - 2 * (1 - self.alpha) * self.kappa[0] * self.nablaH_adim[0, j] / (3 * self.dz_adim)
        ) * T_riv_adim[j]
        c[-1] = (
           8 * (self.alpha) / (3 * self.dz_adim**2)
            + 2 * (self.alpha) * self.kappa[-1] * self.nablaH_adim[-1, j+1] / (3 * self.dz_adim)
        ) * T_aq_adim[j + 1] + (
            8 * (1 - self.alpha) / (3 * self.dz_adim**2)
            + 2 * (1 - self.alpha) * self.kappa[-1] * self.nablaH_adim[-1, j] / (3 * self.dz_adim)
        ) * T_aq_adim[j]

        c += self.phi * self.T_init[0] / self.DT_0
        return c

    def _compute_A_diagonals(self, j, dt_adim): #OK

        lower_diagonal = zeros(self.n_cell - 1, float32)
        lower_diagonal[:] = (
            - (self.alpha) / self.dz_adim**2 + (self.alpha) * self.kappa[1:] * self.nablaH_adim[1:,j+1] / (2*self.dz_adim)
        )

        lower_diagonal[-1] = (
            - 4 * (self.alpha) / (3 * self.dz_adim**2) + 2 * (self.alpha) * self.kappa[-1] * self.nablaH_adim[-1,j+1] / (3*self.dz_adim)
        )

        diagonal = zeros(self.n_cell, float32)
        diagonal[:] = (
            self.beta / dt_adim
            + 2 * (self.alpha) / self.dz_adim**2
            - self.phi * self.alpha
        )
        diagonal[0] = (
            self.beta[0] / dt_adim
            + 4 * (self.alpha) / self.dz_adim**2
        )
        diagonal[-1] = (
            self.beta[-1] / dt_adim
            + 4 * (self.alpha) / self.dz_adim**2
        )

        upper_diagonal = zeros(self.n_cell - 1, float32)
        upper_diagonal[:] = (
            - (self.alpha) / self.dz_adim**2 - (self.alpha) * self.kappa[:-1] * self.nablaH_adim[:-1,j+1] / (2*self.dz_adim)
        )
        upper_diagonal[0] = (
            - 4 * (self.alpha) / (3 * self.dz_adim**2) - 2 * (self.alpha) * self.kappa[0] * self.nablaH_adim[0,j+1] / (3*self.dz_adim)
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
