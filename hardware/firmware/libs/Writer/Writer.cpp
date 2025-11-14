// Writer.cpp
// This file defines the Writer class, which is used to write a serie of measurements to a CSV file.

#ifndef WRITER_CLASS
#define WRITER_CLASS

#include <Arduino.h>
#include <SD.h>
#include <string>
#include <queue>

#include "Writer.hpp"
#include "Time.hpp"
#include "Measure.hpp"

#define DEBUG_WRITER
#ifdef DEBUG_WRITER
#define SD_LOG(msg) Serial.println(msg)
#define SD_LOG_NO_LN(msg) Serial.print(msg)
#else
#define SD_LOG(msg)
#define SD_LOG_NO_LN(msg)
#endif

// Define a comma string for separating CSV columns
const std::string COMA = ";";

unsigned int GetNextLine() {
  // TODO : Now, the function counts the number of lines. It would be more stable if it got the index of the last measurement.

  File readInfile = SD.open(filename); // Open the CSV file in read mode
  unsigned int number_of_lines = 0; // Counter for the lines
  if (readInfile) {
    while (readInfile.available()) {
      // read an entire csv line (which end is a \n)
      if (readInfile.read() == '\n') {
        number_of_lines++;
      }
    } 
  }
  readInfile.close();
  return number_of_lines;
}


// WriteInNewLine: Writes a new line to the CSV file with all the fields from a Measure object
void Writer::WriteInNewLine(Measure& data){
    
    SD_LOG_NO_LN("Writing data ..."); // Debug log
    // Write measurement data as a single CSV line
    //this->file.println(String(data.id)+ COMA + data.date + COMA + data.time + COMA + String(data.chanel1) + COMA + String(data.chanel2) + COMA + String(data.chanel3) + COMA + String(data.chanel4));
    String to_be_printed =data.ToString();
    SD_LOG("to be written set.");
    this->file.println(to_be_printed); 
    SD_LOG_NO_LN(" Done");

    SD_LOG("Flushing ..."); // Ensure data is saved immediately
    this->file.flush();
    SD_LOG_NO_LN(" Done");
}


// Reconnect: Attempts to re-establish connection to the SD card and reopen the CSV file in write mode
bool Writer::Reconnect() {
    this->file.close();
    if (!SD.begin(this->CSPin)) {
        return false;
    }
    this->file = SD.open(filename, FILE_WRITE);
    return this->file;
}


// EstablishConnection: Sets up initial connection to SD card and prepares file for writing
void Writer::EstablishConnection(const int CSpin) {
    this->CSPin = CSpin;
    if (!SD.begin(this->CSPin)) {
        SD_LOG_NO_LN("SD initialization failed!");
        return;
    }
    SD_LOG_NO_LN("SD initialization done.");
    this->next_id = GetNextLine();
    this->file = SD.open(filename, FILE_WRITE);
}

// LogData: Processes raw data, applies a timestamp, and writes it to the CSV file as a new entry
void Writer::LogData(int ncapteur, const std::vector<double>& toute_mesure, String uidString) {
    
    SD_LOG("about to create data");
    // Create a new Measure object
    Measure data (ncapteur, toute_mesure, uidString);
    SD_LOG("data initialised");

    data.id = this->next_id; // Set unique ID for the measurement
    // Check if the connection is still established
    bool is_connected = SD.begin(this->CSPin) && this->file;
    if (!is_connected) {
        SD_LOG_NO_LN("SD connection lost.");
        SD_LOG_NO_LN("Trying to reconnect ...");
        
        // Try to reconnect if lost
        is_connected = this->Reconnect();
        if (!is_connected) {
            SD_LOG("Connection could not be established."); // Log failure if reconnect fails
            return; // Exit if reconnection fails
        }
    }

// Write data if connected
    if (is_connected) {
        SD_LOG_NO_LN("SD connection established WHEN LOG DATA.");
        this->WriteInNewLine(data); // Write data to a new CSV line
    }
    this->next_id++; // Increment ID for next measurement
}

// Dispose: Closes the connection to the CSV file, releasing the file resource
void Writer::Dispose() {
    this->file.close();
}

void Writer::LogString(std::queue<String> receiveQueue) {
    bool is_connected = SD.begin(this->CSPin) && this->file;

    if (!is_connected) {
        SD_LOG_NO_LN("SD connection lost.");
        SD_LOG_NO_LN("Trying to reconnect ...");
        
        // Try to reconnect if lost
        is_connected = this->Reconnect();
        if (!is_connected) {
            SD_LOG("Connection could not be established."); // Log failure if reconnect fails
            return; // Exit if reconnection fails
        }
    }

    if (is_connected) {
        SD_LOG_NO_LN("SD connection established WHEN LOG DATA.");
        String payload;

        while (!receiveQueue.empty()) {
            payload = receiveQueue.front();
            SD_LOG("to be written set.");
            this->file.print(payload);
            SD_LOG_NO_LN(" Done");

            SD_LOG("Flushing ..."); // Ensure data is saved immediately
            this->file.flush();
            SD_LOG_NO_LN(" Done");

            receiveQueue.pop();
        }
    }

}

#endif