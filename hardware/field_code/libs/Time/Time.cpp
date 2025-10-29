#include <RTClib.h>
#include <vector>
#include "Time.hpp"
#include "Reader.hpp"

// ----- RTC -----
RTC_PCF8523 externalRtc;
int measurementCount = 0;

// ----- Configuration -----
Reader reader;
int freq_envoi_lora_seconds = 0;
int freq_mesure_seconds = 0;

std::vector<unsigned long> measurementTimesVec;
std::vector<unsigned long> communicationTimesVec;

GeneralConfig res;

// ------------------------------------------------------------
// Lecture et mise à jour de la configuration
// ------------------------------------------------------------

void LoadConfig() {
  reader.lireConfigCSV("config_sensor.csv");
  freq_envoi_lora_seconds = res.int_config.lora_intervalle_secondes;
  freq_mesure_seconds = res.int_config.intervalle_de_mesure_secondes;
}

void RefreshConfigFromFile() {
  reader.lireConfigCSV("config_sensor.csv");
  freq_envoi_lora_seconds = res.int_config.lora_intervalle_secondes;
  freq_mesure_seconds = res.int_config.intervalle_de_mesure_secondes;

  InitializeMeasurementTimes();
  InitializeMeasurementCount();

  Serial.println("🔄 Configuration mise à jour depuis le fichier CSV.");
}

// ------------------------------------------------------------
// Initialisation RTC externe uniquement
// ------------------------------------------------------------

void InitialiseRTC() {
  if (!externalRtc.begin()) {
    Serial.println("Erreur lors de l'initialisation de la RTC externe !");
  }

  if (externalRtc.lostPower()) {
    
    externalRtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }

  Serial.println("RTC externe initialisée.");
}

// ------------------------------------------------------------
// Fonctions utilitaires
// ------------------------------------------------------------

String UIntTo2DigitString(uint8_t x) {
  String str = String(x);
  if (x < 10) str = "0" + str;
  if (x >= 100) str.remove(2);
  return str;
}

// ------------------------------------------------------------
// Fonctions temporelles
// ------------------------------------------------------------

String GetCurrentDate() {
  DateTime now = externalRtc.now();
  return UIntTo2DigitString(now.day()) + "/" +
         UIntTo2DigitString(now.month()) + "/" +
         String(now.year());
}

String GetCurrentHour() {
  DateTime now = externalRtc.now();
  return UIntTo2DigitString(now.hour()) + ":" +
         UIntTo2DigitString(now.minute()) + ":" +
         UIntTo2DigitString(now.second());
}

unsigned long GetSecondsSinceMidnight() {
  DateTime now = externalRtc.now();
  return now.hour() * 3600UL + now.minute() * 60UL + now.second();
}

// ------------------------------------------------------------
// Gestion des mesures
// ------------------------------------------------------------

void InitializeMeasurementTimes() {
  measurementTimesVec.clear();

  if (freq_mesure_seconds <= 0) return;

  int totalMeasurementsPerDay = 86400 / freq_mesure_seconds;
  if (totalMeasurementsPerDay <= 0) return;

  measurementTimesVec.reserve(totalMeasurementsPerDay);
  for (int i = 0; i < totalMeasurementsPerDay; ++i) {
    unsigned long timeSec = (unsigned long)i * (unsigned long)freq_mesure_seconds;
    measurementTimesVec.push_back(timeSec);
  }
}

void InitializeMeasurementCount() {
  unsigned long currentTime = GetSecondsSinceMidnight();
  measurementCount = 0;

  int totalMeasurementsPerDay = 86400 / freq_mesure_seconds;
  for (int i = 0; i < totalMeasurementsPerDay; i++) {
    if (currentTime > measurementTimesVec[i])
      measurementCount++;
    else
      break;
  }
}

unsigned long CalculateSleepTimeUntilNextMeasurement() {
  unsigned long currentTime = GetSecondsSinceMidnight();

  int totalMeasurementsPerDay = 86400 / freq_mesure_seconds;
  for (int i = 0; i < totalMeasurementsPerDay; i++) {
    if (currentTime < measurementTimesVec[i]) {
      unsigned long nextTime = measurementTimesVec[i];
      return (nextTime - currentTime) * 1000UL;
    }
  }

  unsigned long nextDayFirstTime = measurementTimesVec[0] + 86400UL;
  return (nextDayFirstTime - currentTime) * 1000UL;
}

unsigned long CalculateSleepTimeUntilNextCommunication() {
  unsigned long currentTime = GetSecondsSinceMidnight();

  int totalCommunicationPerDay = 86400 / freq_envoi_lora_seconds;
  for (int i = 0; i < totalCommunicationPerDay; i++) {
    if (currentTime < communicationTimesVec[i]) {
      unsigned long nextTime = communicationTimesVec[i];
      return (nextTime - currentTime) * 1000UL;
    }
  }

  unsigned long nextDayFirstTime = communicationTimesVec[0] + 86400UL;
  return (nextDayFirstTime - currentTime) * 1000UL;
}