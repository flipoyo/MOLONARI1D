
"""
solver_anomaly.py
-----------------

Robust 1D heat-transport solver in saturated porous media, formulated on
**temperature anomaly** (theta = T - T0). It supports time-varying boundary
temperature at the river bed and time-varying hydraulic head difference that
drives advection (via Darcy velocity).

Numerics
========
- Operator splitting (Strang):
    A(dt/2) -> D(dt) -> A(dt/2)
  where:
    * A: advection step, explicit upwind with automatic sub-stepping
         to enforce CFL <= 0.8.
    * D: diffusion step, backward Euler (implicit), tri-diagonal solve.
- Boundary conditions:
    * Top (z=0): Dirichlet on anomaly, theta(0,t) = theta_top(t)
    * Bottom (z=z_max): Neumann zero flux, d(theta)/dz = 0
- Grid: uniform, z in [0, z_max], Nz nodes (including boundaries).
- State variable: theta(t,z) [°C], anomaly around a reference T0 [°C].

Inputs
======
- Time vector t_s [s] (not necessarily constant step, but quasi-regular recommended)
- theta_top(t) [°C] (boundary anomaly at z=0)
- dH(t) [m] : head difference (river - aquifer), defines v(t)
- Material/geometric parameters: intrinsic permeability k [m^2], porosity n [-],
  bulk thermal conductivity lambda_m [W/m/K], solid volumetric heat capacity (rho c)_s [J/m^3/K],
  distance L [m] between river and piezometer for gradient, z_max [m], Nz [nodes].

How velocity is computed
========================
K = (rho_w * g / mu) * k  [m/s]                  (hydraulic conductivity)
q(t) = - K * dH(t) / L     [m/s]                 (Darcy flux; sign conv. river->aquifer)
v(t) = q(t) / n            [m/s]                 (interstitial velocity)

Rationale for "anomaly" formulation
===================================
Working with theta = T - T0 and theta_top with zero mean removes slow DC transients
linked to the deep boundary and/or initial condition. If you want temperatures back,
just add T0: T = T0 + theta.

API overview
============
- dataclasses FluidProps, Geometry, Material to hold physical constants.
- simulate_split_anomaly(t_s, theta_top, dH_t, geom, mat, fluid, theta_init=None)
    -> returns z_grid, theta(t,z), v(t)
- interp_at(z_grid, arr_tz, z_targets): simple linear interpolation helper.
- to_temperature(theta, T0): convert anomaly array back to absolute temperature.

Example
=======
See the __main__ guard at the end for a short demonstration.
"""

from __future__ import annotations
import matplotlib.pyplot as plt
from dataclasses import dataclass
import numpy as np

# ---------------------------- Data classes ----------------------------

@dataclass
class FluidProps:
    """Fluid properties (water defaults near 20°C)."""
    rho_w: float = 1000.0        # [kg/m^3]
    c_w: float = 4182.0          # [J/(kg K)]
    mu: float = 1.002e-3         # [Pa s]
    g: float = 9.81              # [m/s^2]

    @property
    def rho_c_w(self) -> float:
        """Volumetric heat capacity of water [J/(m^3 K)]."""
        return self.rho_w * self.c_w


@dataclass
class Geometry:
    """Geometric parameters of the 1D column."""
    L: float = 1.0               # [m] river–piezometer separation for head gradient
    z_max: float = 0.6           # [m] depth of the domain
    Nz: int = 241                # [-] number of grid nodes (>= 101 recommended)


@dataclass
class Material:
    """Porous medium properties (saturated)."""
    k_intrinsic: float           # [m^2] intrinsic permeability
    n: float                     # [-] porosity
    lambda_m: float              # [W/(m K)] bulk thermal conductivity (saturated)
    rho_c_s: float               # [J/(m^3 K)] solid volumetric heat capacity (matrix)

    def bulk_heat_capacity(self, fluid: FluidProps) -> float:
        """(rho c)_eq = n (rho c)_w + (1-n) (rho c)_s  [J/(m^3 K)]."""
        return self.n * fluid.rho_c_w + (1.0 - self.n) * self.rho_c_s

    def kappa_e(self, fluid: FluidProps) -> float:
        """Effective thermal diffusivity [m^2/s]."""
        return self.lambda_m / self.bulk_heat_capacity(fluid)

    def hydraulic_conductivity(self, fluid: FluidProps) -> float:
        """Hydraulic conductivity K [m/s]."""
        return (fluid.rho_w * fluid.g / fluid.mu) * self.k_intrinsic


# ---------------------------- Numerical kernels ----------------------------

def _advection_upwind(theta: np.ndarray, dz: float, v: float, dt_half: float, theta_top: float) -> np.ndarray:
    """
    One explicit upwind advection half-step with automatic sub-stepping.
    Enforces CFL <= 0.8 for stability.
    Top boundary: Dirichlet theta_top. Bottom: Neumann (copy last interior).
    """
    Nz = theta.size
    if dz <= 0.0:
        return theta

    CFL = abs(v) * dt_half / dz
    nsub = max(1, int(np.ceil(CFL / 0.8)))
    tau = dt_half / nsub

    for _ in range(nsub):
        theta[0] = theta_top
        if v >= 0:  # downward positive -> upwind uses j-1
            for j in range(Nz - 1, 0, -1):
                theta[j] -= v * tau / dz * (theta[j] - theta[j - 1])
        else:       # upward -> upwind uses j+1
            for j in range(0, Nz - 1):
                theta[j] -= v * tau / dz * (theta[j + 1] - theta[j])
            theta[-1] = theta[-2]  # Neumann
    return theta


def _diffusion_implicit(theta: np.ndarray, dz: float, kappa: float, dt: float, theta_top: float) -> np.ndarray:
    """
    One backward-Euler diffusion step with Dirichlet at top, Neumann at bottom.
    Solve tri-diagonal system for interior nodes (j = 1..N).
    """
    Nz = theta.size
    r = kappa * dt / dz**2

    # Unknowns are interior nodes (j=1..N), N = Nz - 1
    N = Nz - 1
    if N < 1:
        return theta

    a = -r * np.ones(N - 1)   # sub-diagonal
    d = (1 + 2*r) * np.ones(N)  # diagonal
    c = -r * np.ones(N - 1)   # super-diagonal
    b = theta[1:].copy()      # RHS

    # Bottom Neumann: laplacian uses mirrored ghost => modify last equation
    d[-1] = 1 + 2*r
    a[-1] = -2*r

    # Top Dirichlet contribution
    b[0] += r * theta_top

    # Thomas algorithm
    for i in range(1, N):
        w = a[i-1] / d[i-1]
        d[i] -= w * c[i-1]
        b[i] -= w * b[i-1]

    U = np.zeros(N)
    U[-1] = b[-1] / d[-1]
    for i in range(N-2, -1, -1):
        U[i] = (b[i] - c[i] * U[i+1]) / d[i]

    out = theta.copy()
    out[0] = theta_top
    out[1:] = U
    return out


# ---------------------------- Main solver ----------------------------

def simulate_split_anomaly(
    t_s: np.ndarray,
    theta_top: np.ndarray,
    dH_t: np.ndarray,
    geom: Geometry,
    mat: Material,
    fluid: FluidProps = FluidProps(),
    theta_init: float | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Integrate theta(t,z) over time with Strang splitting on a uniform grid.

    Parameters
    ----------
    t_s : (Nt,) array of floats
        Time vector in seconds.
    theta_top : (Nt,) array
        Dirichlet anomaly at z=0, same length as t_s. Zero-mean if you want no DC.
    dH_t : (Nt,) array
        Head difference (river - aquifer) [m].
    geom : Geometry
        Domain geometry and grid.
    mat : Material
        Porous medium properties.
    fluid : FluidProps, optional
        Fluid properties (defaults are water @ ~20°C).
    theta_init : float or None
        If None, initializes anomaly to 0 everywhere. Otherwise, fills with this value.

    Returns
    -------
    z : (Nz,) array
        Depth coordinate (z=0 at the river bed, positive downward).
    theta : (Nt, Nz) array
        Anomaly field over time.
    v_t : (Nt,) array
        Interstitial velocity time series used during the integration.
    """
    t_s = np.asarray(t_s)
    theta_top = np.asarray(theta_top)
    dH_t = np.asarray(dH_t)

    assert t_s.shape == theta_top.shape == dH_t.shape, "t_s, theta_top and dH_t must have same shape."

    # Grid & properties
    z = np.linspace(0.0, geom.z_max, geom.Nz)
    dz = z[1] - z[0]
    kappa = mat.kappa_e(fluid)
    K = mat.hydraulic_conductivity(fluid)
    v_t = +(K / mat.n) * (dH_t / geom.L)  # sign convention: positive downward if dH>0

    # State allocation
    theta = np.zeros((len(t_s), geom.Nz), dtype=float)
    if theta_init is not None:
        theta[0, :] = theta_init
    # else keep zeros (anomaly)

    # Time integration
    for k in range(len(t_s) - 1):
        dt = t_s[k+1] - t_s[k]
        v_half = 0.5 * (v_t[k] + v_t[k+1])
        Th = _advection_upwind(theta[k, :].copy(), dz, v_half, dt/2, theta_top[k])
        Th = _diffusion_implicit(Th, dz, kappa, dt, theta_top[k+1])
        Th = _advection_upwind(Th, dz, v_half, dt/2, theta_top[k+1])
        theta[k+1, :] = Th

    return z, theta, v_t


# ---------------------------- Utilities ----------------------------

def interp_at(z_grid: np.ndarray, arr_tz: np.ndarray, z_targets: list[float]) -> np.ndarray:
    """Linear interpolation arr(t,z) at the requested depths (list of floats)."""
    out = []
    for zt in z_targets:
        j = np.searchsorted(z_grid, zt)
        if j == 0:
            out.append(arr_tz[:, 0])
        elif j >= len(z_grid):
            out.append(arr_tz[:, -1])
        else:
            z0, z1 = z_grid[j-1], z_grid[j]
            w = (zt - z0) / (z1 - z0)
            out.append((1 - w) * arr_tz[:, j-1] + w * arr_tz[:, j])
    return np.column_stack(out)


def to_temperature(theta_tz: np.ndarray, T0: float) -> np.ndarray:
    """Convert anomaly field back to absolute temperature: T = T0 + theta."""
    return T0 + theta_tz


# ---------------------------- Demo ----------------------------

if __name__ == "__main__":
    # Small demonstration: daily oscillation at the top, no advection, 500 h.
    T0 = 12.0
    A = 1.0
    period_s = 86400.0
    omega = 2.0 * np.pi / period_s

    # Time vector (15 min steps)
    dt = 900.0
    t_s = np.arange(0.0, 500.0*3600.0 + dt, dt)

    # Boundary anomaly: zero-mean cosine
    theta_top = A * np.cos(omega * t_s)

    # No advection
    dH_t = np.zeros_like(t_s)

    # Geometry & material (example values)
    fluid = FluidProps()
    geom  = Geometry(L=1.0, z_max=0.6, Nz=241)
    mat   = Material(k_intrinsic=1e-11, n=0.1, lambda_m=1.0, rho_c_s=4e6)

    # Run solver
    z_grid, theta_tz, v_t = simulate_split_anomaly(t_s, theta_top, dH_t, geom, mat, fluid)

    # Extract three depths and convert to T for quick sanity-check
    z_targets = [0.10, 0.20, 0.30]
    theta_probe = interp_at(z_grid, theta_tz, z_targets)
    T_probe = to_temperature(theta_probe, T0=T0)
    T_riv = to_temperature(theta_top[:, None], T0=T0)[:, 0]

    # Print quick summary
    print("Grid:", len(z_grid), "nodes; dz =", z_grid[1]-z_grid[0], "m")
    print("kappa =", mat.kappa_e(fluid), "m^2/s")
    print("Max |v| =", float(abs(v_t).max()), "m/s")
    print("T_riv mean over last 24h:", float(T_riv[-int(period_s/dt):].mean()))
    for i, zt in enumerate(z_targets):
        print(f"Depth {zt:.2f} m: mean over last 24h = {float(T_probe[-int(period_s/dt):, i].mean())}")

    plt.figure(figsize=(9,4.8))
    plt.plot(t_s/3600, T_riv, label="Rivière (z=0)")
    for i, zt in enumerate(z_targets):
        plt.plot(t_s/3600, T_probe[:, i], label=f"z = {zt:.2f} m")
    plt.xlabel("Temps (heures)")
    plt.ylabel("Température (°C)")
    plt.title("Resultat du solver")
    plt.legend()
    plt.tight_layout()
    plt.show()