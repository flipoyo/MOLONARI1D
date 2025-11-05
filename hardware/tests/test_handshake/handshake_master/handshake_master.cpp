/*This script demonstrates a basic LoRa receiver using the LoRa library. 
It initializes the LoRa module, listens for incoming packets, and prints the received 
data along with RSSI (Received Signal Strength Indicator) and SNR (Signal-to-Noise Ratio)
 to the Serial Monitor.*/
#include <SPI.h>
#include <Arduino.h>
#include <LoRa.h>

#include "LoRa_Molonari.hpp"

bool handshake_once_worked = false;
int counter = 0;
String laFLUSH = "flushflushflushflushflush";
String appEui = "a8610a35391d6f08";
String devEui = "a8610a34334d710d";

LoraCommunication lora(868E6, devEui, appEui, RoleType::MASTER);
const int ledPin = LED_BUILTIN;
void setup() {
  Serial.begin(9600);
  while (!Serial);

  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, HIGH);
  delay(1000);
  digitalWrite(ledPin, LOW);

  Serial.println("LoRa Receiver");

  if (!LoRa.begin(868E6)) {
    Serial.println("Starting LoRa failed!");
    while (1);
  }
}

void loop() {
  digitalWrite(ledPin, HIGH);
  lora.sendPacket(0, SYN, "SYN");
  Serial.println("one SYN packet sent");
  delay(100);
  digitalWrite(ledPin, LOW);
  delay(200);
  
  /*// try to parse packet
  Serial.println("sending handshake for the : " + String(counter) + "th time.");
  Serial.println("has already worked before ? " + String(handshake_once_worked));
  uint8_t bullshit_arg_shift = 0;

  if(lora.handshake(bullshit_arg_shift)){
    Serial.print("handshake done");
    handshake_once_worked = true;
  }else{
    Serial.print("handshake failed");
  }*/
  /*
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
  }*/
}
