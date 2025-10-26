import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Clean comparison script that reads CSVs relative to the script directory
base = Path(__file__).resolve().parent
f_dim = base / 'T_res_DIM.csv'
f_adim = base / 'T_res_ADIM.csv'

if not f_dim.exists() or not f_adim.exists():
    raise FileNotFoundError(
        f"Required CSV files not found in {base!s}.\n"
        f"Looking for: {f_dim.name} and {f_adim.name}"
    )

# Load and transpose
t_res_dim = pd.read_csv(f_dim, index_col=0).T
t_res_adim = pd.read_csv(f_adim, index_col=0).T

# Compute difference
temperature_diff = t_res_adim.values - t_res_dim.values

# Labels
dates = t_res_dim.index
profondeurs = t_res_dim.columns

# Heatmap via seaborn
plt.figure(figsize=(12, 8))
sns.heatmap(
    temperature_diff,
    xticklabels=profondeurs,
    yticklabels=dates,
    cmap='RdBu_r',
    center=0,
    cbar_kws={'label': 'Écart de température (°C)'}
)
plt.xlabel('Profondeur')
plt.ylabel('Date')
plt.title('Écart de température: T_res_ADIM - T_res_DIM')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Alternative with matplotlib
plt.figure(figsize=(12, 8))
im = plt.imshow(temperature_diff, aspect='auto', cmap='RdBu_r', origin='lower')
plt.colorbar(im, label='Écart de température (°C)')
plt.xticks(range(len(profondeurs)), profondeurs, rotation=45)
plt.yticks(range(len(dates)), dates)
plt.xlabel('Profondeur')
plt.ylabel('Date')
plt.title('Écart de température: T_res_ADIM - T_res_DIM')
plt.tight_layout()
plt.show()
