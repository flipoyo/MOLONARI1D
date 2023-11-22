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

capteur_riviere = pd.read_csv("/Users/marcoul/Desktop/Mines_2A/Molonari/MOLONARI_projet_3-/data_traite/point48_pression_traité.csv", sep = ',', names = ['dates', 'temperature_riviere', 'dH'], skiprows=1)
capteur_ZH = pd.read_csv("/Users/marcoul/Desktop/Mines_2A/Molonari/MOLONARI_projet_3-/data_traite/point48_temperature_traité.csv", sep = ',', names = ['dates', 'temperature_10', 'temperature_20', 'temperature_30', 'temperature_40'], skiprows=1)
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


# set seed for reproducibility
np.random.seed(0)

# conversion mesures de tempétratures
capteur_riviere['temperature_riviere'] = capteur_riviere['temperature_riviere'] + 273.15
capteur_ZH['temperature_10'] = capteur_ZH['temperature_10'] + 273.15
capteur_ZH['temperature_20'] = capteur_ZH['temperature_20'] + 273.15
capteur_ZH['temperature_30'] = capteur_ZH['temperature_30'] + 273.15
capteur_ZH['temperature_40'] = capteur_ZH['temperature_40'] + 273.15

# définition des attributs de colonnes
dH_measures = list(zip(capteur_riviere['dates'],list(zip(capteur_riviere['dH'], capteur_riviere['temperature_riviere']))))
T_measures = list(zip(capteur_ZH['dates'], capteur_ZH[['temperature_10', 'temperature_20', 'temperature_30', 'temperature_40']].to_numpy()))

col_dict = {
	"river_bed": 1., 
    "depth_sensors": [.1, .2, .3, .4],
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

params = Param(moinslog10K=7.943059, n=0.21056272, lambda_s=7.1972322, rhos_cs=2951451.5)

col.compute_solve_transi(params, nb_cells=100)

temperatures = col.get_temps_solve() - 273.15

fig, ax = plt.subplots(figsize=(10, 5), facecolor = 'w')

im = ax.imshow(
    temperatures,
    aspect = "auto",
    extent = [0, temps_en_jours[-1], col.depths_solve[-1], col.depths_solve[0]],
    cmap = "seismic"
)
cbar = fig.colorbar(im, ax=ax)
cbar.set_label("Température en °C")

col.plot_CALC_results(nt=len(col._times))

plt.show()

rmse = col.get_RMSE()
print(f"RMSE premier capteur : {rmse[0]}")
print(f"RMSE deuxième capteur : {rmse[1]}")
print(f"RMSE troisème capteur : {rmse[2]}")
print(f"RMSE globale : {rmse[3]}")

fig, axes = plt.subplots(1, 3, figsize = (20, 5), sharey=True)

axes[0].set_ylabel("Température en °C")

for i, id in enumerate(col.get_id_sensors()):
    axes[i].set_xlabel("Temps (j)")
    axes[i].plot(temps_en_jours, col._T_measures[:, i] - 273.15, label="Mesures")
    axes[i].plot(temps_en_jours, col.get_temps_solve()[id] - 273.15, label="Modèle")
    axes[i].legend()
    axes[i].set_title(f"Capteur {i+1}")

plt.subplots_adjust(wspace=0.05)
plt.show()

plt.plot(temps_en_jours, col.get_flows_solve(col._real_z[0]), label="Débit modèle")
plt.xlabel("Temps (j)")
plt.ylabel("Débit ($m^3/s$)")
plt.legend()
plt.title(f"Débit à {col._real_z[0]} m de profondeur")
plt.show()