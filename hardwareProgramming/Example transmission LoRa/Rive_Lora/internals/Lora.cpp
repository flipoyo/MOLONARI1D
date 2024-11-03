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
        LoRa.end();
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
            uint8_t dest = LoRa.read();
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

bool LoraCommunication::performHandshake( uint8_t shiftback)
{

    String payload;
    uint8_t packetNumber;
    RequestType requestType;

   
    while (true)
    {
        if (receivePacket(packetNumber, requestType, payload) && requestType == SYN && packetNumber == 0 && destination != 0xff)
        {
            // get from the saved variable//////////////////////
            sendPacket(shiftback, SYN, "SYN-ACK");
            break;
        }
    }

    int retries = 0;
    Serial.println("SYN-ACK sent.");
    while (retries < 3)
    {
        if (receivePacket(shiftback, requestType, payload) && requestType == ACK)
        {
            Serial.println("Handshake complete. Ready to receive data.");
            return true;
        }
        else
        {
            Serial.println("No ACK received, retrying ...");
            delay(100 * (retries + 1));
            sendPacket(shiftback, SYN, "SYN-ACK");
        }
    }

    if (retries == 3)
    {
        Serial.println("Handshake failed.");
        stopLoRa();
        return false;
    }
}

int LoraCommunication::receivePackets(std::queue<String> &receiveQueue)
{
    uint8_t packetNumber = 0;
    String payload;
    RequestType requestType;
    uint8_t previous_packetNumber = 0;

    while (true)
    {
        if (receivePacket(packetNumber, requestType, payload))
        {
            switch (requestType)
            {
            case FIN:
                Serial.println("FIN received, session closing.");
                return packetNumber; // End loop to reset the session
            default:
                if (receiveQueue.size() >= MAX_QUEUE_SIZE)
                {
                    Serial.println("Queue full, sending FIN to close session.");
                    return packetNumber; // End loop to reset the session
                }
                if (previous_packetNumber == packetNumber)
                {
                    sendPacket(packetNumber, ACK, "ACK");
                    break;
                }
                previous_packetNumber = packetNumber;
                receiveQueue.push(payload); // Add received data to the queue
                sendPacket(packetNumber, ACK, "ACK");
                Serial.println("ACK sent for packet " + String(packetNumber));
                break;
            }
        }
    }
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
