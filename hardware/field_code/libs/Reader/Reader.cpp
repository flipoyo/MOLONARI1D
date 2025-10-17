// This file defines the implementation of the Reader class, which is used to read a series of measurements from a CSV file.
// Refer to internals/Reader.hpp for the function declarations.

#ifndef READER_CLASS
#define READER_CLASS

#include <SD.h>
#include <queue>

#include "Reader.hpp"

// Debugging macros for logging SD operations
#ifdef SD_DEBUG
#define SD_LOG(msg) Serial.print(msg)
#define SD_LOG_LN(msg) Serial.println(msg)
#else
#define SD_LOG(msg)
#define SD_LOG_LN(msg)
#endif

// Static member to track the current line position in the file
unsigned int Reader::line_cursor = 0;

/**
 * Establish a connection with the SD card and prepare to read from the file.
 * @param shift The number of lines to rewind from the current cursor position.
 * @return True if the connection is established successfully; false otherwise.
 */
bool Reader::EstablishConnection(unsigned int shift)
{
  SD_LOG("SD Reader : establishing connection ...");

  // Attempt to open the file
  this->file = SD.open(filename);
  if (!this->file) {
    SD_LOG("Failed to open file");
    return false;
  }
  
  // Rewind file to the beginning
  this->file.seek(0);

  // Adjust the line_cursor if the shift is valid
  if (shift > line_cursor) {
    return false;
  }
  line_cursor -= shift;

  // Move the file cursor to the `line_cursor` line
  unsigned int lineId = 0;
  while ((lineId < line_cursor) && (this->file.available())) {
    this->file.readStringUntil('\n'); // Skip lines until the desired position
    lineId++;
  }
  
  SD_LOG_LN(" Done");
  return true;
}

/**
 * Update the cursor position by adding a shift and save the updated position.
 * @param shift The number of lines to move forward.
 */
void Reader::UpdateCursor(unsigned int shift)
{
  line_cursor += shift;
  writetomyrecourdfile();
  SD_LOG_LN("--------------UpdateCursor-------------" + String(line_cursor));
}

/**
 * Save the current cursor position to a record file on the SD card.
 */
void Reader::writetomyrecourdfile() {
    String message = "--------------UpdateCursor-------------" + String(line_cursor);
    // Open the record file in append mode
    File cursorFile = SD.open("cursor_position.txt", FILE_WRITE);
    
    if (cursorFile) {
        cursorFile.println(message); // Save the cursor position
        cursorFile.close();          // Close the file
    } else {
        SD_LOG_LN("Failed to save message");
    }
}

/**
 * Load data from the file into a queue, stopping when the queue reaches 250 items or there is no more data.
 * @return A queue containing the loaded data.
 */
std::queue<String> Reader::loadDataIntoQueue()
{
  std::queue<String> Queue;
  while (IsDataAvailable())
  {
    String line = ReadMeasure();
    Queue.push(line);
    if (Queue.size() >= 250) {
      break; // Stop loading if queue reaches its size limit
    }
  }
  return Queue;
}

/**
 * Read the measurement from the current file cursor position.
 * @return A string representing the measurement at the current cursor.
 */
String Reader::ReadMeasure()
{
  String line = this->file.readStringUntil('\n');
  SD_LOG_LN("SD Reader : " + line);
  return line;
}

/**
 * Check if there is more data available to read in the file.
 * @return True if data is available; false otherwise.
 */
bool Reader::IsDataAvailable()
{
  return this->file.available();
}

/**
 * Close the file and release resources associated with the Reader.
 */
void Reader::Dispose()
{
  this->file.close();
}

#endif
