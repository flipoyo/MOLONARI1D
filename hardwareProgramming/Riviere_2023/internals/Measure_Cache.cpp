#ifndef MEASURE_CACHE
#define MEASURE_CACHE

#include "Measure.hpp"


// The number of measures that can be stored in the cache
#define MEASURE_CACHE_SIZE 96

class MeasureCacheClass {
    private :
    unsigned int firstMeasureId = 1;

    bool hasData[MEASURE_CACHE_SIZE];
    Measure measures[MEASURE_CACHE_SIZE];

    // Offset the indices of the measures
    void OffsetMeasures(unsigned int offset) {
        firstMeasureId += offset;

        if (offset > MEASURE_CACHE_SIZE) {
            offset = MEASURE_CACHE_SIZE;
        }

        for (unsigned int i = 0; i < MEASURE_CACHE_SIZE - offset; i++) {
            measures[i] = measures[i + offset];
            hasData[i] = hasData[i + offset];
        }
        for (unsigned int i = MEASURE_CACHE_SIZE - offset; i < MEASURE_CACHE_SIZE; i++)
        {
            measures[i] = Measure();
            hasData[i] = false;
        }
        
    }


    public :

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

    bool IsMeasureAvailable(unsigned int id) {
        unsigned int internalIndex = id - firstMeasureId;
        return hasData[internalIndex];
    }

    Measure GetMeasure(unsigned int id) {
        unsigned int internalIndex = id - firstMeasureId;
        return measures[internalIndex];
    }


    void DeleteMeasureFrom(unsigned int id) {
        unsigned int internalIndex = id - firstMeasureId;

        if (internalIndex >= MEASURE_CACHE_SIZE) {
            return;
        }

        // Offset all the measures
        OffsetMeasures(internalIndex + 1);
    }
};
MeasureCacheClass MeasureCache;


#endif // MEASURE_CACHE_HPP