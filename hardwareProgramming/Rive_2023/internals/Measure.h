
// Check that the file has not been imported before
#ifndef MEASURE_CLASS
#define MEASURE_CLASS

class Measure {
  public:
    unsigned int id;
    char date[11];
    char time[9];
    unsigned short mesure1;
    unsigned short mesure2;
    unsigned short mesure3;
    unsigned short mesure4;

    String ToString() {
      String str = "Measure n°" + String(id);
      str += " (" + String(date) + " " + String(time) + ") : ";
      str += String(mesure1) + ", " ;
      str += String(mesure2) + ", " ;
      str += String(mesure3) + ", " ;
      str += String(mesure4);
      
      return str;
    }

    String ToCSVEntry() {
      String str = String(id) + ",";
      str += String(date) + ",";
      str += String(time) + ",";
      str += String(mesure1) + ",";
      str += String(mesure2) + ",";
      str += String(mesure3) + ",";
      str += String(mesure4);
      
      return str;
    }
};

#endif