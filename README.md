#  ![logo](Figures/logo_MOLONARI_smll.png)  MOLONARI1D ecosystem

MOLONARI stands for "**mo**nitoring **lo**cal des échanges **na**ppe-**ri**vière", which translates in English to **lo**cal **mo**nitoring of **s**tream-aquifer exchanges (LOMOS). This project aims to develop a comprehensive environmental monitoring solution for **water and heat exchanges* * in riverbed environments. 

This repository provides detailed descriptions and scripts on how to build, prepare and deploy a 1D MOLONARI device, from hardware deployment to scientific analysis. A MOLONARI1D device provides **temperature and pressure sensors** in the river bed, at depths ranging from 0 to ~40cm. In the long run, these measures give us informations on water and heat exchanges between the river and the aquifer, and on the aquifer's properties (porosity, permeability, etc.)

![MOLONARI1D_v1.0](Figures/schemaMOLONARI.png)
__MOLONARI 1D v1.0 is composed of two devices, measuring depth distributed temperatures and the associated hydraulic head difference over the riverbed. MOLONARI 1D v2.0 integrates all the sensor in one device only __

**Key attention points** - The MOLONARI1D device is designed with the following key concepts in mind :
- low-tech production
- open-source and replicability
- scalability

## Core Components

Here is an overview of the main features developed so far in the MOLONARI1D project.

### 🔧 **Hardware** - MOLONARI1D Devices Ecosystem
*Arduino-based underwater sensors network*

- **Sensor Nodes**: Waterproof packages with temperature/pressure sensors
- **Relay Stations**: Data aggregation and LoRaWAN communication
- **Communication Protocols**: Custom LoRa (local) + LoRaWAN (wide-area)
- **Power Management**: 8-12 months autonomous operation

### 🔬 **pyheatmy** - Scientific Computing Engine
*Bayesian inference for hydrological parameter estimation*

- **Bayesian inversion, MCMC based**: Infers physical properties of 1D riverbed columns - multichain MCMC also available
- **Data Integration**: Direct coupling with sensor data streams from monitoring systems
- **Uncertainty Quantification**: Provides parameter estimates with confidence intervals
- **Research Extensions**: Modular architecture supporting experimental features

### 📊 **Molonaviz** - Device Management & Visualization  
*PyQt5-based GUI for operational monitoring*

- **Device Registration**: Laboratory and sampling point hierarchy management
- **Data Pipeline**: Quality control workflows from raw sensor data to analysis-ready datasets
- **Analysis Integration**: Direct launching of pyheatmy inference workflows

**⚠️ Requirements**: Python 3.10+ for Molonaviz, Python 3.9+ for pyheatmy

## Network Architecture

MOLONARI1D implements a **multi-tier monitoring network architecture** designed for scalable, autonomous environmental monitoring.

![MOLONARI1D](Figures/Chaine_informations.jpg)

**Data Flow Pipeline:**

```
Underwater Sensors → Relay → Gateway → Server → Database → Analysis Tools
     (Arduino)       (LoRa)  (LoRaWAN)  (Internet) (SQL)   (Python ML/GUI)
```

1. **Field Sensors**: Battery-powered Arduino devices collect temperature/pressure every 15min
2. **Local Communication**: Custom LoRa protocol transmits sensor data to relay daily
3. **Wide Area Network**: LoRaWAN gateway forwards data to internet-connected server
4. **Quality Control**: Server database processes and validates incoming sensor data - backend of Molonaviz
5. **Analysis Interface**: GUI manages devices and launches scientific computing - frontend of Molonaviz
6. **Scientific Inference**: pyheatmy performs Bayesian MCMC inversion for flux estimation

## Repository Structure

```
MOLONARI1D/
├── hardware/              # Arduino-based monitoring devices
│   ├── sensors/             # Temperature, pressure, and demo sensors
│   ├── relay/               # Data aggregation stations
│   ├── shared/              # Common libraries and protocols
│   ├── tests/               # Hardware validation tests
│   └── docs/                # Hardware documentation
├── pyheatmy/              # Scientific computing engine
├── Molonaviz/             # Device management GUI
├── data/                  # Sample datasets
└── dataAnalysis/          # Analysis tools and notebooks
```

## Target Audiences

- **🔬 Research Users**: Operate monitoring systems and analyze flux data
- **💻 Software Developers**: Extend Python ecosystem and analysis tools  
- **🔧 Hardware Developers**: Build and deploy sensor networks
- **📡 Protocol Engineers**: Develop communication systems
- **🏭 Fablabs**: Manufacture and deploy monitoring hardware

## Getting Help

- **📖 Documentation**: See component-specific README files
- **🧪 Examples**: Check `data/` and `dataAnalysis/` directories  
- **🐛 Issues**: Open GitHub issues for support and bug reports
- **💬 Community**: Participate in collaborative development

## Warning on reliability

This version of MOLONARI1D is a development version. Some features are not yet implemented or are incomplete.
Some bugs may also appear. We therefore do not guarantee any reliability on the resulting values of the calculations, however the data format will remain constant during their full implementation. Think of this code as a template that will remain persistent when the features are reliable in their results.

## Recent Improvements (December 2024)

🚀 **Enhanced Development Workflows**: Comprehensive repository reorganization with team-oriented structure, consolidated shared libraries, and automated CI/CD validation for all components.

📚 **Comprehensive Documentation**: Added 15+ README files for Arduino sketches, complete API documentation (MOLONARI1D_API.md), and integration guides between hardware and software components.

🔧 **Improved Hardware Integration**: Better integration between the original `Device/` structure and new organized `hardware/` directory, with clear migration paths and backward compatibility.

✅ **Quality Assurance**: Fixed CI issues, validated all test suites, and ensured robust development workflows for multi-team collaboration.

## Contributors
MOLONARI1D is a teaching and research project held at Mines Paris - PSL since 2021, under the supervision of Nicolas Flipo, Aurélien Baudin, Agnès Rivière, Thomas Romary, and Fabien Ors.

- Nicolas Flipo supervises the development of the MOLONARI 1D ecosystem. He manages the github repository and the developpers' teams. With Fabien Ors and Pierre Guillou, he is in charge of the source code development either for hardware programming, scientific computing, and IT
- Aurelien Baudin and Agnès Rivière supervise the **monitoring device development** and their **_in situ_ deployment**
- Nicolas Flipo and Thomas Romary supervise the development of **pyheatmy**
- Fabien Ors contributed to the 2021 and 2022 editions by conceptualising **molonaviz**, and since 2024 securizing it
- Since 2024, Pierre Guillou secures the software deployment

The MOLONARI1D project is integrated into the french project [EQUIPEX+ TERRA FORMA](https://www.insu.cnrs.fr/fr/cnrsinfo/terra-forma-un-nouveau-paradigme-pour-lobservation-des-territoires "link to TERRA FORMA") led by CNRS. 

The student contributors are, for **pyheatmy**:
- 2021 Mathis Bourdin & Youri Tchouboukoff
- 2022 Guillaume de Rochefort, Loris Megy, Valentin Alleaume
- 2023 Mattéo Leturcq-Daligaux, Nicolas Matte, Mathis Chevé, Zhan Jing, Dan Maurel
- 2024 Martin Jessenne, Ombline Brunet, Alexandre Noël, Jordy Hurtado Jimenez, Aurélie Reynaud, Antoine Bourel de la Roncière, Colin Drouineau

for **molonaviz**:
- 2021 Sandra Clodion & Charlotte de Mailly Nesle
- 2022 software restarted from scratch by Guillaume Vigne
- 2023 Thibault Lambert

for **hardware programming**:
- 2022 Wissam Karrou, Guillaume Rouy, Pierre Louisot 
- 2023 François Bradesi, Aymeric Cardot, Léopold Gravier, Léo Roux
- 2024 Mohammad Kassem, Zehan Huang, Lucas Brandi, Haidar Yousef, Valeria Vega Valenzuela, Zihan Gu, Yufan Han, Yibing Wang

## Copyright

[![License](https://img.shields.io/badge/License-EPL_2.0-blue.svg)](https://opensource.org/licenses/EPL-2.0)

&copy; Contributors to the MOLONARI1D softwares.

*All rights reserved*. This software and the accompanying materials are made available under the terms of the Eclipse Public License (EPL) v2.0 which accompanies this distribution, and is available at http://www.eclipse.org/legal/epl-v20.html.

**pyheatmy** and **molonaviz**  were first released in 2021 under the MIT license.
