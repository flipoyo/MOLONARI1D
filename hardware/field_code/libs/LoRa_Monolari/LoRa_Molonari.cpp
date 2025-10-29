#include <SD.h>
#include <Arduino.h> 
#include "LoRa_Molonari.hpp"
#ifdef LORA_DEBUG
#define LORA_LOG(msg) Serial.print(msg);
#define LORA_LOG_HEX(msg) Serial.print(msg, HEX);
#define LORA_LOG_LN(msg) Serial.println(msg);
#else
#define LORA_LOG(msg)
#define LORA_LOG_HEX(msg)
#define LORA_LOG_LN(msg)
#endif

LoraCommunication::LoraCommunication(long frequency, uint8_t localAdd, uint8_t desti, RoleType role)
    : freq(frequency), localAddress(localAdd), destination(desti), active(false), deviceRole(role)
{
}

void LoraCommunication::startLoRa() {
    if (!active) {
        int retries = 3;
        while (retries--) {
            if (LoRa.begin(freq)) {
                active = true;
                LORA_LOG_LN("LoRa started.");
                return;
            } else {
                LORA_LOG_LN("LoRa failed to start, retrying...");
                delay(1000);
            }
        }
        LORA_LOG_LN("Starting LoRa failed after retries.");
    }
}

void LoraCommunication::stopLoRa() {
    if (active) {
        LoRa.end();
        active = false;
        LORA_LOG_LN("LoRa stopped.");
    }
}

void LoraCommunication::setdesttodefault() {
    destination = 0xff;
}

void LoraCommunication::sendPacket(uint8_t packetNumber, RequestType requestType, const String &payload) {
    if (!active) { LORA_LOG_LN("LoRa inactive"); return; }

    uint8_t b = LoRa.random();
    delay(100 + b);

    if (!LoRa.beginPacket()) {
        LORA_LOG_LN("LoRa busy, cannot send packet");
        return;
    }

    uint8_t checksum = calculateChecksum(destination, localAddress, packetNumber, requestType, payload);
    LoRa.write(checksum);
    LoRa.write(destination);
    LoRa.write(localAddress);
    LoRa.write(packetNumber);
    LoRa.write(requestType);
    LoRa.print(payload);
    LoRa.endPacket();

    LORA_LOG("Packet sent: "); LORA_LOG_LN(payload);

}

bool LoraCommunication::receivePacket(uint8_t &packetNumber, RequestType &requestType, String &payload) {
    if (!active) return false;

    delay(80);
    unsigned long startTime = millis();
    int ackTimeout = 2000;

    while (millis() - startTime < ackTimeout) {
        int packetSize = LoRa.parsePacket();
        if (packetSize) {
            uint8_t receivedChecksum = LoRa.read();
            uint8_t recipient = LoRa.read();
            uint8_t dest = LoRa.read();
            packetNumber = LoRa.read();
            requestType = static_cast<RequestType>(LoRa.read());

            payload = "";
            while (LoRa.available()) payload += (char)LoRa.read();

            if (!isValidDestination(recipient, dest, requestType)) return false;

            uint8_t calculatedChecksum = calculateChecksum(recipient, dest, packetNumber, requestType, payload);
            if (calculatedChecksum != receivedChecksum) return false;

            LORA_LOG_LN("Packet received: " + payload);
            return true;
        }
    }
    return false;
}

bool LoraCommunication::isValidDestination(int recipient, int dest, RequestType requestType) {
    if (recipient != localAddress) return false;
    if (destination == dest || (requestType == SYN && destination == 0xff && myNet.find(dest) != myNet.end())) {
        destination = dest;
        return true;
    }
    return false;
}

uint8_t LoraCommunication::calculateChecksum(int recipient, int dest, uint8_t packetNumber, RequestType requestType, const String &payload) {
    uint8_t checksum = recipient ^ dest ^ packetNumber ^ static_cast<uint8_t>(requestType);
    for (char c : payload) checksum ^= c;
    return checksum;
}

bool LoraCommunication::isLoRaActive() { return active; }

bool LoraCommunication::handshake(uint8_t &shift) {
    if (deviceRole == MASTER) {
        sendPacket(0, SYN, "SYN");
        LORA_LOG_LN("MASTER: SYN sent");

        String payload; uint8_t packetNumber; RequestType requestType;
        int retries = 0;

        while (retries < 6) {
            if (receivePacket(packetNumber, requestType, payload) && requestType == SYN && payload == "SYN-ACK") {
                shift = packetNumber;
                sendPacket(packetNumber, ACK, "ACK");
                LORA_LOG_LN("MASTER: Received SYN-ACK, ACK sent");
                return true;
            } else {
                delay(100 * (retries + 1));
                sendPacket(0, SYN, "SYN");
                LORA_LOG_LN("MASTER: Retrying SYN");
                retries++;
            }
        }
        return false;
    } 
    else { // SLAVE
        String payload; uint8_t packetNumber; RequestType requestType;
        while (true) {
            if (receivePacket(packetNumber, requestType, payload) && requestType == SYN && payload == "SYN") {
                shift = packetNumber;
                sendPacket(shift, SYN, "SYN-ACK");
                LORA_LOG_LN("SLAVE: SYN-ACK sent");
                break;
            }
        }

        int retries = 0;
        while (retries < 6) {
            if (receivePacket(packetNumber, requestType, payload) && requestType == ACK && payload == "ACK") return true;
            delay(100 * (retries + 1));
            sendPacket(shift, SYN, "SYN-ACK");
            retries++;
        }
        return false;
    }
}

uint8_t LoraCommunication::sendPackets(std::queue<String> &sendQueue) {
    uint8_t packetNumber = 0;
    String payload; RequestType requestType; uint8_t receivedPacketNumber;
    while (!sendQueue.empty()) {
        String msg = sendQueue.front();
        sendPacket(packetNumber, DATA, msg);
        int retries = 0;
        while (retries < 6) {
            if (receivePacket(receivedPacketNumber, requestType, payload) && requestType == ACK && receivedPacketNumber == packetNumber) {
                sendQueue.pop();
                packetNumber++;
                break;
            }
            retries++;
        }
        if (retries == 6) { while (!sendQueue.empty()) sendQueue.pop(); break; }
    }
    return packetNumber;
}

int LoraCommunication::receivePackets(std::queue<String> &receiveQueue) {
    uint8_t packetNumber = 0; String payload; RequestType requestType; uint8_t prevPacket = -1;
    unsigned long startTime = millis(); int ackTimeout = 60000;
    receiveQueue.push(String(destination)); //à conserver ?

    while (millis() - startTime < ackTimeout) {
        if (receivePacket(packetNumber, requestType, payload)) {
            switch (requestType) {
                case FIN: return packetNumber;
                default:
                    if (receiveQueue.size() >= MAX_QUEUE_SIZE) return packetNumber;
                    if (prevPacket == packetNumber) { sendPacket(packetNumber, ACK, "ACK"); break; }
                    prevPacket = packetNumber;
                    receiveQueue.push(payload);
                    sendPacket(packetNumber, ACK, "ACK");
            }
        }
    }
    return packetNumber;
}

void LoraCommunication::closeSession(int lastPacket) {
    sendPacket(lastPacket, FIN, "");
    String payload; uint8_t packetNumber; RequestType requestType;
    int retries = 0;
    while (retries < 3) {
        if (receivePacket(packetNumber, requestType, payload) && requestType == FIN && packetNumber == lastPacket) return;
        delay(100 * (retries + 1));
        sendPacket(lastPacket, FIN, "");
        retries++;
    }
}

bool LoraCommunication::receiveConfigUpdate(const char* filepath) {
    uint8_t packetNumber;
    RequestType requestType;
    String payload;

    std::vector<String> newConfigLines; // stockage temporaire des lignes

    Serial.println("Écoute de la nouvelle configuration LoRa...");

    while (true) {
        if (!receivePacket(packetNumber, requestType, payload)) continue;

        if (requestType == DATA && payload.length() > 0) {
            newConfigLines.push_back(payload);
            sendPacket(packetNumber, ACK, "ACK"); // acquittement
        }

        if (requestType == FIN) {
            // Écriture du fichier seulement si FIN reçu
            File newConfig = SD.open(filepath, FILE_WRITE | O_TRUNC);
            if (!newConfig) {
                Serial.print("Impossible d'ouvrir ");
                Serial.println(filepath);
                return false;
            }

            for (auto &line : newConfigLines) {
                newConfig.println(line);
            }

            newConfig.close();
            Serial.println("Réception de la config terminée, fichier mis à jour.");
            return true;
        }
    }
}
