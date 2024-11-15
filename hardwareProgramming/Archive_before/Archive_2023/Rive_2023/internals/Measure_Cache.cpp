// This file defines a "queue" of measures, which will be used to store the measures received from the sensor while waiting for the missing ones.

// Check if the header has already been included
#ifndef MEASURE_CACHE_HPP
#define MEASURE_CACHE_HPP

#include "Measure.hpp"


// Id of the first measurement that this card does not know
extern uint32_t firstMissingMeasurementId;      // Extern means that the variable is defined in another file


template <uint32_t MEASURE_CACHE_SIZE>
class MeasureQueueClass {
    private :
    // Indicates if the measure at the index i is available
    bool hasData[MEASURE_CACHE_SIZE];
    // The measures themselves
    Measure measures[MEASURE_CACHE_SIZE];

    public :
    // Stores a measure in the queue at the write index
    void Add(Measure measure) {
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

    // Return true if there is a measure available
    bool Available() {
        return hasData[0];
    }

    // Return the first measure available, and remove it from the queue
    Measure Dequeue() {
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
};

// Create an instance of the class, so that the functions are accessible from outside the file.

// A storage of the incomming measures, to store them while waiting for the missing ones.
MeasureQueueClass<10> MeasureQueue;


#endif // MEASURE_CACHE_HPP