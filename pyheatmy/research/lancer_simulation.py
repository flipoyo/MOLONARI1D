import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# --- Imports de la bibliothèque ---
from pyheatmy.core import Column
from pyheatmy.layers import Layer, getListParameters
from pyheatmy.params import Param, Prior
from pyheatmy.config import RHO_W, G, DEFAULT_MU, EPSILON

# --- 1. CONFIGURATION DE LA SIMULATION "VÉRITÉ" ---

print("1. Génération des données de 'mesure' synthétiques et réalistes...")

# Paramètres de simulation
NB_TIMESTEPS = 200  # Utilisons un peu plus de points
TIMESTEP_MINUTES = 15  # 15 min
START_DATE = datetime(2025, 10, 1)
NB_CELLS = 60  # Nombre de cellules stable
NOISE_LEVEL = 0.05  # Niveau de bruit à ajouter aux mesures (en Kelvin)

# Géométrie
RIVER_BED_DEPTH = 2.0
DEPTH_SENSORS_ET_FOND = [0.5, 1.0, 1.5, RIVER_BED_DEPTH]  # 3 capteurs + fond
OFFSET = 0.0

# --- PARAMÈTRES (LA VÉRITÉ QUE LA MCMC DOIT TROUVER) ---
vrai_params_c1 = Param(moinslog10IntrinK=16.0, n=0.15, lambda_s=2.5, rhos_cs=5e5, q=0)
vrai_params_c2 = Param(moinslog10IntrinK=16.0, n=0.10, lambda_s=2.5, rhos_cs=5e5, q=0)

couche1_vraie = Layer(name="Vraie Couche 1", zLow=1.0)
couche1_vraie.params = vrai_params_c1
couche2_vraie = Layer(name="Vraie Couche 2", zLow=RIVER_BED_DEPTH)
couche2_vraie.params = vrai_params_c2

mes_couches_vraies = [couche1_vraie, couche2_vraie]

# --- Génération des conditions aux limites (Rivière, Aquifère, Charge) ---
times = [
    START_DATE + timedelta(minutes=i * TIMESTEP_MINUTES) for i in range(NB_TIMESTEPS)
]
time_array = np.linspace(0, 8 * np.pi, NB_TIMESTEPS)  # Plus d'oscillations
T_riv = 15 + 5 * np.sin(time_array) + np.random.randn(NB_TIMESTEPS) * 0.2
T_aq = 12.0 + np.random.randn(NB_TIMESTEPS) * 0.1
dH = 1.0 + 0.2 * np.sin(time_array / 2)

# Formatage des conditions limites
dH_measures = []
for i in range(NB_TIMESTEPS):
    dH_measures.append((times[i], (dH[i], T_riv[i])))

# --- 2. EXÉCUTION DE LA SIMULATION "VÉRITÉ" POUR CRÉER LES MESURES ---

# On crée une première colonne "col_reponse" juste pour générer les données cibles
# On doit lui fournir des T_measures factices pour qu'elle s'initialise
T_measures_factices = [(times[i], [10, 10, 10, 10]) for i in range(NB_TIMESTEPS)]

col_reponse = Column(
    river_bed=RIVER_BED_DEPTH,
    depth_sensors=DEPTH_SENSORS_ET_FOND,
    offset=OFFSET,
    dH_measures=dH_measures,
    T_measures=T_measures_factices,  # Utilise les données factices
    all_layers=mes_couches_vraies,  # Utilise les "vrais" paramètres
    verbose=False,
    nb_cells=NB_CELLS,
)

# Lancement de la simulation "parfaite"
col_reponse.compute_solve_transi(verbose=False)

# Extraction des températures parfaites aux capteurs
# get_temperature_at_sensors() renvoie [T_riv, T1, T2, T3, T_aq] (5 lignes)
# On ne veut que les capteurs et l'aquifère [T1, T2, T3, T_aq] (4 lignes)
temp_parfaites_matrice = col_reponse.get_temperature_at_sensors()
temp_parfaites_capteurs = temp_parfaites_matrice[1:, :]

# Ajout d'un bruit réaliste pour simuler des "mesures"
bruit = np.random.normal(0, NOISE_LEVEL, temp_parfaites_capteurs.shape)
temp_mesures_bruitees = temp_parfaites_capteurs + bruit

# Re-formatage des "vraies" mesures pour la MCMC
T_measures_realistes = []
for i in range(NB_TIMESTEPS):
    # [T1_bruit, T2_bruit, T3_bruit, T_aq_bruit]
    full_temp_list = temp_mesures_bruitees[:, i].tolist()
    T_measures_realistes.append((times[i], full_temp_list))

print("   -> Données de 'mesure' physiquement réalistes générées.")

# --- 3. CONFIGURATION ET EXÉCUTION DE LA MCMC ---

if __name__ == "__main__":
    print("\n2. Création de l'instance 'Test' (avec mauvais paramètres initiaux)...")

    # Paramètres initiaux "mauvais" (ce que l'on suppose au début)
    params_test_c1 = Param(moinslog10IntrinK=12, n=0.1, lambda_s=1.0, rhos_cs=1e6, q=0)
    params_test_c2 = Param(moinslog10IntrinK=12, n=0.1, lambda_s=1.0, rhos_cs=1e6, q=0)

    couche1_test = Layer(name="Couche 1 Test", zLow=1.0)
    couche1_test.params = params_test_c1
    couche2_test = Layer(name="Couche 2 Test", zLow=RIVER_BED_DEPTH)
    couche2_test.params = params_test_c2

    # Création de la colonne principale pour la MCMC
    ma_colonne = Column(
        river_bed=RIVER_BED_DEPTH,
        depth_sensors=DEPTH_SENSORS_ET_FOND,
        offset=OFFSET,
        dH_measures=dH_measures,
        T_measures=T_measures_realistes,  # <-- Utilise les DONNÉES RÉALISTES
        all_layers=[couche1_test, couche2_test],  # <-- Utilise les MAUVAIS paramètres
        verbose=False,
        nb_cells=NB_CELLS,
    )
    print("   -> Instance créée.")

    print("\n3. Configuration de l'optimisation MCMC")

    # Priors (plages de recherche) qui englobent les "vraies" valeurs
    priors_couche_1 = {
        "Prior_moinslog10IntrinK": ((12, 15), 0.01),  # Vrai: 13.8
        "Prior_n": ((0.05, 0.25), 0.01),  # Vrai: 0.15
        "Prior_lambda_s": ((1, 5), 0.1),  # Vrai: 2.5
        "Prior_rhos_cs": ((1e6, 5e6), 1e5),  # Vrai: 2.5e6
        "Prior_q": ((-1e-6, 1e-6), 1e-10),
    }
    priors_couche_2 = {
        "Prior_moinslog10IntrinK": ((12, 15), 0.01),  # Vrai: 14.5
        "Prior_n": ((0.05, 0.25), 0.01),  # Vrai: 0.10
        "Prior_lambda_s": ((1, 5), 0.1),  # Vrai: 1.8
        "Prior_rhos_cs": ((1e6, 5e6), 1e5),  # Vrai: 3.0e6
        "Prior_q": ((-1e-6, 1e-6), 1e-10),
    }

    try:
        ma_colonne.all_layers[0].set_priors_from_dict(priors_couche_1)
        ma_colonne.all_layers[1].set_priors_from_dict(priors_couche_2)
        print("   -> Priors assignés.")

        print("   -> Lancement de la MCMC (cela va prendre plusieurs minutes)...")
        ma_colonne.compute_mcmc(
            verbose=True,
            nb_chain=10,
            nitmaxburning=500,  # Augmenté pour un bon burn-in
            nb_iter=2000,  # Augmenté pour une vraie recherche
        )
        print("   -> MCMC terminée.")

        # -----------------------------------------------------------------
        print("\n4. Lancement de la Simulation Finale (Paramètres optimisés)")
        # -----------------------------------------------------------------

        ma_colonne.get_best_layers()
        print("   -> Meilleurs paramètres MCMC appliqués.")

        ma_colonne.compute_solve_transi(verbose=False)
        print("   -> Calcul direct final terminé.")

        print("   -> Affichage des résultats (APRÈS MCMC)...")
        ma_colonne.plot_all_results()
        print("   -> Graphiques optimisés générés.")

        print("\n   -> Affichage des distributions de paramètres (PDF) trouvées...")
        ma_colonne.plot_all_param_pdf()

        # -----------------------------------------------------------------
        print("\n5. ÉVALUATION DES RÉSULTATS MCMC")
        # -----------------------------------------------------------------
        print("\nParamètres 'VRAIS' (secrets) que nous avons définis :")
        print(f"  Couche 1: {vrai_params_c1}")
        print(f"  Couche 2: {vrai_params_c2}")

        print("\nParamètres 'ESTIMÉS' par la MCMC :")
        best_params = ma_colonne.get_best_param()
        print(f"  Couche 1: {best_params[0]}")
        print(f"  Couche 2: {best_params[1]}")
        print("\n(Les paramètres estimés devraient être proches des paramètres vrais)")

        print("\n--- FIN DE LA SIMULATION COMPLÈTE ---")

    except Exception as e:
        print(
            f"\nUne erreur est survenue pendant la MCMC ou la simulation finale : {e}"
        )