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
LoraCommunication lora(868E6, devEui, appEui, RoleType::SLAVE);
long lastLoRaSend = 0;
long lastMeasure = 0;
unsigned long lastSDOffset = 0;

uint16_t newMeasureInterval = 0;
uint16_t newLoraInterval = 0;

const long sec_in_day = 86400;
bool rattrapage = false;
bool a_line_remains_to_log = false;

// ----- Setup -----
void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);
    
    Serial.begin(115200);
    long end_date = millis() + 5000;
    while (!Serial && millis() < end_date) {}
    
    DEBUG_LOG("\n\n\n\n");
    // Lecture de la configuration CSV
    Reader reader;

    GeneralConfig temp_config_container = reader.lireConfigCSV("conf.csv", CSPin);
    IntervallConfig int_conf = temp_config_container.int_config;
    
    liste_capteurs = temp_config_container.liste_capteurs;
    lora_intervalle_secondes = int_conf.lora_intervalle_secondes;
    intervalle_de_mesure_secondes = int_conf.intervalle_de_mesure_secondes;
    devEui = temp_config_container.rel_config.devEui;
    appEui = temp_config_container.rel_config.appEui;

    if (temp_config_container.succes){
        DEBUG_LOG("lecture config terminée avec succès");
    }
    else {
        DEBUG_LOG("échec de la lecture du fichier config");
    }

    lora.LoraUpdateAttributes(868E6, appEui, devEui, RoleType::SLAVE);

    // Compter les capteurs
    for (auto & _c : liste_capteurs) {
        ncapt++;
    }
    // Allocation dynamique
    sens = new Sensor*[ncapt];
    
    // Initialisation des capteurs
    for (int it = 0; it<ncapt; it++) {
        SensorConfig _c = liste_capteurs[it];
        sens[it] = new Sensor(_c.pin, 4, _c.type_capteur);
        toute_mesure.push_back(0);
        DEBUG_LOG("inserted new Sensor ptr at position " + String(it) + " of sens with attributes :");
        DEBUG_LOG("_c.pin : " + String(_c.pin) + "  _c.type_capteur : " + String(_c.type_capteur) + "\n\n");
    }

    // Initialisation SD et logger
    if (!SD.begin(CSPin)) { while(true) {} }
    logger.EstablishConnection(CSPin);
    InitialiseRTC();
    digitalWrite(LED_BUILTIN, LOW);
    DEBUG_LOG ("Setup finished");
    delay(1000);
}

// ----- Loop -----
void loop() {

    String date = GetCurrentDate();
    String hour = GetCurrentHour();
    DEBUG_LOG(String(ncapt) + " capteurs détectés.");

    
    
    // --- Prendre mesures ---
    long current_Time=GetSecondsSinceMidnight();
    DEBUG_LOG("Temps actuel : " + String(current_Time));
    bool IsTimeToMeasure = ((current_Time - lastMeasure) >= (intervalle_de_mesure_secondes - 1));
    
    DEBUG_LOG("ncapt : " + String(ncapt)); //so far

    if (IsTimeToMeasure) {
        DEBUG_LOG("starting measurement process");
        digitalWrite(LED_BUILTIN, HIGH);
        for (int it = 0; it<ncapt; it++) {
            double v = sens[it]->get_voltage();
            DEBUG_LOG("voltage preleved");
            toute_mesure[it] = v;
            DEBUG_LOG("Measured " + String(v) + " at sensor " + String(it));
            //delay(500);//decreased for demo version
        }
        lastMeasure = current_Time;
        DEBUG_LOG("Voltage recording finished");
        a_line_remains_to_log = true;
        digitalWrite(LED_BUILTIN, LOW);
    }else{
        DEBUG_LOG("Not time to measure yet : current_Time - lastMeasure = " + String(current_Time - lastMeasure) + " ; intervalle_de_mesure_secondes - 1 = " + String(intervalle_de_mesure_secondes - 1));
    }

    
    // --- Stocker sur SD ---
    if(a_line_remains_to_log){
        DEBUG_LOG("launch LogData");
        logger.LogData(ncapt, toute_mesure, devEui);
        DEBUG_LOG("LogData instruction done");
        a_line_remains_to_log = false;
    }

    // --- Envoyer LoRa si intervalle atteint ---
    
    bool IsTimeToLoRa = ((current_Time - lastLoRaSend) >= (lora_intervalle_secondes - 60));

    if (IsTimeToLoRa || rattrapage) {
        digitalWrite(LED_BUILTIN, HIGH);
        File dataFile = SD.open(filename, FILE_READ);
        DEBUG_LOG("File has been opened");

        if (!dataFile) {
            DEBUG_LOG("Impossible d'ouvrir le fichier de données pour LoRa");
            lora.stopLoRa();
            return;
        }

        lora.startLoRa();
        DEBUG_LOG("LoRa ok, about to try handshake");

        uint8_t id = 0;
        if (lora.handshake(id)) {
            Serial.println("HANDSHAKE DONE\n");
            DEBUG_LOG("CalculateSleepTimeUntilNextMeasurement : " + String(CalculateSleepTimeUntilNextMeasurement(lastMeasure, intervalle_de_mesure_secondes)));

            DEBUG_LOG(String(dataFile.available()));
            bool time_to_mesure_soon = CalculateSleepTimeUntilNextMeasurement(lastMeasure, intervalle_de_mesure_secondes) < 1000;
            if(time_to_mesure_soon){
                DEBUG_LOG("Aborting LoRa send, measurement scheduled soon. Switching to rattrapage mode");
                lora.closeSession(0);
                rattrapage = true;
            }
            while ( (!time_to_mesure_soon) && dataFile.available()) { //racourcir de 60000 à 10000 pour les besoins de la démo                
                //at this point, lastSDOffset must point to the first memory address of the first line to be sent
                std::queue<memory_line> linesToSend;
                dataFile.seek(lastSDOffset);
                while (dataFile.available()) {
                    memory_line new_line = memory_line(dataFile.readStringUntil('\n'), dataFile.position());
                    new_line.flush = new_line.flush + "\n";
                    linesToSend.push(new_line);

                // Si la ligne est vide aka plus rien à envoyer
                    if (linesToSend.front().flush.length() == 0) {
                        break;
                    }
                }
                uint32_t end_document_address = dataFile.position();
                DEBUG_LOG("end_document_address : " + String(end_document_address) + "; memory_successor of the last element of sendqueue : " + String(linesToSend.back().memory_successor));
                DEBUG_LOG("SDOffset before sending: " + String(lastSDOffset) + "\n                     SEND ALL PACKETS AND MANAGE MEMORY");
                uint8_t lastPacket = lora.sendAllPacketsAndManageMemory(linesToSend, lastSDOffset, dataFile);
                DEBUG_LOG("SDOffset after sending: " + String(lastSDOffset) + "; end document address : " + String(end_document_address));
                rattrapage = !(lastSDOffset == end_document_address);
                DEBUG_LOG("rattrappage status : " + String(rattrapage) + "\n\n");
                lora.closeSession(lastPacket);
            }    // <-- fermeture du while : on a tout envoyé ou on va bientôt faire une mesure !

            dataFile.close();
            lastLoRaSend = current_Time;

            // --- Réception éventuelle de mise à jour config ---
            DEBUG_LOG("Vérification de mise à jour descendante...");


            uint16_t recvMeasure = 0, recvLora = 0;
            if (lora.receiveConfigUpdate(configFilePath, &recvMeasure, &recvLora, 15000)) {
                DEBUG_LOG("Mise à jour config reçue du master.");
                intervalle_de_mesure_secondes = recvMeasure;
                lora_intervalle_secondes = recvLora;
            } else {
                DEBUG_LOG("Pas de mise à jour reçue.");
            }

            lora.stopLoRa();
        } else {
            Serial.println("Handshake échoué");
        }
        // --- Sommeil jusqu'à prochaine mesure ---
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
        digitalWrite(LED_BUILTIN, LOW);
    }
}