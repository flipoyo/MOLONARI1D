/*This script is a basic **LoRa Sender** using the LoRa library. It transmits packets 
containing a "hello" message along with a counter value over the LoRa network. 
The built-in LED toggles on during transmission for visual feedback.
After sending a packet, it waits for 5 seconds before sending the next one.
Perfect for testing LoRa communication with a corresponding receiver script.*/
#include <SPI.h>
#include <Arduino.h>
#include <LoRa.h>

#include "LoRa_Molonari.hpp"

bool handshake_once_worked = false;
int counter = 0;
String appEui = "70B3D57ED003C0A4";
String devEui = "0018B20000000001";
LoraCommunication lora(868E6, devEui, appEui, RoleType::SLAVE);

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);

  Serial.begin(9600);
  delay(4000);

  digitalWrite(LED_BUILTIN, HIGH);
  delay(1000);
  digitalWrite(LED_BUILTIN, LOW);

  Serial.println("LoRa Sender");

  if (!LoRa.begin(868E6)) {
    Serial.println("Starting LoRa failed!");
    while (1);
  }
}

void loop() {
  Serial.println("listen for handshake for the : " + String(counter) + "th time.");
  Serial.println("has already worked before ? " + String(handshake_once_worked));
  uint8_t bullshit_arg_shift = 0;
  if(lora.handshake(bullshit_arg_shift)){
    Serial.print("handshake done");
    handshake_once_worked = true;
  }else{
    Serial.print("handshake failed");
  }

  /*// send packet
  digitalWrite(LED_BUILTIN, HIGH);
  LoRa.beginPacket();
  LoRa.print("hello ");
  LoRa.print(counter);
  LoRa.endPacket();
  digitalWrite(LED_BUILTIN, LOW);
  */
  counter++;

  delay(200);
}
