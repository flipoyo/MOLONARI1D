# MOLONARI1D ecosystem

## The MOLONARI1D ecosystem

MOLONARI means MOnitoring LOcal des échanges NAppe-RIvière, which translates in english LOcal MOnitoring of Stream-aquifer exchanges (LOMOS)

The ecosystem is dedicated to the monitoring of water and heat exchanges in riverbed. It includes monitoring devices and two softwares under the EPLv2.0 license. 

One software **PyHeatMy** is dedicated to the inference of water and energy fluxes from the data acquired by the monitoring systems. It implements an MCMC approach taht infers the physical properties of a 1D column of a riverbed forced by hydraulic head difference between the top and the bottom of the column, as well as the associated temperatures. The energy of each MCMC iteration is calculated based on the RMSE between simulated and monitored temperatures at three depths of the porous medium column. For more information, please see the associated folder in the current repository.

The other software **Molonaviz** is a GUI that allows for the management of the monitoring devices as "labs", the monitoring data of "sampling points", as the interpretation of the data with **PyHeatMy**. It is designed in a frontend and backend programs that interacts with each other. The frontend uses the Qt library in python, and the backend handles a SQL database. **WARNING**: Molonaviz requires python 3.10 at least. You cannot use molonaviz with an older version of Python.


## Contributors
MOLONARI1D is a teaching and research project held at Mines Paris - PSL since 2021. under the supervision of Nicolas Flipo, Aurélien Baudin, Agnès Rivière, Thomas Romary, and Fabien Ors. 
- Nicolas Flipo supervises the MOLONARI 1D ecosystem
- Aurelien Baudin and Agnès Rivière supervise the monitoring device development and their __in situ__ deployment
- Nicolas Flipo and Thomas Romary supervise the development of **PyHeatMy**
- Fabien Ors contributed to the 2021 and 2022 editions by conceptualising **Molonaviz**

The MOLONARI1D project is integrated into the french project [EQUIPEX+ TERRA FORMA](https://www.insu.cnrs.fr/fr/cnrsinfo/terra-forma-un-nouveau-paradigme-pour-lobservation-des-territoires) "link to TERRA FORMA") led by CNRS. 

The student contributors are, for **PyHeatMy**:
- 2021 Mathis Bourdin & Youri Tchouboukoff
- 2022 Guillaume de Rochefort, Loris Megy, Valentin Alleaume

for **Molonaviz**:
- 2021 
- 2022 software restarted from scratch by Guillaume Vigne

## Copyright

[![License](https://img.shields.io/badge/License-EPL_2.0-blue.svg)](https://opensource.org/licenses/EPL-2.0)

&copy; Contributors to the MOLONARI1D softwares.

*All rights reserved*. This software and the accompanying materials are made available under the terms of the Eclipse Public License (EPL) v2.0 which accompanies this distribution, and is available at http://www.eclipse.org/legal/epl-v20.html.

**PyHeatMy** and **Molonaviz**  were first released under the MIT license.


## Warning on reliability

This version of MOLONARI1D is a development version. Some features are not yet implemented or are incomplete.
Some bugs may also appear. We therefore do not guarantee any reliability on the resulting values of the calculations, however the data format will remain constant during their full implementation. Think of this code as a template that will remain persistent when the features are reliable in their results.



## Installation

Here is a step-by-step guide to install the ecosystem: 
- First install **PyHeatMy**, from the __ad hoc__ folder, by running:
```sh
pip install -r requirements.txt
pip install -e .
```
For more informations on the software, please check the folder

- Second install **Molonaviz**, from the __ad hoc__ folder, by running ```pip install -e .```
For more informations on the software, please check the folder


You are now set to use the ecosystem. To launch it, you can simply run ```molonaviz``` in a terminal.
