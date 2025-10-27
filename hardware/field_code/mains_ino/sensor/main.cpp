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


Sensor** sens;
double *toute_mesure;

Writer logger;
const int CSPin = 5;
const char filename[] = "RECORDS.CSV";
const char* configFilePath = "/config_sensor.csv";

LoraCommunication lora(868E6, 0x01, 0x02, RoleType::SLAVE); // fréquence, adresse locale, adresse distante
unsigned long lastLoRaSend = 0;
unsigned long lastSDOffset = 0;
std::queue<String> sendQueue;

void updateConfigFile(uint16_t measureInterval, uint16_t loraInterval) {

    File file = SD.open("/config_sensor.csv", FILE_READ);
    if (!file) {
        Serial.println("ERREUR : impossible de lire config_sensor.csv");
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

    file = SD.open("/config_sensor.csv", FILE_WRITE | O_TRUNC);
    if (!file) {
        Serial.println("ERREUR : impossible d'écrire config_sensor.csv");
        return;
    }

    for (auto &ligne : lignes) {
        file.println(ligne);
    }

    file.close();
    Serial.println("Fichier config_sensor.csv mis à jour sans toucher aux autres paramètres.");
}


// ----- Setup -----
void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);

    Serial.begin(115200);
    while(!Serial){}

    if (!SD.begin(CSPin)) {
        Serial.println("❌ Impossible d'initialiser la SD");
        while(true){}
    }

    // Vérifier si config_sensor.csv existe
    if (!SD.exists("/config_sensor.csv")) {
        Serial.println("config_sensor.csv absent, en attente de réception LoRa...");
        lora.startLoRa();
        if (lora.receiveConfigUpdate("/config_sensor.csv")) {
            Serial.println("Configuration initiale reçue via LoRa !");
        } else {
            Serial.println("⚠️ Pas de configuration reçue, création par défaut");
            File file = SD.open("/config_sensor.csv", FILE_WRITE);
            if (file) {
                file.println("intervalle_de_mesure_secondes,600");
                file.println("intervalle_lora_secondes,1800");
                file.close();
            }
        }
        lora.stopLoRa();
    }

    // Charger la configuration
    Reader reader;
    reader.lireConfigCSV("config_sensor.csv");

    

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
    if (!SD.begin(CSPin)) { while(true){} }
    logger.EstablishConnection(CSPin);
    InitialiseRTC();

    pinMode(LED_BUILTIN, INPUT_PULLDOWN);
}
static bool rattrapage = false;


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
    logger.LogData(ncapt, toute_mesure); // LogData est dans writer

    // --- Envoyer LoRa si intervalle atteint ---
    unsigned long current_Time=GetSecondsSinceMidnight();
    LORA_INTERVAL_S = config.intervalle_lora_secondes;
    bool IsTimeToLoRa = (current_Time - lastLoRaSend >= LORA_INTERVAL_S);


    if (IsTimeToLoRa || rattrapage) {
        lora.startLoRa();

        // Lire nouvelles lignes depuis SD
        File dataFile = SD.open(filename, FILE_READ);
        if (!dataFile) {
            Serial.println("Impossible to open data file for LoRa sending");
            lora.closeSession(0);
            return;
        }

        dataFile.seek(lastSDOffset); // position sur la prochaine ligne

        while (dataFile.available()) {
            // Vérifier le temps restant avant prochaine mesure
            if (CalculateSleepTimeUntilNextMeasurement() < 60UL) {
                Serial.println("Not enough time before next measurement, stopping LoRa send");
                break;
            }

            std::queue<String> lineToSend;
            lineToSend.push(dataFile.readStringUntil('\n'));
            if (lineToSend.front().length() == 0) {
                rattrapage = false;
                // Ligne vide → fin de fichier
                break;
            }

            // Essayer d'envoyer la ligne jusqu'à 3 fois avec 20 s d'intervalle
            bool success = false;
            for (int attempt = 1; attempt <= 3; attempt++) {
                if (lora.sendPackets(lineToSend)) {
                    success = true;
                    break;
                } else {
                    Serial.println(attempt);
                    if (attempt < 3) {
                        delay(20000); // attendre 20 sec avant de retenter
                    }
                }
            }

            if (success) {
                lastSDOffset = dataFile.position(); // ligne envoyée → avancer le pointeur
                Serial.println("Line sent successfully via LoRa");
            } else {
                Serial.println("Line failed to send after 3 attempts, stopping LoRa send, retrying later");
                rattrapage = false;
                break; // on sort de la boucle pour retenter plus tard
            }
        }

        dataFile.close();
        lora.closeSession(0);
        lastLoRaSend = current_Time;

        // --- Réception éventuelle de mise à jour config ---
        Serial.println("Vérification de mise à jour descendante...");
        lora.startLoRa();

        if (lora.receiveConfigUpdate(configFilePath)) {
            Serial.println("Nouvelle configuration reçue et enregistrée !");
            
            // Recharger la configuration depuis le fichier mis à jour
            Reader reader;
            reader.lireConfigCSV(configFilePath);
            Serial.println("Configuration rechargée depuis le fichier LoRa.");

            LORA_INTERVAL_S = config.intervalle_lora_secondes;

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

