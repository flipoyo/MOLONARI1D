import numpy as np

def gelman_rubin(chains, threshold=1.1):
    """
    author: Nicolas Matte
    Input : chains [3D np.array] - chaînes de Markov calculées en parallèle
            threshold [float] - seuil de l'indicateur de Gelman-Rubin, légèrement supérieur à 1
    
    Output : [bool] - True si et seulement si la phase de burn-in est considérée finie
    """

    _, n_iter, n_param = chains.shape
    
    # Variances intra-chaînes des paramètres
    Var_intra = np.var(chains, axis=1)

    # Moyenne des variances intra-chaîne
    var_intra = np.mean(Var_intra, axis=0)

    # Moyennes de chaque chaîne
    means_chains = np.mean(chains, axis=1)

    # Variance entre les moyennes des chaînes, dite inter-chaînes
    var_inter = np.var(means_chains, axis=0)

    # Calcul de l'indicateur de Gelman-Rubin
    R = np.zeros(n_param)
    for j in range(n_param):
        if np.isclose(var_intra[j], 0) :
            R[j] = 2
        else:
            R[j] = np.sqrt( var_inter[j] / var_intra[j] * (n_iter - 1) / n_iter + 1) # Vérifier la formule

    print("R = ", R)

    # On considère que la phase de burn-in est terminée dès que R < threshold
    return R < threshold