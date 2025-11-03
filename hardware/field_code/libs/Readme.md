# **Présentation des librairies**

Ce document présente les différentes libraires utilisées dans le projet Molonari pour les applications In the Air, ainsi que leur fonctionnement basique avec des schémas. 

## *LoRa_Molonari*
LoRa_Molonari est une librairie permettant la communication sans fil entre deux cartes via le protocole LoRa : 

- Initialisation et gestion de la connexion LoRa : Démarrage et arrêt du module LoRa.
- Envoi et réception de paquets : Avec gestion des checksums et des acquittements.
- Handshake (poignée de main) : Établissement d’une connexion fiable entre un maître et un esclave.
- Fermeture de session : Clôture propre de la communication.

+--------------------+
| startLoRa()        |
+--------------------+
          |
          v
+--------------------+
| Handshake MASTER   |
|  SYN -> SYN-ACK    |
|  ACK               |
+--------------------+
          |
          v
+--------------------+
| sendPackets()      |
|  - sendPacket()    |
|  - attendre ACK    |
+--------------------+
          |
          v
+--------------------+
| receivePackets()   |
|  - receivePacket() |
|  - envoyer ACK     |
+--------------------+
          |
          v
+--------------------+
| closeSession()     |
|  - envoyer FIN     |
|  - attendre FIN    |
+--------------------+


## *LoRaWan_Molonari*
LoRaWAN_Molonari est une librairie permettant l’envoi de données via le réseau LoRaWAN :

- Connexion OTAA : Activation du module LoRaWAN via AppEUI et AppKey.
- Envoi de données : Gestion d’une file d’attente de messages à envoyer.
- Gestion des erreurs : Retry automatique en cas d’échec d’envoi.
- Configuration réseau : Adaptation du débit (ADR) et intervalle de poll.

┌────────────────────────┐
|  File de messages      |
|   (std::queue<String>) |
└───────────┬────────────┘
            |
            v
+------------------------+
| LoraWANCommunication   |
| sendQueue()            |
+------------------------+
            |
            v
+------------------------+
| Boucle sur chaque msg  |
|  - Modem.beginPacket() |
|  - Modem.print(payload)|
|  - Modem.endPacket()   |
+------------------------+
            |
            v
+------------------------+
| Vérification d'erreur  |
|  - si ok : supprimer  |
|    message de la file  |
|  - sinon : retry max 6 |
+------------------------+
            |
            v
+------------------------+
| Transmission réussie ? |
|  - Oui -> message log  |
|  - Non -> abandon msg  |
+------------------------+


## *Measure*
Measure est une librairie permettant de récupérer les données des capteurs et de les mettre en formes : 

- une classe Sensor qui récupère les données des capteurs
- une classe Measure qui met en forme les mesures que on lui envoie

Les données sont renvoyées sous la forme " 'Measure n°' ID, date, heure, mesures " puis sont ensuite renvoyées à Writer.

                  ┌───────────────────────────┐
                  │        Sensor             │
                  └─────────────┬─────────────┘
                                │
             ┌──────────────────┴──────────────────┐
             │                                     │
             ▼                                     ▼
    ┌───────────────────┐                  ┌───────────────────┐
    │ Constructeur par  │                  │ Constructeur complet│
    │ défaut            │                  │ avec pins, offset,│
    │ (dataPin=-1,...)  │                  │ scale, type, id   │
    └─────────┬─────────┘                  └─────────┬─────────┘
              │                                      │
              └──────────────┐──────────────────────┘
                             ▼
                    ┌─────────────────┐
                    │ Sensor::Measure │
                    │ 1. Active capteur (enablePin HIGH) │
                    │ 2. Attente 200 ms                   │
                    │ 3. Lecture analogique sur dataPin  │
                    │ 4. Désactive capteur (LOW)         │
                    │ 5. Retourne valeur (MESURE)        │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Measure       │
                    └─────────┬─────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
    ┌───────────────────────┐     ┌───────────────────────┐
    │ Measure::oneLine()    │     │ Measure::ToString()   │
    │ - Récupère date/heure │     │ - Préfixe "Measure n°"│
    │ - Parcourt vecteur    │     │ - Appelle oneLine()   │
    │   channel[] pour      │     │ - Retourne chaîne     │
    │   formater les valeurs│     └───────────────────────┘
    │ - Retourne ligne CSV  │
    └───────────────────────┘

## *Writer*
Writer est une librairie permettant d'écrire les données sur la carte SD : 

- Gestion des connexions (reconnexion automatique en cas de perte)
- Logs de debug optionnels
- IDs uniques pour chaque mesure
- Formatage CSV standardisé et écriture sur la carte

┌───────────────────────────────┐
│          CAPTEURS             │
│ (Mesure via Sensor/Measure)   │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│          MEASURE              │
│ - Contient les valeurs        │
│ - Formate en CSV (ToString)  │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│           WRITER              │
│                               │
│ LogData()                     │
│ ├─ ApplyContent() → Remplit    │
│ │   les channels               │
│ ├─ Vérifie la connexion SD     │
│ ├─ WriteInNewLine() → Écriture│
│ │   CSV et flush               │
│ └─ Incrémente next_id          │
│                               │
│ Reconnect() → Restaure SD si  │
│ perte de connexion             │
│ Dispose() → Ferme fichier      │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│             SD                │
│ - Stocke les mesures au format│
│   CSV                         │
└───────────────────────────────┘

## *Reader*
Reader est une librairie permettant de récupérer les données enregistrées sur la carte SD après qu'elles aient écrites par Writer: 

- Lire un fichier CSV de configuration pour un système embarqué (paramètres LoRa, capteurs, etc.)
- Gérer un curseur de lecture pour un fichier de données (data.csv)
- Charger les données dans une file d’attente pour traitement ultérieur
- Sauvegarder la position du curseur pour reprendre la lecture après une coupu

                       ┌─────────────────────────────┐
                       │        Reader               │
                       └─────────────┬───────────────┘
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
 ┌─────────────────────┐                           ┌─────────────────────────┐
 │ lireConfigCSV()     │                           │ SD file operations      
 │ - Ouvre fichier CSV │                           │ (data.csv, cursor_position.txt
 │ - Lit ligne par     │                           └─────────┬─────────────
 │   ligne             │                                     │
 │ - Ignore commentaires et vides                          ▼
 │ - Sépare en tokens (id, type, pin, offset, scale, id_capteur) 
 │ - Remplit liste_capteurs vector<SensorConfig> 
 └─────────────────────┘
                                     │
                                     ▼
                       ┌─────────────────────────────┐
                       │ EstablishConnection(shift)  │
                       │ - Ouvre fichier data.csv    │
                       │ - Se place au curseur       │
                       │ - Permet lecture séquentielle│
                       └─────────────┬───────────────┘
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
 ┌─────────────────────┐                           ┌─────────────────────────┐
 │ UpdateCursor(shift) │                           │ loadDataIntoQueue()     │
 │ - Décale line_cursor│                           │ - Lit les prochaines    │
 │ - Sauvegarde curseur│                           │   lignes dans la SD     │
 │   dans cursor.txt   │                           │ - Remplit queue<String> │
 └─────────────────────┘                           └─────────┬─────────────┘
                                     │
                                     ▼
                       ┌─────────────────────────────┐
                       │ ReadMeasure() / IsDataAvailable() │
                       │ - Lit ligne suivante          │
                       │ - Vérifie disponibilité       │
                       └─────────────┬───────────────┘
                                     │
                                     ▼
                       ┌─────────────────────────────┐
                       │ Dispose()                   │
                       │ - Ferme le fichier SD        │
                       └─────────────────────────────┘

## *Time*
Ce fichier gère le temps et les horaires des mesures pour le système basé sur la carte MKR. Il utilise à la fois l’horloge interne de la carte (RTCZero) et une horloge externe (RTC_PCF8523) pour assurer la précision et la persistance après coupure d’alimentation.

                 ┌──────────────────────────┐
                 │  Lecture config CSV      │
                 │  (freq_mesure & freq_LoRa) │
                 └─────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │ Initialisation RTC      │
                  │ internalRtc & externalRtc │
                  └─────────────┬───────────┘
                                │
          ┌─────────────────────┴─────────────────────┐
          │                                           │
          ▼                                           ▼
 ┌─────────────────────┐                     ┌─────────────────────┐
 │ Synchronisation RTC  │                     │ Initialisation vecteur│
 │ interne ↔ externe    │                     │ measurementTimesVec │
 └─────────┬───────────┘                     └─────────┬───────────┘
           │                                           │
           ▼                                           ▼
  ┌─────────────────────┐                   ┌─────────────────────────┐
  │ Obtenir date/heure  │                   │ Calculer temps écoulé   │
  │ GetCurrentDate/Hour │                   │ depuis minuit           │
  └─────────┬───────────┘                   └─────────┬─────────────┘
            │                                            │
            ▼                                            ▼
   ┌─────────────────────┐                     ┌─────────────────────────┐
   │ Initialiser compteur│                     │ Déterminer prochain     │
   │ de mesures           │                     │ instant de mesure       │
   └─────────┬───────────┘                     └─────────┬─────────────┘
             │                                            │
             └───────────────────┬────────────────────────┘
                                 ▼
                      ┌─────────────────────────┐
                      │ CalculateSleepTimeUntil │
                      │ NextMeasurement()       │
                      │  → retourne ms jusqu’à  │
                      │    prochaine mesure     │
                      └─────────────────────────┘
                                 │
                                 ▼
                      ┌─────────────────────────┐
                      │ Microcontrôleur dort    │
                      │ jusqu’à la prochaine    │
                      │ mesure (low power)      │
                      └─────────────────────────┘
                                 │
                                 ▼
                      ┌─────────────────────────┐
                      │ Réveil et prise mesure  │
                      │ via Sensor::Measure()   │
                      └─────────────────────────┘
                                 │
                                (boucle)

## *Waiter*
Ce fichier gère le temps d’attente et la synchronisation des tâches pour l’Arduino, en particulier pour la communication LoRa et la lecture/écriture sur la carte SD.

┌─────────────────────────┐
│       Waiter            │
└────────────┬────────────┘
             │
             ▼
      ┌───────────────┐
      │ startTimer()  │
      │ - mémorise t0 │
      └───────────────┘
             │
             ▼
      ┌───────────────┐
      │ sleepUntil()  │
      │ - calcule dt  │
      │ - deepSleep   │
      └───────────────┘
             │
             ▼
      ┌───────────────┐
      │ delayUntil()  │
      └───────────────┘
             │
 ┌───────────┴───────────┐
 │ Boucle active jusqu'à  │
 │ le temps souhaité      │
 └───────────┬───────────┘
             │
   ┌─────────┴─────────┐
   │ LoRa communication │
   │ - startLoRa()      │
   │ - handshake()      │
   │ - sendPackets()    │
   │ - closeSession()   │
   │ - stopLoRa()       │
   └─────────┬─────────┘
             │
   ┌─────────┴─────────┐
   │ SD Reader          │
   │ - EstablishConnection() │
   │ - loadDataIntoQueue()  │
   │ - UpdateCursor()       │
   │ - Dispose()            │
   └─────────┬─────────┘
             │
             ▼
      ┌───────────────┐
      │ PrintQueue()  │
      │ - afficher et │
      │   vider queue │
      └───────────────┘

