/*This script demonstrates a basic LoRa receiver using the LoRa library. 
It initializes the LoRa module, listens for incoming packets, and prints the received 
data along with RSSI (Received Signal Strength Indicator) and SNR (Signal-to-Noise Ratio)
 to the Serial Monitor.*/
#include <SPI.h>
#include <LoRa.h>

void setup() {
  Serial.begin(9600);
  while (!Serial);

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);
  delay(1000);
  digitalWrite(LED_BUILTIN, LOW);

  Serial.println("LoRa Receiver");

  if (!LoRa.begin(868E6)) {
    Serial.println("Starting LoRa failed!");
    while (1);
  }
}

void loop() {
  // try to parse packet
  int packetSize = LoRa.parsePacket();
  if (packetSize) {
    // received a packet
    Serial.print("Received packet '");

    // read packet
    while (LoRa.available()) {
      Serial.print((char)LoRa.read());
    }

    // print RSSI of packet
    Serial.println("' with RSSI " + String(LoRa.packetRssi()) + "dbm and SNR " + String(LoRa.packetSnr()) + "db");
  }
}
