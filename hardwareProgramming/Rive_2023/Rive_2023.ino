
//#define LORA_DEBUG

#include "internals/Lora.hpp"


#ifdef DEBUG
#define LOG(x) Serial.print(x)
#define LOG_LN(x) Serial.println(x)
#else
#define LOG(x)
#define LOG_LN(x)
#endif


unsigned int firstMissingMeasurementId = 0;



void setup() {
  // put your setup code here, to run once:
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  Serial.begin(115200);
  
  while (!Serial)
  LOG_LN("LoRa relay for Molonari system");
  LOG_LN("15/11/2023");
  LOG_LN("See : https://github.com/flipoyo/MOLONARI1D");
  LOG_LN("");

  LOG_LN("Initialising LoRa");
  InitialiseLora(OnGetMeasureCallback);
  LOG_LN("Done");

  digitalWrite(LED_BUILTIN, LOW);
}

void loop() {
  // put your main code here, to run repeatedly:
  LOG_LN("Requesting measurements");
  bool success = RequestMeasurement(firstMissingMeasurementId, 42);
  if (success) {
    LOG_LN("Request sent successfully");
  } else {
    LOG_LN("Failed to send request");
  }

  delay(10000);
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