# Pressure sensors sampling

Pressure sensors are unique and temperature-dependant: for a same differential pressure, different sensors can yield different voltages, who moreover depend on the sensor's temperature. Those voltages can vary by up to 50% for a same pressure.

The sampling process is hence necessary for determining the real differential pressure between the two water columns. We are trying to determine the following function: $$\Delta P=f(U, T)$$

A first and easy model would be a linear regression:
$$\Delta P = \alpha U + \beta T$$

To determine $\alpha$ and $\beta$, we combine two sampling processes:
- constant $T$, varying $\Delta P$ $\rightarrow$ measured manually by regularly adding water in one of the two columns
- constant $\Delta P$, varying $T$ $\rightarrow$ measured automatically in the thermostatic chamber

We use 4-channel HOBO dataloggers.

## Problems encountered

### Conduction

The temperature of the sensor is not the one of the river because transferring heat requires time.

We overcome this problem with a simple conduction model that implies a phase-shift between the river temperature wave and the sensor temperature wave. In order to determine this phase-shift, we mould a pressure sensor with a temperature probe in direct contact with the sensor. We then run a 48h temperature sine wave in the thermostatic chamber. We have thus the river's temperature log and the pressure sensor's temperature log.

### Connectivity

Some of the channels measured by HOBO yield erratic pressure logs. The data can not be used. This may be due to defaults in the Jack connections.

### Long-run voltage drop

Some of the pressure sensors show a curious behavior: their output voltage slowly drops down (~5mV/minute). This is the case of `sensor XXV`. We do not know where the problem comes from but we can eliminate hypothetical causes:
- temperature sensibility: after a 36h sine-like temperature command in the chamber, the voltage is strictly decreasing despite temperature varying up and down.
- HOBO dataloggers: the problem is independant of the HOBO datalogger or the channel used.
- air bubbles: the voltage comes up again when plugged in a new channel, and starts decreasing again.

Thus, the problem may come from the electronic components, or the battery, despite the flickering of the yellow LED.