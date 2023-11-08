

// Check that the file has not been imported before
#ifndef MEASURE_CLASS
#define MEASURE_CLASS

const char filename[] = "datalog.csv";

class Measure {
  public:
    unsigned int id;
    char date[11];
    char time[9];
    MEASURE_T mesure1;
    MEASURE_T mesure2;
    MEASURE_T mesure3;
    MEASURE_T mesure4;
};

#endif