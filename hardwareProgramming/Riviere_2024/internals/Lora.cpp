#include "Lora.hpp"

// Constructor: Set pin and frequency for the LoRa module
LoraCommunication::LoraCommunication(long frequency, uint8_t localAddress, uint8_t destination)
    : freq(frequency), localAddress(localAddress), destination(destination), active(false)
{
  LoRa.enableCrc();
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
        Serial.println("LoRa started.");
        return;
      }
      else
      {
        Serial.println("LoRa failed to start, retrying...");
        delay(1000); // Delay before retrying
      }
    }
    Serial.println("Starting LoRa failed after retries.");
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
    Serial.println("LoRa stopped.");
  }
}

void LoraCommunication::sendPacket(uint8_t packetNumber, RequestType requestType, const String &payload)
{
  if (active)
  {
    // Flush LoRa buffer to clear any residual data
    uint8_t t = requestType;
    delay(100); // Small delay to ensure buffer is cleared
    LoRa.beginPacket();
    LoRa.write(destination);
    LoRa.write(localAddress);
    LoRa.write(packetNumber);
    LoRa.write(requestType);
    LoRa.write(payload.length()); // Ensure packet length is specified
    LoRa.print(payload);
    LoRa.endPacket();
    Serial.print("Packet sent: ");
    Serial.println(payload);
  }
  else
  {
    Serial.println("LoRa is not active, cannot send packet.");
  }
}

bool LoraCommunication::receivePacket(uint8_t &packetNumber, RequestType &requestType, String &payload)
{
  if (!active)
    return false;
  delay(80);
  int ackTimeout = 2000;
  unsigned long startTime = millis();
  while (millis() - startTime < ackTimeout)
  {
    int packetSize = LoRa.parsePacket();
    if (packetSize)
    {
      int recipient = LoRa.read();
      int dest = LoRa.read();
      packetNumber = LoRa.read();
      requestType = static_cast<RequestType>(LoRa.read());
      uint8_t incomingLength = LoRa.read(); // Get payload length

      payload = "";
      while (LoRa.available())
      {
        payload += (char)LoRa.read();
      }

      if (incomingLength != payload.length())
      {
        Serial.println("Error: message length mismatch.  Message length: " + String(incomingLength) + "Message: " + payload);
        Serial.println();
        return false; // Exit on length error
      }

      if (recipient != localAddress)
      {
        Serial.println("This message is not for me. Sent to: 0x" + String(recipient, HEX));
        Serial.println();
        return false; // Ignore packet if not for this device
      }

      if (destination == dest || (requestType == SYN && destination == 0xff && myNet.find(dest) != myNet.end()))
      {
        destination = dest;
      }
      else
      {
        Serial.println("This message is out of this session.");
        Serial.println();
        return false;
      }

      Serial.println("Received from: 0x" + String(destination, HEX));
      Serial.println("Sent to: 0x" + String(recipient, HEX));
      Serial.println("Packet Number ID: " + String(packetNumber));
      Serial.println("Packet requestType : " + String(requestType) + "  " + String(requestType == SYN));
      Serial.println("Message length: " + String(incomingLength));
      Serial.println("Message: " + payload);
      Serial.println("RSSI: " + String(LoRa.packetRssi()));
      Serial.println("Snr: " + String(LoRa.packetSnr()));
      Serial.println();

      return true;
    }
  }
  return false; // Return false if no packet received within timeout
}

bool LoraCommunication::isLoRaActive()
{
  return active;
}

bool LoraCommunication::performHandshake(int &shift)
{
  sendPacket(0, SYN, "");
  Serial.println("SYN sent, waiting for SYN-ACK...");

  String payload;
  uint8_t packetNumber;
  RequestType requestType;

  if (receivePacket(packetNumber, requestType, payload) && requestType == SYN)
  {
    shift = packetNumber;
    Serial.println("SYN-ACK received, sending final ACK...");
    sendPacket(packetNumber, ACK, "");
    delay(1000);
    return true;
  }
  else
  {
    Serial.println("Handshake failed.");
    stopLoRa();
    return false;
  }
}

int LoraCommunication::sendPackets(std::queue<String> &sendQueue)
{
  int packetNumber = 1;

  String payload;
  RequestType requestType;
  uint8_t receivedPacketNumber;
  int retries = 0;

  while (!sendQueue.empty())
  {
    String message = sendQueue.front(); // Get the current message but don't pop yet
    sendPacket(packetNumber, DATA, message);

    while (retries < 6)
    {
      if (receivePacket(receivedPacketNumber, requestType, payload) && requestType == ACK && receivedPacketNumber == packetNumber)
      {
        Serial.println("ACK received for packet " + String(packetNumber));
        sendQueue.pop(); // Only pop after receiving ACK
        packetNumber++;
        break;
      }
      else if (requestType == FIN)
      {
        while (!sendQueue.empty())
        {
          sendQueue.pop();
        }
      }
      else
      {
        Serial.println("No ACK received, retrying for packet " + String(packetNumber));
        delay(100 * (retries + 1));
        sendPacket(packetNumber, DATA, message);
        retries++;
      }
    }
    if (retries == 6)
    {
      Serial.println("Packet send failed after retries for packet " + String(packetNumber));
      while (!sendQueue.empty())
      {
        sendQueue.pop();
      }
      break;
    }

    delay(100);
  }
  return packetNumber - 1;
}

void LoraCommunication::closeSession(int lastPacket)
{
  sendPacket(lastPacket, FIN, "");
  Serial.println("FIN sent, waiting for final ACK...");

  String payload;
  uint8_t packetNumber;
  RequestType requestType;
  int retries = 0;

  while (retries < 6)
  {
    if (receivePacket(packetNumber, requestType, payload) && requestType == FIN && packetNumber == lastPacket)
    {
      Serial.println("Final ACK received, session closed.");
      return;
    }
    else
    {
      Serial.println("No final ACK, retrying...");
      delay(100 * (retries + 1));
      sendPacket(lastPacket, FIN, "");
      retries++;
    }
    Serial.println("Session closure failed after retries.");
  }
}
