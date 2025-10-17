#include <Arduino.h>
#include <SD.h>
#include <queue>

#include "LoRaWan_Molonari.hpp"
#include "LoRa_Molonari.hpp"
#include "Waiter.hpp"

// ----- Structures -----
struct ConfigRelais {
    String appEui;
    String appKey;
    int CSPin;
    int lora_freq;
    int lora_intervalle_secondes;
};

// ----- Variables globales -----
ConfigRelais config = {"0000000000000000", "72C5FBBF2AB954D3316A1EE13AA3F141", 5, 868E6, 900}; // valeurs par défaut
LoraCommunication lora(868E6, 0xAA, 0xFF, RoleType::MASTER); //regler les problemes !
LoraWANCommunication loraWAN;
std::queue<String> sendingQueue;

unsigned long lastLoraSend = 0;

// ----- Lecture CSV -----
void lireConfigCSV(const char* NomFichier) {
    if (!SD.begin(config.CSPin)) {
        Serial.println("Impossible de monter SD");
        return;
    }

    File f = SD.open(NomFichier);
    if (!f) {
        Serial.println("Fichier CSV non trouvé, utilisation des valeurs par défaut");
        return;
    }

    while (f.available()) {
        String line = f.readStringUntil('\n');
        line.trim();
        if (line.length() == 0 || line.startsWith("#")) continue;

        int idx = line.indexOf(',');
        if (idx < 0) continue;
        String key = line.substring(0, idx);
        String val = line.substring(idx + 1);

        if (key == "appEui") config.appEui = val;
        else if (key == "appKey") config.appKey = val;
        else if (key == "CSPin") config.CSPin = val.toInt();
        else if (key == "lora_freq") config.lora_freq = val.toInt();
        else if (key == "lora_intervalle_secondes") config.lora_intervalle_secondes = val.toInt();
    }
    f.close();
}

// ----- Setup -----
void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);

    Serial.begin(115200);
    unsigned long end_date = millis() + 5000;
    while (!Serial && millis() < end_date) {}

    Serial.println("\n=== Initialisation du Relais Molonari ===");

    // Lecture configuration CSV
    lireConfigCSV("relay_config.csv");
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
    unsigned long wakeUpDelay = (unsigned long)(config.lora_intervalle_secondes * 0.75 * 1000);
    //tout en ms pour le waiter


    unsigned long currentTime = millis();
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
            lastAttempt = millis() / 1000;

            // Transfert vers la queue globale
            while (!receiveQueue.empty()) {
                sendingQueue.push(receiveQueue.front());
                receiveQueue.pop();
            }

            // Envoi via LoRaWAN si intervalle complet atteint
            if (currentTime - lastLoraSend >= (unsigned long)config.lora_intervalle_secondes) {
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

