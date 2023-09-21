//Communication test code 2

#define readPressure 6
#define t1Pin A1                // analog 1
#define t2Pin A2
#define t3Pin A3
#define t4Pin A4
#define pressurePin A0                // analog 0
//#define tempPin 5
#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

RF24 wirelessSPI(7,8);

const byte adresses[][6] = {"00001","00002"};
boolean order = 0;
boolean measure = 0;
int pressure = 0;
int Array[5];
int t1 = 0;
int t2 = 0;
int t3 = 0;
int t4 = 0;
//int temp = 0;

void setup() {
  //pinMode(order,INPUT)
  Serial.begin(9600);
  wirelessSPI.begin();
  Serial.print("Radio rivière connected : ");
  Serial.println(wirelessSPI.isChipConnected() ? "YES" : "NO");
  wirelessSPI.setAutoAck(1);                
  wirelessSPI.enableAckPayload();         
  wirelessSPI.setRetries(5,15);
  wirelessSPI.openWritingPipe(adresses[0]);
  wirelessSPI.openReadingPipe(1, adresses[1]);
  //radio.setPALevel(RF24_24_MIN); //sets the level of communication
}

void loop() {
  //measure = 0;
  delay(500);
  Serial.println("start listening");
  wirelessSPI.startListening();//sets this arduino as receptor
  while(!wirelessSPI.available()){
  }//checks if there is data to read
  wirelessSPI.read(&order, sizeof(order));
    if (order == 1){
      Serial.print("order=");
      Serial.println(order);
      digitalWrite(readPressure, HIGH);//set the pressure trigger on
      delay(50);
      Array[0] = analogRead(t1Pin);
      Array[1] = analogRead(t2Pin);
      Array[2] = analogRead(t3Pin);
      Array[3] = analogRead(t4Pin);
      Array[4] = analogRead(pressurePin); //read pressure on the pressure sensor
      //temp = analogRead(tempPin);   //read temperature of the river on the temperature sensor
      digitalWrite(readPressure, LOW);//set off the pressure trigger
      //digitalWrite(readTemp, LOW);//set off the temperature trigger
      Serial.print("t1=");
      Serial.println(t1);
      Serial.print("t2=");
      Serial.println(t2);
      Serial.print("t3=");
      Serial.println(t3);
      Serial.print("t4=");
      Serial.println(t4);
      Serial.print("pressure=");
      Serial.println(pressure);
      order = 0;
      Serial.print("order=");
      Serial.println(order);
    }
    Serial.println("stop listening");
    wirelessSPI.stopListening();//sets this arduino as emettor
    //measure = 1;
    delay(3000);
    Serial.println("écriture");
    wirelessSPI.write(&order, sizeof(order));
    Serial.println("write order");
    wirelessSPI.write(&Array, sizeof(Array));
    Serial.println("write pressure and temperatures");
  }
  
