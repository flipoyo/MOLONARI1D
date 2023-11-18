// This file defines a way to store measurements in the RAM of the Arduino.
// This is used in parallel to the storage inside the SD card, to enable for redundancy.
// Note : We never tested if the program works properly without the SD card.


#ifndef MEASURE_CACHE
#define MEASURE_CACHE

#include "Measure.hpp"


// The code is inside a class to tidy up which functions corresponds to which functionnality

template <unsigned int MEASURE_CACHE_SIZE>
class MeasureCacheClass {
    private :
    // The id of the first measure stored in the cache
    unsigned int firstMeasureId = 1;

    // Indicates if the measure at the given index is available
    bool hasData[MEASURE_CACHE_SIZE];
    // The measures stored in the cache
    Measure measures[MEASURE_CACHE_SIZE];


    // Offset the internal indices of the measures, and increase the firstMeasureId.
    void OffsetMeasures(unsigned int offset) {
        // Update firstMeasureId
        firstMeasureId += offset;

        // Cap the offset to the size of the cache to avoid overflows.
        if (offset > MEASURE_CACHE_SIZE) {
            offset = MEASURE_CACHE_SIZE;
        }

        // Offset the measures
        for (unsigned int i = 0; i < MEASURE_CACHE_SIZE - offset; i++) {
            measures[i] = measures[i + offset];
            hasData[i] = hasData[i + offset];
        }
        // Empty the last measures
        for (unsigned int i = MEASURE_CACHE_SIZE - offset; i < MEASURE_CACHE_SIZE; i++)
        {
            measures[i] = Measure();
            hasData[i] = false;
        }
        
    }


    public :
    // Stores a measure in the cache
    void AddMeasure(Measure measure) {
        unsigned int internalIndex = measure.id - firstMeasureId;

        if (internalIndex >= MEASURE_CACHE_SIZE) {
            OffsetMeasures(internalIndex - MEASURE_CACHE_SIZE + 1);
            internalIndex = MEASURE_CACHE_SIZE - 1;
        }

        if (hasData[internalIndex]) {
            return;
        }
        measures[internalIndex] = measure;
        hasData[internalIndex] = true;
    }

    // Indicates if a measure is stored in the cache
    bool IsMeasureAvailable(unsigned int id) {
        unsigned int internalIndex = id - firstMeasureId;
        return hasData[internalIndex];
    }

    // Get a measure from the cache
    Measure GetMeasure(unsigned int id) {
        unsigned int internalIndex = id - firstMeasureId;
        return measures[internalIndex];
    }

    // Delete all measures from the cache that have an id lower or equal than the given id
    void DeleteMeasureFrom(unsigned int id) {
        unsigned int offsetAmount = id - firstMeasureId + 1;

        // Offset all the measures
        OffsetMeasures(offsetAmount);
    }
};

// Create an instance of the class, so that the functions are accessible from outside the file

// A storage of the last 96 measures on the RAM. Used in parallel to the storage inside the SD card, to enable for redundancy.
MeasureCacheClass<96> MeasureCache;


#endif // MEASURE_CACHE_HPP