#include <LoRa.h>
#include <ArduinoLowPower.h>

void setup() {
  // put your setup code here, to run once:
  LoRa.begin(868E6);
  LoRa.end();

  pinMode(LORA_RESET, OUTPUT);
  digitalWrite(LORA_RESET, LOW);
  
  LowPower.deepSleep();
}

void loop() {
  // put your main code here, to run repeatedly:
}
