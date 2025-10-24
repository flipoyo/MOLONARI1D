#include "Measure.hpp"
#include "Time.hpp"

// Constructeur par défaut
Sensor::Sensor() 
  : dataPin(-1), enablePin(-1), offset(-1), scale(-1), type_capteur("-1"), id_capteur("-1") {}
// Constructeur complet
Sensor::Sensor(int _dataPin, int _enablePin, float _offset, float _scale, String _type_capteur, String _id_capteur)
  : dataPin(_dataPin), enablePin(_enablePin), offset(_offset), scale(_scale), type_capteur(_type_capteur), id_capteur(_id_capteur) 
{
  pinMode(enablePin, OUTPUT);
  pinMode(dataPin, INPUT);
  analogReadResolution(12); // précision maximale sur MKR
}


MESURE Sensor::Measure() {
  digitalWrite(enablePin, HIGH);
  delay(200); // temps de stabilisation
  MESURE mesure = analogRead(dataPin);
  digitalWrite(enablePin, LOW);
  return mesure;
}

// Retourne une ligne formatée pour une mesure
String Measure::oneLine() {
  String date = GetCurrentDate();
  String hour = GetCurrentHour();


  // Construction de la ligne
  String str = String(id);
  str += " (" + date + " " + hour + " ) : ";

  // Ajouter les valeurs des capteurs
  for (int i = 0; i < ncapteur; i++) {
    str += " " + String(channel[i]);
    if (i < ncapteur - 1) str += ", "; // éviter la virgule finale
  }

  return str;
}
// Retourne une version complète et lisible de la mesure
String Measure::ToString() {
  String str = "Measure n°" + String(id) + ": " + oneLine();
  return str;
}