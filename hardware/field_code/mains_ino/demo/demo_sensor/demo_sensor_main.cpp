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
#include "Memory_monitor.cpp"

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
int ncapt = 0; 

// LoRa
LoraCommunication lora(868E6, 0x01, 0x02, RoleType::SLAVE);
long lastLoRaSend = 0;
long lastMeasure = 0;
long lastSDOffset = 0;
std::queue<String> sendQueue;

uint16_t newMeasureInterval = 0;
uint16_t newLoraInterval = 0;

const long sec_in_day = 86400;


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
    long end_date = millis() + 5000;
    while (!Serial && millis() < end_date) {}
    
    DEBUG_LOG("\n\n\n\n");
    DEBUG_LOG("memory when setup started : " + String(freeMemory()));
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
    for (auto & _c : liste_capteurs) {
        ncapt++;
    }
    // Allocation dynamique
    sens = new Sensor*[ncapt];
    toute_mesure = new double[ncapt];

    // Initialisation des capteurs
    int it = 0;
    for (int it = 0; it<ncapt; it++) {
        SensorConfig _c = liste_capteurs[it];
        sens[it] = new Sensor(_c.pin, 1, _c.type_capteur, _c.id_box);
        DEBUG_LOG("inserted new Sensor ptr at position " + String(it) + " of sens with attributes :");
        DEBUG_LOG("_c.pin : " + String(_c.pin) + "  _c.type_capteur : " + String(_c.type_capteur) + "  _c.id_box : " + String(_c.id_box) + "\n\n");
        toute_mesure[it] = 0;
    }
    DEBUG_LOG("sens contains " + String(it) + " elements");

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
    #ifdef DEBUG_MAIN
    // Asses the good shape of sens. The issue is : sens contains pointers, which may raise seg fault if not initialised properly
    DEBUG_LOG ("starting sens debug loop");
    for (int it = 0; it<ncapt; it++){
     sens[it]->get_voltage();   
    DEBUG_LOG("sens [" + String(it) + "] voltage exists");
    }
    DEBUG_LOG("loop complete, sens seems fine");

    String date = GetCurrentDate();
    DEBUG_LOG("GetCurrentDate finished in main_debug");
    String hour = GetCurrentHour();
    DEBUG_LOG("GetCurrentHour finished in main_debug");
    DEBUG_LOG(String(ncapt));
    DEBUG_LOG("debug messages still work1");
    DEBUG_LOG("Heure actuelle : " + hour);
    DEBUG_LOG("debug messages still work2");
    
    #endif
    
    
    // --- Prendre mesures ---
    long current_Time=GetSecondsSinceMidnight();
    DEBUG_LOG("Temps actuel : " + String(current_Time));
    bool IsTimeToMeasure = ((current_Time - lastMeasure) >= (intervalle_de_mesure_secondes - 1));
    
    DEBUG_LOG("ncapt : " + String(ncapt));//so far

    if (IsTimeToMeasure) {
        DEBUG_LOG("starting measurement process");
        DEBUG_LOG("memory before things break : " + String(freeMemory()));
        for (int it = 0; it<ncapt; it++) {
            double v = sens[it]->get_voltage();
            DEBUG_LOG("voltage preleved");
            toute_mesure[ncapt] = v;
            DEBUG_LOG("value written in toute_mesure");
            //delay(500);//decreased for demo version
            DEBUG_LOG("memory after " + String(it+1) + " iterations : " + freeMemory());
        }
        lastMeasure = current_Time;
        DEBUG_LOG("Voltage recording finished");
    }

    
    // --- Stocker sur SD ---
    DEBUG_LOG("launch LogData");
    logger.LogData(ncapt, toute_mesure);
    DEBUG_LOG("LogData instruction done");
    // --- Envoyer LoRa si intervalle atteint ---
    
    bool IsTimeToLoRa = ((current_Time - lastLoRaSend) >= (lora_intervalle_secondes - 1));//set to 1 for demo instead

    if (IsTimeToLoRa || rattrapage) {
        lora.startLoRa();

        File dataFile = SD.open(filename, FILE_READ);
        if (!dataFile) {
            DEBUG_LOG("Impossible d'ouvrir le fichier de données pour LoRa");
            lora.closeSession(0);
            return;
        }

        dataFile.seek(lastSDOffset);

        while (CalculateSleepTimeUntilNextMeasurement(lastMeasure, intervalle_de_mesure_secondes) > 60000UL && dataFile.available()) {

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
                    DEBUG_LOG("Packet successfully sent");
                    lastSDOffset = dataFile.position();
                    break;

                } else {
                    DEBUG_LOG("Attempt n " + String(attempt) +" failed");
                    if (attempt < 3) delay(1000);//delay significally reduced for demo version
                }
            }

            rattrapage = dataFile.available();
            
        } // <-- fermeture du while !

        dataFile.close();
        lora.closeSession(0);
        lastLoRaSend = current_Time;

        // --- Réception éventuelle de mise à jour config ---
        DEBUG_LOG("Vérification de mise à jour descendante...");
        lora.startLoRa();
        if (lora.receiveConfigUpdate(configFilePath)) {

            DEBUG_LOG("Mise à jour config reçue du master.");

            updateConfigFile(newMeasureInterval, newLoraInterval);

            // On met à jour les variables déjà existantes dans le programme :
            lora_intervalle_secondes = newLoraInterval;

        } else {
            DEBUG_LOG("Pas de mise à jour reçue.");
        }
        lora.stopLoRa();
    }
    // --- Sommeil jusqu'à prochaine mesure ---
    pinMode(LED_BUILTIN, INPUT_PULLDOWN);
    Waiter waiter;

    if (CalculateSleepTimeUntilNextMeasurement(lastMeasure, intervalle_de_mesure_secondes) <= CalculateSleepTimeUntilNextCommunication(lastLoRaSend, lora_intervalle_secondes)){
        DEBUG_LOG('sleeping until next measure, sleeping for ' + String (CalculateSleepTimeUntilNextMeasurement(lastMeasure, intervalle_de_mesure_secondes)*1000UL));
        waiter.sleepUntil(CalculateSleepTimeUntilNextMeasurement(lastMeasure, intervalle_de_mesure_secondes));
    } else {
        DEBUG_LOG('sleeping until next communication ' + String (CalculateSleepTimeUntilNextCommunication(lastLoRaSend, lora_intervalle_secondes)*1000UL));
        waiter.sleepUntil(CalculateSleepTimeUntilNextCommunication(lastLoRaSend, lora_intervalle_secondes));
    }
    // Prevent time variables (current_time) to diverge (time domain is 24 hours, to preserve coherence with GetSecondsSinceMidnight)
    
    if(current_Time >= sec_in_day){
        lastLoRaSend -= current_Time;
        lastMeasure -= current_Time;
        current_Time = 0;
    }
}