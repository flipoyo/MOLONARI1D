#include <Arduino.h>
#include <SD.h>
#include <queue>

#include "LoRaWan_Molonari.hpp"
#include "LoRa_Molonari.hpp"
#include "Waiter.hpp"
#include "Reader.hpp"


LoraCommunication lora(config.lora_freq, 0xAA, 0xFF, RoleType::MASTER);

LoraWANCommunication loraWAN;
std::queue<String> sendingQueue;

unsigned long lastLoraSend = 0;
unsigned long lastAttempt = 0;



// ----- Setup -----
void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);

    Serial.begin(9600);
    unsigned long end_date = millis() + 5000;
    while (!Serial && millis() < end_date) {}

    Serial.println("\n=== Initialisation du Relais Molonari ===");

    // Lecture configuration CSV
    Reader reader;
    reader.lireConfigCSV("relay_config.csv");
    Serial.println("Configuration chargée.");

    // Initialisation LoRa communication
    lora = LoraCommunication(config.lora_freq, 0xAA, 0xFF, RoleType::MASTER);

    // Vérification SD
    if (!SD.begin(config.CSPin)) {
        Serial.println("Erreur SD - arrêt système.");
        while (true) {}
    }

    Serial.println("Initialisation terminée !");
    pinMode(LED_BUILTIN, INPUT_PULLDOWN);
}

// ----- Loop -----
void loop() {
    static unsigned long lastAttempt = 0; // mémorise la dernière tentative de réception (en millisecondes)
    Waiter waiter;
    waiter.startTimer();
    // Si 3/4 du temps d’intervalle est écoulé depuis la dernière tentative LoRa

    unsigned long currentTime = millis();
    unsigned long wakeUpDelay = (unsigned long)(config.intervalle_lora_secondes * 0.75 * 1000UL);  // en ms
    if (currentTime - lastAttempt >= wakeUpDelay) {

        std::queue<String> receiveQueue;
        lora.startLoRa();

        // Réception des paquets via LoRa
        uint8_t deviceId = 0;
        if (lora.handshake(deviceId)) {
            Serial.println("Handshake réussi. Réception des paquets...");
            int last = lora.receivePackets(receiveQueue);
            lora.closeSession(last);
            lora.stopLoRa();

            // Met à jour le temps de la dernière tentative de réception
            lastAttempt = millis() ;

            // Transfert vers la queue globale
            while (!receiveQueue.empty()) {
                sendingQueue.push(receiveQueue.front());
                receiveQueue.pop();
            }

            // Envoi via LoRaWAN si intervalle complet atteint
            if (currentTime - lastLoraSend >= (unsigned long)config.intervalle_lora_secondes*1000UL) {
                if (loraWAN.begin(config.appEui, config.appKey)) {
                    Serial.print("Envoi de ");
                    Serial.print(sendingQueue.size());
                    

                    if (loraWAN.sendQueue(sendingQueue)) {
                        Serial.println("Tous les paquets ont été envoyés !");
                    } else {
                        Serial.println("Certains paquets n’ont pas pu être envoyés, ils seront réessayés.");
                    }
                } else {
                    Serial.println("Connexion LoRaWAN impossible, report de l’envoi.");
                }
                lastLoraSend = currentTime;
            }

        } else {
            Serial.println("Handshake échoué, aucune donnée reçue.");
            lora.stopLoRa();

            // Met quand même à jour lastAttempt pour réessayer après 3/4 du temps
            lastAttempt = millis() ;
        }

        Serial.println("Relais en veille jusqu’à la prochaine fenêtre de communication...");
    }

    // Calcule le temps restant avant le prochain réveil (non bloquant)
    unsigned long nextWakeUp = wakeUpDelay - (currentTime - lastAttempt);
    if ((long)nextWakeUp < 0) nextWakeUp = 0; // sécurité si dépassement

    waiter.sleepUntil(nextWakeUp);
}


