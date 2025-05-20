// SD_Initializer.hpp
#ifndef SD_INITIALIZER_HPP
#define SD_INITIALIZER_HPP

#include <Arduino.h> // Pour String, etc.
#include <SD.h>      // Pour File, SD

// Le nom du fichier CSV
extern const char filename[];

// Vérifie si la SD est déjà initialisée et le fichier existe
bool AlreadyInitialised();

// Initialise la SD et crée le fichier CSV s'il n'existe pas
bool InitialiseLog(const int CSpin, int npressure, int ntemp);

#endif // SD_INITIALIZER_HPP