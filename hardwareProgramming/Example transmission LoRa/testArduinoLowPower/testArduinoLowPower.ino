#include "ArduinoLowPower.h"

class count{
  private:
  static int counter;
  public:
  void printcount(){
    counter++;
    Serial.println("hello " + String(counter));
  }
};
int count::counter = 0;
void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(9600);

  // Increase delay to give time for serial to connect
  delay(1000);

  Serial.println("Starting setup...");
}
count my;
void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  delay(3000);

  // Print a message before going to sleep
  my.printcount();
  Serial.flush();
  Serial.end();
  

  digitalWrite(LED_BUILTIN, LOW);
  delay(2000);

  // Flush serial output before entering sleep
//power sleep mode for 10000 ms (10 seconds)
  LowPower.deepSleep(15000);

Serial.begin(9600);
delay(2000);
// LED will blink once after waking up
}