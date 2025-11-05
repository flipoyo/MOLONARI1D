#include "Reader.hpp"
#include <SD.h>
#include <queue>

// ----- Debug macros -----
#ifdef DEBUG_READER
#define SD_LOG(msg) Serial.print(msg)
#define SD_LOG_LN(msg) Serial.println(msg)
#else
#define SD_LOG(msg)
#define SD_LOG_LN(msg)
#endif

// ----- Variables globales -----
unsigned long LORA_INTERVAL_S = 3UL * 3600UL; // valeur par défaut

// ----- Static member initialization -----
unsigned int Reader::line_cursor = 0;

// ==================== Lecture CSV ====================
GeneralConfig Reader::lireConfigCSV(const char* NomFichier, int CSPin) {
    GeneralConfig res = GeneralConfig();
    if (!SD.begin(CSPin)) {
        Serial.println("Impossible de monter SD");
        res.succes = false;
        return res;
    }

    File f = SD.open(NomFichier);
    if (!f) {
        Serial.println("Fichier CSV non trouvé, utilisation des valeurs par défaut");
        res.succes = false;
        return res;
    }

    Serial.println("Lecture du fichier de configuration...");

    while (f.available()) {
        String line = f.readStringUntil('\n');
        Serial.println("la ligne est : " + String(line));
        line.trim();
        if (line.length() == 0 || line.startsWith("#")) continue;

        // Découper la ligne CSV
        std::vector<String> tokens;
        int last = 0, next = 0;
        while ((next = line.indexOf(',', last)) != -1) {
            Serial.println("le token : " + String(line.substring(last, next)));
            tokens.push_back(line.substring(last, next));
            last = next + 1;
        }
        tokens.push_back(line.substring(last)); // dernier token
        Serial.println("le token : " + String(line.substring(last)));
        Serial.println("la taille:" + String(tokens.size()));

        // ---------- PARAMÈTRES GLOBAUX ----------
        if (tokens.size() == 2) {
            String key = tokens[0];
            String val = tokens[1];

            if (key == "appEui") res.rel_config.appEui = val;
            else if (key == "appKey") res.rel_config.appKey = val;
            else if (key == "CSPin") res.rel_config.CSPin = val.toInt();
            else if (key == "lora_freq") res.rel_config.lora_freq = val.toFloat();


            //config générale des intervalles
            else if (key == "intervalle_de_mesure_secondes") {
                res.int_config.intervalle_de_mesure_secondes = val.toInt();
            }
            else if (key == "lora_intervalle_secondes") {
                res.int_config.lora_intervalle_secondes = val.toInt();
            }
            else {
                Serial.print("Clé inconnue ignorée : ");
                Serial.println(key);
            }
        }

        // ---------- CAPTEURS ----------
        else if (tokens.size() == 4) {
            SensorConfig c;
            c.id = tokens[0];
            c.type_capteur = tokens[1];

            // Gestion du pin (A0, A1, etc.)
            if (tokens[2].startsWith("A"))
                c.pin = tokens[2].substring(1).toInt() + A0;
            else
                c.pin = tokens[2].toInt();

            c.devEUI = tokens[3];
            res.liste_capteurs.push_back(c);
        }

        else {
            Serial.print("Ligne ignorée : ");
            Serial.println(line);
        }
    }

    f.close();
    res.succes = true;
    Serial.println("Configuration chargée avec succès.");
    Serial.print("→ Capteurs trouvés : ");
    Serial.println(res.liste_capteurs.size());

    return res;
}

// ==================== Waiter Methods ====================
bool Reader::EstablishConnection(unsigned int shift)
{
    SD_LOG("SD Reader : establishing connection ...");

    this->file = SD.open("data.csv"); // à adapter selon ton fichier réel
    if (!this->file) {
        SD_LOG_LN("Failed to open file");
        return false;
    }

    this->file.seek(0);
    if (shift > line_cursor) return false;
    line_cursor -= shift;

    unsigned int lineId = 0;
    while ((lineId < line_cursor) && this->file.available()) {
        this->file.readStringUntil('\n');
        lineId++;
    }

    SD_LOG_LN(" Done");
    return true;
}

void Reader::UpdateCursor(unsigned int shift)
{
    line_cursor += shift;
    writetomyrecourdfile();
    SD_LOG_LN("--------------UpdateCursor-------------" + String(line_cursor));
}

void Reader::writetomyrecourdfile()
{
    String message = "--------------UpdateCursor-------------" + String(line_cursor);
    File cursorFile = SD.open("cursor_position.txt", FILE_WRITE);
    if (cursorFile) {
        cursorFile.println(message);
        cursorFile.close();
    } else {
        SD_LOG_LN("Failed to save message");
    }
}

// toutes les fonctions jusqu'ici sont potentiellement inutiles 

std::queue<String> Reader::loadDataIntoQueue()
{
    std::queue<String> Queue;
    while (IsDataAvailable()) {
        String line = ReadMeasure();
        Queue.push(line);
        if (Queue.size() >= 250) break;
    }
    return Queue;
}

String Reader::ReadMeasure()
{
    String line = this->file.readStringUntil('\n');
    SD_LOG_LN("SD Reader : " + line);
    return line;
}

bool Reader::IsDataAvailable()
{
    return this->file.available();
}

void Reader::Dispose()
{
    this->file.close();
}

memory_line::memory_line(String flush_arg, int offset):flush(flush_arg), memory_successor(offset){}
