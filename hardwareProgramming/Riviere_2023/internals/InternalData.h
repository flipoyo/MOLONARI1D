
#include "Measure.h"
#ifndef InternalData_CLASS
#define InternalData_CLASS

class InternalData {
  public:
    unsigned int nbOfMeasures;
    unsigned int availableMemory;
    Measure data[100];
};

#endif