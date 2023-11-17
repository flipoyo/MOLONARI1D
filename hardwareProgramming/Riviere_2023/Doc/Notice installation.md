# LE tuto de mise en place d'un capteur MOLONARI

## 1. Prérequis

### 1.0. Avant-ça

Un diplôme en physique nucléaire OU deux mains fonctionnelles (minimum une) (ou des pieds).

### 1.1. Matériel

- [Arduino MKR WAN 1310](https://docs.arduino.cc/hardware/mkr-wan-1310) (récupération des données + envoi par LoRa)
- [Antenne Waterproof](https://store.arduino.cc/products/dipole-pentaband-waterproof-antenna) (à brancher sur la MKR WAN 1310)
- [Module Adalogger Featherwing SD- RTC](https://www.adafruit.com/product/2922) (à brancher selon le schéma ci-après)

### 1.2. Logiciels

- [Arduino IDE](https://www.arduino.cc/en/software)
- [Visual Studio Code](https://code.visualstudio.com/) (conseillé)

Sur Arduino IDE, il faut installer les librairies suivantes :

- ``Arduino Low Power`` (Mise en veille profonde)
- ``FlashStorage`` (Stockage de données dans la mémoire flash)
- ``LoRa`` (Communication LoRa)
- ``RTCLib`` (Gestion de l'horloge temps réel externe)
- ``RTCZero`` (Gestion de l'horloge temps réel interne à la MKR WAN 1310)
- ``SD`` (Communication carte SD)

### 1.4 Mise en place

Téléverser le code "Riviere_2023.ino" dans l'émetteur qui sera ensuite placé dans la boîte. Téléverser le code "Rive_2023.ino" dans le récepteur.

####Côté émetteur :
Passer les câbles de la sonde de température dans les passes-câbles (dévisser le capot, rentrer les câbles, revisser le capot pour l'étanchéité) voir la photo plus loin pour avoir une idée.

Suivre les branchement du schéma électrique suivant :
![Schéma électrique](schéma_branchement.png)

Ça doit avoir cette tête :
![Vue intérieure](MOLONARI_vue_intérieure.jpg)

Remettre le toit et le visser (fort) pour l'étanchéité (attention sur la photo les vis ne sont pas vissées)
![Vue extérieure](MOLONARI_vue_exterieure.jpg)

####Côté récepteur: