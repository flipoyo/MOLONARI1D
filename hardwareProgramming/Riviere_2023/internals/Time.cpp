// This file will contain all the code to track time using the integrated Real Time Clock (RTC) of the MKR board and the external one.


// Check that the file has not been imported before
#ifndef MY_TIME
#define MY_TIME


#include <RTCZero.h>
#include <RTClib.h>



RTCZero internalRtc;
RTC_PCF8523 externalRtc;


String UIntTo2DigitString(uint8_t x) {
  String str = String(x);

  if (x < 10) {
    str = "0" + str;
  }

  if (x >= 100) {
    str.remove(2);
  }

  return str;
}


// Initialise the RTC module for the first time.
void InitialiseRTC() {
  // Start the internal RTC
  internalRtc.begin();
  
  // Start communication with the external RTC
  bool success = externalRtc.begin();
  if (!success) {
    return;
  }
  
  // If the external RTC has lost power (even its battery), then set its time to the date at which the code was compiled.
  if (externalRtc.lostPower()) {
    externalRtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }
  
  // Set the time of the internal RTC to the time of the external one
  DateTime startingDate = externalRtc.now();
  uint8_t day = startingDate.day();
  uint8_t month = startingDate.month();
  uint8_t year = startingDate.year() % 100;
  uint8_t hour = startingDate.hour();
  uint8_t minute = startingDate.minute();
  uint8_t second = startingDate.second();
  internalRtc.setDate(day, month, year);
  internalRtc.setTime(hour, minute, second);
}

// Return the current date (JJ/MM/AAAA)
String GetCurrentDate() {
  return 
    UIntTo2DigitString(internalRtc.getDay()) +
    "/" +
    UIntTo2DigitString(internalRtc.getMonth()) +
    "/" +
    "20" + UIntTo2DigitString(internalRtc.getYear());
}

// Return the current hour (HH:MM:SS)
String GetCurrentHour() {
  return 
    UIntTo2DigitString(internalRtc.getHours()) +
    ":" +
    UIntTo2DigitString(internalRtc.getMinutes()) +
    ":" +
    UIntTo2DigitString(internalRtc.getSeconds());
}

#endif