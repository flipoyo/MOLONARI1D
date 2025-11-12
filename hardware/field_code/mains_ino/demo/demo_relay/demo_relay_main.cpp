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
#include "Writer.hpp"


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
Writer logger;

GeneralConfig res;

long lastLoraSend = 0;
long lastAttempt = 0;// mémorise la dernière tentative de réception (en millisecondes)

String appEui;
String devEui;
String appKey;
LoraCommunication lora(868E6, devEui, appEui, RoleType::MASTER);
bool modif = false;
int CSPin = 5; // Pin CS par défaut

const char* configFilePath = "conf.csv";

Waiter waiter; //pour ne pas l'indenter dans le loop
unsigned long lastSDOffsetConfig = 0;
unsigned long lastSDOffset = 0;
const char filename[] = "RECORDS.CSV";


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
    res = reader.lireConfigCSV("conf.csv", CSPin);
    Serial.println("Configuration chargée.");

    // Initialisation LoRa communication
    lora.LoraUpdateAttributes(868E6, res.rel_config.appEui, res.rel_config.devEui, RoleType::MASTER);

    // Vérification SD
    if (!SD.begin(res.rel_config.CSPin)) {
        Serial.println("Erreur SD - arrêt système.");
        while (true) {}
    }

    InitialiseRTC();
    logger.EstablishConnection(CSPin);

    Serial.println("Initialisation terminée !");
    pinMode(LED_BUILTIN, INPUT_PULLDOWN);
    digitalWrite(LED_BUILTIN, LOW);
}


// ----- Loop -----
void loop() {
    long currentTime = GetSecondsSinceMidnight();
    
    if (currentTime - lastAttempt >= 2) {
        DEBUG_LOG("Réveil du relais pour vérification communication LoRa...");
        DEBUG_LOG("Fenêtre de communication LoRa atteinte, tentative de réception des paquets...");
        std::queue<String> receiveQueue;
        lora.startLoRa();

        // Réception des paquets via LoRa
        uint8_t deviceId = 0; // initialise avec packetNumber = 0 
        if (lora.handshake(deviceId)) {

            DEBUG_LOG("Handshake réussi. Réception des paquets...");
            int last = lora.receiveAllPackets(receiveQueue);
            lora.sendPacket(last, FIN, "FIN"); // Répond par un FIN de confirmation;

            // Met à jour le temps de la dernière tentative de réception
            lastAttempt = GetSecondsSinceMidnight();

            //envoie du csv
            if (modif==true) { // normalement modif est toujours false pour l'instant : la focntion de modif n'est pa sbien implémentée
                File config = SD.open(configFilePath, FILE_READ);
                config.seek(lastSDOffsetConfig);
                std::queue<memory_line> lines_config;

                while (config.available()) {
                    memory_line new_line = memory_line(config.readStringUntil('\n'), config.position());
                    lines_config.push(new_line);
                        uint8_t lastPacket = lora.sendAllPacketsAndManageMemory(lines_config, lastSDOffsetConfig, config);
                        lora.closeSession(lastPacket);

                        modif = !(lastSDOffsetConfig == config.position());
                }
            }
            lora.stopLoRa();
            

            logger.LogString(receiveQueue);
        } else {
            Serial.println("Handshake échoué, aucune donnée reçue.");
            lora.stopLoRa();

            // Met quand même à jour lastAttempt pour réessayer après l'intervalle de temps
            lastAttempt = GetSecondsSinceMidnight();
        }

        // Envoi via LoRaWAN si intervalle complet atteint

        File dataFile = SD.open(filename, FILE_READ);
        DEBUG_LOG("File has been opened");

        if (!dataFile) {
            DEBUG_LOG("Impossible d'ouvrir le fichier de données pour LoRa");
            return;
        }

        if (loraWAN.begin(res.rel_config.appEui, res.rel_config.appKey)) {
            Serial.println("appKey : " + String(res.rel_config.appKey));
            Serial.println("temps avant communication : " + String(CalculateSleepTimeUntilNextCommunication(lastAttempt, res.int_config.lora_intervalle_secondes)));


            while (CalculateSleepTimeUntilNextCommunication(lastAttempt, res.int_config.lora_intervalle_secondes) > 1000 && dataFile.available()) { //racourcir de 60000 à 10000 pour les besoins de la démo
                //at this point, lastSDOffset must point to the first memory address of the first line to be sent
                DEBUG_LOG("entrée dans le while d'envoi LoRaWAN");
                std::queue<memory_line> linesToSend;
                while (dataFile.available()) {
                    DEBUG_LOG("lecture d'une nouvelle ligne dans le fichier");
                    DEBUG_LOG("data file until espace : " + dataFile.readStringUntil('\n'));
                    memory_line new_line = memory_line(dataFile.readStringUntil('\n'), dataFile.position());
                    DEBUG_LOG(String("new line: ") + new_line.flush);
                    linesToSend.push(new_line);

                // Si la ligne est vide aka plus rien à envoyer
                    if (new_line.flush.length() == 0) {
                        break;
                    }
                }
                int end_document_address = dataFile.position(); // cette ligne ne sert à rien  
                if (loraWAN.sendAllPacketsAndManageMemoryWAN(linesToSend, lastSDOffset, dataFile)) {
                    Serial.println("Tous les paquets ont été envoyés !");
                } else {
                    Serial.println("Certains paquets n’ont pas pu être envoyés, ils seront réessayés.");
                }
            }    

            dataFile.close();

        } else {
            Serial.println("Connexion LoRaWAN impossible, report de l’envoi.");
        }
        lastLoraSend = currentTime;
    
        DEBUG_LOG("about to loop on modem.available()");
        // reception csv et modification
        while (modem.available()) {
            loraWAN.receiveConfig(configFilePath, modif);
            modif = true;
        }

    DEBUG_LOG("Relais en veille jusqu’à la prochaine fenêtre de communication...");
    //delay(500) pas de dodo pour la démo
    }
}






