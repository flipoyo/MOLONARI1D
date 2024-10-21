# Climate Chamber Userguide

---

## 1. Introduction
With AtmoCONTROL, you can graphically create, modify, and save programs with various parameters on the computer and transfer these programs to the climate chamber using a USB disk.
![Climate chamber](./Images/v003.jpg)

## 2. Working with AtmoCONTROL
Since we use the computer in zoom V003 at MINES, the following operations are based on the assumption that the AtmoCONTROL software has been installed and the AtmoCONTROL FDA device license has been successfully set up.

### 2.1 Starting AtmoCONTROL
First, unlock the computer using the MINES email address. The AtmoCONTROL program is available on the desktop (or in the Start menu). It does not allow multiple Windows users to operate on the same computer in parallel. **The student account may have limited usage rights, such as being unable to set temperature parameters.** (Aurélien mentioned that we can use his account temporarily, and he will apply for permissions for us.)

### 2.2 Program Interface
![Interface](./Images/interface.png)
1 Menu bar 
2 Toolbar 
3 Status bar 
4 Signature bar
5 Show/hide status bar
6 Editor, simulation and protocol window 
7 Programming mode switch

#### 2.2.1 Menu bar
![Menu bar](./Images/menu_bar.png)

#### 2.2.2 Toolbar
![Toolbar](./Images/toolbar.png)


#### 2.2.3 Status bar
The status bar gives an overview of the appliances logged on to AtmoCONTROL. Appliances can be added and removed again.

If the appliance is connected to the computer via Ethernet and it has already been logged on once, it is automatically recognised and the current operating state (temperature, alarms) is displayed
![Status bar](./Images/status_bar.png)
Look at this exemple. (1)An appliance of type ICO50; (2) named “Laboratory”; (3) by the user, is registered via Ethernet; 
(4) current operating status in AtmoCONTROL.

### 2.3 Program
In the Editor window, programs can be created: sequences of various parameters (e.g. temperature, pressure and humidity), which the appliance then implements from a definable point in time.

To be able to create a program in AtmoCONTROL, the appliance which is to perform the program must be listed in the status bar and selected. The appliance can, but does not have to, be connected to the computer via the network. 
![Create a program](./Images/create_programs.png)
Select the appliance that will later perform the program by clicking on it in the status bar. An icon bar with the available parameters for this appliance is shown. Additionally, one or two editor threads are displayed, depending on the appliance. The program sequence is determined on these. Two editor threads are always shown for appliances with humidity or pressure control (3 and 4), and one editor thread for all others.

**Bear in mind that the two editor threads are not synchronised.** This means that a specific X position on one thread does not match the same position on the other thread in time. If you want to see the parameter values for a specific point in time, you must change to the simulation mode. While creating the program, you can display the prospective progression of all parameters as a diagram at any time. To do this, click on "Simulation" (see 5 in the image of the part 2.2)


#### 2.3.1 Create a program

**To create a program, just drag the individual parameter icons onto the editor thread one after another in the desired order**, while holding down the left mouse button. It's easy! To remove a parameter icon from an editor thread, select it and, with the mouse button depressed, move it to the recycle bin symbol on the lower right. 
![Drag](./Images/drag.png)

#### 2.3.2 Parameters
If a parameter icon is clicked on an editor thread, it is displayed with an orange frame. The adjustable values – in the example, the ramp name, the duration and the temperature – have a grey background. 
![Tolerance band](./Images/tol.png)
For simulations with constant parameters, 1 represents the duration and 2 the parameter value. In the window on the right that can be displayed and folded, you can edit the tolerance band. We usually set it to the minimum value. Below it is the indicator light on the climate chamber, it is suggested to turn the safe indicator "on".
![SPWT](./Images/SPWT.png)
For time-varying parameters, the only difference is that the right window shows SPWT, which means the setpoint wait. If this is “on”, the program sequence is not continued before the setpoint value is reached, even if the set time has already expired. If this is “off”, the program sequence is continued after the set time has expired, irrespective of whether the setpoint value was reached or not. 

It is worth mentioning that for unknown reasons, we found that if the value of the first stable temperature is not set, the subsequent temperatures will automatically start from 20℃. Therefore, it is recommended to set a stable temperature of at least 5 minutes.
![First two](./Images/first.png)
These are some other available parameters in the icon bar. Take the sinus curve as an exemple, we usually use an ascending straight line, a straight line parallel to the x-axis, and a descending straight line to simulate it.
![Available parameters](./Images/para.png)

#### 2.3.3 Saving
Here we only introduce the way to transfer a program via USB. Click Program -- Export to USB drive. The program is saved on the USB storage medium connected. Then connect the USB data medium to the appliance which is to run the program.
![Saving](./Images/save.jpg)

#### 2.3.4 Loading and running the program
A brief introduction to the climate chamber:
![Buttons](./Images/button.png)
1 Touch to select
2 Return to the main menu
3 You can either turn it to select or press the middle to decide
4 USB

To load the program, you should first touch the "MENU" to go into the "PROG". Then turn the button 3 and press to select your program exported. Once you have selected it, turn the button 3 and press the middle to run it. It's over! Just wait.
![Select](./Images/select.jpg)
![Run](./Images/run.jpg)
![Program begins](./Images/begin.jpg)
The above user guide is not complete. If you have other needs, please refer to https://www.memmert.be/wp-content/uploads/2019/10/AtmoCONTROL-.pdf
### 2.4 Program exemple
We use the function $T=-a\sin{\left(\frac{2\pi}{24}h\right)}+b$ to represent the way of daily temperature change in a region.

We want to convert the sinus function into straight lines so that the climate chamber could work to simulate the daily change. We take the average temperature of Paris on a random day of $20℃$ and the diurnal temperature range of about $8℃$ as example. So here we take $a=4$ and $b=20$. 

With the function, we can integrate and get the area above $T=20$, which is $30.56$. We would like to form the same area above and below average with straight lines.
![DailyT](./Images/dailyT.jpg)
 With the graph of three day’s temperature change above, we can get the heating rate is approximately three times higher than the cooling rate. By calculating the trapezoid size, we will have the following result as an example: 

We start the climate chamber at the simulation of 8am, when the sun starts to heat the earth, we experience a climbing temperature of 4 hours 22 minutes from $16℃$ to $24℃$. Then we maintain the temperature at $24℃$ for 3 hours 28 minutes. Now it should be around 4pm in the afternoon, the temperature starts to decrease slowly, so we set the climate chamber to cool down for 13 hours 4 minutes to reach $16℃$, until it’s early morning again, and the temperature stays at $16℃$ for 3 hours 28 minutes, before the next 8am arrives. We can identify that this model looks pretty similar to the temperature change on the graph above based on the real statistics

In this case, we can successfully simulate the temperature change of one day in Paris, for winter or summer we could simply replace $16-24℃$ by for example $6-14℃$ or $22-30℃$.

