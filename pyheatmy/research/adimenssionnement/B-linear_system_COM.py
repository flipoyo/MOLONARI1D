# Import du type float32 (précision simple) et de la fonction zeros (création de tableaux nuls)
from numpy import float32, zeros

# Import de la fonction solve pour résoudre les systèmes linéaires denses
from numpy.linalg import solve

# import numpy as np  # Commenté, redondant avec l'import ci-dessous
# Import de njit pour la compilation JIT (Just-In-Time) avec Numba (optimisation performance)
from numba import njit
# Import de NumPy pour les opérations sur tableaux
import numpy as np

# Import du solveur tri-diagonal personnalisé et de la fonction de produit matrice-vecteur tri-diagonal
from pyheatmy.solver import solver, tri_product
# Import de toutes les constantes physiques (RHO_W, C_W, LAMBDA_W, ALPHA, etc.)
from pyheatmy.config import *


# Première classe qui définit et initie les paramètres physiques communs des systèmes linéaires de la classe H_stratified et T_stratified
class Linear_system:
    def __init__(
        self,
        Ss_list,  # Liste des coefficients d'emmagasinement spécifique (Specific Storage) par maille [1/m]
        moinslog10IntrinK_list,  # Liste de -log10(perméabilité intrinsèque) par maille [sans dimension]
        n_list,  # Liste des porosités par maille [sans dimension, 0 à 1]
        lambda_s_list,  # Liste des conductivités thermiques du solide par maille [W/(m·K)]
        rhos_cs_list,  # Liste des capacités thermiques volumiques du solide (rho_s * c_s) par maille [J/(m³·K)]
        all_dt,  # Tableau de tous les pas de temps [s]
        dz,  # Pas d'espace vertical (taille d'une maille) [m]
        H_init,  # Charge hydraulique initiale par maille [m]
        T_init,  # Température initiale par maille [K ou °C]
    ):
        # Stockage de -log10(perméabilité intrinsèque) par maille
        self.moinslog10IntrinK_list = moinslog10IntrinK_list
        # Stockage de la température initiale par maille
        self.T_init = T_init
        # Stockage des porosités par maille
        self.n_list = n_list
        # Stockage des capacités thermiques volumiques du solide par maille
        self.rhos_cs_list = rhos_cs_list
        # Stockage des conductivités thermiques du solide par maille
        self.lambda_s_list = lambda_s_list
        # Stockage de la charge hydraulique initiale par maille
        self.H_init = H_init
        # Stockage de tous les pas de temps
        self.all_dt = all_dt
        # Stockage du pas d'espace vertical
        self.dz = dz
        # Stockage des coefficients d'emmagasinement spécifique par maille
        self.Ss_list = Ss_list
        # Calcul de tous les paramètres physiques dérivés (K, mu, ke, ae, etc.)
        self.calc_physical_param()

    # @njit  # Décorateur Numba commenté (pourrait accélérer le calcul si activé)
    def compute_Mu(self, T):  # T: température [K ou °C]
        # mu = MU_A * np.exp(MU_B * 1.0 / T + MU_C * T + MU_D * (T**2))  # Formule complète commentée (peut provoquer overflow)
        # mu = MU_A * np.exp(MU_B * 1.0 / T + MU_C * T + MU_D * (T**2))  # Doublon commenté
        # Utilisation d'une viscosité dynamique constante par défaut [Pa·s ou kg/(m·s)]
        mu = DEFAULT_MU
        # Retour de la viscosité dynamique (constante ou dépendante de T si la formule est activée)
        return mu

    # @njit  # Décorateur Numba commenté
    def compute_K(self, moinslog10IntrinK_list):  # moinslog10IntrinK_list: -log10(k_intrin) par maille
        # Calcul de la conductivité hydraulique K = (rho_w * g * k_intrin) / mu [m/s]
        # où k_intrin = 10^(-moinslog10IntrinK_list) [m²]
        # RHO_W: masse volumique de l'eau [kg/m³], G: accélération de la gravité [m/s²]
        return (RHO_W * G * 10.0**-moinslog10IntrinK_list) * 1.0 / self.mu_list

    def compute_n_cell(self):
        # Calcul du nombre de mailles verticales (égal à la longueur de H_init)
        return len(self.H_init)

    def compute_n_times(self):
        # Calcul du nombre de pas de temps (+1 car on inclut la condition initiale)
        return len(self.all_dt) + 1

    def compute_rho_mc_m_list(self):
        # Calcul de la capacité thermique volumique moyenne du milieu poreux (rho*c)_m [J/(m³·K)]
        # Formule: n * (rho*c)_eau + (1-n) * (rho*c)_solide
        # RHO_W: masse volumique de l'eau [kg/m³], C_W: chaleur spécifique de l'eau [J/(kg·K)]
        return self.n_list * RHO_W * C_W + (1 - self.n_list) * self.rhos_cs_list

    def compute_lambda_m_list(self):
        # Calcul de la conductivité thermique moyenne du milieu poreux lambda_m [W/(m·K)]
        # Formule de moyenne géométrique: (n * sqrt(lambda_w) + (1-n) * sqrt(lambda_s))²
        # LAMBDA_W: conductivité thermique de l'eau [W/(m·K)]
        return (
            self.n_list * (LAMBDA_W) ** 0.5
            + (1.0 - self.n_list) * (self.lambda_s_list) ** 0.5
        ) ** 2

    def compute_ke_list(self):
        # Calcul de la diffusivité thermique effective ke = lambda_m / (rho*c)_m [m²/s]
        return self.lambda_m_list / self.rho_mc_m_list

    def compute_ae_list(self):
        # Calcul du coefficient advectif thermique ae = (rho*c)_eau * K / (rho*c)_m [m/s]
        # Représente l'effet du transport de chaleur par l'écoulement de l'eau
        return RHO_W * C_W * self.K_list / self.rho_mc_m_list

    def compute_dK_list(self, K_list, n_cell, dz):  # K_list: conductivité hydraulique, n_cell: nombre de mailles, dz: pas d'espace
        # Calcul de la dérivée spatiale dK/dz par différences finies [m/s/m = 1/s]
        # Initialisation d'un tableau de taille n_cell
        list = zeros(n_cell, float32)
        # Différence avant pour la première maille: (K[1] - K[0]) / dz
        list[0] = (K_list[1] - K_list[0]) / dz
        # Différence arrière pour la dernière maille: (K[n-1] - K[n-2]) / dz
        list[-1] = (K_list[-1] - K_list[-2]) / dz
        # Différences centrées pour les mailles intérieures: (K[i+1] - K[i-1]) / (2*dz)
        for idx in range(1, len(list) - 1):
            list[idx] = (K_list[idx + 1] - K_list[idx - 1]) / (2 * dz)
        # Retour du tableau dK/dz
        return list

    def compute_H_res(self):
        # Initialisation du tableau des résultats de charge hydraulique H_res [m]
        # Dimensions: (n_cell, n_times) pour stocker H à chaque maille et chaque instant
        H_res = zeros((self.n_cell, self.n_times), float32)
        # Remplissage de la condition initiale (colonne t=0) avec H_init
        H_res[:, 0] = self.H_init[:]
        # Retour du tableau initialisé
        return H_res

    def compute_KsurSs_list(self):
        # Calcul du rapport K/Ss = diffusivité hydraulique [m²/s]
        # Utilisé dans l'équation de diffusivité hydraulique
        return self.K_list / self.Ss_list

    def calc_physical_param(self):
        # Calcul de tous les paramètres physiques dérivés (appelé dans __init__)
        # Nombre de mailles verticales
        self.n_cell = self.compute_n_cell()
        # Nombre de pas de temps (incluant condition initiale)
        self.n_times = self.compute_n_times()
        # Viscosité dynamique de l'eau [Pa·s] (dépendante ou non de T_init)
        self.mu_list = self.compute_Mu(self.T_init)
        # Conductivité hydraulique K [m/s] calculée à partir de la perméabilité intrinsèque
        self.K_list = self.compute_K(self.moinslog10IntrinK_list)
        # Capacité thermique volumique moyenne du milieu poreux [J/(m³·K)]
        self.rho_mc_m_list = self.compute_rho_mc_m_list()
        # Conductivité thermique moyenne du milieu poreux [W/(m·K)]
        self.lambda_m_list = self.compute_lambda_m_list()
        # Diffusivité thermique effective [m²/s]
        self.ke_list = self.compute_ke_list()
        # Coefficient advectif thermique [m/s]
        self.ae_list = self.compute_ae_list()
        # Tableau des résultats de charge hydraulique initialisé
        self.H_res = self.compute_H_res()
        # Dérivée spatiale de la conductivité hydraulique dK/dz [1/s]
        self.dK_list = self.compute_dK_list(self.K_list, self.n_cell, self.dz)
        # Diffusivité hydraulique K/Ss [m²/s]
        self.KsurSs_list = self.compute_KsurSs_list()



# Classe qui définit le système linéaire pour l'équation de la diffusivité hydraulique
class H_stratified(Linear_system):
    def __init__(
        self,
        Ss_list,  # Coefficients d'emmagasinement spécifique par maille [1/m]
        moinslog10IntrinK_list,  # -log10(perméabilité intrinsèque) par maille
        n_list,  # Porosités par maille [0-1]
        lambda_s_list,  # Conductivités thermiques du solide par maille [W/(m·K)]
        rhos_cs_list,  # Capacités thermiques volumiques du solide par maille [J/(m³·K)]
        all_dt,  # Tableau des pas de temps [s]
        q_list,  # Sources/puits de chaleur par maille [W/m³]
        dz,  # Pas d'espace vertical [m]
        H_init,  # Charge hydraulique initiale par maille [m]
        H_riv,  # Charge hydraulique à la limite supérieure (rivière) au cours du temps [m]
        H_aq,  # Charge hydraulique à la limite inférieure (aquifère) au cours du temps [m]
        T_init,  # Température initiale par maille [K ou °C]
        array_K,  # Tableau des conductivités hydrauliques par strate [m/s]
        array_Ss,  # Tableau des coefficients d'emmagasinement par strate [1/m]
        list_zLow,  # Liste des profondeurs des limites basses de chaque strate [m]
        z_solve,  # Profondeurs des centres de mailles [m]
        inter_cara,  # Liste des caractéristiques des interfaces (position, type)
        isdtconstant,  # Booléen indiquant si le pas de temps est constant
        alpha=ALPHA,  # Paramètre du schéma theta (0=explicite, 0.5=Crank-Nicolson, 1=implicite)
    ):
        # Appel du constructeur de la classe parente Linear_system
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
        # Stockage du tableau des conductivités hydrauliques par strate
        self.array_K = array_K
        # Stockage du tableau des coefficients d'emmagasinement par strate
        self.array_Ss = array_Ss
        # Stockage de la liste des profondeurs des limites basses de chaque strate
        self.list_zLow = list_zLow
        # Stockage des profondeurs des centres de mailles
        self.z_solve = z_solve
        # Stockage de la température initiale (redondant avec parent, mais explicite)
        self.T_init = T_init
        # Stockage des caractéristiques des interfaces géologiques
        self.inter_cara = inter_cara
        # Stockage de -log10(perméabilité intrinsèque) (redondant, pour clarté)
        self.moinslog10IntrinK_list = moinslog10IntrinK_list
        # Stockage des coefficients d'emmagasinement (redondant, pour clarté)
        self.Ss_list = Ss_list
        # Stockage du tableau des pas de temps
        self.all_dt = all_dt
        # Stockage du booléen indiquant si dt est constant
        self.isdtconstant = isdtconstant
        # Stockage du pas d'espace vertical
        self.dz = dz
        # Stockage de la charge hydraulique initiale
        self.H_init = H_init
        # Stockage de la charge hydraulique à la limite supérieure (rivière)
        self.H_riv = H_riv
        # Stockage de la charge hydraulique à la limite inférieure (aquifère)
        self.H_aq = H_aq
        # Stockage du paramètre du schéma theta
        self.alpha = alpha
        # Stockage des sources/puits de chaleur
        self.heat_source = q_list

    def compute_H_stratified(self):
        # Méthode principale pour calculer la charge hydraulique stratifiée au cours du temps
        # Test si le pas de temps est constant pour tous les pas
        if self.isdtconstant.all():
            # Si dt constant: optimisation en calculant les matrices A et B une seule fois
            self.compute_H_constant_dt()
        else:
            # Si dt variable: recalcul des matrices A et B à chaque pas de temps
            self.compute_H_variable_dt()
        # Retour du tableau H_res contenant H(z,t) pour toutes les mailles et tous les temps
        return self.H_res

    def compute_H_constant_dt(self):
        # Calcul de H quand le pas de temps est constant (plus efficace)
        # Extraction du pas de temps (constant) depuis le premier élément
        dt = self.all_dt[0]

        # Calcul des 3 diagonales de la matrice B (partie explicite du schéma theta)
        lower_diagonal_B, diagonal_B, upper_diagonal_B = self.compute_B_diagonals(dt)
        # Calcul des 3 diagonales de la matrice A (partie implicite du schéma theta)
        lower_diagonal_A, diagonal_A, upper_diagonal_A = self.compute_A_diagonals(dt)

        # Boucle sur toutes les interfaces géologiques pour corriger le schéma numérique
        for tup_idx in range(len(self.inter_cara)):
            # Correction des diagonales aux interfaces (utilise Keq si interface interne)
            self.correct_numerical_schema(
                tup_idx,
                lower_diagonal_B,
                diagonal_B,
                upper_diagonal_B,
                lower_diagonal_A,
                diagonal_A,
                upper_diagonal_A,
            )

        # Boucle temporelle sur tous les pas de temps
        for j in range(self.n_times - 1):
            # Calcul du vecteur c contenant les contributions des conditions aux limites
            c = self.compute_c(j)
            # Produit matrice-vecteur tri-diagonal: B * H^n + c
            B_fois_H_plus_c = (
                tri_product(
                    lower_diagonal_B, diagonal_B, upper_diagonal_B, self.H_res[:, j]
                )
                + c
            )
            # Résolution du système tri-diagonal A * H^{n+1} = B * H^n + c
            self.H_res[:, j + 1] = solver(
                lower_diagonal_A, diagonal_A, upper_diagonal_A, B_fois_H_plus_c
            )

    def nablaH(self):
        # Calcul du gradient spatial de la charge hydraulique ∇H = dH/dz [sans dimension]
        # Initialisation du tableau nablaH(z,t) pour toutes les mailles et tous les temps
        nablaH = np.zeros((self.n_cell, self.n_times), np.float32)

        # Première maille: différence décentrée avant avec correction 2/3 pour condition limite
        # nablaH[0] ≈ (H[1] - H_riv) / dz, avec facteur 2/(3*dz) pour schéma ordre 2
        nablaH[0, :] = 2 * (self.H_res[1, :] - self.H_riv) / (3 * self.dz)

        # Mailles intérieures: différences centrées ∇H[i] = (H[i+1] - H[i-1]) / (2*dz)
        for i in range(1, self.n_cell - 1):
            nablaH[i, :] = (self.H_res[i + 1, :] - self.H_res[i - 1, :]) / (2 * self.dz)

        # Dernière maille: différence décentrée arrière avec correction 2/3 pour condition limite
        # nablaH[n-1] ≈ (H_aq - H[n-2]) / dz, avec facteur 2/(3*dz)
        nablaH[self.n_cell - 1, :] = (
            2 * (self.H_aq - self.H_res[self.n_cell - 2, :]) / (3 * self.dz)
        )
        # Retour du gradient spatial de H
        return nablaH

    def compute_H_variable_dt(self):
        # Calcul de H quand le pas de temps est variable
        # Boucle sur tous les pas de temps avec leur valeur dt respective
        for j, dt in enumerate(self.all_dt):
            # Calcul des 3 diagonales de B pour le pas de temps dt courant
            lower_diagonal_B, diagonal_B, upper_diagonal_B = self.compute_B_diagonals(
                dt
            )
            # Calcul des 3 diagonales de A pour le pas de temps dt courant
            lower_diagonal_A, diagonal_A, upper_diagonal_A = self.compute_A_diagonals(
                dt
            )

            # Boucle sur toutes les interfaces pour corriger le schéma à chaque pas de temps
            for tup_idx in range(len(self.inter_cara)):
                # Correction des diagonales aux interfaces (Keq si nécessaire)
                self.correct_numerical_schema(
                    tup_idx,
                    lower_diagonal_B,
                    diagonal_B,
                    upper_diagonal_B,
                    lower_diagonal_A,
                    diagonal_A,
                    upper_diagonal_A,
                )

            # Calcul du vecteur c pour le pas de temps j
            c = self.compute_c(j)
            # Produit matrice-vecteur: B * H^n + c
            B_fois_H_plus_c = (
                tri_product(
                    lower_diagonal_B, diagonal_B, upper_diagonal_B, self.H_res[:, j]
                )
                + c
            )
            # Résolution du système A * H^{n+1} = B * H^n + c
            self.H_res[:, j + 1] = solver(
                lower_diagonal_A, diagonal_A, upper_diagonal_A, B_fois_H_plus_c
            )

    def compute_B_diagonals(self, dt):  # dt: pas de temps [s]
        # Construction des 3 diagonales de la matrice B (partie explicite du schéma theta)
        # Équation discrétisée: Ss/dt * H^{n+1} + alpha * K * d²H^{n+1}/dz² = Ss/dt * H^n - (1-alpha) * K * d²H^n/dz²
        # B correspond au côté droit (temps n)
        
        # Diagonale inférieure de B: coefficient pour H_{i-1}^n
        # Formule: alpha * K[i] / dz² pour les mailles intérieures
        lower_diagonal_B = self.K_list[1:] * self.alpha / self.dz**2
        # Dernière entrée: correction 4/3 pour condition limite inférieure
        lower_diagonal_B[-1] = (
            4 * self.K_list[self.n_cell - 1] * self.alpha / (3 * self.dz**2)
        )

        # Diagonale principale de B: coefficient pour H_i^n
        # Formule: Ss/dt - 2 * alpha * K / dz² (terme diffusif centré)
        diagonal_B = self.Ss_list * 1 / dt - 2 * self.K_list * self.alpha / self.dz**2
        # Première entrée: correction 4/3 pour condition limite supérieure (rivière)
        diagonal_B[0] = (
            self.Ss_list[0] * 1 / dt - 4 * self.K_list[0] * self.alpha / self.dz**2
        )
        # Dernière entrée: correction 4/3 pour condition limite inférieure (aquifère)
        diagonal_B[-1] = (
            self.Ss_list[self.n_cell - 1] * 1 / dt
            - 4 * self.K_list[self.n_cell - 1] * self.alpha / self.dz**2
        )

        # Diagonale supérieure de B: coefficient pour H_{i+1}^n
        # Formule: alpha * K[i] / dz² pour les mailles intérieures
        upper_diagonal_B = self.K_list[:-1] * self.alpha / self.dz**2
        # Première entrée: correction 4/3 pour condition limite supérieure
        upper_diagonal_B[0] = 4 * self.K_list[0] * self.alpha / (3 * self.dz**2)

        # Retour des 3 diagonales de la matrice B
        return lower_diagonal_B, diagonal_B, upper_diagonal_B

    def compute_A_diagonals(self, dt):  # dt: pas de temps [s]
        # Construction des 3 diagonales de la matrice A (partie implicite du schéma theta)
        # A correspond au côté gauche (temps n+1)
        
        # Diagonale inférieure de A: coefficient pour H_{i-1}^{n+1}
        # Formule: -(1-alpha) * K[i] / dz² (signe négatif car déplacé à gauche)
        lower_diagonal_A = -self.K_list[1:] * (1 - self.alpha) / self.dz**2
        # Dernière entrée: correction 4/3 pour condition limite inférieure
        lower_diagonal_A[-1] = (
            -4 * self.K_list[self.n_cell - 1] * (1 - self.alpha) / (3 * self.dz**2)
        )

        # Diagonale principale de A: coefficient pour H_i^{n+1}
        # Formule: Ss/dt + 2 * (1-alpha) * K / dz² (signe positif car à gauche)
        diagonal_A = (
            self.Ss_list * 1 / dt + 2 * self.K_list * (1 - self.alpha) / self.dz**2
        )
        # Première entrée: correction 4/3 pour condition limite supérieure
        diagonal_A[0] = (
            self.Ss_list[0] * 1 / dt
            + 4 * self.K_list[0] * (1 - self.alpha) / self.dz**2
        )
        # Dernière entrée: correction 4/3 pour condition limite inférieure
        diagonal_A[-1] = (
            self.Ss_list[self.n_cell - 1] * 1 / dt
            + 4 * self.K_list[self.n_cell - 1] * (1 - self.alpha) / self.dz**2
        )

        # Diagonale supérieure de A: coefficient pour H_{i+1}^{n+1}
        # Formule: -(1-alpha) * K[i] / dz²
        upper_diagonal_A = -self.K_list[:-1] * (1 - self.alpha) / self.dz**2
        # Première entrée: correction 4/3 pour condition limite supérieure
        upper_diagonal_A[0] = -4 * self.K_list[0] * (1 - self.alpha) / (3 * self.dz**2)

        # Retour des 3 diagonales de la matrice A
        return lower_diagonal_A, diagonal_A, upper_diagonal_A

    def correct_numerical_schema(
        self,
        tup_idx,  # Indice de l'interface courante dans la liste inter_cara
        lower_diagonal_B,  # Diagonale inférieure de B (modifiée in-place)
        diagonal_B,  # Diagonale principale de B (modifiée in-place)
        upper_diagonal_B,  # Diagonale supérieure de B (modifiée in-place)
        lower_diagonal_A,  # Diagonale inférieure de A (modifiée in-place)
        diagonal_A,  # Diagonale principale de A (modifiée in-place)
        upper_diagonal_A,  # Diagonale supérieure de A (modifiée in-place)
    ):
        # Méthode de correction du schéma numérique aux interfaces géologiques
        # Traite les discontinuités de conductivité hydraulique entre strates
        
        # Extraction des conductivités des deux strates séparées par l'interface
        K1 = self.array_K[tup_idx]  # Conductivité hydraulique de la strate supérieure [m/s]
        K2 = self.array_K[tup_idx + 1]  # Conductivité hydraulique de la strate inférieure [m/s]

        # Cas 1: Interface alignée exactement sur un nœud de maillage (flag == 0)
        if self.inter_cara[tup_idx][1] == 0:
            # Extraction de l'indice de maille où se trouve l'interface
            pos_idx = int(self.inter_cara[tup_idx][0])
            # Correction de la diagonale principale de B: utilise K1 au-dessus et K2 en-dessous
            diagonal_B[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                - (K1 + K2) * self.alpha / self.dz**2
            )
            # Correction de la diagonale inférieure de B: utilise K1 (strate supérieure)
            lower_diagonal_B[pos_idx - 1] = K1 * self.alpha / self.dz**2
            # Correction de la diagonale supérieure de B: utilise K2 (strate inférieure)
            upper_diagonal_B[pos_idx] = K2 * self.alpha / self.dz**2
            # Correction de la diagonale principale de A: utilise K1 et K2
            diagonal_A[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                + (K1 + K2) * (1 - self.alpha) / self.dz**2
            )
            # Correction de la diagonale inférieure de A: utilise K1
            lower_diagonal_A[pos_idx - 1] = -K1 * (1 - self.alpha) / self.dz**2
            # Correction de la diagonale supérieure de A: utilise K2
            upper_diagonal_A[pos_idx] = -K2 * (1 - self.alpha) / self.dz**2
        else:
            # Cas 2: Interface située à l'intérieur d'une maille (flag != 0)
            # Nécessite le calcul d'une conductivité équivalente Keq
            
            # Extraction de l'indice de maille contenant l'interface
            pos_idx = int(self.inter_cara[tup_idx][0])
            # Calcul de la position relative x de l'interface dans la maille [0-1]
            # x = distance de l'interface au centre pos_idx / distance entre centres pos_idx et pos_idx+1
            x = (self.list_zLow[tup_idx] - self.z_solve[pos_idx]) / (
                self.z_solve[pos_idx + 1] - self.z_solve[pos_idx]
            )
            # Calcul de la conductivité équivalente Keq par moyenne harmonique pondérée
            # Keq = 1 / (x/K1 + (1-x)/K2) - assure la continuité du flux à l'interface
            Keq = 1 / (x / K1 + (1 - x) / K2)
            
            # Correction pour la maille pos_idx (contient une partie de K1 et une partie de Keq)
            # Diagonale principale de B pour maille pos_idx: utilise K1 (au-dessus) et Keq (interface)
            diagonal_B[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                - (K1 + Keq) * self.alpha / self.dz**2
            )
            # Diagonale inférieure de B: connexion avec maille au-dessus (K1)
            lower_diagonal_B[pos_idx - 1] = K1 * self.alpha / self.dz**2
            # Diagonale supérieure de B: connexion avec maille en-dessous via Keq
            upper_diagonal_B[pos_idx] = Keq * self.alpha / self.dz**2
            # Même logique pour la matrice A (partie implicite)
            diagonal_A[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                + (K1 + Keq) * (1 - self.alpha) / self.dz**2
            )
            lower_diagonal_A[pos_idx - 1] = -K1 * (1 - self.alpha) / self.dz**2
            upper_diagonal_A[pos_idx] = -Keq * (1 - self.alpha) / self.dz**2

            # Correction pour la maille pos_idx+1 (contient une partie de Keq et une partie de K2)
            # Diagonale principale de B pour maille pos_idx+1: utilise K2 (en-dessous) et Keq (interface)
            diagonal_B[pos_idx + 1] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                - (K2 + Keq) * self.alpha / self.dz**2
            )
            # Diagonale inférieure de B: connexion avec maille au-dessus via Keq
            lower_diagonal_B[pos_idx] = Keq * self.alpha / self.dz**2
            # Diagonale supérieure de B: connexion avec maille en-dessous (K2)
            upper_diagonal_B[pos_idx + 1] = K2 * self.alpha / self.dz**2
            # Même logique pour la matrice A
            diagonal_A[pos_idx + 1] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                + (K2 + Keq) * (1 - self.alpha) / self.dz**2
            )
            lower_diagonal_A[pos_idx] = -Keq * (1 - self.alpha) / self.dz**2
            upper_diagonal_A[pos_idx + 1] = -K2 * (1 - self.alpha) / self.dz**2

    def compute_c(self, j):  # j: indice du pas de temps courant
        # Calcul du vecteur c contenant les contributions des conditions aux limites de Dirichlet
        # et des termes sources/puits
        
        # Initialisation d'un vecteur nul de taille n_cell
        c = zeros(self.n_cell, float32)
        # Condition limite supérieure (rivière, première maille)
        # Formule: 8*K/(3*dz²) * [(1-alpha)*H_riv^{n+1} + alpha*H_riv^n]
        # Facteur 8/3 provient du schéma aux différences finies d'ordre 2 à la frontière
        c[0] = (8 * self.K_list[0] / (3 * self.dz**2)) * (
            (1 - self.alpha) * self.H_riv[j + 1] + self.alpha * self.H_riv[j]
        )
        # Condition limite inférieure (aquifère, dernière maille)
        # Formule similaire avec H_aq
        c[-1] = (8 * self.K_list[self.n_cell - 1] / (3 * self.dz**2)) * (
            (1 - self.alpha) * self.H_aq[j + 1] + self.alpha * self.H_aq[j]
        )
        # Soustraction du terme source/puits de chaleur (peut être 0 si pas de source)
        c -= self.heat_source
        # Retour du vecteur c
        return c



# Classe qui définit le système linéaire pour l'équation de la chaleur (transport thermique)
class T_stratified(Linear_system):
    def __init__(
        self,
        nablaH,  # Gradient spatial de la charge hydraulique ∇H(z,t) calculé par H_stratified
        Ss_list,  # Coefficients d'emmagasinement spécifique par maille [1/m]
        moinslog10IntrinK_list,  # -log10(perméabilité intrinsèque) par maille
        n_list,  # Porosités par maille [0-1]
        lambda_s_list,  # Conductivités thermiques du solide par maille [W/(m·K)]
        rhos_cs_list,  # Capacités thermiques volumiques du solide par maille [J/(m³·K)]
        all_dt,  # Tableau des pas de temps [s]
        q_list,  # Sources/puits de chaleur par maille [W/m³]
        dz,  # Pas d'espace vertical [m]
        H_init,  # Charge hydraulique initiale par maille [m] (pour calcul de K)
        H_riv,  # Charge hydraulique à la limite supérieure (rivière) [m]
        H_aq,  # Charge hydraulique à la limite inférieure (aquifère) [m]
        T_init,  # Température initiale par maille [K ou °C]
        T_riv,  # Température à la limite supérieure (rivière) au cours du temps [K ou °C]
        T_aq,  # Température à la limite inférieure (aquifère) au cours du temps [K ou °C]
        alpha=ALPHA,  # Paramètre du schéma theta (0=explicite, 0.5=Crank-Nicolson, 1=implicite)
        N_update_Mu=N_UPDATE_MU,  # Fréquence de mise à jour de la viscosité en fonction de T
    ):
        # Appel du constructeur de la classe parente Linear_system
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
        # Stockage des coefficients d'emmagasinement
        self.Ss_list = Ss_list
        # Stockage de -log10(perméabilité intrinsèque)
        self.moinslog10IntrinK_list = moinslog10IntrinK_list
        # Stockage des porosités
        self.n_list = n_list
        # Stockage des conductivités thermiques du solide
        self.lambda_s_list = lambda_s_list
        # Stockage des capacités thermiques volumiques du solide
        self.rhos_cs_list = rhos_cs_list
        # Stockage de la charge hydraulique à la limite supérieure
        self.H_riv = H_riv
        # Stockage de la charge hydraulique à la limite inférieure
        self.H_aq = H_aq
        # Stockage du gradient de charge hydraulique ∇H (utilisé pour l'advection thermique)
        self.nablaH = nablaH
        # Stockage de la température initiale
        self.T_init = T_init
        # Stockage de la température à la limite supérieure (rivière)
        self.T_riv = T_riv
        # Stockage de la température à la limite inférieure (aquifère)
        self.T_aq = T_aq
        # Stockage du paramètre du schéma theta
        self.alpha = alpha
        # Stockage de la fréquence de mise à jour de mu(T)
        self.N_update_Mu = N_update_Mu
        # Stockage des sources/puits de chaleur
        self.heat_source = q_list

    def compute_T_stratified(self):
        # Méthode principale pour calculer la température stratifiée au cours du temps
        # Résout l'équation advection-diffusion de la chaleur
        
        # Initialisation du tableau des résultats de température T_res [K ou °C]
        # Dimensions: (n_cell, n_times) pour stocker T à chaque maille et chaque instant
        self.T_res = np.zeros((self.n_cell, self.n_times), np.float32)
        # Remplissage de la condition initiale (colonne t=0) avec T_init
        self.T_res[:, 0] = self.T_init
        # Boucle temporelle sur tous les pas de temps avec leur valeur dt respective
        for j, dt in enumerate(self.all_dt):
            # Mise à jour de la viscosité Mu(T) tous les N_update_Mu pas de temps
            # (permet de prendre en compte la dépendance de mu vis-à-vis de T)
            if j % self.N_update_Mu == 1:
                # Recalcul de mu basé sur la température au pas précédent
                self.mu_list = self.compute_Mu(self.T_res[:, j - 1])

            # Calcul de T au temps times[j+1] en résolvant le système A*T^{n+1} = B*T^n + c

            # Construction des 3 diagonales de la matrice B (partie explicite)
            lower_diagonal = self._compute_lower_diagonal(j)
            diagonal = self._compute_diagonal(j, dt)
            upper_diagonal = self._compute_upper_diagonal(j)

            # Calcul du vecteur c contenant les conditions aux limites
            c = self._compute_c(j)

            # Produit matrice-vecteur: B * T^n + c
            B_fois_T_plus_c = (
                tri_product(lower_diagonal, diagonal, upper_diagonal, self.T_res[:, j])
                + c
            )

            # Construction des 3 diagonales de la matrice A (partie implicite)
            lower_diagonal_A, diagonal_A, upper_diagonal_A = self._compute_A_diagonals(
                j, dt
            )

            # Tentative de résolution avec le solveur tri-diagonal rapide
            try:
                self.T_res[:, j + 1] = solver(
                    lower_diagonal_A, diagonal_A, upper_diagonal_A, B_fois_T_plus_c
                )
            # Si échec (matrice mal conditionnée), utilise le solveur dense de NumPy
            except Exception:
                # Construction de la matrice A complète (dense)
                A = self._construct_A_matrix(
                    lower_diagonal_A, diagonal_A, upper_diagonal_A
                )
                # Résolution avec solveur dense
                self.T_res[:, j + 1] = solve(A, B_fois_T_plus_c)

        # Retour du tableau T_res contenant T(z,t) pour toutes les mailles et tous les temps
        return self.T_res

    def _compute_lower_diagonal(self, j):  # j: indice du pas de temps courant
        # Calcul de la diagonale inférieure de la matrice B pour l'équation de chaleur
        # Combine les effets de diffusion thermique (ke) et d'advection (ae * ∇H)
        
        # Formule pour mailles intérieures: alpha*ke/dz² - alpha*ae/(2*dz)*∇H
        # - Terme diffusif: ke/dz² (proportionnel à d²T/dz²)
        # - Terme advectif: -ae/(2*dz)*∇H (transport par l'écoulement, décentré amont)
        lower_diagonal = (self.ke_list[1:] * self.alpha / self.dz**2) - (
            self.alpha * self.ae_list[1:] / (2 * self.dz)
        ) * self.nablaH[1:, j]
        # Dernière entrée: correction 4/3 pour condition limite inférieure (aquifère)
        lower_diagonal[-1] = (
            4 * self.ke_list[self.n_cell - 1] * self.alpha / (3 * self.dz**2)
            - (2 * self.alpha * self.ae_list[self.n_cell - 1] / (3 * self.dz))
            * self.nablaH[self.n_cell - 1, j]
        )
        # Retour de la diagonale inférieure
        return lower_diagonal

    def _compute_diagonal(self, j, dt):  # j: indice du temps, dt: pas de temps [s]
        # Calcul de la diagonale principale de la matrice B pour l'équation de chaleur
        
        # Formule générale: 1/dt - 2*alpha*ke/dz²
        # - 1/dt: terme de stockage thermique (d/dt)
        # - 2*alpha*ke/dz²: coefficient du terme diffusif centré
        diagonal = 1 / dt - 2 * self.ke_list * self.alpha / self.dz**2
        # Première entrée: correction 4/3 pour condition limite supérieure (rivière)
        diagonal[0] = 1 / dt - 4 * self.ke_list[0] * self.alpha / self.dz**2
        # Dernière entrée: correction 4/3 pour condition limite inférieure (aquifère)
        diagonal[-1] = (
            1 / dt - 4 * self.ke_list[self.n_cell - 1] * self.alpha / self.dz**2
        )
        # Retour de la diagonale principale
        return diagonal

    def _compute_upper_diagonal(self, j):  # j: indice du pas de temps courant
        # Calcul de la diagonale supérieure de la matrice B pour l'équation de chaleur
        
        # Formule pour mailles intérieures: alpha*ke/dz² + alpha*ae/(2*dz)*∇H
        # - Terme diffusif: ke/dz²
        # - Terme advectif: +ae/(2*dz)*∇H (signe + car connexion avec maille aval)
        upper_diagonal = (self.ke_list[:-1] * self.alpha / self.dz**2) + (
            self.alpha * self.ae_list[:-1] / (2 * self.dz)
        ) * self.nablaH[:-1, j]
        # Première entrée: correction 4/3 pour condition limite supérieure
        upper_diagonal[0] = (
            4 * self.ke_list[0] * self.alpha / (3 * self.dz**2)
            + (2 * self.alpha * self.ae_list[0] / (3 * self.dz)) * self.nablaH[0, j]
        )
        # Retour de la diagonale supérieure
        return upper_diagonal

    def _compute_c(self, j):  # j: indice du pas de temps courant
        # Calcul du vecteur c contenant les contributions des conditions aux limites de Dirichlet
        # pour l'équation de la chaleur (incluant advection et diffusion)
        
        # Initialisation d'un vecteur nul de taille n_cell
        c = np.zeros(self.n_cell, np.float32)
        # Condition limite supérieure (rivière, première maille)
        # Formule complexe combinant diffusion et advection aux frontières
        # Partie 1: terme de diffusion 8*ke/(3*dz²) * [(1-alpha)*T_riv^{n+1} + alpha*T_riv^n]
        # Partie 2: terme d'advection avec gradient ∇H à la frontière
        c[0] = (
            8 * self.ke_list[0] * (1 - self.alpha) / (3 * self.dz**2)
            - 2 * (1 - self.alpha) * self.ae_list[0] * self.nablaH[0, j] / (3 * self.dz)
        ) * self.T_riv[j + 1] + (
            8 * self.ke_list[0] * self.alpha / (3 * self.dz**2)
            - 2 * self.alpha * self.ae_list[0] * self.nablaH[0, j] / (3 * self.dz)
        ) * self.T_riv[
            j
        ]
        # Condition limite inférieure (aquifère, dernière maille)
        # Formule similaire mais avec signe + pour l'advection (écoulement entrant)
        c[-1] = (
            8 * self.ke_list[self.n_cell - 1] * (1 - self.alpha) / (3 * self.dz**2)
            + 2
            * (1 - self.alpha)
            * self.ae_list[self.n_cell - 1]
            * self.nablaH[self.n_cell - 1, j]
            / (3 * self.dz)
        ) * self.T_aq[j + 1] + (
            8 * self.ke_list[self.n_cell - 1] * self.alpha / (3 * self.dz**2)
            + 2
            * self.alpha
            * self.ae_list[self.n_cell - 1]
            * self.nablaH[self.n_cell - 1, j]
            / (3 * self.dz)
        ) * self.T_aq[
            j
        ]

        # c += self.heat_source[:, j]  # Commenté: ajout éventuel de termes sources
        # Retour du vecteur c
        return c

    def _compute_A_diagonals(self, j, dt):  # j: indice du temps, dt: pas de temps [s]
        # Calcul des 3 diagonales de la matrice A (partie implicite) pour l'équation de chaleur
        
        # Diagonale inférieure de A: coefficient pour T_{i-1}^{n+1}
        # Formule: -(1-alpha)*ke/dz² + (1-alpha)*ae/(2*dz)*∇H
        # Signe négatif car terme déplacé à gauche de l'équation
        lower_diagonal = (
            -(self.ke_list[1:] * (1 - self.alpha) / self.dz**2)
            + ((1 - self.alpha) * self.ae_list[1:] / (2 * self.dz)) * self.nablaH[1:, j]
        )

        # Dernière entrée: correction 4/3 pour condition limite inférieure
        lower_diagonal[-1] = (
            -4 * self.ke_list[self.n_cell - 1] * (1 - self.alpha) / (3 * self.dz**2)
            + (2 * (1 - self.alpha) * self.ae_list[self.n_cell - 1] / (3 * self.dz))
            * self.nablaH[self.n_cell - 1, j]
        )

        # Diagonale principale de A: coefficient pour T_i^{n+1}
        # Formule: 1/dt + 2*(1-alpha)*ke/dz² - heat_source/(rho*c)_m
        # - 1/dt: terme de stockage
        # - 2*(1-alpha)*ke/dz²: diffusion
        # - heat_source/(rho*c)_m: terme source normalisé
        diagonal = (
            1 / dt
            + 2 * self.ke_list * (1 - self.alpha) / self.dz**2
            - self.heat_source / self.rho_mc_m_list
        )
        # Première entrée: correction 4/3 pour condition limite supérieure + source
        diagonal[0] = (
            1 / dt
            + 4 * self.ke_list[0] * (1 - self.alpha) / self.dz**2
            - self.heat_source[0] / self.rho_mc_m_list[0]
        )
        # Dernière entrée: correction 4/3 pour condition limite inférieure + source
        diagonal[-1] = (
            1 / dt
            + 4 * self.ke_list[self.n_cell - 1] * (1 - self.alpha) / self.dz**2
            - self.heat_source[-1] / self.rho_mc_m_list[-1]
        )

        # Diagonale supérieure de A: coefficient pour T_{i+1}^{n+1}
        # Formule: -(1-alpha)*ke/dz² - (1-alpha)*ae/(2*dz)*∇H
        upper_diagonal = (
            -(self.ke_list[:-1] * (1 - self.alpha) / self.dz**2)
            - ((1 - self.alpha) * self.ae_list[:-1] / (2 * self.dz))
            * self.nablaH[:-1, j]
        )
        # Première entrée: correction 4/3 pour condition limite supérieure
        upper_diagonal[0] = (
            -4 * self.ke_list[0] * (1 - self.alpha) / (3 * self.dz**2)
            - (2 * (1 - self.alpha) * self.ae_list[0] / (3 * self.dz))
            * self.nablaH[0, j]
        )

        # Retour des 3 diagonales de la matrice A
        return lower_diagonal, diagonal, upper_diagonal

    def _construct_A_matrix(self, lower_diagonal, diagonal, upper_diagonal):
        # Construction de la matrice A complète (dense) à partir des 3 diagonales
        # Utilisée comme solution de secours si le solveur tri-diagonal échoue
        
        # Initialisation d'une matrice nulle n_cell × n_cell
        A = np.zeros((self.n_cell, self.n_cell), float32)
        # Première ligne: diagonale principale et diagonale supérieure
        A[0, 0] = diagonal[0]
        A[0, 1] = upper_diagonal[0]
        # Lignes intérieures: les 3 diagonales (inférieure, principale, supérieure)
        for i in range(1, self.n_cell - 1):
            A[i, i - 1] = lower_diagonal[i - 1]
            A[i, i] = diagonal[i]
            A[i, i + 1] = upper_diagonal[i]
        # Dernière ligne: diagonale inférieure et diagonale principale
        A[self.n_cell - 1, self.n_cell - 1] = diagonal[self.n_cell - 1]
        A[self.n_cell - 1, self.n_cell - 2] = lower_diagonal[self.n_cell - 2]
        # Retour de la matrice complète A
        return A



# Classe expérimentale pour le couplage Hydraulique-Température-Conductivité (HTK)
# Actuellement similaire à H_stratified, mais prévue pour intégrer:
# - la dépendance de K vis-à-vis de T (via mu(T))
# - le terme div(K) dans l'équation hydraulique
# - le couplage itératif H ↔ T ↔ K
class HTK_stratified(Linear_system):
    def __init__(
        self,
        lambda_s_list,  # Conductivités thermiques du solide par maille [W/(m·K)]
        rhos_cs_list,  # Capacités thermiques volumiques du solide par maille [J/(m³·K)]
        n_list,  # Porosités par maille [0-1]
        T_init,  # Température initiale par maille [K ou °C]
        array_K,  # Tableau des conductivités hydrauliques par strate [m/s]
        array_Ss,  # Tableau des coefficients d'emmagasinement par strate [1/m]
        list_zLow,  # Liste des profondeurs des limites basses de chaque strate [m]
        z_solve,  # Profondeurs des centres de mailles [m]
        inter_cara,  # Liste des caractéristiques des interfaces (position, type)
        moinslog10IntrinK_list,  # -log10(perméabilité intrinsèque) par maille
        Ss_list,  # Coefficients d'emmagasinement spécifique par maille [1/m]
        all_dt,  # Tableau des pas de temps [s]
        isdtconstant,  # Booléen indiquant si le pas de temps est constant
        dz,  # Pas d'espace vertical [m]
        H_init,  # Charge hydraulique initiale par maille [m]
        H_riv,  # Charge hydraulique à la limite supérieure (rivière) [m]
        H_aq,  # Charge hydraulique à la limite inférieure (aquifère) [m]
        heatsource,  # Sources/puits de chaleur par maille [W/m³]
        alpha=ALPHA,  # Paramètre du schéma theta
    ):
        # Appel du constructeur de la classe parente Linear_system
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
        # Stockage des conductivités thermiques du solide
        self.lambda_s_list = lambda_s_list
        # Stockage des capacités thermiques volumiques du solide
        self.rhos_cs_list = rhos_cs_list
        # Stockage des porosités
        self.n_list = n_list
        # Stockage de la température initiale
        self.T_init = T_init
        # Stockage du tableau des conductivités hydrauliques par strate
        self.array_K = array_K
        # Stockage du tableau des coefficients d'emmagasinement par strate
        self.array_Ss = array_Ss
        # Stockage de la liste des profondeurs des limites basses de chaque strate
        self.list_zLow = list_zLow
        # Stockage des profondeurs des centres de mailles
        self.z_solve = z_solve
        # Stockage des caractéristiques des interfaces géologiques
        self.inter_cara = inter_cara
        # Stockage de -log10(perméabilité intrinsèque)
        self.moinslog10IntrinK_list = moinslog10IntrinK_list
        # Stockage des coefficients d'emmagasinement
        self.Ss_list = Ss_list
        # Stockage du tableau des pas de temps
        self.all_dt = all_dt
        # Stockage du booléen indiquant si dt est constant
        self.isdtconstant = isdtconstant
        # Stockage du pas d'espace vertical
        self.dz = dz
        # Stockage de la charge hydraulique initiale
        self.H_init = H_init
        # Stockage de la charge hydraulique à la limite supérieure (rivière)
        self.H_riv = H_riv
        # Stockage de la charge hydraulique à la limite inférieure (aquifère)
        self.H_aq = H_aq
        # Stockage du paramètre du schéma theta
        self.alpha = alpha
        # Stockage des sources/puits de chaleur
        self.heat_source = heatsource
        # Appel de la méthode de calcul HTK (actuellement identique à H_stratified)
        self.compute_HTK_stratified()

    def compute_HTK_stratified(self):
        # Méthode principale pour calculer H avec couplage HTK
        # Actuellement: résout uniquement l'équation hydraulique (comme H_stratified)
        # TODO: ajouter boucle itérative H → T → K → H jusqu'à convergence
        
        # Test si le pas de temps est constant
        if self.isdtconstant:
            # Si dt constant: optimisation (calcul matrices une seule fois)
            self.compute_H_constant_dt()
        else:
            # Si dt variable: recalcul des matrices à chaque pas de temps
            self.compute_H_variable_dt()
        # Retour du tableau H_res contenant H(z,t)
        return self.H_res

    def compute_H_constant_dt(self):
        # Calcul de H quand le pas de temps est constant
        # Code identique à H_stratified.compute_H_constant_dt()
        
        # Extraction du pas de temps constant
        dt = self.all_dt[0]

        # Calcul des 3 diagonales de la matrice B (partie explicite)
        lower_diagonal_B, diagonal_B, upper_diagonal_B = self.compute_B_diagonals(dt)
        # Calcul des 3 diagonales de la matrice A (partie implicite)
        lower_diagonal_A, diagonal_A, upper_diagonal_A = self.compute_A_diagonals(dt)

        # Boucle sur toutes les interfaces pour corriger le schéma numérique
        for tup_idx in range(len(self.inter_cara)):
            # Correction des diagonales aux interfaces (utilise Keq si interface interne)
            self.correct_numerical_schema(
                tup_idx,
                lower_diagonal_B,
                diagonal_B,
                upper_diagonal_B,
                lower_diagonal_A,
                diagonal_A,
                upper_diagonal_A,
            )

        # Boucle temporelle sur tous les pas de temps
        for j in range(self.n_times - 1):
            # Calcul du vecteur c contenant les contributions des conditions aux limites
            c = self.compute_c(j)
            # Produit matrice-vecteur tri-diagonal: B * H^n + c
            B_fois_H_plus_c = (
                tri_product(
                    lower_diagonal_B, diagonal_B, upper_diagonal_B, self.H_res[:, j]
                )
                + c
            )
            # Résolution du système tri-diagonal A * H^{n+1} = B * H^n + c
            self.H_res[:, j + 1] = solver(
                lower_diagonal_A, diagonal_A, upper_diagonal_A, B_fois_H_plus_c
            )

    def compute_H_variable_dt(self):
        # Calcul de H quand le pas de temps est variable
        # Code identique à H_stratified.compute_H_variable_dt()
        
        # Boucle sur tous les pas de temps avec leur valeur dt respective
        for j, dt in enumerate(self.all_dt):
            # Calcul des 3 diagonales de B pour le pas de temps dt courant
            lower_diagonal_B, diagonal_B, upper_diagonal_B = self.compute_B_diagonals(
                dt
            )
            # Calcul des 3 diagonales de A pour le pas de temps dt courant
            lower_diagonal_A, diagonal_A, upper_diagonal_A = self.compute_A_diagonals(
                dt
            )

            # Boucle sur toutes les interfaces pour corriger le schéma à chaque pas de temps
            for tup_idx in range(len(self.inter_cara)):
                # Correction des diagonales aux interfaces (Keq si nécessaire)
                self.correct_numerical_schema(
                    tup_idx,
                    lower_diagonal_B,
                    diagonal_B,
                    upper_diagonal_B,
                    lower_diagonal_A,
                    diagonal_A,
                    upper_diagonal_A,
                )

            # Calcul du vecteur c pour le pas de temps j
            c = self.compute_c(j)
            # Produit matrice-vecteur: B * H^n + c
            B_fois_H_plus_c = (
                tri_product(
                    lower_diagonal_B, diagonal_B, upper_diagonal_B, self.H_res[:, j]
                )
                + c
            )
            # Résolution du système A * H^{n+1} = B * H^n + c
            self.H_res[:, j + 1] = solver(
                lower_diagonal_A, diagonal_A, upper_diagonal_A, B_fois_H_plus_c
            )

    def compute_B_diagonals(self, dt):  # dt: pas de temps [s]
        # Construction des 3 diagonales de la matrice B
        # Code identique à H_stratified.compute_B_diagonals()
        # TODO: ajouter termes supplémentaires avec dK/dz si div(K) activé
        
        # Diagonale inférieure: coefficient pour H_{i-1}^n
        lower_diagonal_B = self.K_list[1:] * self.alpha / self.dz**2
        # Dernière entrée: correction 4/3 pour condition limite inférieure
        lower_diagonal_B[-1] = (
            4 * self.K_list[self.n_cell - 1] * self.alpha / (3 * self.dz**2)
        )

        # Diagonale principale: coefficient pour H_i^n
        diagonal_B = self.Ss_list * 1 / dt - 2 * self.K_list * self.alpha / self.dz**2
        # Première entrée: correction 4/3 pour condition limite supérieure
        diagonal_B[0] = (
            self.Ss_list[0] * 1 / dt - 4 * self.K_list[0] * self.alpha / self.dz**2
        )
        # Dernière entrée: correction 4/3 pour condition limite inférieure
        diagonal_B[-1] = (
            self.Ss_list[self.n_cell - 1] * 1 / dt
            - 4 * self.K_list[self.n_cell - 1] * self.alpha / self.dz**2
        )

        # Diagonale supérieure: coefficient pour H_{i+1}^n
        upper_diagonal_B = self.K_list[:-1] * self.alpha / self.dz**2
        # Première entrée: correction 4/3 pour condition limite supérieure
        upper_diagonal_B[0] = 4 * self.K_list[0] * self.alpha / (3 * self.dz**2)

        # Retour des 3 diagonales
        return lower_diagonal_B, diagonal_B, upper_diagonal_B

    def compute_A_diagonals(self, dt):  # dt: pas de temps [s]
        # Construction des 3 diagonales de la matrice A
        # Code identique à H_stratified.compute_A_diagonals()
        # TODO: ajouter termes supplémentaires avec dK/dz si div(K) activé
        
        # Diagonale inférieure: coefficient pour H_{i-1}^{n+1}
        lower_diagonal_A = -self.K_list[1:] * (1 - self.alpha) / self.dz**2
        # Dernière entrée: correction 4/3 pour condition limite inférieure
        lower_diagonal_A[-1] = (
            -4 * self.K_list[self.n_cell - 1] * (1 - self.alpha) / (3 * self.dz**2)
        )

        # Diagonale principale: coefficient pour H_i^{n+1}
        diagonal_A = (
            self.Ss_list * 1 / dt + 2 * self.K_list * (1 - self.alpha) / self.dz**2
        )
        # Première entrée: correction 4/3 pour condition limite supérieure
        diagonal_A[0] = (
            self.Ss_list[0] * 1 / dt
            + 4 * self.K_list[0] * (1 - self.alpha) / self.dz**2
        )
        # Dernière entrée: correction 4/3 pour condition limite inférieure
        diagonal_A[-1] = (
            self.Ss_list[self.n_cell - 1] * 1 / dt
            + 4 * self.K_list[self.n_cell - 1] * (1 - self.alpha) / self.dz**2
        )

        # Diagonale supérieure: coefficient pour H_{i+1}^{n+1}
        upper_diagonal_A = -self.K_list[:-1] * (1 - self.alpha) / self.dz**2
        # Première entrée: correction 4/3 pour condition limite supérieure
        upper_diagonal_A[0] = -4 * self.K_list[0] * (1 - self.alpha) / (3 * self.dz**2)

        # Retour des 3 diagonales
        return lower_diagonal_A, diagonal_A, upper_diagonal_A

    def correct_numerical_schema(
        self,
        tup_idx,  # Indice de l'interface courante dans la liste inter_cara
        lower_diagonal_B,  # Diagonale inférieure de B (modifiée in-place)
        diagonal_B,  # Diagonale principale de B (modifiée in-place)
        upper_diagonal_B,  # Diagonale supérieure de B (modifiée in-place)
        lower_diagonal_A,  # Diagonale inférieure de A (modifiée in-place)
        diagonal_A,  # Diagonale principale de A (modifiée in-place)
        upper_diagonal_A,  # Diagonale supérieure de A (modifiée in-place)
    ):
        # Méthode de correction du schéma numérique aux interfaces géologiques
        # Code identique à H_stratified.correct_numerical_schema()
        # Voir commentaires détaillés dans H_stratified pour explication complète
        
        # Extraction des conductivités des deux strates séparées par l'interface
        K1 = self.array_K[tup_idx]  # Conductivité de la strate supérieure [m/s]
        K2 = self.array_K[tup_idx + 1]  # Conductivité de la strate inférieure [m/s]

        # Cas 1: Interface alignée exactement sur un nœud (flag == 0)
        if self.inter_cara[tup_idx][1] == 0:
            # Position de l'interface
            pos_idx = int(self.inter_cara[tup_idx][0])
            # Correction de la diagonale principale de B
            diagonal_B[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                - (K1 + K2) * self.alpha / self.dz**2
            )
            # Correction de la diagonale inférieure de B
            lower_diagonal_B[pos_idx - 1] = K1 * self.alpha / self.dz**2
            # Correction de la diagonale supérieure de B
            upper_diagonal_B[pos_idx] = K2 * self.alpha / self.dz**2
            # Correction de la diagonale principale de A
            diagonal_A[pos_idx] = (
                self.Ss_list[pos_idx] * 1 / self.all_dt[0]
                + (K1 + K2) * (1 - self.alpha) / self.dz**2
            )
            # Correction de la diagonale inférieure de A
            lower_diagonal_A[pos_idx - 1] = -K1 * (1 - self.alpha) / self.dz**2
            # Correction de la diagonale supérieure de A
            upper_diagonal_A[pos_idx] = -K2 * (1 - self.alpha) / self.dz**2
        else:
            # Cas 2: Interface située à l'intérieur d'une maille (flag != 0)
            # Calcul de Keq (conductivité équivalente) par moyenne harmonique pondérée
            
            # Position de l'interface
            pos_idx = int(self.inter_cara[tup_idx][0])
            # Fraction de la maille entre les centres [0-1]
            x = (self.list_zLow[tup_idx] - self.z_solve[pos_idx]) / (
                self.z_solve[pos_idx + 1] - self.z_solve[pos_idx]
            )
            # Conductivité équivalente par moyenne harmonique
            Keq = 1 / (x / K1 + (1 - x) / K2)
            
            # Correction pour la maille pos_idx (contient K1 et Keq)
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

            # Correction pour la maille pos_idx+1 (contient Keq et K2)
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

    def compute_c(self, j):  # j: indice du pas de temps courant
        # Calcul du vecteur c contenant les contributions des conditions aux limites
        # Code identique à H_stratified.compute_c()
        
        # Initialisation d'un vecteur nul
        c = zeros(self.n_cell, float32)
        # Condition limite supérieure (rivière): 8*K/(3*dz²) * [(1-alpha)*H_riv^{n+1} + alpha*H_riv^n]
        c[0] = (8 * self.K_list[0] / (3 * self.dz**2)) * (
            (1 - self.alpha) * self.H_riv[j + 1] + self.alpha * self.H_riv[j]
        )
        # Condition limite inférieure (aquifère)
        c[-1] = (8 * self.K_list[self.n_cell - 1] / (3 * self.dz**2)) * (
            (1 - self.alpha) * self.H_aq[j + 1] + self.alpha * self.H_aq[j]
        )
        # c += self.heat_source[:, j]  # Commenté: ajout éventuel de termes sources
        # Retour du vecteur c
        return c



if __name__ == "__main__":
    L = 0.5
    print(1)
