#include <SD.h>
#include <SPI.h>
#include "RTClib.h"
#include <EEPROM.h>
#include <nRF24L01.h>
#include <RF24.h>

RF24 wirelessSPI(7,8);
File instruction_file;
File logfile;
File testFile;
const byte adresses[][6] = {"00001","00002"};
const int chipSelect = 10;
RTC_DS1307 RTC;
int start_year0, start_month0, start_day0, start_hour0, start_minute0, start_second0, end_year0, end_month0, end_day0, end_hour0, end_minute0, end_second0, time_gap_hours0, time_gap_minutes0, time_gap_seconds0;
int index = 0;
bool interruption=false;//boolean that is equal to 1 if the SD card has been removed and 0 if the SD card is connected
boolean order = 0;
boolean first_opening=true;
char filename0[] = "LOGGER00.CSV";//global variable representing the name of the file we'll be writing in (we need to define it as a global variable in order to use it in the void loop too)

//assign a port of the Arduino to each thing we measure
#define ECHO_TO_SERIAL   1// echo data to serial port
#define readPressure 6
#define t1Pin A1                // analog 1
#define t2Pin A2
#define t3Pin A3
#define t4Pin A4
#define pressurePin A0                // analog 1
//#define tempPin 5
#define SYNC_INTERVAL 1000 // mills between calls to flush() - to write data to the card
uint32_t syncTime = 0; // time of last sync()

void error(String str)//definition of an error function
{
  Serial.print("error: ");
  Serial.println(str);
  while(1);
}
//function that indicates whether one date is before another (returns a boolean) 
bool isBefore(int year1,int month1,int day1,int hour1,int minutes1,int seconds1,int year2,int month2,int day2,int hour2,int minutes2,int seconds2){
  if(year1<year2){
    return true;
  }
  if(year1==year2){
    if(month1<month2){
      return true;
    }
    if(month1==month2){
      if(day1<day2){
        return true;
      }
      if(day1==day2){
        if(hour1<hour2){
          return true;
        }
        if(hour1==hour2){
          if(minutes1<minutes2){
            return true;
          }
          if(minutes1==minutes2){
            if(seconds1<=seconds2){
              return true;
            }
          }
        }
      }
    }
  }
  return false;
}

//function that returns false if a line of a CSV file is longer than maxLen or if the line is the last one andtrue otherwise
bool readLine(File &f, char* line, size_t maxLen) {
  for (size_t n = 0; n < maxLen; n++) {
    int c = f.read();
    if ( c < 0 && n == 0) return false;  // EOF
    if (c < 0 || c == '\n') {
      line[n] = 0;
      return true;
    }
    line[n] = c;
  }
  return false; // line too long
}

bool readVals(long* start_year,long* start_month, long* start_day, long* start_hour, long* start_minute, long* start_second, long* end_year, long* end_month, long* end_day, long* end_hour, long* end_minute, long* end_second, long* time_gap_hours, long* time_gap_minutes, long* time_gap_seconds) {
  //readVals is a function that reads a line of a CSV file; line is the line to read, ptr is a pointer and str is a pointer too
  char line[200], *ptr, *str;
  if (!readLine(instruction_file, line, sizeof(line))) {
    return false;  // EOF or too long
  }
  *start_year = strtol(line, &ptr, 10);//strtol(line,&ptr,10) returns the first characters of the line, until it finds a character that is not a number, so it returns the year of the starting date
  if (ptr == line) return false;  // bad number if equal
  while (*ptr) {
    if (*ptr++ == ':') break;
  }//at the end of the while loop, ptr points to the first colon, the one that separates the start year and the start month
  *start_month = strtol(ptr, &str, 10);//strtol(ptr,&str,10) returns the first characters after the ptr pointer (so after the first colon) until it finds a character that is not a number, so it returns the month of the starting date
  while (*ptr) {
    if (*ptr++ == ':') break;//we iterate the same principle over and over for the day, hour, minute and second of the starting date
  }
  *start_day = strtol(ptr, &str, 10);
  while (*ptr) {
    if (*ptr++ == ':') break;
  }
  *start_hour = strtol(ptr, &str, 10);
  while (*ptr) {
    if (*ptr++ == ':') break;
  }
  *start_minute = strtol(ptr, &str, 10);
  while (*ptr) {
    if (*ptr++ == ':') break;
  }
  *start_second = strtol(ptr, &str, 10);
  while (*ptr) {
    if (*ptr++ == ',') break;//this time we don't wait until we find a colon, we rather wait until we find a comma since it's a comma that splits the starting date and the end date
  }
  *end_year = strtol(ptr, &str, 10);
  while (*ptr) {
    if (*ptr++ == ':') break;
  }
  *end_month = strtol(ptr, &str, 10);
  while (*ptr) {
    if (*ptr++ == ':') break;
  }
  *end_day = strtol(ptr, &str, 10);
  while (*ptr) {
    if (*ptr++ == ':') break;
  }
  *end_hour = strtol(ptr, &str, 10);
  while (*ptr) {
    if (*ptr++ == ':') break;
  }
  *end_minute = strtol(ptr, &str, 10);
  while (*ptr) {
    if (*ptr++ == ':') break;
  }
  *end_second = strtol(ptr, &str, 10);
  while (*ptr) {
    if (*ptr++ == ',') break;//this time we also wait until we find a comma since it is a comma that splits the end date and the time gap
  }
  *time_gap_hours = strtol(ptr, &str, 10);
  while (*ptr) { 
    if (*ptr++ == ':') break;
  }
  *time_gap_minutes = strtol(ptr, &str, 10);
  while (*ptr) {
    if (*ptr++ == ':') break;
  }
  *time_gap_seconds = strtol(ptr, &str, 10);
  return str != ptr;
}

void setup(){
  long start_year, start_month, start_day, start_hour, start_minute, start_second, end_year, end_month, end_day, end_hour, end_minute, end_second, time_gap_hours, time_gap_minutes, time_gap_seconds;
  Serial.begin(9600);
  pinMode(10,OUTPUT);//port 10 is the port that is connected to the SD Card
  if (!SD.begin()) {
    interruption = true;
  }
  else {
    instruction_file = SD.open("test3.csv");//open the file with instructions in reading mode
    if (!instruction_file) {
    return;
    }
  }
 

  //we affect a value to the local variables by using readVals and then we affect a value to the global variables
  while (readVals(&start_year, &start_month, &start_day, &start_hour, &start_minute, &start_second, &end_year, &end_month, &end_day, &end_hour, &end_minute, &end_second, &time_gap_hours, &time_gap_minutes, &time_gap_seconds)) {
    start_year0 = start_year;
    start_month0 = start_month;
    start_day0 = start_day;
    start_hour0 = start_hour;
    start_minute0 = start_minute;
    start_second0 = start_second;
    end_year0 = end_year;
    end_month0 = end_month;
    end_day0 = end_day;
    end_hour0 = end_hour;
    end_minute0 = end_minute;
    end_second0 = end_second;
    time_gap_hours0 = time_gap_hours;
    time_gap_minutes0 = time_gap_minutes;
    time_gap_seconds0 = time_gap_seconds;
  }
  if(ECHO_TO_SERIAL){
    Serial.println("Instructions read");
  }
  instruction_file.close();
  char filename[] = "LOGGER00.CSV";
  //loop on all numbers between 00 and 99; filename is finally "LOGGER" followed by the first integer n between 00 and 99 so that "LOGGERn" doesn't already exist
  for (uint8_t i = 0; i < 100; i++) {
    filename[6] = i/10 + '0';
    filename[7] = i%10 + '0';
    filename0[6] = i/10 + '0';
    filename0[7] = i%10 + '0';
    if (! SD.exists(filename)) {
      // only open a new file if it doesn't exist
      logfile = SD.open(filename, FILE_WRITE); 
      break;  // leave the loop!
    }
  }
  

  
  #if ECHO_TO_SERIAL
    Serial.print("Logging to: ");
    Serial.println(filename);//print the name of the file that we've just created and in which we'll write the data
  #endif //ECHO_TO_SERIAL
  // connect to the Real Time Clock (RTC)
  Wire.begin();  
  if (!RTC.begin()) {
    logfile.println("RTC failed");
  #if ECHO_TO_SERIAL
    Serial.println("RTC failed");
  #endif  //ECHO_TO_SERIAL
  }
  logfile.println("date,t1,t2,t3,t4,pressure");    
  #if ECHO_TO_SERIAL
    Serial.println("date,t1,t2,t3,t4,pressure");
  #endif //ECHO_TO_SERIAL
  logfile.flush();
  logfile.close();
}
void loop() {
  // fetch the time
  DateTime now;
  digitalWrite(readPressure, HIGH);//set the 1st temperature trigger on
  now = RTC.now();
  //the following loop sets the value of the boolean interruption to True if the SD card has just been removed
  if(!interruption){
    testFile =  SD.open("test.csv");
    if(!testFile){
      interruption = true;
    }
  }
  //if the SD card had was not inserted at the last measure then check whether it's been inserted again;
  //if it has just been inserted again, then affect again the port 10 to the card and open the logfile in writing mode again to restart the measures without having to stop the measuring session
  //if it has just been inserted again, write also in the CSV logfile the measure data that have been stored in the EEPROM memory of the Arduino during the time the SD card was ejected
  if(interruption){
    pinMode(10,OUTPUT);//port 10 is the port that is connected to the SD card
    if (SD.begin()) {
      interruption = false;
      logfile = SD.open(filename0, FILE_WRITE);
      if(first_opening){
        logfile.println("date,t1,t2,t3,t4,pressure"); //write the title of the columns in logfile CSV file
        first_opening = false;
      }
      int j = 0;
      while (j < index){//index is the integer just after the index of the last byte of the EEPROM memory in which a measure data has been stored during the time SD card was ejected
        logfile.print(1792+EEPROM[j]);//the EEPROM converts the integers into their remainder modulo 256, so until the year 2042 we have to calculate 1792+EEPROM[j] to find the real year
        logfile.print("/");
        //write 01 rather than 1 for january, 02 rather than 2 for february etc. in order to have a date in the standard type
        if(EEPROM[j+1]<10){
          logfile.print("0");
        }
        logfile.print(EEPROM[j+1]);//prints the month in the logfile
        logfile.print("/");
        if(EEPROM[j+2]<10){
          logfile.print("0");
        }
        logfile.print(EEPROM[j+2]);//prints the day
        logfile.print(" ");
        if(EEPROM[j+3]<10){
          logfile.print("0");
        }
        logfile.print(EEPROM[j+3]);//prints the hour
        logfile.print(":");
        if(EEPROM[j+4]<10){
          logfile.print("0");
        }
        logfile.print(EEPROM[j+4]);//prints the minute
        logfile.print(":");
        if(EEPROM[j+5]<10){
          logfile.print("0");
        }
        logfile.print(EEPROM[j+5]);//prints the second
        logfile.print(", ");    
        logfile.print(EEPROM[j+6]);//write t1 in the CSV file to two decimal places
        j = j + 7;//increase the pointer to the EEPROM memory so that it points to the next free byte of the EEPROM
        logfile.print(", ");
        logfile.print(EEPROM[j]);//write t2 in the logfile
        j = j+1;
        logfile.print(", ");
        logfile.print(EEPROM[j]);//write t3 in the logfile
        j = j+1;
        logfile.print(", ");
        logfile.print(EEPROM[j]);//write t4 in the logfile
        //j = j+1;
        //logfile.print(", ");
        //logfile.print(EEPROM[j]);//write temp in the logfile
        logfile.println();
        logfile.flush();
        logfile.close();  
      }
      index = 0;//once all the data stored in the EEPROM have been copied to the CSV logfile, set the index to 0 so that, the next time the SD card is removed, we start writing the measures fromthe beginning of the EEPROM; that enables us to use the maximum of the EEPROM
    }
  }
  //if the current time is between the starting date and the end date, then we write the date in the format YYYY/MM/DD hh:mm:ss followed by the four temperatures
  if(isBefore(start_year0, start_month0, start_day0, start_hour0, start_minute0, start_second0, now.year(), now.month(), now.day(), now.hour(), now.minute(), now.second())&&isBefore(now.year(), now.month(), now.day(), now.hour(), now.minute(), now.second(),end_year0,end_month0,end_day0,end_hour0,end_minute0,end_second0)){
    if(!interruption){//in other words, if the SD card is inserted
      logfile = SD.open(filename0,FILE_WRITE);
      logfile.print(now.year(), DEC);
       logfile.print("/");
      //write 01 rather than 1 for january, 02 rather than 2 for february etc. in order to have a date in the standard type
      if(now.month()<10){
        logfile.print("0");
      }
      logfile.print(now.month(), DEC);
      logfile.print("/");
      if(now.day()<10){
        logfile.print("0");
      }
      logfile.print(now.day(), DEC);
      logfile.print(" ");
      if(now.hour()<10){
        logfile.print("0");
      }
      logfile.print(now.hour(), DEC);
      logfile.print(":");
      if(now.minute()<10){
        logfile.print("0");
      }
      logfile.print(now.minute(), DEC);
      logfile.print(":");
      if(now.second()<10){
        logfile.print("0");
      }
      logfile.print(now.second(), DEC);
      logfile.flush();
      logfile.close();
    }
    //if the SD card isn't inserted then we store the data about the measure times in the EEPROM (electrically erasable programmable read-only memory) waiting that the SD card is inserted again
    if(interruption){ //in other words, if the SD card is not inserted
      int now_year = now.year();
      int now_month = now.month();
      int now_day = now.day();
      int now_hour = now.hour();
      int now_minute = now.minute();
      int now_second = now.second();
      EEPROM.put(index,now_year);
      EEPROM.put(index+1,now_month);
      EEPROM.put(index+2,now_day);
      EEPROM.put(index+3,now_hour);
      EEPROM.put(index+4,now_minute);
      EEPROM.put(index+5,now_second);
    }
    //if ECHO_TO_SERIAL is true, then write in the Serial monitor exactly the same information as in the logfile
    #if ECHO_TO_SERIAL
    Serial.print(now.year(), DEC);
    Serial.print("/");
    if(now.month()<10){
      Serial.print("0");
    }
    Serial.print(now.month(), DEC);
    Serial.print("/");
    if(now.day()<10){
      Serial.print("0");
    }
    Serial.print(now.day(), DEC);
    Serial.print(" ");
    if(now.hour()<10){
      Serial.print("0");
    }
    Serial.print(now.hour(), DEC);
    Serial.print(":");
    if(now.minute()<10){
      Serial.print("0");
    }
    Serial.print(now.minute(), DEC);
    Serial.print(":");
    if(now.second()<10){
      Serial.print("0");
    }
    Serial.print(now.second(), DEC);
    #endif //ECHO_TO_SERIAL
    delay(10);
    int gotArray[5];
    int t1;
    int t2;
    int t3;
    int t4;
    int pressure;
    boolean measure_available = false;
    //int temp;
    wirelessSPI.begin();
    wirelessSPI.openWritingPipe(adresses[1]);//sends data to the underwater arduino
    wirelessSPI.openReadingPipe(1,adresses[0]);//receives data form the underwater arduino
    wirelessSPI.setAutoAck(1);             
    wirelessSPI.enableAckPayload();        
    wirelessSPI.setRetries(5,15);
    wirelessSPI.setPALevel(RF24_PA_HIGH);//sets the level of transmission, min for close trans/em and max for far trans/em

    while(!measure_available){
      wirelessSPI.stopListening();//sets this arduino as emettor
      order = 1;
      wirelessSPI.write(&order, sizeof(order));
      delay(100);
      //order = 0;
      wirelessSPI.startListening();
      int i0 = 0;
      while(i0<10 && !measure_available){
        if(wirelessSPI.available()){
          wirelessSPI.read(&order, sizeof(order));
          if (order == 0){
            measure_available = true;
            //Serial.println("boucle if");
            wirelessSPI.read(&gotArray,sizeof(gotArray));
          }
        }
        i0 += 1;
        delay(100);
      }
    }
    t1 = gotArray[0]
    t2 = gotArray[1]
    t3 = gotArray[2]
    t4 = gotArray[3]
    pressure = gotArray[4]
    
    if(!interruption){//if the SD card is inserted then write the temperatures in the CSV logfile of the SD card
      logfile = SD.open(filename0, FILE_WRITE);
      logfile.print(", ");    
      logfile.print(t1);//write the 1st temperature in the CSV file
      logfile.print(", ");
      logfile.print(t2);
      logfile.print(", ");
      logfile.print(t3);
      logfile.print(", ");
      logfile.print(t4);
      logfile.print(", ");
      logfile.print(pressure);
      //Serial.println("écriture dans le logfile");
      /*logfile.print(", ");
      logfile.print(temp);*/
      logfile.println();
      logfile.flush();//necessary command to write really the data in the logfile and not lose it
      logfile.close();
    }
    if(interruption){//if the SD card isn't inserted then write the temperatures in the EEPROM memory to store them waiting the SD card is inserted again
      EEPROM.put(index+6,t1);
      index = index+7;//we increase the index to set it equal to the next free byte of the EEPROM memory
      EEPROM.put(index,t2);
      index=index+1;
      EEPROM.put(index,t3);
      index = index+1;
      EEPROM.put(index,t4);
      index = index+1;
      EEPROM.put(index,pressure);
      index = index+1;
      /*EEPROM.put(index,temp);
      index = index+1;*/
    }
    #if ECHO_TO_SERIAL
      Serial.print(", ");    
      Serial.print(t1);//write the 1st temperature in the serial monitor
      Serial.print(", ");
      Serial.print(t2);
      Serial.print(", ");    
      Serial.print(t3);
      Serial.print(", ");
      Serial.print(t4);
      Serial.print(", ");
      Serial.print(pressure);
      /*Serial.print(", ");
      Serial.print(temp);*/
    #endif //ECHO_TO_SERIAL
    #if ECHO_TO_SERIAL
      Serial.println();
    #endif // ECHO_TO_SERIAL
    digitalWrite(readPressure, LOW);//set off the 1st temperature trigger
  }
  //Serial.println("fermeture du fichier de mesures");
  syncTime= millis();
  delay(3600000*time_gap_hours0+60000*time_gap_minutes0+1000*time_gap_seconds0);//wait the time gap defined in the instructions before making the next measure
  }
