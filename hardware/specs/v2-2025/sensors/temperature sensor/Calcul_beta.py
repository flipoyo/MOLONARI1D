import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Chemin vers votre fichier CSV — modifier si besoin
csv_path = Path(r"c:\MOLONARI1D\hardware\specs\v2-2025\sensors\temperature sensor\tests_beta_temperature.csv")

# Lire le CSV
df = pd.read_csv(csv_path, sep=',', skiprows=1)
#print(df.head())
df.columns = ['index', 'Time', 'Temperature', 'Voltage', 'none', 'none2']
df[['Temperature','Voltage']] = df[['Temperature','Voltage']].astype(float)
donnees_utiles = df[['Temperature','Voltage']]
#print(donnees_utiles.head())
used_data = donnees_utiles.iloc[650:911]
print(used_data.head())
used_data['Temp_K'] = used_data['Temperature'] + 273.15
used_data['inv_T'] = 1/(used_data['Temp_K']) 

print(used_data.head())
to_keep = used_data[['inv_T', 'Voltage']]
to_keep.to_csv("bonnes_donnees_utiles_etalonnage_thermometres2.csv", index=False, sep=';') #; nécessaire pour excel