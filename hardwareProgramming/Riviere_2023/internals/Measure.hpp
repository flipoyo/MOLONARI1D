

// Check that the file has not been imported before
#ifndef MEASURE_CLASS
#define MEASURE_CLASS

const char filename[] = "riviere.csv";

class Measure {
  public:
    // Numéro de la mesure
    unsigned int id;
    // Date au format "dd/mm/yyyy"
    char date[11];
    // Heure au format "hh:mm:ss"
    char time[9];

    // Valeurs des mesures
    MEASURE_T mesure1;
    MEASURE_T mesure2;
    MEASURE_T mesure3;
    MEASURE_T mesure4;

    String ToString() {
      String str = "Measure n°" + String(id);
      str += " (" + String(date) + " " + String(time) + ") : ";
      str += String(mesure1) + ", " ;
      str += String(mesure2) + ", " ;
      str += String(mesure3) + ", " ;
      str += String(mesure4);
      
      return str;
    }
};

#endif