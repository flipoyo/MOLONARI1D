//Communication test code 2

#define readPressure 2 //switch to measure pressure
//#define readTemp 8
#define pressurePin A1 // analog 1
//#define tempPin A2
#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

RF24 radio(7,8);

const byte adresses[][6] = {"00001","00002"};
boolean order = 0;
boolean measure = 0;
float pressure = 0;

void setup() {
  //pinMode(order,INPUT)
  Serial.begin(9600);
  radio.begin();
  Serial.print("Radio rivière connected : ");
  Serial.println(radio.isChipConnected() ? "YES" : "NO");
  radio.openWritingPipe(adresses[0]);
  radio.openReadingPipe(1, adresses[1]);
  //radio.setPALevel(RF24_24_MIN); //sets the level of communication
}

void loop() {
  //measure = 0;
  delay(500);
  Serial.println("start listening");
  radio.startListening();//sets this arduino as receptor
  while(!radio.available()){
  }//checks if there is data to read
  radio.read(&order, sizeof(order));
    if (order == 1){
      Serial.print("order=");
      Serial.println(order);
      digitalWrite(readPressure, HIGH);//set the pressure trigger on
      //digitalWrite(readTemp, HIGH);//set the temperature trigger on
      delay(50);
      pressure = analogRead(pressurePin); //read pressure on the pressure sensor
      //float temp = analogRead(tempPin);   //read temperature of the river on the temperature sensors
      digitalWrite(readPressure, LOW);//set off the pressure trigger
      //digitalWrite(readTemp, LOW);//set off the temperature trigger
      Serial.print("pressure=");
      Serial.println(pressure);
      order = 0;
      Serial.print("order=");
      Serial.println(order);
    }
    Serial.println("stop listening");
    radio.stopListening();//sets this arduino as emettor
    //measure = 1;
    delay(3000);
    Serial.println("écriture");
    radio.write(&order, sizeof(order));
    Serial.println("write order");
    //radio.write(&measure, sizeof(measure));
    radio.write(&pressure, sizeof(pressure));
    Serial.println("write pressure");
  }
  
