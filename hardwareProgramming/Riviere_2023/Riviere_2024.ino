#include "internals/Lora.hpp"
//#include "internals/Reader.hpp"
//#include "internals/SD_Initializer.cpp"
#include <queue>  // Using standard library queue

uint8_t localAddress = 0xaa;
LoraCommunication lora(868E6, localAddress);
std::queue<String> sendQueue;  // Queue for storing SD card data to send
//Reader dataReader; 
//const int CSPin = 5;
//const char filename[] = "RIVIERE.CSV";
void setup() {
  // Enable the builtin LED during initialisation
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  // Initialise Serial
  Serial.begin(115200);
  // Wait up to 5 seconds for serial to connect
  unsigned long end_date = millis() + 5000;
  while (!Serial && millis() < end_date) {
    // Do nothing
  }

  /*// Initialise SD Card
  Serial.print("Initialising SD card ...");
  bool success = InitialiseLog(CSPin);
  if (success) {
    Serial.println(" Done");
  } else {
    Serial.println(" Failed");
    noInterrupts();
    while (true) {}
  }*/

  //dataReader.EstablishConnection(0);  // Start reading from the file, line_cursor will be preserved
  

  // Disable the builtin LED
  pinMode(LED_BUILTIN, INPUT_PULLDOWN);

  Serial.println("Initialisation complete !");
  
  Serial.println("Waiting to start communication...");
}

void loadDataIntoQueue() {
  for(int i = 1 ; i <= 280 ;i++) {
    String line = "hellor from riviere" + String(i);
    sendQueue.push(line);
    if (sendQueue.size() >= 300) break;  // Limit queue size if necessary
  }
}

void loop() {
  Serial.println("Starting new communication session...");
  lora.startLoRa();
  uint8_t destination = 0xbb;

  if (performHandshake(destination)) {
    loadDataIntoQueue();  // Load data from SD card to sendQueue
    sendPackets(destination);
  }

  lora.stopLoRa();
  delay(10000);
}

bool performHandshake(uint8_t destination) {
  lora.sendPacket(destination, 0, SYN, "");
  Serial.println("SYN sent, waiting for SYN-ACK...");

  String payload;
  uint8_t packetNumber, sender;
  RequestType requestType;

  if (lora.receivePacket(sender, packetNumber, requestType, payload) && sender == destination && requestType == SYN && packetNumber == 0) {
    Serial.println("SYN-ACK received, sending final ACK...");
    lora.sendPacket(destination, packetNumber, ACK, "");
    delay(1000);
    return true;
  } else {
    Serial.println("Handshake failed.");
    lora.stopLoRa();
    return false;
  }
}

int sendPackets(uint8_t destination) {
  int packetNumber = 1;
  while (!sendQueue.empty()) {
    String message = sendQueue.front();  // Get the current message but don't pop yet
    lora.sendPacket(destination, packetNumber, DATA, message);

    // Wait for ACK from Rive
    String payload;
    RequestType requestType;
    uint8_t receivedPacketNumber;
    int retries = 0;
    uint8_t sender;

    while (retries < 6) {
      if (lora.receivePacket(sender, receivedPacketNumber, requestType, payload) && sender == destination && requestType == ACK && receivedPacketNumber == packetNumber) {
        Serial.println("ACK received for packet " + String(packetNumber));
        sendQueue.pop();  // Only pop after receiving ACK
        break;
      } else {
        Serial.println("No ACK received, retrying for packet " + String(packetNumber));
        delay(100 * (retries + 1));
        lora.sendPacket(destination, packetNumber, DATA, message);
        retries++;
      }
    }
    if (retries == 6) {
      Serial.println("Packet send failed after retries for packet " + String(packetNumber));
      break;
    }
    packetNumber++;
    delay(500);
  }
  closeSession(destination, packetNumber);
}

void closeSession(uint8_t destination, int lastPacket) {
  lora.sendPacket(destination, lastPacket, FIN, "");
  Serial.println("FIN sent, waiting for final ACK...");

  String payload;
  uint8_t sender, packetNumber;
  RequestType requestType;
  int retries = 0;

  while (retries < 3) {
    if (lora.receivePacket(sender, packetNumber, requestType, payload) && sender == destination && requestType == FIN && packetNumber == lastPacket) {
      Serial.println("Final ACK received, session closed.");
      return;
    } else {
      Serial.println("No final ACK, retrying...");
      delay(100 * (retries + 1));
      lora.sendPacket(destination, lastPacket, FIN, "");
      retries++;
    }
  }
   while (!sendQueue.empty()) {
    sendQueue.pop();
   }
  Serial.println("Session closure failed after retries.");
}
