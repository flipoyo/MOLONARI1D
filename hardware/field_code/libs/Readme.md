# **Présentation des librairies**

Ce document présente les différentes libraires utilisées dans le projet Molonari pour les applications In the Air, ainsi que leur fonctionnement basique avec des schémas. 

*LoRa_Molonari*
Ce module fournit une classe LoraCommunication permettant d’établir, maintenir et fermer une communication fiable entre deux modules LoRa (type SX127x).
Il gère les handshakes, l’envoi/réception de paquets, les ACK/FIN, et la vérification d’intégrité via un checksum.
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
|  - recevoir DATA   |
|  - envoyer ACK     |
+--------------------+
          |
          v
+--------------------+
| closeSession()     |
|  - envoyer FIN     |
|  - attendre FIN    |
+--------------------+


*LoRaWan_Molonari*
Ce fichier fournit un wrapper simple pour LoRaWAN : initialisation, connexion au réseau et envoi fiable de messages à partir d’une file. Il gère les retries, les logs de debug et la synchronisation des envois.

+------------------------+
|  File de messages      |
|   (std::queue<String>) |
+------------------------+
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


*Measure*
Ce fichier définit deux classes principales : Sensor et Measure, utilisées pour la lecture et la représentation des données de capteurs (pression, température, etc.) sur une carte Arduino MKR. La classe Sensor gère l’acquisition de données depuis un capteur analogique. La classe Measure gère la représentation et le formatage des mesures collectées.

                  ┌───────────────────────────┐
                  │        Sensor              │
                  └─────────────┬─────────────┘
                                │
             ┌──────────────────┴──────────────────┐
             │                                     │
             ▼                                     ▼
    ┌───────────────────┐                  ┌───────────────────┐
    │ Constructeur par  │                  │ Constructeur complet│
    │ défaut             │                  │ avec pins, offset,  │
    │ (dataPin=-1,...)   │                  │ scale, type, id    │
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


*Reader*
Ce fichier définit la classe Reader et gère principalement la lecture et le traitement des fichiers CSV sur la carte SD, ainsi que le suivi de la position de lecture pour s'assurer entre autres de l'envoi des mesures qui n'auraient pas pu être envoyées précédemment. 
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
 │ - Décale line_cursor │                           │ - Lit les prochaines    │
 │ - Sauvegarde curseur │                           │   lignes dans la SD     │
 │   dans cursor.txt    │                           │ - Remplit queue<String> │
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

*Time*
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

*Waiter*
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

*Writer*
Ce fichier gère l’écriture des mesures dans un fichier CSV sur carte SD et s’assure que chaque mesure a un ID unique et que la connexion SD est fiable.

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
