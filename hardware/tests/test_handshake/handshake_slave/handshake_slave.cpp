/*This script is a basic **LoRa Sender** using the LoRa library. It transmits packets 
containing a "hello" message along with a counter value over the LoRa network. 
The built-in LED toggles on during transmission for visual feedback.
After sending a packet, it waits for 5 seconds before sending the next one.
Perfect for testing LoRa communication with a corresponding receiver script.*/
#include <SPI.h>
#include <Arduino.h>
#include <LoRa.h>

#include "LoRa_Molonari.hpp"

int handshake_once_worked = 0;
int counter = 0;
String appEui = "a8610a35391d6f08";
String devEui = "a8610a34334d710d";
LoraCommunication lora(868E6, devEui, appEui, RoleType::SLAVE);
const int ledPin = LED_BUILTIN;
void setup() {
  pinMode(ledPin, OUTPUT);

  Serial.begin(9600);
  unsigned int time = millis() + 4000;
  while (!Serial && millis() < time) {};

  digitalWrite(ledPin, HIGH);
  delay(1000);
  digitalWrite(ledPin, LOW);

  Serial.println("LoRa Receiver");

  if (!LoRa.begin(868E6)) {
    Serial.println("Starting LoRa failed!");
    while (1);
  }
  lora.startLoRa();
}

uint8_t packetNumber = 0;
RequestType requestType;
String payload;

void loop() {
  
  counter++;
  /*
  digitalWrite(ledPin, HIGH);
  int packetSize = LoRa.parsePacket();
  digitalWrite(ledPin, LOW);
  if(lora.receivePacket(packetNumber, requestType, payload)){
    Serial.print("Received Packet !!! it took " + String (counter) + " tries");
    Serial.print(", packetNumber: " + String(packetNumber));
    Serial.print(", requestType: " + String((uint8_t)requestType)); 
    Serial.println(", payload: " + payload);
    counter = 0;
  };*/
  //delay(300);
  //delay(100);
  Serial.print("listen for handshake for the : " + String(counter) + "th time. ");
  Serial.println("it has already worked before at least " + String(handshake_once_worked) + " times.");
  uint8_t bullshit_arg_shift = 0;
  digitalWrite(ledPin, HIGH);
  if(lora.handshake(bullshit_arg_shift)){
    Serial.print("handshake done \n\n\n ");
    handshake_once_worked++;
  }else{
    Serial.print("handshake failed");
  };
  digitalWrite(ledPin, LOW);
  delay(50);

  /*// send packet
  digitalWrite(LED_BUILTIN, HIGH);
  LoRa.beginPacket();
  LoRa.print("hello ");
  LoRa.print(counter);
  LoRa.endPacket();
  digitalWrite(LED_BUILTIN, LOW);
  */

  delay(100);
}
