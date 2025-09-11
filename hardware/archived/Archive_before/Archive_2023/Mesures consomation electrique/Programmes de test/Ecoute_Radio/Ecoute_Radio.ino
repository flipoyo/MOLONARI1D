#include <LoRa.h>
#include <ArduinoLowPower.h>

void setup() {
  LoRa.begin(868E6);
  LoRa.receive();

  LowPower.attachInterruptWakeup(LORA_IRQ, onReceiveLoraPacket, RISING);
  LowPower.deepSleep();
}

void loop() {
  LowPower.deepSleep();
}

void onReceiveLoraPacket() {
  // Do nothing
}
