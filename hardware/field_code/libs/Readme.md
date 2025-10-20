**Présentation des librairies**

Ce document présente les différentes libraires utilisées dans le projet Molonari pour les applications In the Air. 

*LoRa_Molonari*
Ce module fournit une classe LoraCommunication permettant d’établir, maintenir et fermer une communication fiable entre deux modules LoRa (type SX127x).
Il gère les handshakes, l’envoi/réception de paquets, les ACK/FIN, et la vérification d’intégrité via un checksum.
--> LoraCommunication(long frequency, uint8_t localAdd, uint8_t desti, RoleType role);
frequency : fréquence LoRa (ex. 868E6)
localAdd : adresse du module courant
desti : adresse du destinataire
role : MASTER ou SLAVE