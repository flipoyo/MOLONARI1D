#include "Measure.hpp"
#include "Time.hpp"


#ifndef DEBUG_LOG
#define DEBUG_LOG(msg) Serial.println(msg)
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

Measure::Measure(const int& ncapt, const double* toute_mesure):ncapteur(ncapt){
  for (int iterator = 0; iterator < ncapteur; iterator ++){
    channel.push_back(toute_mesure[iterator]);
  } 
  this->time = GetCurrentHour();
  this->date = GetCurrentDate();
}

// Retourne une ligne formatée pour une mesure
String Measure::oneLine() {
  String date = GetCurrentDate();

  String hour = GetCurrentHour();
  DEBUG_LOG("Heure actuelle : " + hour);

  DEBUG_LOG(ncapteur);

  // Construction de la ligne
  String str = uidString;
  str += " ; " + String(id) + " ; " + date + " ; " + hour + "  ; ";

  // Ajouter les valeurs des capteurs
  for (int i = 0; i < ncapteur; i++) {
    str += " " + String(channel[i]);
    if (i < ncapteur) str += "; ";

  }
  DEBUG_LOG("end of initialization of one LineMeasure" + str);
  return str;
}
// Retourne une version complète et lisible de la mesure
String Measure::ToString() {
  String str = oneLine();

  return str;
}