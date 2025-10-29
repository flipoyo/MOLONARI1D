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

// Capteurs
Sensor** sens;
double *toute_mesure;

// Logger
Writer logger;
const int CSPin = 5;
const char filename[] = "RECORDS.CSV";
const char* configFilePath = "/config_sensor.csv";

// LoRa
LoraCommunication lora(868E6, 0x01, 0x02, RoleType::SLAVE);
unsigned long lastLoRaSend = 0;
unsigned long lastSDOffset = 0;
std::queue<String> sendQueue;

static bool rattrapage = false;

// ----- Setup -----
void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);

    Serial.begin(115200);
    unsigned long end_date = millis() + 5000;
    while (!Serial && millis() < end_date) {}

    // Initialisation SD
    if (!SD.begin(CSPin)) {
        Serial.println("Impossible d'initialiser la SD");
        while(true) {}
    }


    // --- Charger la configuration ---
    Reader reader;
    reader.lireConfigCSV(configFilePath);


    // Compter les capteurs
    int ncapteur = 0;
    for (auto & _c : liste_capteurs) ncapteur++;

    // Allocation dynamique
    sens = new Sensor*[ncapteur];
    toute_mesure = new double[ncapteur];

    // Initialisation des capteurs
    int it = 0;
    for (const auto & _c : liste_capteurs) {
        sens[it] = new Sensor(_c.pin, 1, _c.type_capteur, _c.id_box);
        toute_mesure[it] = 0;
        it++;
    }

    // Initialisation SD et logger
    if (!SD.begin(CSPin)) { while(true) {} }
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
        delay(2000);
    }

    // --- Stocker sur SD ---
    logger.LogData(ncapt, toute_mesure);

    // --- Envoyer LoRa si intervalle atteint ou s'il faut rattraper du retard d'envoi ---
    unsigned long currentTime = GetSecondsSinceMidnight();
    LORA_INTERVAL_S = config.intervalle_lora_secondes;
    bool IsTimeToLoRa = (currentTime - lastLoRaSend >= LORA_INTERVAL_S);
     if (IsTimeToLoRa || rattrapage) {
        lora.startLoRa();

        File dataFile = SD.open(filename, FILE_READ);
        if (!dataFile) {
            Serial.println("Impossible d'ouvrir le fichier de données pour LoRa");
            lora.closeSession(0);
            return;
        }

        dataFile.seek(lastSDOffset);

        while (CalculateSleepTimeUntilNextMeasurement() > 60UL && dataFile.available()) {

            std::queue<String> lineToSend;
            lineToSend.push(dataFile.readStringUntil('\n'));

            // S'il n'y a plus rien à envoyer
            if (lineToSend.front().length() == 0) {
                rattrapage = false;
                break;
            }

            // Tentative d'envoi 3 fois
            for (int attempt = 1; attempt <= 3; attempt++) {

                if (lora.sendPackets(lineToSend)) {
                    lastSDOffset = dataFile.position();
                    break;

                } else {
                    Serial.println(attempt);
                    if (attempt < 3) delay(20000);
                }
            }

            rattrapage = dataFile.available();
            
        } // <-- fermeture du while !

        dataFile.close();
        lora.closeSession(0);
        lastLoRaSend = currentTime;

        // --- Réception éventuelle de mise à jour config ---
        Serial.println("Vérification de mise à jour descendante...");
        lora.startLoRa();
        if (lora.receiveConfigUpdate(configFilePath)) {
            Serial.println("Nouvelle configuration reçue et enregistrée !");
            Reader reader;
            reader.lireConfigCSV(configFilePath);
            RefreshConfigFromFile();
        } else {
            Serial.println("Pas de mise à jour reçue.");
        }
        lora.stopLoRa();
    }
    // --- Sommeil jusqu'à prochaine mesure ---
    pinMode(LED_BUILTIN, INPUT_PULLDOWN);
    Waiter waiter;
    waiter.sleepUntil(CalculateSleepTimeUntilNextMeasurement());
}