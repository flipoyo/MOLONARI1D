# Calibration of the temperature sensors

The temperature sensors that are used are : 
- HOBO TMC6 HD
They are NTC thermistors, which means that they have a voltage divider bridge inside, with a variable resistance, that is linked to the temperature variation. The temperature sensor measures a voltage and thanks to the voltage-temperature law (see below), we can obtain the temperature. 

The voltage-temperature law is : 

$ T = 1/((1/\beta)*ln(v_{mes}/(V-v_{mes})) + 1/298.15)$ 

with $v_{mes}$, the voltage measured by the temperature sensor and $T$ the temperature. 

This law has two parameters : V and $\beta$. 

- We immersed two sensors in hot water and left them there for about ten minutes, allowing the water to cool to room temperature. The total temperature variation must be sufficient (minimum 10°C). Using a 4-channel HOBO datalogger device we measured for the two sensors at the same temperature the voltage for one and the temperature for the other and then by using a linear regression between $ln(v_{mes}/(v-v_{mes}))$ and $1/T$ we obtained $\beta = 3834K±0,5$%.

- The parameter V is given by the electronic circuit to which the sensor is connected. Indeed, it delivers a voltage of 3.3V, so $V=3.3$. 


You can find in the same folder the Python file (Calcul_beta.py) used to clean the csv datas and create a new csv with only the useful datas, that was then used in an Excel file to determine the $\beta$ parameter with its uncertainty, thanks to the DROITEREG function. 

### Here is an image of the temperature sensor. 

![Temperature sensor](capteur_temperature_avec_cables.jpg)

3D printing files and instructions for the thermometer/pressure shaft are available in the "shaft" folder.

