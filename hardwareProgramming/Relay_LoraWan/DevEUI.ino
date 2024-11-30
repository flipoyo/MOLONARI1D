#include <MKRWAN.h>

      LoRaModem modem;

      void setup() {
          Serial.begin(115200);
          while (!Serial);

          if (!modem.begin(EU868)) { // Use your region's frequency
              Serial.println("Failed to start module");
              while (1);
          }

          Serial.print("Device EUI: ");
          Serial.println(modem.deviceEUI());
      }

      void loop() {
      }

