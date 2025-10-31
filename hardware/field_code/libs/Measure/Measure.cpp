#include "Measure.hpp"
#include "Time.hpp"


#define DEBUG_MEASURE
#ifdef DEBUG_MEASURE
#define DEBUG_LOG(msg) Serial.println(msg)
#else 
#define DEBUG_LOG(msg)
#endif

// Constructeur par défaut
Sensor::Sensor() 
  : dataPin(-1), enablePin(-1), type_capteur("-1"), id_box("-1") {}
// Constructeur complet
Sensor::Sensor(int _dataPin, int _enablePin, String _type_capteur, String _id_box)
  : dataPin(_dataPin), enablePin(_enablePin), type_capteur(_type_capteur), id_box(_id_box) 
{
  pinMode(enablePin, OUTPUT);
  pinMode(dataPin, INPUT);
  analogReadResolution(12); // précision maximale sur MKR
}


double Sensor::get_voltage() {
  digitalWrite(enablePin, HIGH);
  delay(200);
  double voltage = analogRead(dataPin);
  digitalWrite(enablePin, LOW);
  return voltage;
}

Measure::Measure(const int& ncapt, const double* toute_mesure):ncapt(ncapt){
  for (int iterator = 0; iterator < ncapt; iterator ++){
    channel.push_back(toute_mesure[iterator]);
  }
  DEBUG_LOG("Initialised channel attribute of a Measure object");
  this->time = GetCurrentHour();
  this->date = GetCurrentDate();
  DEBUG_LOG("Measure object well initialised");
}

// Retourne une ligne formatée pour une mesure
String Measure::oneLine() {
  DEBUG_LOG("starting oneLine");
  String date = GetCurrentDate();
  DEBUG_LOG("GetCurrentDate finished in oneLine");
  String hour = GetCurrentHour();
  DEBUG_LOG("GetCurrentHour finished in oneLine");
  DEBUG_LOG(String(ncapt));
  DEBUG_LOG("debug messages still work1");
  
  DEBUG_LOG("Heure actuelle : " + date);
  DEBUG_LOG("debug messages still work2");

  // Construction de la ligne
  String str = String(id);
  str += " ; " + date + " ; " + hour + "  ; ";

  // Ajouter les valeurs des capteurs
  for (int i = 0; i < ncapt; i++) {
    str += " " + String(channel[i]);
    if (i < ncapt) str += "; ";

  }
  DEBUG_LOG("end of initialization of one LineMeasure" + str);
  return str;
}
// Retourne une version complète et lisible de la mesure
String Measure::ToString() {
  DEBUG_LOG("going to oneLine");
  String str = oneLine();
  DEBUG_LOG("oneLine finished");
  return str;
}