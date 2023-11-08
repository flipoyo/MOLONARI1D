#include <SD.h>
#include <SPI.h>
#include <String.h>
#include "Measure.h"
#include "Reader.h"

#ifndef READER_CLASS
#define READER_CLASS

// Convert a CSV line (Arduino String Type= into a Measure.
Measure Reader::StringToMeasure(String line){
  Measure measure;
  String delimiter = ",";
  String token;
  line.concat(delimiter);
  int i = 0;
  int pos = 0;
  while ((pos = line.indexOf(delimiter)) != -1) {
    token = line.substring(0, pos);
    switch (i)
    {
    case 0:
      measure.id = token.toRealNumber();
      break;
    case 1:
      strncpy(measure.date, token.c_str(), 11);
      break;
    case 2:
      strncpy(measure.time, token.c_str(), 9);
      break;
    case 3:
      measure.mesure1 = token.toRealNumber();
      break;
    case 4:
      measure.mesure2 = token.toRealNumber();
      break;
    case 5:
      measure.mesure3 = token.toRealNumber();
      break;
    case 6:
      measure.mesure4 = token.toRealNumber();
      break;
    default:
      break;
    }
    line.remove(0, pos + delimiter.length());
    i++;
  }
  return measure;
}

Reader::Reader()
{
    this->line_cursor = 0;
}

void Reader::EstablishConnection()
{
    this->file = SD.open(filename);
}

void Reader::MoveCursor(unsigned int lineId) {
      while (this->line_cursor < lineId) {
          this->file.readStringUntil('\n');
          this->line_cursor++;
      }
    }

Measure Reader::ReadMeasure() {
    String line = this->file.readStringUntil('\n');
    this->line_cursor++;
    return this->StringToMeasure(line);

}

bool Reader::ThereIsDataNext() {
    return this->file.available();
}

Reader::~Reader()
{
    this->file.close();
}

#endif