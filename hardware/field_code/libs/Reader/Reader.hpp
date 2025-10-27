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
    String id_box; //pour l'export des données
    int pin;


};

struct RelayConfig {
    String appEui;
    String appKey;
    int CSPin;
    float lora_freq;
    int intervalle_de_mesure_secondes;
    int intervalle_lora_secondes;
};

// Variables globales (extern pour éviter redéfinitions)
extern RelayConfig config;
extern std::vector<SensorConfig> liste_capteurs;

// Variables globales associées à la logique du programme
extern int FREQUENCE_MINUTES;
extern unsigned long LORA_INTERVAL_S;

// ---- Classe Reader ----
class Reader {
private:
    File file;                        // Objet pour gérer le fichier
    static unsigned int line_cursor;  // Position actuelle de lecture dans le fichier

public:
    Reader() = default;

    // ----- Lecture CSV -----
    void lireConfigCSV(const char* NomFichier);

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
