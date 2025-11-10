#include <Arduino.h>
#include <SD.h>
#include <LoRa.h>
#include <ArduinoLowPower.h>

#include "Pressure_Sensor.hpp"
#include "Temp_Sensor.hpp"
#include "Writer.hpp"
#include "LoRa_Molonari.hpp"
#include "Time.cpp"
#include "Waiter.hpp"
#include <queue>
#include <vector>

// ----- Structures -----
struct Capteur {
    String id;
    String type; // "pression" ou "temperature"
    int pin;
    float offset;
    float facteur;
};

// ----- Variables globales -----
std::vector<Capteur> liste_capteurs; // Capteurs lus depuis CSV
int FREQUENCE_MINUTES = 15; //initialisation par défaut
int LORA_INTERVAL_H = 3;//initialisation par défaut

PressureSensor **pSens;
TemperatureSensor **tempSensors;
double *pressure;
double *temperature;

Writer logger;
const int CSPin = 5;
const char filename[] = "RECORDS.CSV";

LoraCommunication lora(868E6, 0x01, 0x02); // fréquence, adresse locale, adresse distante
unsigned long lastLoRaSend = 0;
unsigned long LORA_INTERVAL_S = 3UL * 3600UL; // initialisation par défaut
unsigned long lastSDOffset = 0;
std::queue<String> sendQueue;

// ----- Lecture CSV -----
void lireConfigCSV(const char* NomFichier) {
    if (!SD.begin(CSPin)) { Serial.println("Impossible de monter SD"); return; }

    File f = SD.open(NomFichier);
    if (!f) { Serial.println("Fichier CSV non trouvé"); return; }

    while (f.available()) {
        String line = f.readStringUntil('\n');
        //supprimer les espaces inutiles dans les lignes : 
        line.trim(); 
        if (line.length() == 0 || line.startsWith("#")) continue;

        // Paramètres globaux
        if (line.startsWith("mesure_frequence_minutes")) {
            //trouver la place de la virgule, notre séparateur : 
            int idx = line.indexOf(',');
            FREQUENCE_MINUTES = line.substring(idx + 1).toInt();
        } else if (line.startsWith("lora_intervalle_secondes")) {
            int idx = line.indexOf(',');
            LORA_INTERVAL_S = line.substring(idx + 1).toInt();
        } else {
            // Capteurs
            String tokens[5];
            int first = 0, last = 0, tokenIdx = 0;
            while (last >= 0 && tokenIdx < 5) {
                last = line.indexOf(',', first);
                if (last < 0) last = line.length();
                tokens[tokenIdx++] = line.substring(first, last);
                first = last + 1;
            }
            Capteur c;
            c.id = tokens[0];
            c.type = tokens[1];
            // Conversion des pins A0-A5 en int
            //important de laisser A0 en fin de ligne pour la ledcture de Analogread ?
            if (tokens[2].startsWith("A")) c.pin = tokens[2].substring(1).toInt() + A0;
            else c.pin = tokens[2].toInt();
            c.offset = tokens[3].toFloat();
            c.facteur = tokens[4].toFloat();
            liste_capteurs.push_back(c);
        }
    }
    f.close();
}


// ----- Setup -----
void setup() {
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, HIGH);

    //
    Serial.begin(115200);
    unsigned long end_date = millis() + 5000;
    while (!Serial && millis() < end_date) {}

    // Lecture de la configuration CSV
    lireConfigCSV("capteurs_config.csv");
    int LORA_INTERVAL = LORA_INTERVAL_S;

    // Compter les capteurs
    int npressure = 0, ntemp = 0;
    for (auto &c : liste_capteurs) {
        if (c.type == "pression") npressure++;
        else if (c.type == "temperature") ntemp++;
    }

    // Allocation dynamique
    pSens = new PressureSensor*[npressure];
    tempSensors = new TemperatureSensor*[ntemp];
    pressure = new double[npressure];
    temperature = new double[ntemp];

    // Initialisation des capteurs
    int ip = 0, it = 0;
    for (auto &c : liste_capteurs) {
        if (c.type == "pression") {
            pSens[ip] = new PressureSensor(c.pin, 1);
            pressure[ip] = 0;
            ip++;
        } else if (c.type == "temperature") {
            tempSensors[it] = new TemperatureSensor(c.pin, 1, c.offset, c.facteur);
            temperature[it] = 0;
            it++;
        }
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
    int npressure = 0, ntemp = 0;
    for (auto &c : liste_capteurs) {
        if (c.type == "pression") {
            pressure[npressure] = pSens[npressure]->MeasurePressure();
            npressure++;
        } else if (c.type == "temperature") {
            temperature[ntemp] = tempSensors[ntemp]->MeasureTemperature();
            ntemp++;
        }
    }

    // --- Stocker sur SD ---
    String date = GetCurrentDate();
    String hour = GetCurrentHour();
    logger.LogData(date, hour, pressure, temperature);

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

            int shift = 0;
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
