#ifndef MEASURE_CACHE_HPP
#define MEASURE_CACHE_HPP

#include "Measure.h"


// The number of measures that can be stored in the cache
#define MEASURE_CACHE_SIZE 10

extern uint32_t firstMissingMeasurementId;

bool hasData[MEASURE_CACHE_SIZE];
Measure measures[MEASURE_CACHE_SIZE];

void AddMeasure(Measure measure) {
    unsigned int internalIndex = measure.id - firstMissingMeasurementId;

    if (internalIndex >= MEASURE_CACHE_SIZE) {
        return;
    }

    if (hasData[internalIndex]) {
        return;
    }
    measures[internalIndex] = measure;
    hasData[internalIndex] = true;
}

bool IsMeasureAvailable() {
    return hasData[0];
}

Measure GetMeasure() {
    Measure measure = measures[0];

    // Offset all the measures
    for (unsigned int i = 0; i < MEASURE_CACHE_SIZE-1; i++) {
        measures[i] = measures[i + 1];
        hasData[i] = hasData[i + 1];
    }
    measures[MEASURE_CACHE_SIZE - 1] = Measure();
    hasData[MEASURE_CACHE_SIZE - 1] = false;
    
    return measure;
}


#endif // MEASURE_CACHE_HPP