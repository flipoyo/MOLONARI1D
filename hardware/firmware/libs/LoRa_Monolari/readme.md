# LoRa Communication Library

Une bibliothèque Arduino pour gérer la communication LoRa entre un MASTER et un SLAVE, avec gestion des paquets, contrôle d’intégrité, et sessions fiables.

---

## Table des matières
- [Description](#description)  
- [Fonctionnalités](#fonctionnalités)  
- [Installation](#installation)  
- [Utilisation](#utilisation)  
- [Licence](#licence)  
---

## Description

Cette bibliothèque permet de créer une communication LoRa robuste entre deux dispositifs Arduino (ou compatibles).

Elle inclut :
- Envoi et réception de paquets avec ACK et checksum.
- Gestion des sessions avec SYN, SYN-ACK, ACK, et FIN.
- Contrôle de destination pour éviter les paquets indésirables.
- Retransmission automatique en cas d’échec.

---

## Fonctionnalité

- Communication point-à-point ou multi-destinations.
- Support des rôles MASTER et SLAVE.
- Gestion automatique de la file d’attente (std::queue) pour les messages à envoyer et à recevoir.
- Vérification d’intégrité avec checksum simple XOR.
- Limite de taille de file d’attente configurable (MAX_QUEUE_SIZE).

---
MASTER                           SLAVE
  |                                |
  |---- SYN (packet 0) ------------>|  // Master initie le handshake
  |                                |
  |<--- SYN-ACK (packet 0) --------|  // Slave répond avec SYN-ACK
  |                                |
  |---- ACK (packet 0) ------------>|  // Master confirme la synchro
  |                                |
  |        HANDSHAKE TERMINÉ        |

  // --- Transmission de données ---
  |---- DATA (packet 1) ----------->|
  |                                |
  |<--- ACK (packet 1) ------------|  // Slave confirme la réception
  |---- DATA (packet 2) ----------->|
  |                                |
  |<--- ACK (packet 2) ------------|
  |              ...               |

  // --- Fin de session ---
  |---- FIN (lastPacket) ---------->|
  |                                |
  |<--- FIN (lastPacket) ----------|  // Slave confirme la fin
  |                                |
  |         SESSION TERMINÉE       |
 
---

1. **LoraCommunication::LoraCommunication(long frequency, uint8_t localAdd, uint8_t desti, RoleType role)**
Initialise un objet LoRa avec :
- freq : fréquence LoRa (ex: 915 MHz)
- localAddress : adresse locale du device
- destination : adresse du destinataire
- deviceRole : MASTER ou SLAVE
- active : booléen indiquant si LoRa est actif (initialement false)

2. **void LoraCommunication::startLoRa()**
Active le module LoRa avec LoRa.begin(freq).
- Essaie jusqu’à 3 fois en cas d’échec.
- Active active = true si réussite.
- Affiche les logs si debug activé.

3. **void LoraCommunication::stopLoRa()**
- Désactive le module LoRa (LoRa.end()) et met active = false.
- Log de confirmation si debug.

4. **setdesttodefault()**
- Remet la destination à 0xff (broadcast).

5. **void LoraCommunication::sendPacket(uint8_t packetNumber, RequestType requestType, const String &payload)**
Envoie un paquet LoRa structuré :
- checksum → pour vérifier l’intégrité
- destination → destinataire
- localAddress → émetteur
- packetNumber → numéro du paquet
- requestType → SYN, ACK, DATA, FIN
- payload → contenu du message

Attends un petit délai aléatoire avant d’envoyer pour éviter les collisions.
Utilise LoRa.beginPacket() et LoRa.endPacket().

6. **bool LoraCommunication::receivePacket(uint8_t &packetNumber, RequestType &requestType, String &payload)**
- Vérifie s’il y a un paquet disponible (LoRa.parsePacket()).
- Lit les champs : checksum, destinataire, émetteur, numéro de paquet, type de requête, payload.
- Vérifie la destination avec isValidDestination.
- Vérifie la checksum pour l’intégrité.
- Retourne true si paquet valide reçu.

7. **bool LoraCommunication::isValidDestination(int recipient, int dest, RequestType requestType)**
- Vérifie si le paquet reçu est destiné à ce device.
- Si SYN et destination par défaut (0xff) et destinataire connu (myNet), accepte le paquet et définit destination.

8. **bool LoraCommunication::isValidDestination(int recipient, int dest, RequestType requestType)**
- Vérifie si le paquet reçu est destiné à ce device.
- Si SYN et destination par défaut (0xff) et destinataire connu (myNet), accepte le paquet et définit destination

9. **uint8_t LoraCommunication::calculateChecksum(...)**
- Calcul simple XOR entre tous les octets du paquet : recipient, dest, packetNumber, requestType et payload.
- Permet de détecter les erreurs de transmission.

10. **bool LoraCommunication::isLoRaActive()**
- Retourne l’état actuel du module (true si LoRa est actif).

11. **bool LoraCommunication::handshake(uint8_t &shift)**
Gère la synchronisation MASTER/SLAVE :
- MASTER : envoie SYN → attend SYN-ACK → renvoie ACK
- SLAVE : attend SYN → renvoie SYN-ACK → attend ACK
- shift reçoit le numéro du paquet initial pour synchronisation.
Retry automatique en cas d’échec (max 6 fois).

12. **uint8_t LoraCommunication::sendPackets(std::queue<String> &sendQueue)**
Envoie tous les messages dans la queue.

Pour chaque message :
- Envoie DATA
- Attend ACK
- Retry jusqu’à 6 fois
Retourne le nombre de paquets envoyés.

13. **int LoraCommunication::receivePackets(std::queue<String> &receiveQueue)**
- Attend les paquets entrants pendant 60 secondes ou jusqu’à FIN.
- Vérifie le numéro du paquet pour éviter les doublons.
- Push le payload dans la queue receiveQueue.
- Envoie ACK pour chaque paquet reçu.
- Retourne le dernier numéro de paquet reçu.

14. **void LoraCommunication::closeSession(int lastPacket)**
- Envoie FIN pour terminer la session.
- Attends confirmation FIN de l’autre côté.
- Retry jusqu’à 3 fois.

## Installation

1. Installer la bibliothèque [LoRa](https://github.com/sandeepmistry/arduino-LoRa) pour Arduino via le Library Manager.
2. Copier les fichiers LoRa_Molonari.hpp et LoRa_Molonari.cpp dans votre projet Arduino.
3. Inclure la bibliothèque dans votre sketch 

# LoRa Communication Library

Une bibliothèque Arduino pour gérer la communication LoRa entre un MASTER et un SLAVE, avec gestion des paquets, contrôle d’intégrité, et sessions fiables.

---

## Table des matières
- [Description](#description)  
- [Fonctionnalités](#fonctionnalités)  
- [Installation](#installation)  
- [Utilisation](#utilisation)  
- [Licence](#licence)  
---

## Description

Cette bibliothèque permet de créer une communication LoRa robuste entre deux dispositifs Arduino (ou compatibles).

Elle inclut :
- Envoi et réception de paquets avec ACK et checksum.
- Gestion des sessions avec SYN, SYN-ACK, ACK, et FIN.
- Contrôle de destination pour éviter les paquets indésirables.
- Retransmission automatique en cas d’échec.

---

## Fonctionnalité

- Communication point-à-point ou multi-destinations.
- Support des rôles MASTER et SLAVE.
- Gestion automatique de la file d’attente (std::queue) pour les messages à envoyer et à recevoir.
- Vérification d’intégrité avec checksum simple XOR.
- Limite de taille de file d’attente configurable (MAX_QUEUE_SIZE).

---
MASTER                           SLAVE
  |                                |
  |---- SYN (packet 0) ------------>|  // Master initie le handshake
  |                                |
  |<--- SYN-ACK (packet 0) --------|  // Slave répond avec SYN-ACK
  |                                |
  |---- ACK (packet 0) ------------>|  // Master confirme la synchro
  |                                |
  |        HANDSHAKE TERMINÉ        |

  // --- Transmission de données ---
  |---- DATA (packet 1) ----------->|
  |                                |
  |<--- ACK (packet 1) ------------|  // Slave confirme la réception
  |---- DATA (packet 2) ----------->|
  |                                |
  |<--- ACK (packet 2) ------------|
  |              ...               |

  // --- Fin de session ---
  |---- FIN (lastPacket) ---------->|
  |                                |
  |<--- FIN (lastPacket) ----------|  // Slave confirme la fin
  |                                |
  |         SESSION TERMINÉE       |
 
---

1. **LoraCommunication::LoraCommunication(long frequency, uint8_t localAdd, uint8_t desti, RoleType role)**
Initialise un objet LoRa avec :
- freq : fréquence LoRa (ex: 915 MHz)
- localAddress : adresse locale du device
- destination : adresse du destinataire
- deviceRole : MASTER ou SLAVE
- active : booléen indiquant si LoRa est actif (initialement false)

2. **void LoraCommunication::startLoRa()**
Active le module LoRa avec LoRa.begin(freq).
- Essaie jusqu’à 3 fois en cas d’échec.
- Active active = true si réussite.
- Affiche les logs si debug activé.

3. **void LoraCommunication::stopLoRa()**
- Désactive le module LoRa (LoRa.end()) et met active = false.
- Log de confirmation si debug.

4. **setdesttodefault()**
- Remet la destination à 0xff (broadcast).

5. **void LoraCommunication::sendPacket(uint8_t packetNumber, RequestType requestType, const String &payload)**
Envoie un paquet LoRa structuré :
- checksum → pour vérifier l’intégrité
- destination → destinataire
- localAddress → émetteur
- packetNumber → numéro du paquet
- requestType → SYN, ACK, DATA, FIN
- payload → contenu du message

Attends un petit délai aléatoire avant d’envoyer pour éviter les collisions.
Utilise LoRa.beginPacket() et LoRa.endPacket().

6. **bool LoraCommunication::receivePacket(uint8_t &packetNumber, RequestType &requestType, String &payload)**
- Vérifie s’il y a un paquet disponible (LoRa.parsePacket()).
- Lit les champs : checksum, destinataire, émetteur, numéro de paquet, type de requête, payload.
- Vérifie la destination avec isValidDestination.
- Vérifie la checksum pour l’intégrité.
- Retourne true si paquet valide reçu.

7. **bool LoraCommunication::isValidDestination(int recipient, int dest, RequestType requestType)**
- Vérifie si le paquet reçu est destiné à ce device.
- Si SYN et destination par défaut (0xff) et destinataire connu (myNet), accepte le paquet et définit destination.

8. **bool LoraCommunication::isValidDestination(int recipient, int dest, RequestType requestType)**
- Vérifie si le paquet reçu est destiné à ce device.
- Si SYN et destination par défaut (0xff) et destinataire connu (myNet), accepte le paquet et définit destination

9. **uint8_t LoraCommunication::calculateChecksum(...)**
- Calcul simple XOR entre tous les octets du paquet : recipient, dest, packetNumber, requestType et payload.
- Permet de détecter les erreurs de transmission.

10. **bool LoraCommunication::isLoRaActive()**
- Retourne l’état actuel du module (true si LoRa est actif).

11. **bool LoraCommunication::handshake(uint8_t &shift)**
Gère la synchronisation MASTER/SLAVE :
- MASTER : envoie SYN → attend SYN-ACK → renvoie ACK
- SLAVE : attend SYN → renvoie SYN-ACK → attend ACK
- shift reçoit le numéro du paquet initial pour synchronisation.
Retry automatique en cas d’échec (max 6 fois).

12. **uint8_t LoraCommunication::sendPackets(std::queue<String> &sendQueue)**
Envoie tous les messages dans la queue.

Pour chaque message :
- Envoie DATA
- Attend ACK
- Retry jusqu’à 6 fois
Retourne le nombre de paquets envoyés.

13. **int LoraCommunication::receivePackets(std::queue<String> &receiveQueue)**
- Attend les paquets entrants pendant 60 secondes ou jusqu’à FIN.
- Vérifie le numéro du paquet pour éviter les doublons.
- Push le payload dans la queue receiveQueue.
- Envoie ACK pour chaque paquet reçu.
- Retourne le dernier numéro de paquet reçu.

14. **void LoraCommunication::closeSession(int lastPacket)**
- Envoie FIN pour terminer la session.
- Attends confirmation FIN de l’autre côté.
- Retry jusqu’à 3 fois.

## Installation

1. Installer la bibliothèque [LoRa](https://github.com/sandeepmistry/arduino-LoRa) pour Arduino via le Library Manager.
2. Copier les fichiers LoRa_Molonari.hpp et LoRa_Molonari.cpp dans votre projet Arduino.
3. Inclure la bibliothèque dans votre sketch 

