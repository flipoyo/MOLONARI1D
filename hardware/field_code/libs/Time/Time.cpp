// This file contains all the code to manage time using the MKR board's integrated Real Time Clock (RTC) and an external RTC.

//Time doit récupérer lora_intervalle_secondes de config_sensor.csv


#include <RTCZero.h>
#include <RTClib.h>
#include<vector>

#include "Time.hpp"
#include "Reader.hpp"


// Declare the RTC objects: internal (MKR) and external
RTCZero internalRtc;
RTC_PCF8523 externalRtc;
int measurementCount = 0;


// Lecture de la configuration CSV
Reader reader;
int freq_envoi_lora_seconds = 0;
int freq_mesure_seconds = 0;

std::vector<unsigned long> measurementTimesVec;

void LoadConfig() {
  // Read configuration (call this from setup or main)
  reader.lireConfigCSV("config_sensor.csv");
  freq_envoi_lora_seconds = config.intervalle_lora_secondes;
  freq_mesure_seconds = config.intervalle_de_mesure_secondes;
}



// Helper function to convert an integer to a 2-digit string (e.g., 7 -> "07")
String UIntTo2DigitString(uint8_t x) {
  String str = String(x);

  if (x < 10) {
    str = "0" + str; // Add leading zero for single digits
  }

  if (x >= 100) {
    str.remove(2); // Keep only the first two digits if it's 100 or more
  }

  return str;
}

// Initialize both the internal and external RTCs
void InitialiseRTC() {
  // Start the internal RTC
  internalRtc.begin();
  
  // Start communication with the external RTC
  bool success = externalRtc.begin();
  if (!success) {
    return; // Stop if the external RTC is not available
  }
  
  // If the external RTC lost power, set its time to the compile time of this code
  if (externalRtc.lostPower()) {
    externalRtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }
  
  // Sync the internal RTC with the external RTC
  DateTime startingDate = externalRtc.now();
  uint8_t day = startingDate.day();
  uint8_t month = startingDate.month();
  uint8_t year = startingDate.year() % 100; // Get the last two digits of the year
  uint8_t hour = startingDate.hour();
  uint8_t minute = startingDate.minute();
  uint8_t second = startingDate.second();
  internalRtc.setDate(day, month, year);
  internalRtc.setTime(hour, minute, second);
}

// Get the current date in "DD/MM/YYYY" format
String GetCurrentDate() {
  return 
    UIntTo2DigitString(internalRtc.getDay()) +
    "/" +
    UIntTo2DigitString(internalRtc.getMonth()) +
    "/" +
    "20" + UIntTo2DigitString(internalRtc.getYear());
}

// Get the current time in "HH:MM:SS" format
String GetCurrentHour() {
  return 
    UIntTo2DigitString(internalRtc.getHours()) +
    ":" +
    UIntTo2DigitString(internalRtc.getMinutes()) +
    ":" +
    UIntTo2DigitString(internalRtc.getSeconds());  
}

// Get the current time in seconds since midnight
unsigned long GetSecondsSinceMidnight() {
  uint8_t hour = internalRtc.getHours();
  uint8_t minute = internalRtc.getMinutes();
  uint8_t second = internalRtc.getSeconds();
  return hour * 3600 + minute * 60 + second; // Convert hours and minutes to seconds
}
void InitializeMeasurementTimes() {
  // Vider d'abord le vecteur existant
  measurementTimesVec.clear();

  // Vérifie que la fréquence est bien définie
  if (freq_mesure_seconds <= 0) {
    return; // Rien à faire si la fréquence n'est pas configurée
  }

  // Calcul du nombre total de mesures possibles dans une journée
  // (on ignore le reste si 86400 n'est pas divisible par freq_mesure_seconds)
  int totalMeasurementsPerDay = 86400 / freq_mesure_seconds; // 86400 = secondes dans une journée
  if (totalMeasurementsPerDay <= 0) {
    return;
  }

  // Remplis le vecteur avec les instants de mesure (en secondes depuis minuit)
  measurementTimesVec.reserve(static_cast<size_t>(totalMeasurementsPerDay));
  for (int i = 0; i < totalMeasurementsPerDay; ++i) {
    unsigned long timeSec = static_cast<unsigned long>(i) * static_cast<unsigned long>(freq_mesure_seconds);
    measurementTimesVec.push_back(timeSec);
  }
}



// Determine how many measurements have already been done today
void InitializeMeasurementCount() {
  unsigned long currentTime = GetSecondsSinceMidnight(); // Current time in seconds
  measurementCount = 0;
  
  // Find the first measurement that hasn't been done yet
  int totalMeasurementsPerDay = 86400 / freq_mesure_seconds; // 86400 = secondes dans une journée
  for (int i = 0; i < totalMeasurementsPerDay; i++) {
    if (currentTime > measurementTimesVec[i]) {
      measurementCount++;
    } else {
      break; // Stop once the current time is less than the next measurement time
    }
  }
}

// Calculate the time (in ms) until the next measurement
unsigned long CalculateSleepTimeUntilNextMeasurement() {


  unsigned long currentTime = GetSecondsSinceMidnight(); // Current time in seconds
  
  // Find the next measurement time
  int totalMeasurementsPerDay = 86400 / freq_mesure_seconds; // 86400 = secondes dans une journée
  for (int i = 0; i < totalMeasurementsPerDay; i++) {
    if (currentTime < measurementTimesVec[i]) {
      unsigned long nextTime = measurementTimesVec[i];
      return (nextTime - currentTime) * 1000; // Convert seconds to milliseconds
    }
  }
  
  // If no measurement is left today, calculate the time until the next day's first measurement
  unsigned long nextDayFirstTime = measurementTimesVec[0] + 24 * 3600; // First time of the next day
  return (nextDayFirstTime - currentTime) * 1000;
}

