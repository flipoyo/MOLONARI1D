/*This script is a basic **LoRa Sender** using the LoRa library. It transmits packets 
containing a "hello" message along with a counter value over the LoRa network. 
The built-in LED toggles on during transmission for visual feedback.
After sending a packet, it waits for 5 seconds before sending the next one.
Perfect for testing LoRa communication with a corresponding receiver script.*/
#include <SPI.h>
#include <LoRa.h>

int counter = 0;

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
  Serial.print("Sending packet: ");
  Serial.println(counter);

  // send packet
  digitalWrite(LED_BUILTIN, HIGH);
  LoRa.beginPacket();
  LoRa.print("hello ");
  LoRa.print(counter);
  LoRa.endPacket();
  digitalWrite(LED_BUILTIN, LOW);

  counter++;

  delay(5000);
}
