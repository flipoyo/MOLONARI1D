from IPython.display import Audio, display
import numpy as np

audio_file = r'.\Frequentieeeeel.mp3'

try:
    # Créer un élément audio qui se déclenche automatiquement
    display(Audio(url=audio_file, autoplay=True))
    
except FileNotFoundError:
    print(f"Attention : Le fichier audio '{audio_file}' n'a pas été trouvé.")