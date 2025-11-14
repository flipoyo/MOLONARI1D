#include <MKRWAN.h>
//#include <RTCZero.h>

LoRaModem modem;
//RTCZero rtc;

String appEui = "a8610a3433408f04";   // AppEUI (JoinEUI)
String appKey = "00112233445566778899AABBCCDDEEFF";  // AppKey (16 octets hex)

void setup() {
  Serial.begin(9600);
  while (!Serial);

  //rtc.begin();
  //rtc.setEpoch(1697542500); // exemple : timestamp initial

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


void loop() {
  String data = "20251017,1621,2723,23,21,18,14\n20251017,1626,2743,13,41,38,16";

  /*if (!modem.available()) {
  Serial.println("Modem non disponible, redémarrage...");
  modem.restart();
  modem.begin(EU868);
}
*/
  // --- Envoi du payload ---
  modem.beginPacket();
  modem.write(data);
  int err = modem.endPacket(true); // true = envoi confirmé

  if(err > 0){
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
  }

  delay(100000); // 5 min
}

