#include <queue>
#include <vector>
#include <Arduino.h>
#include <SD.h>
#include <LoRa.h>
#include <ArduinoLowPower.h>

#include "Measure.hpp"
#include "Writer.hpp"
#include "LoRa_Molonari.hpp"
#include "Time.hpp"
#include "Waiter.hpp"
#include "Reader.hpp"


int LORA_INTERVAL_H = 3;//initialisation par défaut

Sensor** sens;
double *toute_mesure;

Writer logger;
const int CSPin = 5;
const char filename[] = "RECORDS.CSV";

LoraCommunication lora(868E6, 0x01, 0x02, RoleType::SLAVE); // fréquence, adresse locale, adresse distante
unsigned long lastLoRaSend = 0;
unsigned long lastSDOffset = 0;
std::queue<String> sendQueue;



// ----- Setup -----
void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);

    Serial.begin(115200);
    unsigned long end_date = millis() + 5000;
    while (!Serial && millis() < end_date) {}

    // Lecture de la configuration CSV
    Reader reader;
    reader.lireConfigCSV("config_sensor.csv");
    Serial.println("Configuration chargée.");

    // Compter les capteurs
    int ncapteur = 0; 
    for (auto &c : liste_capteurs) {
        ncapteur++;
    }

    // Allocation dynamique
    sens = new Sensor*[ncapteur];
    toute_mesure = new double[ncapteur];

    // Initialisation des capteurs
    int it = 0;
    for (auto &c : liste_capteurs) {
        sens[it] = new Sensor(c.pin, 1, c.offset, c.scale, c.type);
        toute_mesure[it] = 0;
        it++;
    }

    // Initialisation SD et logger
    if (!SD.begin(CSPin)) { while(true){} }
    logger.EstablishConnection(CSPin);
    InitialiseRTC();

    pinMode(LED_BUILTIN, INPUT_PULLDOWN);
}

// ----- Loop -----

void loop() {
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);

    // --- Prendre mesures ---
    int ncapt = 0;
    for (auto &c : liste_capteurs) {
        toute_mesure[ncapt] = sens[ncapt]->Measure();
        ncapt++;
        }
    
    // --- Stocker sur SD ---
    logger.LogData(ncapt, toute_mesure); // LogData est dans writer

    // --- Envoyer LoRa si intervalle atteint ---
    unsigned long current_Time=GetSecondsSinceMidnight();
    if (current_Time - lastLoRaSend >= LORA_INTERVAL_S) {
        lora.startLoRa();

        // Lire nouvelles lignes depuis SD
        File dataFile = SD.open("RECORDS.CSV", FILE_READ);
        if (dataFile) {
            dataFile.seek(lastSDOffset);
            while (dataFile.available()) {
                String line = dataFile.readStringUntil('\n');
                if (line.length() > 0) sendQueue.push(line);
            }
            unsigned long currentOffset = dataFile.position();
            dataFile.close();

            uint8_t shift = 0;
            if (lora.handshake(shift)) {
                if (!sendQueue.empty()) {
                    lora.sendPackets(sendQueue);  // vidée seulement après ACK
                    lora.closeSession(0);
                }
                lastSDOffset = currentOffset; // mise à jour après succès
            } else {
                Serial.println("Handshake LoRa échoué, données non envoyées.");
            }
        } else {
            Serial.println("Impossible d'ouvrir RECORDS.CSV");
        }

        lora.stopLoRa();
        lastLoRaSend = current_Time;
    }

    // --- Sommeil jusqu'à prochaine mesure ---
    pinMode(LED_BUILTIN, INPUT_PULLDOWN);
    Waiter waiter;
    unsigned long sleepTime = CalculateSleepTimeUntilNextMeasurement();
    waiter.sleepUntil(sleepTime);
}

