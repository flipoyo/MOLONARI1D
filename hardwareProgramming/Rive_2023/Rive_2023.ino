

// Define the data-type of a measurement
#define MEASURE_T double


// Uncomment htis line to enable dignostics log on serial about the main loop
//#define DEBUG
// Uncomment this line to enable diagnostics log on serial for lora operations
//#define LORA_DEBUG

#ifdef DEBUG
#define LOG(x) Serial.print(x)
#define LOG_LN(x) Serial.println(x)
#else
#define LOG(x)
#define LOG_LN(x)
#endif




#include "internals/Lora.hpp"
#include "internals/Waiter.hpp"
#include "internals/Measure_Cache.cpp"

#include <FlashStorage.h>


uint32_t firstMissingMeasurementId = 1;
FlashStorage(firstMissingMeasurementIdFlash, uint32_t);



void setup() {
  // Enable the builtin LED during initialisation
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  // Initialise serial
  Serial.begin(115200);
  
  // Wait for connection to start
  while (!Serial) {
    // Do nothing
  }
  LOG_LN("LoRa relay for Molonari system");
  LOG_LN("See : https://github.com/flipoyo/MOLONARI1D");
  LOG_LN("");

  // Initialising flash from flash
  pinMode(0, INPUT_PULLDOWN);
  if (digitalRead(0) == HIGH) {
    LOG_LN("Resetting flash");
    firstMissingMeasurementIdFlash.write(1);
  } else {
    LOG_LN("Reading settings from flash");
    firstMissingMeasurementId = firstMissingMeasurementIdFlash.read();
  }

  // Input for compatibility mode with Arduino IDE plotter
  pinMode(1, INPUT_PULLDOWN);

  // Initialise Lora
  LOG_LN("Initialising LoRa");
  InitialiseLora(OnGetMeasureCallback);
  LOG_LN("Done");

  // Disable the builtin LED
  digitalWrite(LED_BUILTIN, LOW);
}



void loop() {
  Waiter waiter;
  waiter.startTimer();

  // Request measurement
  LOG_LN("Requesting measurements from n°" + String(firstMissingMeasurementId));
  bool success = RequestMeasurement(firstMissingMeasurementId, 42);
  if (success) {
    LOG_LN("Request sent successfully");
  } else {
    LOG_LN("Failed to send request");
  }

  // Wait for 10 seconds
  waiter.delayUntil(5000);
}


void OnGetMeasureCallback(Measure measure) {
  LOG_LN("Received measure");
  AddMeasure(measure);

  while (IsMeasureAvailable()) {
    firstMissingMeasurementId++;
    firstMissingMeasurementIdFlash.write(firstMissingMeasurementId);
    Measure measure = GetMeasure();

    if (digitalRead(1) == HIGH) {
      // Compatibility mode with Arduino IDE plotter
      Serial.println("T1:" + String(measure.mesure1) + " T2:" + String(measure.mesure2) + " T3:" + String(measure.mesure3) + " T4:" + String(measure.mesure4));
    } else {
      // Default mode
      Serial.println(measure.ToCSVEntry());
    }
  }
}