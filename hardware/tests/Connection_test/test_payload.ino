#include <pb.h>
#include <pb_common.h>
#include <pb_decode.h>
#include <pb_encode.h>
#include <MKRWAN.h>
#include "sensor.pb.h"

LoRaModem modem;

String appEui = "a8610a3433408f04";   // AppEUI (JoinEUI)
String appKey = "00112233445566778899AABBCCDDEEFF";  // AppKey (16 octets hex)

void setup() {
  Serial.begin(9600);
  while (!Serial);

  encode();

  Serial.println("Initialisation du modem LoRa...");
  if (!modem.begin(EU868)) {  // Pour l’Europe : EU868
    Serial.println("Échec d'initialisation du modem LoRa !");
    while (true);
  }

  Serial.print("Version modem : ");
  Serial.println(modem.version());
  Serial.print("DevEUI : ");
  Serial.println(modem.deviceEUI());

  Serial.println("Tentative de join OTAA...");
  int connected = modem.joinOTAA(appEui, appKey);

  if (!connected) {
    Serial.println("Échec du join LoRaWAN, réessai...");
    while (!modem.joinOTAA(appEui, appKey)) {
      Serial.print(".");
      delay(10000);
    }
  }

  Serial.println("\nConnecté au réseau LoRaWAN !");
}

void printBuffer(uint8_t* buf, size_t len) {
  for (size_t i = 0; i < len; i++) {
    Serial.print(buf[i], HEX);
    Serial.print(" ");
  }
  Serial.println();
}

String toBase64(const uint8_t *data, size_t len) {
  const char base64_table[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  String result;
  size_t i = 0;

  while (i < len) {
    uint32_t octet_a = i < len ? data[i++] : 0;
    uint32_t octet_b = i < len ? data[i++] : 0;
    uint32_t octet_c = i < len ? data[i++] : 0;

    uint32_t triple = (octet_a << 16) | (octet_b << 8) | octet_c;

    result += base64_table[(triple >> 18) & 0x3F];
    result += base64_table[(triple >> 12) & 0x3F];
    result += (i - 1 < len) ? base64_table[(triple >> 6) & 0x3F] : '=';
    result += (i < len) ? base64_table[triple & 0x3F] : '=';
  }

  return result;
}


void encode() {
  SensorData msg = SensorData_init_zero;

  strncpy(msg.UI, "ferhfuieriu", sizeof(msg.UI));
  msg.time = 1024251555;
  msg.measurements_count = 5;
  msg.measurements[0] = 0.9;
  msg.measurements[1] = 1.78;
  msg.measurements[2] = 2.78;
  msg.measurements[3] = 3.90;
  msg.measurements[4] = 43.89;

  uint8_t buffer[64];
  pb_ostream_t stream = pb_ostream_from_buffer(buffer,sizeof(buffer));
  if (!pb_encode(&stream,SensorData_fields,&msg)){
    Serial.println("Erreur");
    return;
  }

  size_t message_length = stream.bytes_written;

    // === Encodage Base64 via la stack LoRa ===
  String encoded = toBase64(buffer, message_length);
  Serial.print("Encoded (base64): ");
  Serial.println(encoded);

  Serial.print("Base64 (via modem): ");
  Serial.println(encoded);

  Serial.write(buffer, message_length); // pour debug local

}


void loop() {
  encode();

  String data = "20251017,1621,2723,23,21,18,14\n20251017,1626,2743,13,41,38,16";

  // --- Envoi du payload vers le modem ---
  modem.beginPacket();
  modem.write(data);   // <-- ici
  int err = modem.endPacket(true);       // true = envoi confirmé

  if(err > 0){
    Serial.println("Uplink envoyé, lecture RX1/RX2...");
    unsigned long start = millis();
    while(millis() - start < 2000){ // fenêtre RX1
        int packetSize = modem.parsePacket();
        if(packetSize){
            uint8_t downlink[64];
            int len = modem.readBytes(downlink, sizeof(downlink));
            Serial.print("📩 Downlink reçu (UnconfirmedDataDown) : ");
            for(int i=0; i<len; i++){
                Serial.print(downlink[i], HEX);
                Serial.print(" ");
            }
            Serial.println();
            break;
        }
    }
}


 /* if(err > 0){
    Serial.println("✅ Payload envoyé !");

    if (modem.available()) {
      String rcv = modem.readString();
      Serial.print("📩 Message reçu du réseau : ");
      Serial.println(rcv);
    } else {
    Serial.println("Aucun message reçu en downlink.");
    } 
  } else {
    Serial.print("⚠️ Erreur envoi : ");
    Serial.println(err);
  } */

  delay(100000); // 100 s
}
