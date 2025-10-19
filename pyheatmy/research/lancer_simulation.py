import numpy as np
from datetime import datetime, timedelta

from pyheatmy.core import Column
from pyheatmy.layers import Layer
from pyheatmy.params import Param


# Cette section crée un jeu de données réaliste pour faire fonctionner la simulation.

print("1. Génération des données synthétiques...")

# Paramètres de la simulation
NB_TIMESTEPS = 100  # Nombre de points dans le temps (ex: 100 mesures)
TIMESTEP_MINUTES = 15  # Intervalle entre chaque mesure en minutes
START_DATE = datetime(2025, 10, 1)

# Géométrie de la colonne
RIVER_BED_DEPTH = 2.0  # Profondeur totale de la colonne en mètres
DEPTH_SENSORS = [0.5, 1.0, 1.5, RIVER_BED_DEPTH]  # Profondeur des 3 capteurs
OFFSET = 0.1  # Décalage


# Définition de trois couches distinctes
couche1 = Layer(name="Sable", zLow=0.5)  # 1. Cette couche s'arrête maintenant à 0.5m
couche1.params = Param(moinslog10IntrinK=12.5, n=0.15, lambda_s=2.8, rhos_cs=2e6, q=0.1)

# 2. On ajoute une nouvelle couche intermédiaire
couche2 = Layer(name="Argile", zLow=1.5)  # Elle va de 0.5m à 1.5m
couche2.params = Param(
    moinslog10IntrinK=15.0, n=0.08, lambda_s=1.2, rhos_cs=5e6, q=0.1
)  # Avec ses propres paramètres

# 3. La dernière couche va maintenant de 1.5m jusqu'au fond
couche3 = Layer(name="Gravier", zLow=RIVER_BED_DEPTH)
couche3.params = Param(moinslog10IntrinK=11.0, n=0.20, lambda_s=3.5, rhos_cs=3e6, q=0.1)

# 4. On met les trois couches dans la liste
mes_couches = [couche1, couche2, couche3]

# Création de la série temporelle
times = [
    START_DATE + timedelta(minutes=i * TIMESTEP_MINUTES) for i in range(NB_TIMESTEPS)
]

# Génération des conditions aux limites (températures et charge)
# On utilise une sinusoïde pour simuler des variations journalières.
time_array = np.linspace(0, 4 * np.pi, NB_TIMESTEPS)
T_riv = (
    15 + 5 * np.sin(time_array) + np.random.randn(NB_TIMESTEPS) * 0.2
)  # Température rivière
T_aq = 12.0 + np.random.randn(NB_TIMESTEPS) * 0.1  # Température aquifère (plus stable)
dH = 1.0 + 0.2 * np.sin(time_array / 2)  # Charge hydraulique de la rivière

# Formatage des données pour le constructeur de la classe Column
dH_measures = []
for i in range(NB_TIMESTEPS):
    dH_measures.append((times[i], (dH[i], T_riv[i])))

# Génération des mesures des capteurs intermédiaires
# On interpole linéairement entre la rivière et l'aquifère pour le réalisme.
T_sensors_data = []
for i in range(NB_TIMESTEPS):
    sensor_temps = []
    for depth in DEPTH_SENSORS:
        # Interpolation linéaire + un peu de bruit
        temp = T_riv[i] + (T_aq[i] - T_riv[i]) * (depth / RIVER_BED_DEPTH)
        temp += np.random.randn() * 0.1
        sensor_temps.append(temp)
    T_sensors_data.append(sensor_temps)

# Formatage final des mesures de température
T_measures = []
for i in range(NB_TIMESTEPS):
    # La structure attend [T_sensor1, T_sensor2, ..., T_aquifere]
    full_temp_list = T_sensors_data[i]
    T_measures.append((times[i], full_temp_list))

print("   -> Données générées avec succès.")

# --- ÉTAPE 3: EXÉCUTION DU CODE PRINCIPAL ---

# Ce bloc ne s'exécute que si vous lancez ce fichier directement.
if __name__ == "__main__":
    print("\n2. Création de l'instance de la classe Column...")

    # Création de l'objet (instance) de la classe Column.
    # On utilise les données synthétiques générées ci-dessus.
    # C'est ici que l'on active le mode "bavard" pour le débogage.
    ma_colonne = Column(
        river_bed=RIVER_BED_DEPTH,
        depth_sensors=DEPTH_SENSORS,
        offset=OFFSET,
        dH_measures=dH_measures,
        T_measures=T_measures,
        all_layers=mes_couches,  # On passe la liste de couches
        verbose=True,
    )

    print("   -> Instance créée.")
    print("\n3. Lancement de la simulation et des calculs...")

    # Appel d'une méthode qui va déclencher le calcul `compute_solve_transi`.
    # C'est pendant l'exécution de cette ligne que vos matrices H_gauche
    # et H_droite seront affichées dans le terminal.
    try:
        ma_colonne.compute_solve_transi(verbose=True)
        ma_colonne.plot_all_results()
        print("\n4. Simulation terminée. Les graphiques devraient s'afficher.")
    except Exception as e:
        print(f"\nUne erreur est survenue pendant l'exécution : {e}")
