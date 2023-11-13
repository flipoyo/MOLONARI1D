// This file will contain all the code to track time using the integrated Real Time Clock (RTC) of the MKR board


// Check that the file has not been imported before
#ifndef TIME
#define TIME


#include <RTClib.h>



RTC_PCF8523 rtc;


// Initialise the RTC module for the first time.
void InitialiseRTC() {

    if (! rtc.begin()) {
        Serial.println("Couldn't find RTC");
        Serial.flush();
        while (1) delay(10);
    }


    // When time needs to be set on a new device, or after a power loss, the
    // following line sets the RTC to the date & time this sketch was compiled
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
    
}

//Return date in format YYYY-MM-DD
String GetCurrentDate() {
    //Get the time and return the date
  DateTime time = rtc.now();
  return 
    time.timestamp(DateTime::TIMESTAMP_DATE);
}

// Return the current hour (HH:MM:SS)
String GetCurrentHour() {
    //Get the time and return the hour
    DateTime time = rtc.now();
  return 
    time.timestamp(DateTime::TIMESTAMP_TIME);
}

#endif