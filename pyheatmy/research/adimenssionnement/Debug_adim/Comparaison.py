import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Chargement des fichiers CSV
from pathlib import Path

# Chargement des fichiers CSV (chemin relatif au script)
base = Path(__file__).resolve().parent


########## T :

f_dim = base / 'T_res_DIM.csv'
f_adim = base / 'T_res_ADIM.csv'

if not f_dim.exists() or not f_adim.exists():
    raise FileNotFoundError(
        f"Required CSV files not found in {base!s}.\n"
        f"Looking for: {f_dim.name} and {f_adim.name}"
    )

# Transposition pour avoir les dates en lignes et les profondeurs en colonnes
t_res_dim = pd.read_csv(f_dim, index_col=0)
t_res_adim = pd.read_csv(f_adim, index_col=0)

# Conversion en matrices numpy
# Les lignes représentent les dates et les colonnes les profondeurs
matrix_dim = t_res_dim.values
matrix_adim = t_res_adim.values

# Calcul de l'écart de température
temperature_diff = matrix_adim - matrix_dim

print(t_res_dim.shape)

# Préparation des données pour le graphique
dates = t_res_dim.index  # Dates en abscisse
profondeurs = [k for k in range(t_res_dim.shape[0])]  # Profondeurs en ordonnée

# Version alternative avec matplotlib uniquement
plt.figure(figsize=(12, 8))

im = plt.imshow(temperature_diff, aspect='auto', cmap='RdBu_r', origin='lower')
im.set_clim(-np.max(np.abs(temperature_diff)), np.max(np.abs(temperature_diff)))
plt.colorbar(im, label='Écart de température (°C)')

# Configuration des ticks
plt.yticks(range(len(profondeurs)), profondeurs, rotation=45)
plt.gca().invert_yaxis()
plt.ylabel('Profondeur')
plt.xlabel('Date')
plt.title('Écart de température: T_res_ADIM - T_res_DIM')

plt.tight_layout()

########## H :

f_dim = base / 'H_res_DIM.csv'
f_adim = base / 'H_res_ADIM.csv'

if not f_dim.exists() or not f_adim.exists():
    raise FileNotFoundError(
        f"Required CSV files not found in {base!s}.\n"
        f"Looking for: {f_dim.name} and {f_adim.name}"
    )

# Transposition pour avoir les dates en lignes et les profondeurs en colonnes
t_res_dim = pd.read_csv(f_dim, index_col=0)
t_res_adim = pd.read_csv(f_adim, index_col=0)

# Conversion en matrices numpy
# Les lignes représentent les dates et les colonnes les profondeurs
matrix_dim = t_res_dim.values
matrix_adim = t_res_adim.values

# Calcul de l'écart de température
temperature_diff = matrix_adim - matrix_dim

print(t_res_dim.shape)

# Préparation des données pour le graphique
dates = t_res_dim.index  # Dates en abscisse
profondeurs = [k for k in range(t_res_dim.shape[0])]  # Profondeurs en ordonnée

# Version alternative avec matplotlib uniquement
plt.figure(figsize=(12, 8))

im = plt.imshow(temperature_diff, aspect='auto', cmap='RdBu_r', origin='lower')
im.set_clim(-np.max(np.abs(temperature_diff)), np.max(np.abs(temperature_diff)))
plt.colorbar(im, label='Écart de hauteur de charge (m)')

# Configuration des ticks
plt.yticks(range(len(profondeurs)), profondeurs, rotation=45)
plt.gca().invert_yaxis()
plt.ylabel('Profondeur')
plt.xlabel('Date')
plt.title('Écart de hauteur de charge: H_res_ADIM - H_res_DIM')

plt.tight_layout()



plt.show()
