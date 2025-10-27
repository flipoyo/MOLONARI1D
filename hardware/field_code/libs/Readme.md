# **Présentation des librairies**

Ce document présente les différentes libraires utilisées dans le projet Molonari pour les applications In the Air. 

## *LoRa_Molonari*

LoRa_Molonari est une librairie permettant la communication sans fil entre deux cartes via le protocole LoRa : 

- Initialisation et gestion de la connexion LoRa : Démarrage et arrêt du module LoRa.
- Envoi et réception de paquets : Avec gestion des checksums et des acquittements.
- Handshake (poignée de main) : Établissement d’une connexion fiable entre un maître et un esclave.
- Fermeture de session : Clôture propre de la communication.

## *LoRaWan_Molonari*

LoRaWAN_Molonari est une librairie permettant l’envoi de données via le réseau LoRaWAN en mode OTAA (Over-The-Air Activation) :

- Connexion OTAA : Activation du module LoRaWAN via AppEUI et AppKey.
- Envoi de données : Gestion d’une file d’attente de messages à envoyer.
- Gestion des erreurs : Retry automatique en cas d’échec d’envoi.
- Configuration réseau : Adaptation du débit (ADR) et intervalle de poll.

## *Measure* 

Measure est une librairie permettant de récupérer les données des capteurs et de les mettre en formes : 

- une classe Sensor qui lit les données et les récupère
- une classe Measure qui met en forme les mesures que on lui envoie

## *Reader*

