/*
This firmware will be is meant for the LoRa relay in the Molonari system.

Functionalities :
  - Request measurements from the sensors
  - Print the measurements on the serial port

In long term, this firmware will be able to :
  - Send the measurements to the server

Required hardware :
 - Arduino MKR WAN 1310
*/


// ----- Settings -----

// Define the data-type of a measurement
#define MEASURE_T double


// Uncomment this line to enable dignostics log on serial about the main loop
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


// ----- Dependencies -----

#include "internals/Lora.hpp"
#include "internals/Waiter.hpp"
#include "internals/Measure_Cache.cpp"

#include <FlashStorage.h>


// ----- Main loop variables -----

// Id of the first measurement that this card does not know
uint32_t firstMissingMeasurementId = 1;
// Flash storage for the firstMissingMeasurementId
FlashStorage(firstMissingMeasurementIdFlash, uint32_t);


// ----- Main Setup -----

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

  // Initialising flash
  pinMode(0, INPUT_PULLDOWN);   // INPUT_PULLDOWN -> The pin is defaulted to 0 even if it is not connected to anything. Otherwise, it could have a random value
  if (digitalRead(0) == LOW || firstMissingMeasurementIdFlash.read() == 0) {
    // Reset the variables stored into flash
    LOG_LN("Resetting flash");
    firstMissingMeasurementIdFlash.write(1);
  } else {
    // Initialise firstMissingMeasurementId using flash
    LOG_LN("Reading settings from flash");
    firstMissingMeasurementId = firstMissingMeasurementIdFlash.read();
  }

  // Setup pin 1 as input for compatibility mode with Arduino IDE plotter
  pinMode(1, INPUT_PULLDOWN);

  // Initialise Lora
  LOG_LN("Initialising LoRa");
  InitialiseLora(OnGetMeasureCallback);
  LOG_LN("Done");

  // Disable the builtin LED
  digitalWrite(LED_BUILTIN, LOW);
}


// ----- Main loop -----

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


// Function called when a measure is received
void OnGetMeasureCallback(Measure measure) {
  LOG_LN("Received measure");
  MeasureQueue.Add(measure);

  while (MeasureQueue.Available()) {
    firstMissingMeasurementId++;
    firstMissingMeasurementIdFlash.write(firstMissingMeasurementId);
    Measure measure = MeasureQueue.Dequeue();

    if (digitalRead(1) == HIGH) {
      // Compatibility mode with Arduino IDE plotter
      Serial.println("T1:" + String(measure.chanel1) + " T2:" + String(measure.chanel2) + " T3:" + String(measure.chanel3) + " T4:" + String(measure.chanel4));
    } else {
      // Default mode
      Serial.println(measure.ToCSVEntry());
    }
  }
}