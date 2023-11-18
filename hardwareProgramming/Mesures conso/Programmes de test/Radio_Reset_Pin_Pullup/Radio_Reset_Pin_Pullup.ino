#include <LoRa.h>
#include <ArduinoLowPower.h>

void setup() {
  for (uint8_t pin = 0; pin < NUM_DIGITAL_PINS; pin++)
  {
    // Set the pin to input pullup to save battery
    pinMode(pin, INPUT_PULLUP);
  }

  pinMode(LORA_RESET, OUTPUT);
  digitalWrite(LORA_RESET, LOW);
  
  LowPower.deepSleep();
}

void loop() {
  // put your main code here, to run repeatedly:
}
