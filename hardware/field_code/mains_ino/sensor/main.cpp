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
std::vector<double> toute_mesure;

GeneralConfig config;
std::vector<SensorConfig> liste_capteurs;
int lora_intervalle_secondes;
int intervalle_de_mesure_secondes;
String devEui;
String appEui;


//std::string FileName = "conf_sen.csv"; Impossible to use that because SD.open() takes squid string arguments
Writer logger;
const int CSPin = 5;
const char filename[] = "RECORDS.CSV";
const char* configFilePath = "conf.csv";
int ncapt = 0; 

// LoRa
LoraCommunication lora(868E6, devEui, appEui, MASTER);
long lastLoRaSend = 0;
long lastMeasure = 0;
long lastSDOffset = 0;
std::queue<String> sendQueue;

uint16_t newMeasureInterval = 0;
uint16_t newLoraInterval = 0;

const long sec_in_day = 86400;


void updateConfigFile(uint16_t measureInterval, uint16_t loraInterval) {

    File file = SD.open("conf.csv", FILE_READ);
    if (!file) {
        Serial.println("ERREUR : impossible de lire conf.csv");
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
    
    file = SD.open("conf.csv", FILE_WRITE | O_TRUNC);
    if (!file) {
        Serial.println("ERREUR : impossible d'écrire conf.csv");
        return;
    }

    for (auto &ligne : lignes) {
        file.println(ligne);
    }

    file.close();
    Serial.println("Fichier conf.csv mis à jour sans toucher aux autres paramètres.");
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

    GeneralConfig temp_config_container = reader.lireConfigCSV("conf.csv", CSPin);
    IntervallConfig int_conf = temp_config_container.int_config;
    
    liste_capteurs = temp_config_container.liste_capteurs;
    lora_intervalle_secondes = int_conf.lora_intervalle_secondes;
    intervalle_de_mesure_secondes = int_conf.intervalle_de_mesure_secondes;
    devEui= temp_config_container.rel_config.devEui;
    appEui= temp_config_container.rel_config.appEui;

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
    
    // Initialisation des capteurs
    int it = 0;
    for (int it = 0; it<ncapt; it++) {
        SensorConfig _c = liste_capteurs[it];
        sens[it] = new Sensor(_c.pin, 1, _c.type_capteur);
        toute_mesure.push_back(0);
        DEBUG_LOG("inserted new Sensor ptr at position " + String(it) + " of sens with attributes :");
        DEBUG_LOG("_c.pin : " + String(_c.pin) + "  _c.type_capteur : " + String(_c.type_capteur) + "\n\n");
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
            toute_mesure[it] = v;
            DEBUG_LOG("value " + String(v) + "written in toute_mesure");
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
    
    bool IsTimeToLoRa = ((current_Time - lastLoRaSend) >= (lora_intervalle_secondes - 60));

    IsTimeToLoRa = true; //a supprimer, pour les besoins du debugs
    if (IsTimeToLoRa || rattrapage) {

        File dataFile = SD.open(filename, FILE_READ);
        DEBUG_LOG("File has been opened");

        if (!dataFile) {
            Serial.println("Impossible d'ouvrir le fichier de données pour LoRa");
            lora.stopLoRa();
            return;
        }

        lora.startLoRa();
        DEBUG_LOG("LoRa ok");

        dataFile.seek(lastSDOffset);

        DEBUG_LOG("CalculateSleepTimeUntilNextMeasurement : " + String(CalculateSleepTimeUntilNextMeasurement(lastMeasure, intervalle_de_mesure_secondes)));

        while (CalculateSleepTimeUntilNextMeasurement(lastMeasure, intervalle_de_mesure_secondes) > 60000 && dataFile.available()) { //racourcir de 60000 à 10000 pour les besoins de la démo


            std::queue<String> lineToSend;
            lineToSend.push(dataFile.readStringUntil('\n'));

            // Si la ligne est vide aka plus rien à envoyer
            if (lineToSend.front().length() == 0) {
                rattrapage = false;
                break;
            }

            // Tentative d'envoi 3 fois de suite 
            for (int attempt = 1; attempt <= 3; attempt++) {

                if (lora.sendPackets(lineToSend)) {
                    DEBUG_LOG("Packet successfully sent");
                    lastSDOffset = dataFile.position();
                    break;

                } else {
                    DEBUG_LOG("Attempt n " + String(attempt) +" failed");
                    if (attempt < 3) delay(20000);
                }
            }
            if (!dataFile.available()) {
                rattrapage = false;
            }

        } // <-- fermeture du while : on a tout envoyé ou on va bientôt faire une mesure !

        dataFile.close();
        lastLoRaSend = current_Time;

        // --- Réception éventuelle de mise à jour config ---
        Serial.println("Vérification de mise à jour descendante...");


        uint16_t recvMeasure = 0, recvLora = 0;
        if (lora.receiveConfigUpdate(configFilePath, &recvMeasure, &recvLora, 15000)) {
            Serial.println("Mise à jour config reçue du master.");
            intervalle_de_mesure_secondes = recvMeasure;
            lora_intervalle_secondes = recvLora;
        } else {
            DEBUG_LOG("Pas de mise à jour reçue.");
        }

        lora.stopLoRa();
    }
    // --- Sommeil jusqu'à prochaine mesure ---
    pinMode(LED_BUILTIN, INPUT_PULLDOWN);
    Waiter waiter;
    DEBUG_LOG("waiter instancié");

    if (CalculateSleepTimeUntilNextMeasurement(lastMeasure, intervalle_de_mesure_secondes) <= CalculateSleepTimeUntilNextCommunication(lastLoRaSend, lora_intervalle_secondes)){
        long time_to_sleep = CalculateSleepTimeUntilNextMeasurement(lastMeasure, intervalle_de_mesure_secondes)*1000;
        DEBUG_LOG("sleeping until next measure, sleeping for " + String (time_to_sleep)+ "ms");
        waiter.sleepUntil(CalculateSleepTimeUntilNextMeasurement(lastMeasure, intervalle_de_mesure_secondes));
    } else {
        DEBUG_LOG("sleeping until next communication " + String (CalculateSleepTimeUntilNextCommunication(lastLoRaSend, lora_intervalle_secondes)*1000)+"ms");
        waiter.sleepUntil(CalculateSleepTimeUntilNextCommunication(lastLoRaSend, lora_intervalle_secondes));
    }
    // Prevent time variables (current_time) to diverge (time domain is 24 hours, to preserve coherence with GetSecondsSinceMidnight)
    
    if(current_Time >= sec_in_day){
        lastLoRaSend -= current_Time;
        lastMeasure -= current_Time;
        current_Time = 0;
    }
}