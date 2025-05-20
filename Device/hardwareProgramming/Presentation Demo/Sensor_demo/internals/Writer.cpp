// This file defines the Writer class, which is used to write a serie of measurements to a CSV file.
// See internals/Writer.hpp for the class declarations.

// Check that this file is included only once
#ifndef WRITER_CLASS
#define WRITER_CLASS

#include "Writer.hpp"
#include "Time.cpp"

#include <Arduino.h>
#include <SD.h>




#define SD_LOG(msg) Serial.print(msg)
#define SD_LOG_LN(msg) Serial.println(msg)

// Define a comma string for separating CSV columns
const String COMA = String(',');

// GetNextLine function: Returns the number of lines in the CSV file, representing the next ID.
// SHOULD BE CALLED ONLY ONCE to initialize next_id
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

// ApplyCurrentTime function: Sets the current date and time in the Measure object
void ApplyCurrentTime(Measure* measure) {
    GetCurrentHour().toCharArray(measure->time, 9);
    GetCurrentDate().toCharArray(measure->date, 11);
}

//Class methods

// WriteInNewLine: Writes a new line to the CSV file with all the fields from a Measure object
void Writer::WriteInNewLine(Measure *data){
    
    SD_LOG("Writing data ..."); // Debug log
    // Write measurement data as a single CSV line
    //this->file.println(String(data.id)+ COMA + data.date + COMA + data.time + COMA + String(data.chanel1) + COMA + String(data.chanel2) + COMA + String(data.chanel3) + COMA + String(data.chanel4));
    this->file.println(data->oneLine()); // Write the string representation of the measurement
    SD_LOG_LN(data->ToString()); // Log the measurement details

    SD_LOG("Flushing ..."); // Ensure data is saved immediately
    this->file.flush();
    SD_LOG_LN(" Done");
}

// ApplyContent: Fills a Measure object with raw data values for each channel
void Writer::ApplyContent(Measure* measure, int npressure,double  *pressure, int ntemp,double *temp) {
    String str;
    str = "Applying content ..." + String(measure->id) + " with " + String(npressure) + " pressure and " + String(ntemp) + " temperature";
    SD_LOG_LN(str); // Log the number of pressure and temperature sensors
     for(int i = 0; i < npressure; i++) {
        measure->chanelP[i] = pressure[i]; // Assign pressure values
    }
    for(int i = 0; i < ntemp; i++) {
        measure->chanelT[i] = temp[i]; // Assign temperature values
    }
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
    this->next_id = GetNextLine();
    this->file = SD.open(filename, FILE_WRITE);
}

// LogData: Processes raw data, applies a timestamp, and writes it to the CSV file as a new entry
void Writer::LogData(int npressure, double *pressure, int ntemp, double *temperature) {

    // Create a new Measure object
    Measure *data;
    String str;
    data = new Measure(npressure,ntemp); // Initialize the Measure object

    this->ApplyContent(data,npressure,pressure,ntemp,temperature); // Assign channel values
    ApplyCurrentTime(data); // Assign current time and date
    data->id = this->next_id; // Set unique ID for the measurement

    // Check if the connection is still established
    SD_LOG_LN("Trying to LogData ...");
    bool is_connected = SD.begin(this->CSPin) && this->file;
    if (!is_connected) {
        SD_LOG_LN("SD connection lost.");
        SD_LOG_LN("Trying to reconnect ...");
        
        // Try to reconnect if lost
        is_connected = this->Reconnect();
        if (!is_connected) {
            SD_LOG_LN("Connection could not be established."); // Log failure if reconnect fails
            delete data; // Free the Measure object
            SD_LOG_LN("Exiting ...");
            return; // Exit if reconnection fails
        }
    }

// Write data if connected
    if (is_connected) {
        str = "Writing a new line with " + String(data->id) + " ...";
        SD_LOG_LN(str); // Log the ID of the measurement being written
        this->WriteInNewLine(data); // Write data to a new CSV line
    }
    this->next_id++; // Increment ID for next measurement
    delete data; // Free the Measure object

}

// Dispose: Closes the connection to the CSV file, releasing the file resource
void Writer::Dispose() {
    this->file.close();
}



#endif