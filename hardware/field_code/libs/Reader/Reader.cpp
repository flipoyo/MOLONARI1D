#include "Reader.hpp"
#include <SD.h>
#include <queue>

// ----- Debug macros -----
#ifdef SD_DEBUG
#define SD_LOG(msg) Serial.print(msg)
#define SD_LOG_LN(msg) Serial.println(msg)
#else
#define SD_LOG(msg)
#define SD_LOG_LN(msg)
#endif

// ----- Variables globales -----
RelayConfig config;
std::vector<SensorConfig> liste_capteurs;
unsigned long LORA_INTERVAL_S = 3UL * 3600UL; // valeur par défaut

// ----- Static member initialization -----
unsigned int Reader::line_cursor = 0;

// ==================== Lecture CSV ====================
bool Reader::lireConfigCSV(const char* NomFichier) {
    if (!SD.begin(config.CSPin)) {
        Serial.println("Impossible de monter SD");
        return false;
    }

    File f = SD.open(NomFichier);
    if (!f) {
        Serial.println("Fichier CSV non trouvé, utilisation des valeurs par défaut");
        return false;
    }

    Serial.println("Lecture du fichier de configuration...");

    while (f.available()) {
        String line = f.readStringUntil('\n');
        line.trim();  
        if (line.length() == 0 || line.startsWith("#")) continue;

        int idx = line.indexOf(',');
        if (idx < 0) continue;

        String key = line.substring(0, idx);
        String val = line.substring(idx + 1);

        // ---------- PARAMÈTRES GLOBAUX ----------
        if (key == "appEui") config.appEui = val;
        else if (key == "appKey") config.appKey = val;
        else if (key == "CSPin") config.CSPin = val.toInt();
        else if (key == "lora_freq") config.lora_freq = val.toFloat();
        else if (key == "intervalle_de_mesure_secondes") {
            int freq_sec = val.toInt();
            config.intervalle_de_mesure_secondes = freq_sec;
        }
        else if (key == "intervalle_lora_secondes") {
            LORA_INTERVAL_S = val.toInt();
            config.intervalle_lora_secondes = LORA_INTERVAL_S;
        }

        // ---------- CAPTEURS ----------
        else {
            String tokens[4];
            int first = 0, last = 0, tokenIdx = 0;
            while (last >= 0 && tokenIdx < 4) {
                last = line.indexOf(',', first);
                if (last < 0) last = line.length();
                tokens[tokenIdx++] = line.substring(first, last);
                first = last + 1;
            }

            if (tokenIdx >= 3) {  
                SensorConfig c;
                c.id = tokens[0];
                c.type_capteur = tokens[1];
                if (tokens[2].startsWith("A"))
                    c.pin = tokens[2].substring(1).toInt() + A0;
                else
                    c.pin = tokens[2].toInt();

                c.id_box = (tokenIdx >= 4) ? tokens[3] : "";
                liste_capteurs.push_back(c);
            }
        }
    }
    f.close();
    Serial.println("Configuration chargée avec succès.");
    return true;
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
