#include "Lora.hpp"

#ifdef LORA_DEBUG
#define LORA_LOG(msg) Serial.print(msg);
#define LORA_LOG_HEX(msg) Serial.print(msg, HEX);
#define LORA_LOG_LN(msg) Serial.println(msg);
#else
#define LORA_LOG(msg)
#define LORA_LOG_HEX(msg)
#define LORA_LOG_LN(msg)
#endif
// Constructor: Set pin and frequency for the LoRa module
LoraCommunication::LoraCommunication(long frequency, uint8_t localAdd, uint8_t desti)
    : freq(frequency), localAddress(localAdd), destination(desti), active(false)
{
}

void LoraCommunication::startLoRa()
{
  if (!active)
  {
    int retries = 3;
    while (retries--)
    {
      if (LoRa.begin(freq))
      {
        active = true;
        LORA_LOG_LN("LoRa started.");
        return;
      }
      else
      {
        LORA_LOG_LN("LoRa failed to start, retrying...");
        delay(1000); // Delay before retrying
      }
    }
    LORA_LOG_LN("Starting LoRa failed after retries.");
  }
}

void LoraCommunication::stopLoRa()
{
  if (active)
  {
    LoRa.end(); // This internally calls LoRa.sleep() and stops SPI

    // Step 3: Pull the RESET pin low to cut power if connected directly
    pinMode(LORA_RESET, OUTPUT);
    digitalWrite(LORA_RESET, LOW);
    active = false;
    LORA_LOG_LN("LoRa stopped.");
  }
}

// IL MANQUE LA FONCITION setdesttodefault

void LoraCommunication::sendPacket(uint8_t packetNumber, RequestType requestType, const String &payload)
{
  if (active)
  { 
    uint8_t b = LoRa.random();
    delay(100 + b); // Small delay to ensure buffer is cleared
    bool success = (bool)LoRa.beginPacket();
    if (!success)
    {
      LORA_LOG_LN("Aborting transmission : LoRa module busy");
      return;
    }
    // Calculate and append a simple checksum
    uint8_t checksum = calculateChecksum(destination, localAddress, packetNumber, requestType, payload);
    LoRa.write(checksum);
    LoRa.write(destination);
    LoRa.write(localAddress);
    LoRa.write(packetNumber);
    LoRa.write(requestType);
    //LoRa.write(payload.length()); // Specify payload length
    LoRa.print(payload);

    LoRa.endPacket();

    LORA_LOG("Packet sent: ");
    LORA_LOG_LN(payload);
  }
  else
  {
    LORA_LOG_LN("LoRa is not active, cannot send packet.");
  }
}

bool LoraCommunication::receivePacket(uint8_t &packetNumber, RequestType &requestType, String &payload)
{
  if (!active)
    return false;

  delay(80); // Small delay for synchronization
  int ackTimeout = 2000;
  unsigned long startTime = millis();

  while (millis() - startTime < ackTimeout)
  {
    int packetSize = LoRa.parsePacket();
    if (packetSize)
    {
      uint8_t receivedChecksum = LoRa.read(); // Read the checksum byte
      uint8_t recipient = LoRa.read();
      uint8_t dest = LoRa.read();
      packetNumber = LoRa.read();
      requestType = static_cast<RequestType>(LoRa.read());
      //uint8_t incomingLength = LoRa.read(); // Get payload length

      payload = "";
      while (LoRa.available())
      {
        payload += (char)LoRa.read();
      }

      /*// Verify length
      if (incomingLength != payload.length())
      {
        LORA_LOG_LN("Error: message length mismatch. Expected: " + String(incomingLength) + ", Actual: " + String(payload.length()));
        return false;
      }*/

      // Verify destination
      if (!isValidDestination(recipient, dest, requestType))
      {
        LORA_LOG_LN("Message is not for this device or is out of session.");
        return false;
      }

      // Verify checksum
      uint8_t calculatedChecksum = calculateChecksum(recipient, dest, packetNumber, requestType, payload);
      if (calculatedChecksum != receivedChecksum)
      {
        LORA_LOG_LN("Checksum mismatch: packet discarded.");
        return false;
      }

      // Log received packet details
      LORA_LOG_LN("Received from: 0x" + String(dest, HEX));
      LORA_LOG_LN("Sent to: 0x" + String(recipient, HEX));
      LORA_LOG_LN("Packet Number ID: " + String(packetNumber));
      LORA_LOG_LN("Packet requestType: " + String(requestType));
      //Serial.println("Message length: " + String(incomingLength));
      LORA_LOG_LN("Message: " + payload);
      LORA_LOG_LN("RSSI: " + String(LoRa.packetRssi()));
      LORA_LOG_LN("SNR: " + String(LoRa.packetSnr()));
      LORA_LOG_LN();

      return true;
    }
  }
  return false; // Return false if no packet received within timeout
}

// Helper function to validate the destination of incoming packets
bool LoraCommunication::isValidDestination(int recipient, int dest, RequestType requestType)
{
  if (recipient != localAddress)
  {
    return false; // Not for this device
  }
  if (destination == dest || (requestType == SYN && destination == 0xff && myNet.find(dest) != myNet.end()))
  {
    destination = dest;
    return true;
  }
  return false; // Out of session or invalid destination
}

// Helper function to calculate a simple checksum for data integrity verification
uint8_t LoraCommunication::calculateChecksum(int recipient, int dest, uint8_t packetNumber, RequestType requestType, const String &payload)
{
  uint8_t checksum = recipient ^ dest ^ packetNumber ^ static_cast<uint8_t>(requestType);
  for (char c : payload)
  {
    checksum ^= c;
  }
  return checksum;
}

bool LoraCommunication::isLoRaActive()
{
  return active;
}

// LA FONCTION SUIVANTE N'A PAS LE MEME NOM
bool LoraCommunication::performHandshake(int &shift)
{
// CE BOUT DE CODE N'EST PAS PRESENT DANS L'AUTRE 1
  sendPacket(0, SYN, "");
  LORA_LOG_LN("SYN sent, waiting for SYN-ACK...");
//

  String payload;
  uint8_t packetNumber;
  RequestType requestType;
  int retries = 0;

  // MANQUE UN BOUT DE CODE 2

  // BOUCLE WHILE Y A RIEN QUI EST PAREIL !
  while (retries < 6)
    if (receivePacket(packetNumber, requestType, payload) && requestType == SYN)
    {
      shift = packetNumber;
      LORA_LOG_LN("SYN-ACK received, sending final ACK...");
      sendPacket(packetNumber, ACK, "");
      delay(1000);
      return true;
    }
    else
    {
      uint8_t b = LoRa.random();
      delay(int(b) * (retries + 1));
      sendPacket(0, SYN, "");
      retries++;
    }
  LORA_LOG_LN("Handshake failed.");
  return false;
}

// FONCTION NON PRESENTE DANS L'AUTRE DOCUMENT ET MANQUE RECEIVE
uint8_t LoraCommunication::sendPackets(std::queue<String> &sendQueue)
{
  uint8_t packetNumber = 0;

  String payload;
  RequestType requestType;
  uint8_t receivedPacketNumber;
  int retries = 0;

  while (!sendQueue.empty())
  {
    String message = sendQueue.front(); // Get the current message but don't pop yet
    sendPacket(packetNumber, DATA, message);
    retries = 0;

    while (retries < 6)
    {
      if (receivePacket(receivedPacketNumber, requestType, payload) && requestType == ACK && receivedPacketNumber == packetNumber)
      {
        LORA_LOG_LN("ACK received for packet " + String(packetNumber));
        sendQueue.pop(); // Only pop after receiving ACK
        packetNumber++;
        break;
      }
      else if (requestType == FIN)
      {
        LORA_LOG_LN("FIN received for packet " + String(packetNumber));
        while (!sendQueue.empty())
        {
          sendQueue.pop();
        }
        packetNumber++;
        break;
      }
      else
      {
        LORA_LOG_LN("No ACK received, retrying for packet " + String(packetNumber));
        uint8_t b = LoRa.random();
        delay(int(b) * (retries + 1));
        sendPacket(packetNumber, DATA, message);
        retries++;
      }
    }
    if (retries == 6)
    {
      LORA_LOG_LN("Packet send failed after retries for packet " + String(packetNumber));
      while (!sendQueue.empty())
      {
        sendQueue.pop();
      }
      break;
    }

    delay(100);
  }
  return packetNumber;
}

// PAS LA MEME NATURE D'OBJET EN ARGUMENT
void LoraCommunication::closeSession(uint8_t lastPacket)
{
  sendPacket(lastPacket, FIN, "");
  LORA_LOG_LN("FIN sent, waiting for final ACK...");

  String payload;
  uint8_t packetNumber;
  RequestType requestType;
  int retries = 0;

  while (retries < 3)
  {
    if (receivePacket(packetNumber, requestType, payload) && requestType == FIN && packetNumber == lastPacket)
    {
      LORA_LOG_LN("Final ACK received, session closed.");
      return;
    }
    else
    {
      LORA_LOG_LN("No final ACK, retrying...");
      uint8_t b = LoRa.random();
      delay(int(b) * (retries + 1));
      sendPacket(lastPacket, FIN, "");
      retries++;
    }
  }
  LORA_LOG_LN("Session closure failed after retries.");
}
