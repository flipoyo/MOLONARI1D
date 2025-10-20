from IPython.display import Audio, display
import numpy as np

def play_jingle():

    audio_file = r'.\Frequentieeeeel.mp3'

    # Créer un élément audio qui se déclenche automatiquement
    display(Audio(url=audio_file, autoplay=True))