#ifndef MY_TIME
#define MY_TIME

#include <RTClib.h>
#include <vector>

// ----- RTC -----
extern RTC_PCF8523 externalRtc;
extern std::vector<unsigned long> measurementTimesVec;
extern int measurementCount;

// ----- Fonctions -----
String UIntTo2DigitString(uint8_t x);

void InitialiseRTC();

String GetCurrentDate();
String GetCurrentHour();
unsigned long GetSecondsSinceMidnight();

unsigned long CalculateSleepTimeUntilNextMeasurement(unsigned long previousMeasurementTime, int measurementInterval);
unsigned long CalculateSleepTimeUntilNextCommunication(unsigned long previousCommunicationTime, int communicationInterval);

#endif // MY_TIME
