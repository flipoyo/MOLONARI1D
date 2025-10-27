#include "Measure.hpp"
#include "Time.hpp"

// Initialise the temperature sensor for the first time. 
Sensor::Sensor() : dataPin(-1), enablePin(-1), offset(-1), scale(-1), type_capteur("-1") {
  // Default constructor body (if needed)
}

Sensor::Sensor(int _dataPin, int _enablePin, float _offset, float _scale, String _type_capteur) : dataPin(_dataPin), enablePin(_enablePin), offset(_offset), scale(_scale), type_capteur(_type_capteur) {
  // Attribute a pin to the temperature measurement and the power
  pinMode(enablePin, OUTPUT);
  pinMode(dataPin, INPUT);
  
  analogReadResolution(12);   // Set precision to 12 bit (maximum of this board)
}

// Measure the temperature
MESURE Sensor::Measure() {
  //Power the sensor only when we measure
  digitalWrite(enablePin, HIGH);
  digitalWrite(this->alimPin, HIGH);
  delay(200);
  MESURE mesure = analogRead(dataPin);
  digitalWrite(enablePin, LOW);
  digitalWrite(this->alimPin, LOW); 
  return mesure;
}

String Measure::oneLine() {

    String date = GetCurrentHour();
    String time = GetCurrentDate();
    unsigned long time_in_second = GetSecondsSinceMidnight();

    int i;
    String str = String(id);                        // Add ID
    str += " (" + String(date) + " " + String(time) + " " + String(time_in_second) + ") : ";      // Add timestamp
    for (i = 0; i < ncapteur ; i++) {
        str += String(channel[i]) + ", ";                             // Add sensor i data
    };                             
    str += String(channel[i]);                                        // Add last sensor data
    
    return str; // Return the constructed string
    }

//Probablement pas utilisé
String Measure::ToString(){
      //int i;
      String str = "Measure n°" + oneLine();                                      // Add last sensor data
    
    return str; // Return the constructed string
    }  
