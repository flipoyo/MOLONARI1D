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
void RefreshConfigFromFile();
void LoadConfig();

String GetCurrentDate();
String GetCurrentHour();
unsigned long GetSecondsSinceMidnight();

void InitializeMeasurementTimes();
void InitializeMeasurementCount();
unsigned long CalculateSleepTimeUntilNextMeasurement();

#endif // MY_TIME
