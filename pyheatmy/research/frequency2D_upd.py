import numpy as np
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class TwoDConfig:
    through_origin: bool = True         # impose y(0)=0  -> pas de terme constant
    alpha_lrt: float = 0.05             # seuil LRT
    use_aicc: bool = True               # sélection principale via AICc
    show_fit_labels: bool = True        # légendes des courbes
    # sécurité numérique pour le log(A/A0) construit en amont
    eps: float = 1e-12                  

@dataclass
class TwoDDecision:
    which: str                          # '1D' | '2D' | 'HiPoly'
    metrics: Dict[str, Any]             # coeffs, RSS, AICc, p-values, etc.

# ---------- Helpers numériques ----------

def _design_matrix(z: np.ndarray, deg: int, through_origin: bool) -> np.ndarray:
    """
    Construit la matrice de Vandermonde pour un polynôme de degré 'deg'.
    - Si through_origin=True : colonnes z^1, z^2, ..., z^deg  (pas de constante)
    - Sinon : colonnes 1, z, z^2, ..., z^deg
    """
    z = np.asarray(z, dtype=float).ravel()
    if deg < 0:
        raise ValueError("deg must be >= 0")
    if through_origin:
        if deg == 0:
            # modèle y=0 (trivial) rarement pertinent; on évite
            return np.zeros((z.size, 0))
        cols = [z**k for k in range(1, deg+1)]
        X = np.column_stack(cols)
    else:
        cols = [np.ones_like(z)] + [z**k for k in range(1, deg+1)]
        X = np.column_stack(cols)
    return X

def _fit_poly_constrained(z: np.ndarray, y: np.ndarray, deg: int, through_origin: bool):
    """
    Moindres carrés (lstsq) pour le polynôme de degré 'deg' avec ou sans intercept.
    Retourne (coeffs, y_pred, rss).
    - Conventions des coeffs:
        through_origin=True  -> c[0]*z + c[1]*z^2 + ... + c[deg-1]*z^deg
        through_origin=False -> c[0] + c[1]*z + ... + c[deg]*z^deg
    """
    X = _design_matrix(z, deg, through_origin)
    if X.size == 0:
        raise ValueError("Design matrix is empty; check deg and through_origin.")
    c, *_ = np.linalg.lstsq(X, y, rcond=None)
    y_pred = X @ c
    rss = float(np.sum((y - y_pred)**2))
    return c, y_pred, rss

def _aicc_from_rss(n: int, rss: float, k: int) -> float:
    """
    AICc pour régression gaussienne avec sigma^2_MLE = rss/n.
    AIC = n*ln(rss/n) + 2k + C ; AICc = AIC + 2k(k+1)/(n-k-1)
    La constante C s’annule dans les comparaisons -> on la garde implicite.
    """
    if n <= k + 1:
        # pénalisation très forte si sous-déterminé
        return np.inf
    if rss <= 0:
        rss = np.finfo(float).tiny
    return n * np.log(rss / n) + 2 * k + (2 * k * (k + 1)) / (n - k - 1)

def _lrt_pvalue(rss_small: float, rss_large: float, df: int) -> float:
    """
    Likelihood Ratio Test pour modèles emboîtés (large inclut small).
    Stat LRT = n*ln(RSS_small/RSS_large) * 2 ? Non:
    Pour régressions gaussiennes avec sigma inconnu et MLE, la stat classique est:
        Λ = (RSS_large / RSS_small)^{n/2}
        -2 ln Λ = n ln(RSS_small/RSS_large) ~ χ²_{df}
    Ici on utilise: 2 ln(RSS_small/RSS_large) * n/???  -> prudence.
    Plus robuste: test F:
        F = ((RSS_small - RSS_large)/df) / (RSS_large/(n - k_large))
      Mais on veut rester aligné avec ta version χ²:
        χ² ≈ 2 * ln(RSS_small/RSS_large)  (approximation utilisée précédemment)
    On conserve donc ta convention pour cohérence.
    """
    from scipy.stats import chi2
    if rss_large <= 0 or rss_small <= 0:
        return 0.0
    stat = 2.0 * np.log(rss_small / rss_large)
    p = 1.0 - chi2.cdf(stat, df)
    return float(p)

# ---------- Décision sur 1D / 2D / HiPoly (deg = N-2) ----------

def decide_1d_2d_hipoly(z: np.ndarray,
                        y: np.ndarray,
                        *,
                        config: Optional[TwoDConfig] = None,
                        show_plot: bool = False) -> TwoDDecision:
    """
    Fitte trois modèles sur y = ln(A(z)/A0):
      - 1D : polynôme degré 1      (linéaire)
      - 2D : polynôme degré 2      (quadratique)
      - HiPoly : polynôme degré N-2 (N = nb de points)
    Applique AICc comme critère principal et LRT comme test d'emboîtement.
    """
    if config is None:
        config = TwoDConfig()
    z = np.asarray(z, float).ravel()
    y = np.asarray(y, float).ravel()
    if z.size != y.size:
        raise ValueError("z and y must have the same length.")
    n = z.size
    if n < 2:
        raise ValueError("Need at least 2 points.")
    # degrés admissibles
    deg1 = 1
    deg2 = 2 if n >= 3 else 1
    degh = max(1, n - 2)              # demandé: N-2
    degh = max(degh, deg2)            # s’assure que HiPoly ≥ 2 quand possible

    # nombres de paramètres k (sans intercept si through_origin=True)
    # through_origin=True  -> k = deg
    # through_origin=False -> k = deg + 1
    def k_params(deg: int) -> int:
        return deg if config.through_origin else deg + 1

    # Fits
    c1, y1, rss1 = _fit_poly_constrained(z, y, deg1, config.through_origin)
    c2, y2, rss2 = _fit_poly_constrained(z, y, deg2, config.through_origin)
    ch, yh, rssh = _fit_poly_constrained(z, y, degh, config.through_origin)

    k1, k2, kh = k_params(deg1), k_params(deg2), k_params(degh)
    aicc1 = _aicc_from_rss(n, rss1, k1)
    aicc2 = _aicc_from_rss(n, rss2, k2)
    aicch = _aicc_from_rss(n, rssh, kh)

    # LRT (emboîtements 1D ⊂ 2D ⊂ HiPoly)
    p_12 = _lrt_pvalue(rss1, rss2, df=k2 - k1) if k2 > k1 else 1.0
    p_2h = _lrt_pvalue(rss2, rssh, df=kh - k2) if kh > k2 else 1.0

    # Choix via AICc
    aiccs = np.array([aicc1, aicc2, aicch])
    which_idx = int(np.argmin(aiccs))
    which = ['1D', '2D', 'HiPoly'][which_idx]

    metrics = {
        "deg1": deg1, "deg2": deg2, "degh": degh,
        "coeffs_deg1": c1, "coeffs_deg2": c2, "coeffs_degh": ch,
        "rss_deg1": rss1, "rss_deg2": rss2, "rss_degh": rssh,
        "aicc_deg1": aicc1, "aicc_deg2": aicc2, "aicc_degh": aicch,
        "p_LRT_1_vs_2": p_12, "p_LRT_2_vs_H": p_2h,
        "k_deg1": k1, "k_deg2": k2, "k_degh": kh,
        "n_points": n
    }

    # Optionnel: visualisation des trois fits
    if show_plot:
        import matplotlib.pyplot as plt
        z_plot = np.linspace(z.min(), z.max(), 400)
        # re-prédire sur grille pour les courbes
        def predict(c, deg, through_origin, zval):
            if through_origin:
                # y = sum_{k=1..deg} c[k-1] z^k
                Xg = np.column_stack([zval**k for k in range(1, deg+1)])
            else:
                Xg = np.column_stack([np.ones_like(zval)] + [zval**k for k in range(1, deg+1)])
            return Xg @ c

        y1g = predict(c1, deg1, config.through_origin, z_plot)
        y2g = predict(c2, deg2, config.through_origin, z_plot)
        yhg = predict(ch, degh, config.through_origin, z_plot)

        plt.figure(figsize=(7, 5))
        plt.scatter(z, y, s=30, label='data', alpha=0.8)
        lab1 = f'1D (deg=1), RSS={rss1:.3e}, AICc={aicc1:.2f}'
        lab2 = f'2D (deg=2), RSS={rss2:.3e}, AICc={aicc2:.2f}'
        labh = f'HiPoly (deg={degh}), RSS={rssh:.3e}, AICc={aicch:.2f}'
        plt.plot(z_plot, y1g, '--', label=lab1)
        plt.plot(z_plot, y2g, '-.', label=lab2)
        plt.plot(z_plot, yhg, '-', label=labh)
        if config.show_fit_labels:
            plt.legend()
        plt.xlabel('Depth z (m)')
        plt.ylabel('log(A(z)/A0)')
        plt.title(f'Model selection (AICc) → {which}')
        plt.grid(True, ls=':')
        plt.tight_layout()
        plt.show()

    return TwoDDecision(which=which, metrics=metrics)

# ---------- Intégration avec ta classe frequency_analysis ----------

def decide_for_fa_period(fa, period_index: int = 0, config: Optional[TwoDConfig] = None, show_plot: bool = False) -> TwoDDecision:
    """
    Extrait A(z) pour une période (index) depuis 'fa' (instance de frequency_analysis)
    et applique decide_1d_2d_hipoly avec les trois fits.
    Hypothèse: fa._AMPS_AT_PEAKS (n_signals x n_periods) et fa._depths existent,
               y = ln(A(z)/A(0)) est construit ici.
    """
    if config is None:
        config = TwoDConfig()

    A_mat = getattr(fa, "_AMPS_AT_PEAKS", None)
    if A_mat is None:
        raise ValueError("fa._AMPS_AT_PEAKS is not set. Run fa.estimate_a(...) once to populate amplitudes.")
    if period_index < 0 or period_index >= A_mat.shape[1]:
        raise IndexError("period_index out of range.")

    A_by_depth = np.asarray(A_mat[:, period_index], float)
    # profondeur : si fa._depths ne contient pas la profondeur 0 implicite, on la préfixe
    depths = np.asarray(getattr(fa, "_depths", None), float)
    if depths is None:
        # essaie aussi fa._depths du state interne (fa.set_inputs(...))
        depths = np.asarray(getattr(fa, "_depths", None), float)
    if depths is None:
        raise ValueError("Depths not found on 'fa'. Set them in the state (fa.set_inputs(depths=...)) or attach fa._depths.")

    # Normalisation pour correspondre à A(z) rangée comme [A(0), A(z1), ...]
    if depths.shape[0] == A_by_depth.shape[0] - 1:
        depths = np.concatenate(([0.0], depths))
    if depths.shape[0] != A_by_depth.shape[0]:
        raise ValueError("Depths and amplitude vector lengths do not match even after attempting to prepend 0.")

    # construit y = ln(A/A0)
    A0 = max(A_by_depth[0], config.eps)
    y = np.log(np.maximum(A_by_depth, config.eps) / A0)

    return decide_1d_2d_hipoly(depths, y, config=config, show_plot=show_plot)