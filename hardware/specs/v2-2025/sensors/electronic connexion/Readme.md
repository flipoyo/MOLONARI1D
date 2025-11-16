# Bulding tutorial of the MOLONARI 1D electronic circuit

__based on the work of the MOLONARI2024 team - changes made by the MOLONARI2025 team__

ENERGY!!! talk about the battery (for pressure sensor - talk about piles!!!! for Wheatstone bridge!!!! )
checker si les In the Air ont déjà mis les infos des codes à mettre sur les cartes... 

## Sensors' electronic circuit

### 1. Equipment

- One [Arduino MKR WAN 1310](https://docs.arduino.cc/hardware/mkr-wan-1310) (data collection + LoRa transmission)
- One [Adalogger Featherwing SD-RTC Module](https://www.adafruit.com/product/2922) (to connect as per the instructions below - see section 2. Connections)
- One [Waterproof Antenna](https://store.arduino.cc/products/dipole-pentaband-waterproof-antenna) (to connect to the MKR WAN 1310)
- Micro USB - USB cables or batteries (to power the boards). Note: USB connection allows for power supply and communication with the computer (for code and Serial port). It also allows charging a battery connected to the MKR WAN.

### 2. Connections

For the connections, two functionnal sensors' electronic circuits were soldered by the MOLONARI2025 team. This section is useful in order to solder more electronic circuits. 

By *connections* we mean the electrical connections between the *MKR WAN 1310* (A) and the *Adalogger Featherwing* (B) (SD + RTC), as well as with the sensors. For more clarity, you can find the *pinouts* (= pin mappings of a board) at the following links:

- [Pinout MKR WAN 1310](https://docs.arduino.cc/hardware/mkr-wan-1310) → "Pinout +"
- [Pinout Featherwing](https://learn.adafruit.com/adafruit-adalogger-featherwing/pinouts)

It is interesting to note that the pins not used on the Featherwing are useless and especially **connected to nothing**. So you can run cables on the breadboard lines associated with these pins (which are not).

Each step is detailed below, but here is a diagram that summarizes everything:
![Connection diagram](Images/connectingClockAndSDToArduinoMKR1310.png)

For a detailed diagram of how to solder the electronic circuit, please see the document 'electronic connexion\Electronic circuit soldering diagram.pdf'.

### 2.1. Power supply part

Make sure the battery power goes well to the *Featherwing*. This means connecting, as indicated on *diagram 1*:

* the grounds (GND). It is recommended to reserve a line of the breadboard for the use of a common ground (this is a common practice that facilitates wiring and its revision). In the case of the first prototype realized, the red line was reserved as ground. 
* the VCC pin (A) to the 3.3V port (B). Since the SD card needs to be connected to the VCC port all the time we recommend to assign a whole line in the bread board where is the *Featherwing* to the VCC.
* the sensors. We assigned one digital port (pin 1) to feed the sensors only when the Arduino is not sleep (when it has to take the measurements), we reserved a whole line for that in the breadboard where the Arduino is.

### 2.2. SD part

Here, there are 4 pairs of pins to connect to ensure communication:

* The chosen CS pin on (A) (we took 5)* to the SDCS pin (B)
* The following 3 pins (they ensure SPI communication) be careful it's very technical:
  * (A) SCK - SCK (B)
  * (A) MOSI - MOSI (B)
  * (A) MISO - MISO (B)

**<u>Note:</u>** The CS pin on (A) is optional, it must in any case match the "`const int CSPin`" appearing in the file [Sensor.ino](../Sensor/Sensor.ino) (see below). Do NOT take pin 6. The reason is simple: it is directly connected to the built-in LED of the board, and it will light up every time you communicate with the SD module, and it will drain the battery.

### 2.3. RTC part

For the RTC, there are 2 wires to connect:

*   (A) SCL - SCL (B)
*   (A) SDA - SDA (B)

### 2.4. Sensors

This part applies to temperature sensors (rod with 5 thermistors). If you use a differential sensor (for pressure) you will need to get information. Otherwise, for the temperature part, the cable output of each sensor consists of 3 parts:

* The yellow cable → ground (GND)
* The blue cable → 3.3V power supply (VCC)
* the white cable → board pin (we took A1, A2, A3, and A4)

**Note:**  
To save energy, we cut off the power to the sensors when not in use, as we mentioned before. To do this, we simply connected the + of the sensor power supply (blue cable) to pin 2 which is connected to the black line in the breadboard, in this way the sensors are only feed when it is necessary.


## Relay's electronic circuit

The electronic circuit for the relay is the same as for the sensors with one small difference, it doesn't have the blockers, those green components that are used to connect the sensors to the circuit. Because no sensors are connected to the relay's electronic circuit, neither does it need the wires connecting the ground (GND) to the green blocker. 

This circuit only has the connections between the Arduino card and the Adalogger. 

Here is a picture of the relay's electronic circuit : 






## 3. The code to insert into the circuits.

You will need a *USB - Micro USB* cable connected to a computer with Arduino IDE and the code to insert.  
**Very important:** the main code file (in our case [Sensor.ino](../Sensor/Sensor.ino)) must be in a folder with the **same name** (that's how it is).

To know which code to insert into which electronic circuit, please refer to ... 

### 3.1. Sensor code (in the river)

For the sensor, it's the code [Sensor.ino](../Sensor/Sensor.ino) that needs to be loaded.

Before uploading the code, make sure the pins (CSPin and sensor pins) match what is actually happening, otherwise, the worst thing that can happen to someone doing this kind of thing will happen: the code compiles and it still doesn't work...

Then it's Upload (the button with the arrow). If the Arduino does not appear when you are asked to choose the board while it is properly connected, press the reset button on the Arduino twice. Then, reselect the COM port to the right of the upload button. If after that it still doesn't work: google and good luck :)

In order to better understand the sensor code, you can see the file *2 - Explaining the sensor code* which explains each section of the code and the classes necessary for its operation.

### 3.2. Relay code (on the shore)

It's the same, but with the right code ([Relay.ino](../Relay/Relay.ino)). Simple, right?




















## 4. Finalize

*Note: Some instructions in this part are only useful if you want to do a demo. For tests, you can simply connect the boards to a computer via USB, to have a Serial connection. In particular, you can skip putting the electronics in the waterproof box.*

### 4.1 Transmitter side:
Pass the temperature probe cables through the cable glands (unscrew the cover, insert the cables, screw the cover back on for sealing). See the photo below for an idea.  
Put ballast at the bottom of the box to prevent it from floating. Plan at least 2~3 kg.

It should look like this:
![Interior view](Images/MOLONARI_vue_intérieure.jpg)

Then you need to **delete all files from the SD card** and insert it into the Adalogger. All that's left is to connect the antenna and the battery.  

If everything goes well, the orange LED should light up and then turn off. It lights up as soon as the program starts and turns off when it has successfully initialized. If the LED does not turn off, it is probably due to an SD card problem.  
NB: it is normal for the green LED not to light up when the Arduino is on battery, the manufacturers did this to avoid wasting power.

Put the roof back on and screw it (tightly) for sealing (note in the photo the screws are not screwed in)  
![Exterior view](Images/MOLONARI_vue_exterieure.jpg)

### 4.2 Receiver side:

If you want to do a demo, connect the antenna to the Arduino, and connect the Arduino to a computer via USB. On the computer, open software that will read what the Arduino sends on the Serial port. (For example, the `Serial Monitor` of `Arduino IDE`)  
Here too, if everything goes well the orange LED should light up and then turn off. If it does not turn off, it is probably because there is no software using the Serial port on the computer.  

This year we placed a box on the ground where it should be placed in relay in case we put the whole system in the river ready to take and send data. The Arduino must be connected to an antenna and a battery. As proposed improvements for future editions, it is recommended to place a second Arduino in the box that is ready to take control in case the first Arduino stops communicating with the sensor for any reason.

![Relay box](Images/relay_box.jpeg)

Additional options:  
- **Curve on Arduino IDE**: If you want the data to appear on a curve, connect `pin 1` to `VCC` (+3V) on the receiving Arduino, and launch the `Serial Plotter` of `Arduino IDE`.

