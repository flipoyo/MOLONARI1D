#include <FlashStorage.h>

// Define the size of each measurement data
#define MEASUREMENT_SIZE 20

// Define the maximum number of measurements to store
#define MAX_MEASUREMENTS (2 * 1024 * 1024) / MEASUREMENT_SIZE

// Define the starting address for storing measurements in flash
#define FLASH_START_ADDRESS 0

// Create a FlashStorage object to interact with the flash memory
// FlashStorageClass flashData[MAX_MEASUREMENTS];

class Measurement {
public:
  float temperature;
  float pressure;

  Measurement() : temperature(0), pressure(0) {}

  Measurement(float temp, float press) : temperature(temp), pressure(press) {}
};


FlashStorage(flashData[MAX_MEASUREMENTS], Measurement[MAX_MEASUREMENTS]);

class FlashMeasurementStorage {
public:
  void appendMeasurement(const Measurement& measurement) {
    if (measurementCount < MAX_MEASUREMENTS) {
      flashData[measurementCount].write(measurement);
      measurementCount++;
    }
  }

  void retrieveMeasurement(int index, Measurement& measurement) {
    if (index >= 0 && index < measurementCount) {
      flashData[index].read(measurement);
    }
  }

  int getMeasurementCount() {
    return measurementCount;
  }

private:
  int measurementCount = 0;
};

FlashMeasurementStorage measurementStorage;

void setup() {
  // Initialize the Arduino board
  Serial.begin(9600);
}

void loop() {
  // Sample temperature and pressure values
  float temperatureValue = 25.5;
  float pressureValue = 1013.2;

  // Create a measurement
  Measurement measurement(temperatureValue, pressureValue);

  // Append the measurement to the flash storage
  measurementStorage.appendMeasurement(measurement);

  // You can also retrieve measurements as needed
  int measurementIndex = 0;
  Measurement retrievedMeasurement;
  measurementStorage.retrieveMeasurement(measurementIndex, retrievedMeasurement);

  // Print the retrieved measurement
  Serial.print("Retrieved Measurement - Temperature: ");
  Serial.print(retrievedMeasurement.temperature);
  Serial.print(", Pressure: ");
  Serial.println(retrievedMeasurement.pressure);

  delay(1000); // Delay for testing
}
