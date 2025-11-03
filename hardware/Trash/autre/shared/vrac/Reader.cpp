// NOT COMPLETE AT ALL, SENSOR INTERNALS IS BETTER

// This file defines the Reader class, which is used to read a serie of measurements from a CSV file.
// See internals/Reader.hpp for the definitions.

// Check that the file has not been imported before
#ifndef READER_CLASS
#define READER_CLASS

#include <SD.h>

#include "Measure.hpp"
#include "Reader.hpp"
#include <queue>

#ifdef SD_DEBUG
#define SD_LOG(msg) Serial.print(msg)
#define SD_LOG_LN(msg) Serial.println(msg)
#else
#define SD_LOG(msg)
#define SD_LOG_LN(msg)
#endif

unsigned int Reader::line_cursor = 0;

bool Reader::EstablishConnection(unsigned int shift)
{
  SD_LOG("SD Reader : establishing connection ...");
  // Open the file and check for success
  this->file = SD.open(filename);
  if (!this->file) {
    SD_LOG("Failed to open file");
    return false;
  }
  
  // Rewind file to start from the beginning
  this->file.seek(0);

  // Adjust line_cursor safely
  if (shift > line_cursor) {
    return false;
  }
  line_cursor -= shift;

  // Move file cursor to `line_cursor` line
  unsigned int lineId = 0;
  while ((lineId < line_cursor) && (this->file.available())) {
    this->file.readStringUntil('\n');
    lineId++;
  }
  
  SD_LOG_LN(" Done");
  return true;
}

void Reader::UpdateCursor(unsigned int shift)
{
  line_cursor = line_cursor + shift;
  writetomyrecourdfile();
  SD_LOG_LN("--------------UpdateCursor-------------" + String(line_cursor));
}

void Reader::writetomyrecourdfile() {
    String message = "--------------UpdateCursor-------------" + String(line_cursor);
    // Open the file in append mode to avoid overwriting previous entries
    File cursorFile = SD.open("cursor_position.txt", FILE_WRITE);
    
    if (cursorFile) {
        // Write the custom message along with the current cursor position
        cursorFile.println(message);           // Write the passed message
      
        
        cursorFile.close();  // Close the file to save changes
        
   
    } else {
        SD_LOG_LN("Failed to save message");
    }
}

std::queue<String> Reader::loadDataIntoQueue()
{
  std::queue<String> Queue;
  while (IsDataAvailable())
  {
    String line = ReadMeasure();
    Queue.push(line);
    if (Queue.size() >= 250)
      break; // Limit queue size if necessary
  }
  return Queue;
}
String Reader::ReadMeasure()
{
  
  String line = this->file.readStringUntil('\n');
  SD_LOG_LN("SD Reader : "+ line);
  return line;

}

bool Reader::IsDataAvailable()
{
  return this->file.available();
}

void Reader::Dispose()
{
  this->file.close();
}

#endif