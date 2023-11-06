

// Check that the file has not been imported before
#ifndef MEASURE_CLASS
#define MEASURE_CLASS

const char filename[] = "datalog.csv";

class Measure {
  public:
    unsigned int id;
    char date[11];
    char time[9];
    unsigned short mesure1;
    unsigned short mesure2;
    unsigned short mesure3;
    unsigned short mesure4;
};

#endif