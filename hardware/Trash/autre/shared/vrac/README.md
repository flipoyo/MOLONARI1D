Voici des informations sur les différents fichiers de vrac à trier : 
-temperature_sensor : il faudrait potentiellement modifier le fichier mesure pour qu'il récupère également la pression

-Measure.hpp (déjà c'est bizarre il n'a pas de cpp) -> à refaire intégralement, il manque des données et des défintions : pas bien 

-Time.cpp (pas de hpp) -> gestion du temps en synchronisant l'horloge interne (à la carte Arduino) et l'horloge externe (plus fiable): lit la date et l'heure courante 
Définit également combien de temps la carte doit dormir avant la prochaien minute (ici 15mins)
On sychronise l'interne sur l'externe.
Doit être appelé dans Lora 

Attention ! Il faudrait l'inclure dans Lora.cpp en initialisant les horloges 
#include "MyTime.hpp"
void setup() {
  Serial.begin(9600);
  InitialiseRTC();
  InitializeMeasurementTimes();
  InitializeMeasurementCount();
}

Peut-être faudrait-il l'inclure ailleurs mais à voir 

Ranger le fichier dans les protocoles généraux 


Objectifs des documents (merci ChatGPT) 


Carte 1 (capteur) : mesurer température et pression, stocker temporairement, envoyer via LoRa.

Carte 2 (récepteur) : recevoir les mesures LoRa et les écrire dans un fichier CSV sur la SD.

📝 Carte 1 – Émetteur (rivières)

1.⁠ ⁠Initialisation

Initialiser les capteurs : TemperatureSensor + PressureSensor.

Initialiser l’horloge RTC (My_Time.hpp) pour timestamp.

Initialiser LoRa (Lora.hpp) pour envoyer des données.

2.⁠ ⁠Boucle principale

Lire les capteurs :

Température et pression.

Créer un objet Measure avec id, date, heure et valeurs capteurs.

Envoyer la mesure :

Mettre la mesure dans une file (queue) si tu veux envoyer plusieurs.

Utiliser Lora.sendPackets(queue) pour envoyer.

Attendre les ACK pour chaque paquet.

Gestion du timing :

Calculer le temps jusqu’à la prochaine mesure (CalculateSleepTimeUntilNextMeasurement()).

Mettre en basse consommation (Waiter.sleepUntil() ou LowPower.Sleep()).

📝 Carte 2 – Récepteur + SD

1.⁠ ⁠Initialisation

Initialiser LoRa (Lora.hpp) pour recevoir les données.

Initialiser la carte SD (Writer.hpp) et créer le fichier CSV si nécessaire (Internal_Log.hpp).

Initialiser RTC pour timestamp, si on veut corréler les mesures.

2.⁠ ⁠Boucle principale

Recevoir les données :

Lora.receivePacket() pour récupérer chaque mesure.

Vérifier le type et checksum.

Si paquet DATA → stocker dans la queue.

Écrire dans le CSV :

Pour chaque mesure dans la queue → Writer.LogData().

Incrémenter l’ID et enregistrer timestamp.

Envoyer ACK :

Après réception et stockage, envoyer ACK au capteur via LoRa (Lora.sendPacket(ACK)).

Basse consommation :

Si aucune mesure à recevoir → LowPower.Sleep() pour économiser la batterie.

⚡ Remarques

Les deux cartes utilisent les mêmes modules, juste que l’émetteur lit et envoie, tandis que le récepteur reçoit et écrit.

On peut ajouter un handshake au début de la session pour synchroniser les deux cartes (performHandshake()).

Le récepteur peut être configuré pour attendre plusieurs mesures avant d’écrire sur la SD, ou écrire mesure par mesure.

