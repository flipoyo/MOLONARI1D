from dataclasses import dataclass
import numpy as np
from typing import Optional, Dict, Any


# -----------------------------
# Result container
# -----------------------------
@dataclass
class Decision:
    is_2D: bool
    reason: str
    metrics: Dict[str, Any]   # contains z, y, rss, coeffs, AICc, p-value, etc.


# -----------------------------
# Configuration container
# -----------------------------
@dataclass
class TwoDConfig:
    # Fit type: either enforce y(0)=0 or allow an intercept
    through_origin: bool = True
    # Show LRT details in reason
    alpha_lrt: float = 0.05
    # Small epsilon to avoid log(0)
    eps: float = 1e-12
    # Whether to draw plots by default from high-level helpers
    default_show_plot: bool = False


# -----------------------------
# Core tester class
# -----------------------------
class TwoDTester:
    """
    Teste si un profil log-amplitude y(z) est mieux décrit par un modèle 1D linéaire
    que par un modèle 2D quadratique en z. Deux variantes de régression sont offertes:
      - through_origin=True  : y = c1*z  (1D)  vs y = c1*z + c2*z^2  (2D)
      - through_origin=False : y = c0 + c1*z  (1D)  vs y = c0 + c1*z + c2*z^2  (2D)

    Les comparaisons s'appuient sur AICc et sur un Likelihood Ratio Test (LRT),
    avec k (nbre de paramètres) adapté à la contrainte choisie.
    """

    def __init__(self, config: Optional[TwoDConfig] = None):
        self.config = config or TwoDConfig()

    # ---------- Linear algebra helpers ----------

    @staticmethod
    def _fit_least_squares(X: np.ndarray, y: np.ndarray):
        """Return coeffs, y_pred, rss."""
        # Solve min ||X c - y||_2
        c, *_ = np.linalg.lstsq(X, y, rcond=None)
        y_pred = X @ c
        rss = float(np.sum((y - y_pred) ** 2))
        return c, y_pred, rss

    @staticmethod
    def _design_1d(z: np.ndarray, through_origin: bool):
        """
        Build design matrix for '1D' model:
          - through_origin=True  -> columns: [z]                  (k=1)
          - through_origin=False -> columns: [1, z]               (k=2)
        """
        z = np.asarray(z, float).ravel()
        if through_origin:
            X = z.reshape(-1, 1)
            k = 1
        else:
            X = np.column_stack([np.ones_like(z), z])
            k = 2
        return X, k

    @staticmethod
    def _design_2d(z: np.ndarray, through_origin: bool):
        """
        Build design matrix for '2D' model:
          - through_origin=True  -> columns: [z, z^2]             (k=2)
          - through_origin=False -> columns: [1, z, z^2]          (k=3)
        """
        z = np.asarray(z, float).ravel()
        z2 = z * z
        if through_origin:
            X = np.column_stack([z, z2])
            k = 2
        else:
            X = np.column_stack([np.ones_like(z), z, z2])
            k = 3
        return X, k

    # ---------- Information criteria & LRT ----------

    @staticmethod
    def _aicc(n: int, rss: float, sigma2_hat: float, k: int) -> float:
        """
        AICc pour erreurs gaussiennes avec variance sigma2_hat fournie.
        log-vraisemblance: L = -0.5*n*log(2πσ^2) - RSS/(2σ^2)
        AIC = 2k - 2L
        AICc = AIC + 2k(k+1)/(n-k-1)
        """
        # Robustness
        sigma2_hat = max(sigma2_hat, 1e-30)
        L = -0.5 * n * np.log(2 * np.pi * sigma2_hat) - 0.5 * rss / sigma2_hat
        AIC = 2 * k - 2 * L
        # Avoid division by zero if n-k-1 <= 0:
        denom = max(1, n - k - 1)
        AICc = AIC + (2 * k * (k + 1)) / denom
        return float(AICc)

    @staticmethod
    def _lrt_pvalue(rss1: float, rss2: float, k1: int, k2: int) -> float:
        """
        Likelihood Ratio Test (nested models) with Gaussian errors & common variance.
        Test statistic:  Λ = 2 * ln(L2/L1) = 2 * ln(rss1/rss2)   (for MLE with σ^2 factored out)
        DOF = k2 - k1.
        """
        from scipy.stats import chi2
        # Guard rails:
        rss1 = max(rss1, 1e-30)
        rss2 = max(rss2, 1e-30)
        df = max(1, k2 - k1)
        LRT = 2.0 * np.log(rss1 / rss2)
        p = 1.0 - chi2.cdf(LRT, df)
        return float(p)

    # ---------- Public API ----------
    def decide_1d_vs_2d(self, z: np.ndarray, y: np.ndarray,
                        show_plot: Optional[bool] = None) -> Decision:
        """
        Decide between 1D and 2D given (z, y).
        y is typically log(A(z)/A(0)) so que y(0)=0 en théorie.
        """

        cfg = self.config
        if show_plot is None:
            show_plot = cfg.default_show_plot

        z = np.asarray(z, float).ravel()
        y = np.asarray(y, float).ravel()

        # Finite mask
        m = np.isfinite(z) & np.isfinite(y)
        z = z[m]; y = y[m]
        n = z.size
        if n < 2:
            return Decision(False, "Not enough points (n<2).", {"n": n})

        # Build designs
        X1, k1 = self._design_1d(z, cfg.through_origin)
        X2, k2 = self._design_2d(z, cfg.through_origin)

        # Fit
        c1, y1, rss1 = self._fit_least_squares(X1, y)
        c2, y2, rss2 = self._fit_least_squares(X2, y)

        # Sigma estimate from 1D residuals (unbiased ~ dof=n-k1)
        dof1 = max(1, n - k1)
        sigma2_hat = rss1 / dof1

        # Criteria
        aicc1 = self._aicc(n, rss1, sigma2_hat, k1)
        aicc2 = self._aicc(n, rss2, sigma2_hat, k2)
        p_lrt = self._lrt_pvalue(rss1, rss2, k1, k2)

        # Decisions
        better_aicc = (aicc2 < aicc1)
        better_lrt = (p_lrt < cfg.alpha_lrt)
        is_2D = bool(better_aicc or better_lrt)

        reason = []
        reason.append(f"AICc(1D)={aicc1:.3f}, AICc(2D)={aicc2:.3f} → {'2D' if better_aicc else '1D'}")
        reason.append(f"LRT p={p_lrt:.3g} (alpha={cfg.alpha_lrt}) → {'2D' if better_lrt else '1D'}")
        reason = " | ".join(reason)

        # Plot (optional)
        if show_plot:
            import matplotlib.pyplot as plt
            z_plot = np.linspace(np.nanmin(z), np.nanmax(z), 200)
            # Build prediction design matrices for plotting
            if cfg.through_origin:
                X1p = z_plot.reshape(-1, 1)
                X2p = np.column_stack([z_plot, z_plot**2])
            else:
                X1p = np.column_stack([np.ones_like(z_plot), z_plot])
                X2p = np.column_stack([np.ones_like(z_plot), z_plot, z_plot**2])

            y1p = X1p @ c1
            y2p = X2p @ c2

            plt.figure(figsize=(6, 4))
            plt.scatter(z, y, s=30, label="Data")
            plt.plot(z_plot, y1p, label=f"1D fit (k={k1}, RSS={rss1:.3g})", linestyle="--")
            plt.plot(z_plot, y2p, label=f"2D fit (k={k2}, RSS={rss2:.3g})")
            ttl = "Constrained through origin" if cfg.through_origin else "Free intercept"
            plt.title(f"1D vs 2D — {ttl}\n{reason}")
            plt.xlabel("Depth z (m)")
            plt.ylabel("y(z) = log[A(z)/A(0)]")
            plt.grid(True, ls=":")
            plt.legend()
            plt.tight_layout()
            plt.show()

        metrics = {
            "z": z, "y": y,
            "coeffs_deg1": c1, "coeffs_deg2": c2,
            "rss_deg1": rss1, "rss_deg2": rss2,
            "k1": k1, "k2": k2, "n": n,
            "sigma2_hat": sigma2_hat,
            "aicc1": aicc1, "aicc2": aicc2,
            "p_lrt": p_lrt,
            "through_origin": cfg.through_origin
        }
        return Decision(is_2D=is_2D, reason=reason, metrics=metrics)

    # ---------- Convenience wrappers ----------

    def decide_from_amplitudes(self, depths: np.ndarray, amplitudes_at_period: np.ndarray,
                               show_plot: Optional[bool] = None) -> Decision:
        """
        Entrée: profondeur 'depths' et amplitude spectrale A(z) pour UNE période.
        On construit y(z) = log(A(z)/A(0)) puis on appelle decide_1d_vs_2d.
        """
        cfg = self.config
        if show_plot is None:
            show_plot = cfg.default_show_plot

        depths = np.asarray(depths, float).ravel()
        A = np.asarray(amplitudes_at_period, float).ravel()

        if A.size != depths.size:
            raise ValueError("depths and amplitudes_at_period must have the same length.")

        if A[0] <= 0:
            raise ValueError("Reference amplitude A(0) <= 0; cannot normalize.")

        eps = cfg.eps
        y = np.log(np.maximum(A, eps) / max(A[0], eps))
        return self.decide_1d_vs_2d(depths, y, show_plot=show_plot)

    def decide_for_fa_period(self, fa, period_index: int = 0,
                             show_plot: Optional[bool] = None) -> Decision:
        """
        Utilitaire pour travailler directement avec ton objet `frequency_analysis` :
          - lit fa._AMPS_AT_PEAKS  (matrice (n_signaux x n_périodes))
          - lit fa._depths         (vector)
          - ajuste depths pour inclure z=0 si besoin
        """
        cfg = self.config
        if show_plot is None:
            show_plot = cfg.default_show_plot

        if not hasattr(fa, "_AMPS_AT_PEAKS"):
            raise ValueError("fa._AMPS_AT_PEAKS not found. Run fa.estimate_a(...) first to populate amplitudes.")

        A_all = fa._AMPS_AT_PEAKS[:, period_index]  # shape (n_signaux,)
        depths = np.asarray(fa._depths, float).ravel()

        # Si depths ne contient pas la rivière (z=0) mais A_all oui, on préfixe 0:
        if depths.shape[0] == A_all.shape[0] - 1:
            depths = np.concatenate(([0.0], depths))

        if depths.shape[0] != A_all.shape[0]:
            raise ValueError(f"Mismatch: depths has length {depths.shape[0]} but amplitudes {A_all.shape[0]}.")

        return self.decide_from_amplitudes(depths, A_all, show_plot=show_plot)