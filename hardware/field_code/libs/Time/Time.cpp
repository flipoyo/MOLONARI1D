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


void InitialiseRTC() {
  if (!externalRtc.begin()) {
    Serial.println("Erreur lors de l'initialisation de la RTC externe !");
  }
  if (externalRtc.lostPower()) {
    
    externalRtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }
  Serial.println("RTC externe initialisée.");
}


String UIntTo2DigitString(uint8_t x) {
  String str = String(x);
  if (x < 10) str = "0" + str;
  if (x >= 100) str.remove(2);
  return str;
}

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

unsigned long CalculateSleepTimeUntilNextMeasurement(unsigned long previousMeasurementTime, int measurementInterval) {
  //retourne en ms
  unsigned long currentTime = GetSecondsSinceMidnight();
  unsigned long time_to_sleep = (measurementInterval - (currentTime - previousMeasurementTime)) * 1000UL;
  return (time_to_sleep);
}

unsigned long CalculateSleepTimeUntilNextCommunication(unsigned long previousCommunicationTime, int communicationInterval) {
  //retourne en ms
  unsigned long currentTime = GetSecondsSinceMidnight();
  unsigned long timeToSleep = (communicationInterval - (currentTime - previousCommunicationTime)) * 1000UL;
  return (timeToSleep);
}