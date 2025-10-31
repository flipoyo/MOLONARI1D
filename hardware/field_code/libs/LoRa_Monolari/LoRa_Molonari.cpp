#include <SD.h>
#include <Arduino.h> 
#include "LoRa_Molonari.hpp"
#define DEBUG_MAIN
#define DEBUG_MEASURE
#define DEBUG_WRITER
#define DEBUG_READER

#ifdef DEBUG_MAIN
#define DEBUG_LOG(msg) Serial.println(msg)
#define DEBUG_LOG_NO_LN(msg) Serial.print(msg)
#else
#define DEBUG_LOG(msg)
#define DEBUG_LOG_NO_LN(msg)
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
                this -> active = true;
                DEBUG_LOG("LoRa started.");
                return;
            } else {
                DEBUG_LOG("LoRa failed to start, retrying...");
                delay(1000);
            }
        }
        DEBUG_LOG("Starting LoRa failed after retries.");
    }
}

void LoraCommunication::stopLoRa() {
    if (active) {
        LoRa.end();
        this -> active = false;
        DEBUG_LOG("LoRa stopped.");
    }
}

void LoraCommunication::setdesttodefault() {
    destination = 0xff;
}

void LoraCommunication::sendPacket(uint8_t packetNumber, RequestType requestType, const String &payload) {
    if (!active) { DEBUG_LOG("LoRa inactive"); return; }

    uint8_t b = random(10, 80);
    delay(100 + b);

    if (!LoRa.beginPacket()) {
        DEBUG_LOG("LoRa busy, cannot send packet");
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

    DEBUG_LOG("Packet sent: "); DEBUG_LOG(payload);

}

bool LoraCommunication::receivePacket(uint8_t &packetNumber, RequestType &requestType, String &payload) {
    if (!active) return false;

    delay(10);
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

            DEBUG_LOG("Packet received: " + payload);
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
        DEBUG_LOG("MASTER: SYN sent");

        String payload; uint8_t packetNumber; RequestType requestType;
        int retries = 0;

        while (retries < 6) {
            if (receivePacket(packetNumber, requestType, payload) && requestType == SYN && payload == "SYN-ACK") {
                shift = packetNumber;
                sendPacket(packetNumber, ACK, "ACK");
                DEBUG_LOG("MASTER: Received SYN-ACK, ACK sent");
                return true;
            } else {
                delay(100 * (retries + 1));
                sendPacket(0, SYN, "SYN");
                DEBUG_LOG("MASTER: Retrying SYN");
                retries++;
            }
        }
        return false;
    } 
    else { // SLAVE
        String payload; uint8_t packetNumber; RequestType requestType;
        int n = 0;
        while (n < 50) {
            n++;
            if (receivePacket(packetNumber, requestType, payload) && requestType == SYN && payload == "SYN") {
                shift = packetNumber;
                sendPacket(shift, SYN, "SYN-ACK");
                DEBUG_LOG("SLAVE: SYN-ACK sent");
                break;
            }
        if (n == 50) {
            DEBUG_LOG("SLAVE: No SYN received");
            return false;
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
}}

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

bool LoraCommunication::receiveConfigUpdate(const char* filepath, uint16_t* outMeasureInterval, uint16_t* outLoraInterval, unsigned long timeout_ms) {
    uint8_t packetNumber;
    RequestType requestType;
    String payload;

    std::vector<String> newConfigLines; // stockage temporaire des lignes

    Serial.println("Écoute de la nouvelle configuration LoRa...");

    unsigned long start = millis();
    while (millis() - start < timeout_ms) {
        // petite attente pour éviter busy-loop
        if (!receivePacket(packetNumber, requestType, payload)) {
            delay(50);
            continue;
        }

        if (requestType == DATA && payload.length() > 0) {
            payload.trim(); // supprime CR/LF
            if (payload.length() > 0) {
                // Écrire d'abord en mémoire
                newConfigLines.push_back(payload);
                // ACK **après** avoir stocké en RAM (et idéalement après écriture SD, mais on postpose)
                sendPacket(packetNumber, ACK, "ACK");
            }
            continue;
        }

        if (requestType == FIN) {
            // Écriture atomique : on écrit d'abord sur un fichier temporaire
            const char* tmpPath = "tmp_conf.csv";
            File tmp = SD.open(tmpPath, FILE_WRITE | O_TRUNC);
            if (!tmp) {
                Serial.print("Impossible d'ouvrir ");
                Serial.println(tmpPath);
                return false;
            }

            for (auto &line : newConfigLines) {
                tmp.println(line);
            }
            tmp.close();

            // Remplacer l'ancien fichier (supprime puis renommer si possible)
            // Si SD.rename est disponible, on peut faire SD.remove(filepath); SD.rename(tmpPath, filepath);
            // Sinon on réécrit:
            if (!SD.remove(filepath)) {
                // si le fichier n'existait pas, remove peut échouer mais ce n'est pas fatal
                Serial.println("Warning: ancienne conf non supprimée (peut ne pas exister).");
            }

            File newF = SD.open(filepath, FILE_WRITE | O_TRUNC);
            if (!newF) {
                Serial.print("Impossible de créer ");
                Serial.println(filepath);
                return false;
            }
            File tmpRead = SD.open(tmpPath, FILE_READ);
            if (!tmpRead) {
                Serial.println("Impossible d'ouvrir tmp pour lecture");
                newF.close();
                return false;
            }
            while (tmpRead.available()) {
                newF.write(tmpRead.read());
            }
            tmpRead.close();
            newF.close();
            SD.remove(tmpPath);
            

            Serial.println("Réception de la config terminée, fichier mis à jour.");

            // Parser les lignes reçues pour extraire les intervalles
            for (auto &line : newConfigLines) {
                String copy = line;
                copy.trim();
                if (copy.startsWith("intervalle_de_mesure_secondes")) {
                    int idx = copy.indexOf(',');
                    if (idx >= 0) {
                        String val = copy.substring(idx + 1);
                        val.trim();
                        long vv = val.toInt();
                        if (vv > 0 && outMeasureInterval) *outMeasureInterval = (uint16_t)vv;
                    }
                } else if (copy.startsWith("intervalle_lora_secondes")) {
                    int idx = copy.indexOf(',');
                    if (idx >= 0) {
                        String val = copy.substring(idx + 1);
                        val.trim();
                        long vv = val.toInt();
                        if (vv > 0 && outLoraInterval) *outLoraInterval = (uint16_t)vv;
                    }
                }
            }

            return true;
        }
    } // fin timeout

    Serial.println("Timeout: pas de configuration complète reçue.");
    return false;
}
