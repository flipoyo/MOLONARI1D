// This is a small, focused test script using the LoraCommunication class,
// simulating scenarios with non-real data to quickly debug and refine the protocol
// without deploying the entire system.

#include "./internals/Lora.hpp"
#include <queue> // Using standard library queue for managing data packets

// Define device and relay addresses for communication
uint8_t MyAddress = 0xcc; // Address of this device
uint8_t RelayAdd = 0xaa;  // Address of the relay device

void setup()
{
  // Configure the built-in LED for feedback during initialization
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH); // Turn LED on to indicate initialization

  // Initialize Serial communication for debugging
  Serial.begin(9600);
  
  // Wait up to 5 seconds for Serial connection to establish
  unsigned long end_date = millis() + 5000;
  while (!Serial && millis() < end_date)
  {
    // Waiting for Serial connection
  }

  // Debugging setup complete
  // Uncomment for additional initialization messages
  // Serial.println("Initialization complete!");
  // Serial.println("Waiting to start communication...");
}

// Function to simulate loading data into a queue for transmission
std::queue<String> loadDataIntoQueue(int shift)
{
  std::queue<String> Queue; // Initialize an empty queue

  // Populate the queue with simulated data records
  for (int i = 100 - shift; i <= 280; i++)
  {
    String line = "hellor from riviere" + String(i + 1); // Example data format
    Queue.push(line); // Add data to the queue
    
    // Limit the queue size to 200 items for testing
    if (Queue.size() >= 200)
      break;
  }

  return Queue; // Return the filled queue
}

// Create a LoraCommunication object with the specified frequency and addresses
LoraCommunication lora(868E6, MyAddress, RelayAdd);

void loop()
{
  Serial.println("Starting new communication session...");
  
  // Initialize LoRa communication
  lora.startLoRa();
  
  int shift = 0; // Variable to simulate shifting data (could represent a data offset)
  
  // Perform a handshake with the relay
  if (lora.performHandshake(shift))
  {
    // Load data into a queue after successful handshake
    std::queue<String> sendQueue = loadDataIntoQueue(shift);
    
    // Send the packets from the queue
    uint8_t last = lora.sendPackets(sendQueue);
    
    // Close the communication session with the relay
    lora.closeSession(last);
  }

  // Stop LoRa communication to save power
  lora.stopLoRa();

  // Delay before starting the next session
  delay(10000); // 10-second delay between communication sessions
}
