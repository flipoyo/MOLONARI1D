/*This test code verifies the functionality of the **MKRWAN** library by simulating 
data transmission to a LoRaWAN server using OTAA authentication. It includes features 
like payload retries, low-power modem mode, and adaptive data rate configuration.*/

#include <MKRWAN.h>
#include <queue>
LoRaModem modem;

// Define array of records
String data[96];

void setup() {
  // Setup the serial connection for debugging
  Serial.begin(9600);
  while (!Serial);

  // Call SetUpLoRaWAN function to connect the Arduino with the TTN server
  while (!SetUpLoRaWAN()) {
    Serial.println("Error in initialization of LoRaWAN. Retrying...");
    delay(10000);
  }

  // Fill the data array with 96 records for testing purposes
  for (int i = 0; i < 96; i++) {
    data[i] = "2024-11-07,10:00:12,21.55,22.11,21.99,21.a" + String(i);
  }
}

void loop() {
  // Call SendQueue function to send the records
  if (SendQueue(data)) {
    Serial.println("All records sent successfully!");
  } else {
    Serial.println("Failed to send all records. Retrying...");
  }

  // Put the modem into low-power mode to save energy
  modem.sleep(true);

  // Add delay before the next sending cycle (example: 24-hour delay for daily updates)
  delay(86400000); // 86400000 ms = 24 hours
}

// Function to send a queue of data
bool SendQueue(String* d) {
  int counter = 0; // Counter for retry attempts
  
  for (int i = 0; i < 96; i++) {
    String payload = d[i];
    int err;
    
    do {
      counter++;
      
      // Begin sending the payload
      modem.beginPacket();
      modem.print(payload);
      err = modem.endPacket(true); // Confirmed sending
      
      if (err <= 0) {
        Serial.println("Error in sending. Retrying...");
        delay(10000); // Retry delay
      }

      // Stop retries if the limit is reached
      if (counter == 20) {
        Serial.println("Retry limit reached. Aborting...");
        return false;
      }
    } while (err <= 0);
    
    // Log the sent payload
    Serial.print("Sent: ");
    Serial.println(payload);
    
    // Delay between sending records
    delay(10000);
  }
  
  return true;
}

// Function to setup the LoRaWAN connection
bool SetUpLoRaWAN() {
  // Enter the appEUI and appKey from the TTN server
  String appEui = "0000000000000000";
  String appKey = "387BC5DEF778168781DDE361D4407953";
  
  // Initialize the modem with the regional band (e.g., EU868)
  if (!modem.begin(EU868)) {
    Serial.println("Failed to start module");
    return false;
  }

  // Join the network using OTAA (Over-The-Air-Activation)
  int connected = modem.joinOTAA(appEui, appKey);
  if (!connected) {
    Serial.println("Failed to connect. Ensure signal strength or move near a window.");
    return false;
  }

  // Configure modem settings
  modem.minPollInterval(60); // Set minimum polling interval to 60 seconds
  modem.setADR(true); // Enable Adaptive Data Rate (ADR)

  // Send a confirmation message to indicate the start of transmission
  int err;
  do {
    modem.beginPacket();
    modem.print("Start Sending...");
    err = modem.endPacket(true);
    delay(8000);
  } while (err <= 0);

  // Put the modem into low-power mode to save energy until needed
  modem.sleep(true);

  Serial.println("LoRaWAN setup successful.");
  return true;
}
