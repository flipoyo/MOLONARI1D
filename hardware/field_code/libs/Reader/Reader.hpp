#ifndef READER_HPP
#define READER_HPP

#include <Arduino.h>
#include <SD.h>
#include <vector>
#include <queue>

// ---- Structures globales ----
struct SensorConfig {
    String id;
    String type_capteur;
    int pin;//TODO rename dataPin 
};

struct IntervallConfig{
    int intervalle_de_mesure_secondes; //mettre un nom différent de celui du relais pour éviter confusion ??
    int lora_intervalle_secondes;
};


struct RelayConfig {
    String appEui;
    String appKey;
    String devEui; // utile pour le sensor
    int CSPin;
    float lora_freq;
    int intervalle_de_mesure_secondes;
    int lora_intervalle_secondes;
};

struct GeneralConfig {
    RelayConfig rel_config;
    std::vector<SensorConfig> liste_capteurs;
    IntervallConfig int_config;
    bool succes = true;
};

// Variables globales (extern pour éviter redéfinitions)

// Variables globales associées à la logique du programme : à supprimer plus tard ?
//extern int FREQUENCE_MINUTES;
//extern unsigned long LORA_INTERVAL_S;

// ---- Classe Reader ----
class Reader {
private:
    File file;                        // Objet pour gérer le fichier
    static unsigned int line_cursor;  // Position actuelle de lecture dans le fichier

public:
    Reader() = default;

    // ----- Lecture CSV -----
    GeneralConfig lireConfigCSV(const char* NomFichier, int CSPin = 5);

    // ----- Méthodes pour Waiter -----
    bool EstablishConnection(unsigned int shift);
    void UpdateCursor(unsigned int lineId);
    void writetomyrecourdfile();
    std::queue<String> loadDataIntoQueue();
    String ReadMeasure();
    bool IsDataAvailable();
    void Dispose();
};

#endif // READER_HPP
