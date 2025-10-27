#include "Measure.hpp"
#include "Time.hpp"

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


MESURE Sensor::Measure() {
  digitalWrite(enablePin, HIGH);
  digitalWrite(this->alimPin, HIGH);
  delay(200);
  MESURE mesure = analogRead(dataPin);
  digitalWrite(enablePin, LOW);
  digitalWrite(this->alimPin, LOW); 
  return mesure;
}

// Retourne une ligne formatée pour une mesure
String Measure::oneLine() {
  String date = GetCurrentDate();
  String hour = GetCurrentHour();


  // Construction de la ligne
  String str = String(id);
  str += " (" + date + " " + hour + " ) : ; ";

  // Ajouter les valeurs des capteurs
  for (int i = 0; i < ncapteur; i++) {
    str += " " + String(channel[i]);
    if (i < ncapteur - 1) str += "; "; // éviter le point-virgule final
  }

  return str;
}
// Retourne une version complète et lisible de la mesure
String Measure::ToString() {
  String str = "Measure n°" + String(id) + ": ; " + oneLine();
  return str;
}