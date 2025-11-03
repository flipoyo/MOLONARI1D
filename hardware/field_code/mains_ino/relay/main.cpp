#include <Arduino.h>
#include <SD.h>
#include <queue>
#include "ArduinoLowPower.h"
#include <MKRWAN.h>

#include "LoRaWan_Molonari.hpp"
#include "LoRa_Molonari.hpp"
#include "Waiter.hpp"
#include "Reader.hpp"
#include "Time.hpp"


#define DEBUG_MAIN
#define DEBUG_MEASURE
#define DEBUG_WRITER
#define DEBUG_READER

#ifdef DEBUG_MAIN
#define DEBUG_LOG(msg) Serial.println(msg)
#define DEBUG_LOG_NO_LN(msg) Serial.print(msg)
#else
#define DEBUG_LOG(msg)
#define DEBUG_LOG_NO_LN(msg)
#endif


LoRaModem modem;



LoraWANCommunication loraWAN;
std::queue<String> sendingQueue;



GeneralConfig res;

unsigned long lastLoraSend = 0;
unsigned long lastAttempt = 0;

String appEui;
String devEui;
LoraCommunication lora(868E6, devEui, appEui, MASTER);
bool modif = false;
int CSPin = 5; // Pin CS par défaut

const char* configFilePath = "conf_rel.csv";

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
    res=reader.lireConfigCSV("conf.csv", CSPin);
    Serial.println("Configuration chargée.");

    // Initialisation LoRa communication
    lora = LoraCommunication(res.int_config.lora_intervalle_secondes, res.rel_config.appEui, res.rel_config.devEui, RoleType::MASTER);

    // Vérification SD
    if (!SD.begin(res.rel_config.CSPin)) {
        Serial.println("Erreur SD - arrêt système.");
        while (true) {}
    }

    Serial.println("Initialisation terminée !");
    pinMode(LED_BUILTIN, INPUT_PULLDOWN);

    digitalWrite(LED_BUILTIN, LOW);
}

// ----- Loop -----
void loop() {
    static unsigned long lastAttempt = 0; // mémorise la dernière tentative de réception (en millisecondes)
    static Waiter waiter; //pour ne pas l'indenter dans le loop
    
    unsigned long currentTime = GetSecondsSinceMidnight();
    DEBUG_LOG("Intervalle restant pour agir :"+ String(currentTime - lastAttempt) + " / " + String(res.int_config.lora_intervalle_secondes));
    if (currentTime - lastAttempt >= 2) { //res.int_config.lora_intervalle_secondes en vrai, change pour les besoins du test
        DEBUG_LOG("Fenêtre de communication LoRa atteinte, tentative de réception des paquets...");

        std::queue<String> receiveQueue;
        lora.startLoRa();

        // Réception des paquets via LoRa
        uint8_t deviceId = 0;
        if (lora.handshake(deviceId)) {
            Serial.println("Handshake réussi. Réception des paquets...");
            int last = lora.receivePackets(receiveQueue);
            lora.closeSession(last);

            // Met à jour le temps de la dernière tentative de réception
            lastAttempt = GetSecondsSinceMidnight();

            //envoie du csv
            if (modif==true) {
                File config = SD.open(configFilePath, FILE_READ);
                config.seek(0);

                while (config.available()) {
                    std::queue<String> line_config;
                    line_config.push(config.readStringUntil('\n'));
                    
                for (int attempt = 1; attempt <= 3; attempt++) {

                    if (lora.sendPackets(line_config)) {
                        break;

                    } else {
                        if (attempt < 3) delay(20000);
                        }
                    }
                }   
                modif = false;
            }

            lora.stopLoRa();

            // Transfert vers la queue globale
            while (!receiveQueue.empty()) {
                sendingQueue.push(receiveQueue.front());
                receiveQueue.pop();
            }

            // Envoi via LoRaWAN si intervalle complet atteint

            appEui=res.rel_config.appEui;
            devEui=res.rel_config.devEui;
            

            if (loraWAN.begin(appEui, devEui)) {
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

            // Met quand même à jour lastAttempt pour réessayer après l'intervalle de temps
            lastAttempt = GetSecondsSinceMidnight();
        }

        // reception csv et modification
        while (modem.available()) {
            loraWAN.receiveConfig(configFilePath, modif);
            modif = true;
        }

        Serial.println("Relais en veille jusqu’à la prochaine fenêtre de communication...");

    // Calcule le temps restant avant le prochain réveil (non bloquant)
    unsigned long nextWakeUp = res.int_config.lora_intervalle_secondes * 1000UL - (currentTime - lastAttempt);
    if ((long)nextWakeUp < 0) nextWakeUp = 0; // sécurité si dépassement

    LowPower.idle();

}


