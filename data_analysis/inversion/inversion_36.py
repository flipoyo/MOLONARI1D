"""
Ce code effectue une inversion de donénes dans le cas d'une colonne de sol avec une seule couche
"""

from core import *
from params import *
from layers import *
from solver import *
from state import *
from utils import *
 
# importing
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

capteur_riviere = pd.read_csv("inversion/data_cleanded/point36_pression_cleaned.csv", sep = ',', names = ['dates', 'temperature_riviere', 'dH'], skiprows=1)
capteur_ZH = pd.read_csv("inversion/data_cleanded/point36_temperature_cleaned.csv", sep = ',', names = ['dates', 'temperature_10', 'temperature_20', 'temperature_30'], skiprows=1)
etalonage_capteur_riv = pd.read_csv('configuration/pressure_sensors/P508.csv')

def convertDates(df: pd.DataFrame):
    """
    Convert dates from a list of strings by testing several different input formats
    Try all date formats already encountered in data points
    If none of them is OK, try the generic way (None)
    If the generic way doesn't work, this method fails
    (in that case, you should add the new format to the list)
    
    This function works directly on the giving Pandas dataframe (in place)
    This function assumes that the first column of the given Pandas dataframe
    contains the dates as characters string type
    
    For datetime conversion performance, see:
    See https://stackoverflow.com/questions/40881876/python-pandas-convert-datetime-to-timestamp-effectively-through-dt-accessor
    """
    formats = ("%m-%d-%y %H:%M:%S", "%m-%d-%y %I:%M:%S %p",
               "%d-%m-%y %H:%M",    "%d-%m-%y %I:%M %p",
               "%m-%d-%Y %H:%M:%S", "%m-%d-%Y %I:%M:%S %p", 
               "%d-%m-%Y %H:%M",    "%d-%m-%Y %I:%M %p",
               "%y/%m/%d %H:%M:%S", "%y/%m/%d %I:%M:%S %p", 
               "%y/%m/%d %H:%M",    "%y/%m/%d %I:%M %p",
               "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %I:%M:%S %p", 
               "%Y/%m/%d %H:%M",    "%Y/%m/%d %I:%M %p",
               None)
    times = df[df.columns[0]]
    for f in formats:
        try:
            # Convert strings to datetime objects
            new_times = pd.to_datetime(times, format=f)
            # Convert datetime series to numpy array of integers (timestamps)
            new_ts = new_times.values.astype(np.int64)
            # If times are not ordered, this is not the appropriate format
            test = np.sort(new_ts) - new_ts
            if np.sum(abs(test)) != 0 :
                #print("Order is not the same")
                raise ValueError()
            # Else, the conversion is a success
            #print("Found format ", f)
            df[df.columns[0]] = new_times
            return
        
        except ValueError:
            #print("Format ", f, " not valid")
            continue
    
    # None of the known format are valid
    raise ValueError("Cannot convert dates: No known formats match your data!")

convertDates(capteur_riviere)
convertDates(capteur_ZH)

'''
# on met en mémoire la totalité des mesures de pression et de température
capteur_riviere_tot = capteur_riviere
capteur_ZH_tot = capteur_ZH

# on ne garde que les mesures entre 2019-06-01 00:00:00 et 2019-06-10 00:00:00 pour réduire le temps de calcul
capteur_riviere = capteur_riviere[4000:5000]
capteur_ZH = capteur_ZH[4000:5000]
'''

# set seed for reproducibility
np.random.seed(0)

# conversion des mesures de pression
#intercept = float(etalonage_capteur_riv['P508'][2])
#a = float(etalonage_capteur_riv['P508'][3])
#b = float(etalonage_capteur_riv['P508'][4])
#capteur_riviere['dH'] = (capteur_riviere['tension'].astype(float)-intercept-capteur_riviere['temperature_riviere'].astype(float)*b)/a

# conversion mesures de tempétratures
capteur_riviere['temperature_riviere'] = capteur_riviere['temperature_riviere'] + 273.15
capteur_ZH['temperature_10'] = capteur_ZH['temperature_10'] + 273.15
capteur_ZH['temperature_20'] = capteur_ZH['temperature_20'] + 273.15
capteur_ZH['temperature_30'] = capteur_ZH['temperature_30'] + 273.15

# définition des attributs de colonnes
dH_measures = list(zip(capteur_riviere['dates'],list(zip(capteur_riviere['dH'], capteur_riviere['temperature_riviere']))))
T_measures = list(zip(capteur_ZH['dates'], capteur_ZH[['temperature_10', 'temperature_20', 'temperature_30']].to_numpy()))

col_dict = {
	"river_bed": 1., 
    "depth_sensors": [.1, .2, .3],
	"offset": .0,
    "dH_measures": dH_measures,
	"T_measures": T_measures,
    "sigma_meas_P": None,
    "sigma_meas_T": None,
    "inter_mode": 'lagrange'
}

print(capteur_riviere.head())
print(capteur_ZH.head())

col = Column.from_dict(col_dict)

temps_en_jours = np.array([i for i in range(len(col._times))]) / (4*24)

params = Param(
    moinslog10K = 4,
    n = .1,
    lambda_s = 2,
    rhos_cs = 4e6
)

params_tuple = (4, .1, 2, 4e6)

assert params == params_tuple

col.compute_solve_transi(params, nb_cells=100)

temperatures = col.get_temps_solve() - 273.15

fig, ax = plt.subplots(figsize=(10, 5), facecolor = 'w')

im = ax.imshow(
    temperatures,
    aspect = "auto",
    extent = [0, temps_en_jours[-1], col.depths_solve[-1], col.depths_solve[0]],
    cmap = "Spectral_r"
)

col.plot_CALC_results(nt=len(col._times))

plt.show()

rmse = col.get_RMSE()
print(f"RMSE premier capteur : {rmse[0]}")
print(f"RMSE deuxième capteur : {rmse[1]}")
print(f"RMSE globale : {rmse[2]}")

fig, axes = plt.subplots(1, 2, figsize = (20, 5), sharey=True)

axes[0].set_ylabel("Température en °C")

for i, id in enumerate(col.get_id_sensors()):
    axes[i].set_xlabel("Temps (j)")
    axes[i].plot(temps_en_jours, col._T_measures[:, i] - 273.15, label="Mesures")
    axes[i].plot(temps_en_jours, col.get_temps_solve()[id] - 273.15, label="Modèle")
    axes[i].legend()
    axes[i].set_title(f"Capteur {i+1}")

plt.subplots_adjust(wspace=0.05)
plt.show()

#Inversion MMC

priors_couche_1 = {
    "moinslog10K": ((4, 9), .001), # (intervalle, sigma)
    "n": ((.01, .25), .005),
    "lambda_s": ((1, 5), .05),
    "rhos_cs": ((1e6,1e7), 1e5),
}

all_priors = [
    ['Couche 1', 0.3, priors_couche_1]
]

col.compute_mcmc(
    nb_iter = 1000,
    all_priors = all_priors,
    nb_cells = 100,
    sigma2=1.0,
    nb_chain=10
)

fig, axes = plt.subplots(2, 4, figsize=(30, 20))

for id_layer, layer_distribs in enumerate(col.get_all_params()):
    axes[id_layer, 0].hist(layer_distribs[::, 0])
    axes[id_layer, 0].set_title(f"Couche {id_layer + 1} : moinslog10K")
    axes[id_layer, 1].hist(layer_distribs[::, 1])
    axes[id_layer, 1].set_title(f"Couche {id_layer + 1} : n")
    axes[id_layer, 2].hist(layer_distribs[::, 2])
    axes[id_layer, 2].set_title(f"Couche {id_layer + 1} : lambda_s")
    axes[id_layer, 3].hist(layer_distribs[::, 3])
    axes[id_layer, 3].set_title(f"Couche {id_layer + 1} : rhos_cs")
plt.show()

bestLayers = col.get_best_layers()

col.compute_solve_transi(bestLayers, nb_cells=100)

col.get_RMSE()

fig, axes = plt.subplots(1, 2, figsize = (20, 5), sharey=True)

axes[0].set_ylabel("Température en °C")

for i, id in enumerate(col.get_id_sensors()):
    axes[i].set_xlabel("Temps (j)")
    axes[i].plot(temps_en_jours, col._T_measures[:, i] - 273.15, label="Mesures")
    axes[i].plot(temps_en_jours, col.get_temps_solve()[id] - 273.15, label="Modèle")
    axes[i].legend()
    axes[i].set_title(f"Capteur {i+1}")

plt.subplots_adjust(wspace=0.05)
plt.show()

rmse = col.get_RMSE()
print(f"RMSE premier capteur : {rmse[0]}")
print(f"RMSE deuxième capteur : {rmse[1]}")
print(f"RMSE globale : {rmse[2]}")

col.plot_CALC_results(nt=len(col._times))
plt.show()


#Affichage des quantiles 

fig, axes = plt.subplots(2, 2, figsize=(20, 10), sharex='col', sharey='row')

axes[0, 0].set_xlabel("Temps (j)")
axes[1, 0].set_ylabel("Débit en m/s")

for i, q in enumerate(col.get_quantiles()):
    axes[0, i].imshow(col.get_temps_quantile(q), aspect='auto', cmap='Spectral_r', extent=[0, temps_en_jours[-1], col._real_z[-1], col._real_z[0]])
    axes[0, i].set_title(f"Quantile de température : {100*q} %")

    axes[1, i].imshow(col.get_flows_quantile(q), aspect='auto', cmap='Spectral_r', extent=[0, temps_en_jours[-1], col._real_z[-1], col._real_z[0]])
    axes[1, i].set_title(f"Quantile de débit : {100*q} %")
    axes[1, i].set_xlabel("Temps (j)")
plt.show()

fig, axes = plt.subplots(1, 3, figsize = (20, 5), sharey=True)

axes[0].set_ylabel("Température en °C")

for i, id in enumerate(col.get_id_sensors()):
    axes[i].set_xlabel("Temps (j)")
    axes[i].plot(temps_en_jours, col._T_measures[:, i] - 273.15, label="Mesures")
    for q in col.get_quantiles():
        axes[i].plot(temps_en_jours, col.get_temps_quantile(q)[id] - 273.15, label=f"Quantile {q}")
    axes[i].legend()
    axes[i].set_title(f"Capteur {i+1}")

plt.subplots_adjust(wspace=0.05)
plt.show()


"""
On va maintenant afficher un graphe avecv les quantiles de débit à profondeur fixée
"""

n = 0

plt.plot(temps_en_jours, col.get_flows_solve(col._real_z[n]), label="Débit modèle")
for q in col.get_quantiles():
    plt.plot(temps_en_jours, col.get_flows_quantile(q)[n,:], label=f"Quantile {q}")
plt.xlabel("Temps (j)")
plt.ylabel("Débit ($m^3/s$)")
plt.legend()
plt.title(f"Quantiles de débit à {col._real_z[n]} m de profondeur")
plt.show()

#Calcul écart interquartile
ecart_interquartile = col.get_flows_quantile(0.95)[n,:] - col.get_flows_quantile(0.05)[n,:]
mean_ecart_interquartile = np.mean(ecart_interquartile)/np.mean(col.get_flows_solve(col._real_z[n])) 
print("Ecart interquantile relatif à la profondeur 0 : ", mean_ecart_interquartile)
