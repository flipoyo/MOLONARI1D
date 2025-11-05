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

long lastLoraSend = 0;
long lastAttempt = 0;// mémorise la dernière tentative de réception (en millisecondes)

String appEui;
String devEui;
LoraCommunication lora(868E6, devEui, appEui, RoleType::MASTER);
bool modif = false;
int CSPin = 5; // Pin CS par défaut

const char* configFilePath = "conf_rel.csv";

Waiter waiter; //pour ne pas l'indenter dans le loop
unsigned long lastSDOffset = 0;


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
    lora.LoraUpdateAttributes(868E6, res.rel_config.appEui, res.rel_config.devEui, RoleType::MASTER);

    // Vérification SD
    if (!SD.begin(res.rel_config.CSPin)) {
        Serial.println("Erreur SD - arrêt système.");
        while (true) {}
    }
    InitialiseRTC();

    Serial.println("Initialisation terminée !");
    pinMode(LED_BUILTIN, INPUT_PULLDOWN);
    digitalWrite(LED_BUILTIN, LOW);
}


// ----- Loop -----
void loop() {
    long currentTime = GetSecondsSinceMidnight();
    
    if (currentTime - lastAttempt >= 2) { //res.int_config.lora_intervalle_secondes
        DEBUG_LOG("Réveil du relais pour vérification communication LoRa...");
        DEBUG_LOG("Fenêtre de communication LoRa atteinte, tentative de réception des paquets...");
        std::queue<String> receiveQueue;
        lora.startLoRa();

        // Réception des paquets via LoRa
        uint8_t deviceId = 0; // initialise avec packetNumber = 0 
        if (lora.handshake(deviceId)) {

            DEBUG_LOG("Handshake réussi. Réception des paquets...");
            int last = lora.receivePackets(receiveQueue);
            lora.sendPacket(last, FIN, ""); // Répond par un FIN de confirmation;

            // Met à jour le temps de la dernière tentative de réception
            lastAttempt = GetSecondsSinceMidnight();

            //envoie du csv
            if (modif==true) { // normalement modif est toujours false pour l'instant : la focntion de modif n'est pa sbien implémentée
                File config = SD.open(configFilePath, FILE_READ);
                config.seek(lastSDOffset);
                std::queue<memory_line> lines_config;

                while (config.available()) {
                    memory_line new_line = memory_line(config.readStringUntil('\n'), config.position());
                    lines_config.push(new_line);
                    
                        uint8_t lastPacket = lora.sendAllPacketsAndManageMemory(lines_config, lastSDOffset, config);
                        lora.closeSession(lastPacket);

                        modif = !(lastSDOffset == config.position());
                }

                lora.stopLoRa();

                // Transfert vers la queue globale
                while (!receiveQueue.empty()) {
                    sendingQueue.push(receiveQueue.front());
                    receiveQueue.pop();
                }

                // Envoi via LoRaWAN si intervalle complet atteint
            

                if (loraWAN.begin(res.rel_config.appEui, res.rel_config.devEui)) {
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
    }
    
    DEBUG_LOG("about to loop on modem.available()");
    // reception csv et modification
    while (modem.available()) {
        loraWAN.receiveConfig(configFilePath, modif);
        modif = true;
    }

    DEBUG_LOG("Relais en veille jusqu’à la prochaine fenêtre de communication...");

    // Calcule le temps restant avant le prochain réveil (non bloquant)
    lastAttempt=GetSecondsSinceMidnight();
    
    /*
    long time_to_sleep = CalculateSleepTimeUntilNextCommunication(lastAttempt, lora_intervalle_secondes); 
    DEBUG_LOG("sleeping until next communication " + String (time_to_sleep) + "ms");
    LowPower.idle(time_to_sleep);
    */
    delay(5000);
}






