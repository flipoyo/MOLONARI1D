#include <pb.h>
#include <pb_common.h>
#include <pb_decode.h>
#include <pb_encode.h>
#include <MKRWAN.h>
#include "sensor.pb.h"

LoRaModem modem;

#include "arduino_secrets.h" 
// Please enter your sensitive data in the Secret tab or arduino_secrets.h 
String appEui = SECRET_APP_EUI; // AppEUI (JoinEUI)
String appKey = SECRET_APP_KEY; // AppKey (16 hex bytes)

String appEui = "a8610a3433408f04";   // AppEUI (JoinEUI)
String appKey = "00112233445566778899aabbccddeeff";  // AppKey (16 hex bytes)

void setup() {
  Serial.begin(9600);
  while (!Serial);

  Serial.println("Initializing LoRa modem...");
  if (!modem.begin(EU868)) {  // For Europe: EU868
    Serial.println("LoRa modem initialization failed!");
    while (true);
  }

  Serial.print("Modem version: ");
  Serial.println(modem.version());
  Serial.print("DevEUI: ");
  Serial.println(modem.deviceEUI());

  Serial.println("Attempting OTAA join...");
  int connected = modem.joinOTAA(appEui, appKey);

  if (!connected) {
    Serial.println("LoRaWAN join failed, retrying...");
    while (!modem.joinOTAA(appEui, appKey)) {
      Serial.print(".");
      delay(10000);
    }
  }

  Serial.println("\nConnected to LoRaWAN network!");
}

bool encode(uint8_t *outBuffer, size_t outSize, size_t &messageLength) {
    SensorData msg = SensorData_init_zero;

    strncpy(msg.UI, "ferhfuieriu", sizeof(msg.UI));
    msg.time = 1024251555;
    msg.measurements_count = 6;
    msg.measurements[0] = 0.9;
    msg.measurements[1] = 1.78;
    msg.measurements[2] = 2.78;
    msg.measurements[3] = 3.90;
    msg.measurements[4] = 43.89;
    msg.measurements[5] = 4.8;

    pb_ostream_t stream = pb_ostream_from_buffer(outBuffer, outSize);
    if (!pb_encode(&stream, SensorData_fields, &msg)) {
        Serial.println("Protobuf encoding error!");
        return false;
    }

    messageLength = stream.bytes_written;
    Serial.print("Binary payload (length ");
    Serial.print(messageLength);
    Serial.println(" bytes) ready to send!");
    return true;
}

void loop() {
  //String data = "20251017,1621,2723,23,21,18,14";
  uint8_t buffer[64];
  size_t messageLength = 0;

  if (!encode(buffer, sizeof(buffer), messageLength)) {
      Serial.println("Error, payload not sent");
      delay(10000);
      return;
  }

  // --- Send binary payload to the modem ---
  modem.beginPacket();
  modem.write(buffer, messageLength);  // Direct binary send
  int err = modem.endPacket(true);     // true = confirmed uplink

  if (err > 0) {
    Serial.println("Message sent correctly!");
  } else {
    Serial.println("Error sending message :(");
    Serial.println("(you may send a limited number of messages per minute, depending on signal strength");
    Serial.println("this can vary from one message every few seconds to one per minute)");
  }

  /* Code to try receiving data from the server.
     Currently causes the board to hang when something is received
     (it stays in the decoding loop and never exits).
  delay(1000);
  if (!modem.available()) {
    Serial.println("No downlink message received at this time.");
    return;
  }
  char rcv[64];
  int i = 0;
  while (modem.available()) {
    rcv[i++] = (char)modem.read();
  }
  Serial.print("Received: ");
  for (unsigned int j = 0; j < i; j++) {
    Serial.print(rcv[j] >> 4, HEX);
    Serial.print(rcv[j] & 0xF, HEX);
    Serial.print(" ");
  }
  Serial.println();
*/
  delay(1 * 60000); // wait 1 minute before next message
}