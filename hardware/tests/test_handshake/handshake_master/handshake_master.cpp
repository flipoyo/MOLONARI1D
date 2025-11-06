/*This script demonstrates a basic LoRa receiver using the LoRa library. 
It initializes the LoRa module, listens for incoming packets, and prints the received 
data along with RSSI (Received Signal Strength Indicator) and SNR (Signal-to-Noise Ratio)
 to the Serial Monitor.*/
#include <SPI.h>
#include <Arduino.h>
#include <LoRa.h>

#include "LoRa_Molonari.hpp"

int handshake_worked = 0;
int handshake_failed = 0;
int counter = 0;
String laFLUSH = "flushflushflushflushflush";
String appEui = "a8610a35391d6f08";
String devEui = "a8610a34334d710d";
long previous_time = millis();

LoraCommunication lora(868E6, devEui, appEui, RoleType::MASTER);
const int ledPin = LED_BUILTIN;
void setup() {
  Serial.begin(9600);
  unsigned int time = millis() + 4000;
  while (!Serial && millis() < time) {};

  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, HIGH);
  delay(1000);
  digitalWrite(ledPin, LOW);

  Serial.println("LoRa sender via sendpacket");

  if (!LoRa.begin(868E6)) {
    Serial.println("Starting LoRa failed!");
    while (1);
  }
  lora.startLoRa();
  previous_time = millis();
}

void loop() {
  /*
  digitalWrite(ledPin, HIGH);
  lora.startLoRa();
  lora.sendPacket(0, SYN, "SYN");
  digitalWrite(ledPin, LOW);
  Serial.println("one SYN packet sent");
  delay(100);*/

  //lora.stopLoRa();
  //delay(500);
  
  // try to parse packet
  Serial.print("sending handshake for the : " + String(counter) + "th time. ");
  uint8_t bullshit_arg_shift = 0;
  digitalWrite(ledPin, HIGH);
  if(lora.handshake(bullshit_arg_shift)){
    Serial.println("handshake done. \n\n It took " + String(millis() - previous_time) + " ms.\n\n\n");
    handshake_worked ++;
    previous_time = millis();
  }else{
    Serial.println("handshake failed. \n\n It took " + String(millis() - previous_time) + " ms.\n\n\n");
    handshake_failed ++;
  };
  Serial.println("success : " + String(handshake_worked) + "; failure(s): " + String(handshake_failed) + ".\n");
  digitalWrite(ledPin, LOW);
  //delay(500);
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
