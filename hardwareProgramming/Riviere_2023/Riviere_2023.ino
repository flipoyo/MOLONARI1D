/*
This firmware will be is meant for the arduino in the river bed of the Molonari system.

Functionalities :
  - Making measurements from the temperature and pressure sensors.
  - Sending the measurements via LoRa
  - Saving the measurements in an internal memory

Required hardware :
Arduino MKR WAN 1310
*/

#include "internals/Lora.cpp"
#include "internals/Low_Power.cpp"
#include "internals/Pressure_Sensor.cpp"
#include "internals/Temp_Sensor.cpp"
#include "internals/Time.cpp"
#include "internals/Internal_Log.cpp"


void setup() {
  // put your setup code here, to run once:
  InitialiseLora();
  InitialiseRTC();
  InitialiseLog();
}


void loop() {
  // put your main code here, to run repeatedly:

}