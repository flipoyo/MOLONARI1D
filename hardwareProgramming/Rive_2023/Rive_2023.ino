
#include "internals/Lora.hpp"

unsigned int firstMissingMeasurementId = 0;



void setup() {
  // put your setup code here, to run once:

  Serial.begin(115200);
  
  while (!Serial)

  Serial.println("Initialising LoRa");
  InitialiseLora(OnGetMeasureCallback);
  Serial.println("Done");
}

void loop() {
  // put your main code here, to run repeatedly:
  Serial.println("Requesting measurements");
  bool success = RequestMeasurement(firstMissingMeasurementId, 42);
  if (success) {
    Serial.println("Request sent successfully");
  } else {
    Serial.println("Failed to send request");
  }

  delay(10000);
}


void OnGetMeasureCallback(Measure measure) {
  if (measure.id == firstMissingMeasurementId) {
    firstMissingMeasurementId++;
  }

  Serial.println("Received measure : ");
  Serial.println(measure.ToString());
}