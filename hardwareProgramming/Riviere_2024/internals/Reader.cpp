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
  this->file = SD.open(filename);
  unsigned int lineId = 0;
  if (line_cursor - shift >= 0)
  {
    line_cursor = line_cursor - shift;
  }
  else
  {
    return false;
  }

  while ((lineId < line_cursor) && (this->file.available()))
  {
    this->file.readStringUntil('\n');
  }
  return true;

  SD_LOG_LN(" Done");
}

void Reader::UpdateCursor(unsigned int shift)
{

  line_cursor = line_cursor + shift;
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

  SD_LOG("SD Reader : Reading measure n°" + String(line_cursor) + " ...");
  String line = this->file.readStringUntil('\n');
  return line;

  SD_LOG_LN(" Done");
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