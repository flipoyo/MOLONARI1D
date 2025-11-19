# Pressure sensors sampling

## In this folder

- `AtmoCONTROL_command_generation.ipynb` : The thermostatic chamber only accepts temperature ramps as input. This file contains a program that can break down any signal into ramps
- `AtmoCONTROL_userguide.md` : Userguide of the thermostatic chamber
- `cleaner.ipynb` : program to clean the data generated for several calibrations in the thermostatic chamber
- `phase_shift.ipynb` : program to determine the second-order low-pass filter suitable for modeling conduction in the sensor.

## Introduction

Pressure sensors are unique and temperature-dependant: for a same differential pressure, different sensors can yield different voltages, who moreover depend on the sensor's temperature. Those voltages can vary by up to 50% for a same pressure.

The sampling process is hence necessary for determining the real differential pressure between the two water columns. We are trying to understand the following relation : $$U = f(\Delta H, T)$$ in order to determine the following function: $$\Delta H=f(U, T)$$

The ideal model is : 
$$
U = \alpha \Delta H
$$

This model needs to be corrected in temperature. The sensor manufacturer offers the following formula :
$$
U_{corr} = U_{mes} + (T_0 - T)\frac{\partial U_{mes}}{\partial T}
$$
With $U_{corr} = \alpha(T_0)\Delta H - \beta(T_0)$, that is, the linear calibration linking $U$ to $\Delta H$ was performed at a constant temperature $T_0$

To determine the right equation, we combine two sampling processes:
- constant $T$, varying $\Delta H$ $\rightarrow$ measured manually by regularly adding water in one of the two columns
- constant $\Delta H$, varying $T$ $\rightarrow$ measured automatically in the thermostatic chamber

We use 4-channel HOBO dataloggers.

## Problems encountered and proposed solutions

### Conduction

The temperature of the sensor is not the one of the river because transferring heat requires time.

We overcome this problem with a conduction model that implies a phase-shift between the river temperature wave and the sensor temperature wave.

The model used in the previous years, which is still efficient, is : 
$$
\phi = a\frac{\partial T}{\partial t} + b
$$

(the internal temperature would then be $T_{int} = T_{ext}(t - \phi)$)

In 2025, we proposed another more intuitive method, consisting of assimilating conduction to a second-order low-pass filter without oscillations. Its advantage is that only one temperature window is needed to determine the coefficients.

In the Laplace domain :

$$
T_{int}(p) = H(p)T_{ext}(p)
$$
where :
$$
H(p) = \frac{1}{(1 + \tau_1 p)(1 + \tau_2 p)}
$$

$\tau_1$ and $\tau_2$ are obtained by optimisation, using the least squares method on experimental data. For `sensor XV` : $\tau_1 = 377.91s$ and $\tau_2 = 922.88s$ were found.

(Comparison with experimental data on a sinus : $MSE = 0.01$)

### Connectivity

Some of the channels measured by HOBO yield erratic pressure logs. The data can not be used. This may be due to defaults in the Jack connections.

### Long-run voltage drop

Some of the pressure sensors show a curious behavior: their output voltage slowly drops down (~5mV/minute). This is the case of `sensor XXV`. We do not know where the problem comes from but we can eliminate hypothetical causes:
- temperature sensibility: after a 36h sine-like temperature command in the chamber, the voltage is strictly decreasing despite temperature varying up and down.
- HOBO dataloggers: the problem is independant of the HOBO datalogger or the channel used.
- air bubbles: the voltage comes up again when plugged in a new channel, and starts decreasing again.

Thus, the problem may come from the electronic components, or the battery, despite the flickering of the yellow LED.

## Calibration protocol

### Linear relation between $U_{corr}$ and $\Delta H$

With constant $T$, vary $\Delta H$ $\rightarrow$ measured manually by regularly adding water in one of the two columns. Voltage is given by the datalogger.

![Sampling setup](</differential pressure sensor/calibration/pictures/setup_sampling.jpg> "Dispositif de mesures à T ambiante")

Then, use a linear regression to obtain $\alpha$. Remember to write down temperature.

### Temperature correction (phase shift)

#### If you have a sensor with an internal thermistor

Put the differential pressure sensor in a climate chamber. Program two successive 4-hours periods, at two different temperatures $T_1$ and $T_2$ (with $T_2 - T_1 = 5$°C for example). Use a datalogger to record internal temperature $T_{int}$.

Then, use the code in `phase_shift.ipynb` in order to determine $\tau_1$ and $\tau_2$ of the low-pass filter. You can then adapt them slightly so that they better match the voltage supplied by your other sensors (through minimization of the MSE).

Alternatively, determine $a$ and $b$ in the equation $\phi = a\frac{\partial T}{\partial t} + b$ mentionned above. 

#### Else

Impose a diffential pressure close to 0. Instead of $T_{int}$, use $f(U) = mU + p$, where $m$ and $p$ are such that $f(U)(t=0) = T_1$ and $f(U)(t\rightarrow \inf) = T_2$