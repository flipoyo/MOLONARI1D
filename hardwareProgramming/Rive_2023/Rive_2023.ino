

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


unsigned int firstMissingMeasurementId = 1;



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

  // Re-enable Lora receiving
  // I am not sure how but it seems to help
  LoRa.receive();

  // Request measurement
  LOG_LN("Requesting measurements from n°" + String(firstMissingMeasurementId));
  bool success = RequestMeasurement(firstMissingMeasurementId, 42);
  if (success) {
    LOG_LN("Request sent successfully");
  } else {
    LOG_LN("Failed to send request");
  }

  // Wait for 10 seconds
  waiter.delayUntil(10000);
}


void OnGetMeasureCallback(Measure measure) {
  if (measure.id == firstMissingMeasurementId) {
    firstMissingMeasurementId++;
  } else {
    LOG_LN("Wrong measure received : got n°" + String(measure.id) + " insted of n°" + String(firstMissingMeasurementId));
  }

  LOG_LN("Received measure : ");
  Serial.println(measure.ToCSVEntry());
}