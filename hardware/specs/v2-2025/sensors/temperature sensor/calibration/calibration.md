# Calibration protocol

The thermistor being connected to an Arduino board, we will obtain the voltage only. Therefore, we need to understand the link between voltage and temperature.

The use of two sensors is recommended to avoid having to repeat an experiment as accurately as possible.
The first one is used to get a voltage, and the second a temperature. We use 4-channel HOBO dataloggers.

Immerse both sensors in hot water and leave them there for about ten minutes, allowing the water to cool to room temperature. The total temperature variation must be sufficient (minimum 10°C). 

The equation linking voltage and temperature is :
$$
\log(\frac{v_{mes}}{V_{ref} - v_{mes}}) = \beta (\frac{1}{T} - \frac{1}{T_{atm}})
$$

Use the data from the experiment and a linear regression to determine $\beta$

With our CTN thermistor, the numeric values were :
- $V_{ref} = 3,3V$ (sensor's input voltage)
- $\beta = 3834K±0,5$%
- $T_{atm} = 298,15K$

