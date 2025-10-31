#include <queue>
#include <vector>
#include <Arduino.h>
#include <SD.h>
#include <LoRa.h>
#include <string>
#include <ArduinoLowPower.h>

#include "Measure.hpp"
#include "Writer.hpp"
#include "LoRa_Molonari.hpp"
#include "Time.hpp"
#include "Waiter.hpp"
#include "Reader.hpp"

// define DEBUG_LOG
#ifndef DEBUG_LOG
#define DEBUG_LOG(msg) Serial.println(msg)
#endif
Sensor** sens;
double *toute_mesure;


GeneralConfig config;
std::vector<SensorConfig> liste_capteurs;
int lora_intervalle_secondes;
int intervalle_de_mesure_secondes;

//std::string FileName = "conf_sen.csv"; Impossible to use that because SD.open() takes squid string arguments
Writer logger;
const int CSPin = 5;
const char filename[] = "RECORDS.CSV";
const char* configFilePath = "/config_sensor.csv";

// LoRa
LoraCommunication lora(868E6, 0x01, 0x02, RoleType::SLAVE);
unsigned long lastLoRaSend = 0;
unsigned long lastMeasure = 0;
unsigned long lastSDOffset = 0;
std::queue<String> sendQueue;

uint16_t newMeasureInterval = 0;
uint16_t newLoraInterval = 0;


void updateConfigFile(uint16_t measureInterval, uint16_t loraInterval) {

    File file = SD.open("/conf_sen.csv", FILE_READ);
    if (!file) {
        Serial.println("ERREUR : impossible de lire conf_sen.csv");
        return;
    }

    std::vector<String> lignes;
    while (file.available()) {
        lignes.push_back(file.readStringUntil('\n'));
    }
    file.close();

    for (auto &ligne : lignes) {
        if (ligne.startsWith("intervalle_de_mesure_secondes")) {
            ligne = "intervalle_de_mesure_secondes," + String(measureInterval);
        }
        else if (ligne.startsWith("intervalle_lora_secondes")) {
            ligne = "intervalle_lora_secondes," + String(loraInterval);
        }
    }
    
    file = SD.open("/conf_sen.csv", FILE_WRITE | O_TRUNC);
    if (!file) {
        Serial.println("ERREUR : impossible d'écrire conf_sen.csv");
        return;
    }

    for (auto &ligne : lignes) {
        file.println(ligne);
    }

    file.close();
    Serial.println("Fichier conf_sen.csv mis à jour sans toucher aux autres paramètres.");
}

bool rattrapage = false;

// ----- Setup -----
void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);

    Serial.begin(115200);
    unsigned long end_date = millis() + 5000;
    while (!Serial && millis() < end_date) {}

    DEBUG_LOG("\n\n\n\n");
    // Lecture de la configuration CSV
    Reader reader;

    GeneralConfig temp_config_container = reader.lireConfigCSV("conf_sen.csv", CSPin);
    IntervallConfig int_conf = temp_config_container.int_config;
    
    liste_capteurs = temp_config_container.liste_capteurs;
    lora_intervalle_secondes = int_conf.lora_intervalle_secondes;
    intervalle_de_mesure_secondes = int_conf.intervalle_de_mesure_secondes;

    if (temp_config_container.succes){
        DEBUG_LOG("lecture config terminée avec succès");
    }
    else {
        DEBUG_LOG("échec de la lecture du fichier config");
    }


    // Compter les capteurs
    int ncapteur = 0; 
    for (auto & _c : liste_capteurs) {
        ncapteur++;
    }
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
    DEBUG_LOG ("Setup finished");
}

// ----- Loop -----
void loop() {
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);

    // --- Prendre mesures ---
    unsigned long current_Time=GetSecondsSinceMidnight();
    bool IsTimeToMeasure = ((current_Time - lastMeasure) >= (intervalle_de_mesure_secondes));

    int ncapt = 0;

    if (IsTimeToMeasure) {
        for (auto &c : liste_capteurs) {
            toute_mesure[ncapt] = sens[ncapt]->get_voltage();
            ncapt++;
            delay(2000);
        }
        lastMeasure = current_Time;
    }

    DEBUG_LOG(ncapt);//so far so good
    
    // --- Stocker sur SD ---
    logger.LogData(ncapt, toute_mesure);
  // --- Envoyer LoRa si intervalle atteint ---

    // --- Envoyer LoRa si intervalle atteint ---
    
    bool IsTimeToLoRa = ((current_Time - lastLoRaSend) >= (lora_intervalle_secondes - 180UL));

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
        lastLoRaSend = current_Time;

        // --- Réception éventuelle de mise à jour config ---
        Serial.println("Vérification de mise à jour descendante...");
        lora.startLoRa();
        if (lora.receiveConfigUpdate(configFilePath)) {

            Serial.println("Mise à jour config reçue du master.");

            updateConfigFile(newMeasureInterval, newLoraInterval);

            // On met à jour les variables déjà existantes dans le programme :
            lora_intervalle_secondes = newLoraInterval;

        } else {
            Serial.println("Pas de mise à jour reçue.");
        }
        lora.stopLoRa();
    }
    // --- Sommeil jusqu'à prochaine mesure ---
    pinMode(LED_BUILTIN, INPUT_PULLDOWN);
    Waiter waiter;

    if (CalculateSleepTimeUntilNextMeasurement() <= CalculateSleepTimeUntilNextCommunication()){
        waiter.sleepUntil(CalculateSleepTimeUntilNextMeasurement());
    } else {
        waiter.sleepUntil(CalculateSleepTimeUntilNextCommunication());
    }
    
}