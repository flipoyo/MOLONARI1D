#  ![logo](Figures/logo_MOLONARI_smll.png)  MOLONARI1D ecosystem



MOLONARI means MOnitoring LOcal des échanges NAppe-RIvière, which translates in english LOcal MOnitoring of Stream-aquifer exchanges (LOMOS)

The ecosystem is dedicated to the monitoring of water and heat exchanges in riverbed. It includes monitoring devices and two softwares under the EPLv2.0 license. 

One software **pyheatmy** is dedicated to the inference of water and energy fluxes from the data acquired by the monitoring systems. It implements an MCMC approach taht infers the physical properties of a 1D column of a riverbed forced by hydraulic head difference between the top and the bottom of the column, as well as the associated temperatures. The energy of each MCMC iteration is calculated based on the RMSE between simulated and monitored temperatures at three depths of the porous medium column. For more information, please see the associated folder in the current repository.

The other software **molonaviz** is a GUI that allows for the management of the monitoring devices as "labs", the monitoring data of "sampling points", as the interpretation of the data with **pyheatmy**. It is designed in a frontend and backend programs that interacts with each other. The frontend uses the Qt library in python, and the backend handles a SQL database. **WARNING**: Molonaviz requires python 3.10 at least. Always secure your python version operating in a virtual python environment (see below).


## Contributors
MOLONARI1D is a teaching and research project held at Mines Paris - PSL since 2021, under the supervision of Nicolas Flipo, Aurélien Baudin, Agnès Rivière, Thomas Romary, and Fabien Ors.

- Nicolas Flipo supervises the development of the MOLONARI 1D ecosystem
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

for **hardwareProgramming**:
- 2022 Wissam Karrou, Guillaume Rouy, Pierre Louisot 
- 2023 François Bradesi, Aymeric Cardot, Léopold Gravier, Léo Roux
- 2024 Mohammad Kassem, Zehan Huang, Lucas Brandi, Haidar Yousef, Valeria Vega Valenzuela, Zihan Gu, Yufan Han, Yibing Wang

## Copyright

[![License](https://img.shields.io/badge/License-EPL_2.0-blue.svg)](https://opensource.org/licenses/EPL-2.0)

&copy; Contributors to the MOLONARI1D softwares.

*All rights reserved*. This software and the accompanying materials are made available under the terms of the Eclipse Public License (EPL) v2.0 which accompanies this distribution, and is available at http://www.eclipse.org/legal/epl-v20.html.

**pyheatmy** and **molonaviz**  were first released in 2021 under the MIT license.


## Warning on reliability

This version of MOLONARI1D is a development version. Some features are not yet implemented or are incomplete.
Some bugs may also appear. We therefore do not guarantee any reliability on the resulting values of the calculations, however the data format will remain constant during their full implementation. Think of this code as a template that will remain persistent when the features are reliable in their results.

![MOLONARI1D](Figures/schemaMOLONARI.png)

## Get the sources

Due to the large history of commits, cloning the repositroy may need to be performed using "Shallow clone" option:

`git clone --depth=1 https://github.com/flipoyo/MOLONARI1D.git`


## Installation

Here is a step-by-step guide to install the ecosystem: 
- First install **pyheatmy**, from the **pyheatmy** folder, by running ```pip install -e .```
For more informations on the software, please check the folder.

- Second install **molonaviz**, from the **Molonaviz** folder, by running ```pip install -e .```
For more informations on the software, please check the folder.

You are now set to use the ecosystem. To launch it, you can simply run ```molonaviz``` in a terminal.

## Virtual environments for linux

### 1. **Using `pyenv` to Manage Multiple Versions of Python**

`pyenv` is a convenient tool for installing and managing multiple versions of Python on your Ubuntu system. Installing `pyenv`:

1.1. **Install the necessary dependencies:**

   ```bash
   sudo apt update
   sudo apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
   ```

1.2. **Install `pyenv`:**

   You can install `pyenv` using the official installation script:

   ```bash
   curl https://pyenv.run | bash
   ```

   Follow the on-screen instructions to add the following lines to your `~/.bashrc` file (or `~/.zshrc` if you use `zsh`):

   ```bash
   export PATH="$HOME/.pyenv/bin:$PATH"
   eval "$(pyenv init --path)"
   eval "$(pyenv init -)"
   eval "$(pyenv virtualenv-init -)"
   ```

   Reload your shell configuration file with `source ~/.bashrc` or open a new terminal.

1.3. **Install a specific version of Python:**

   ```bash
   pyenv install 3.10.12
   ```

   Replace `3.10.12` with the version of Python you want to install.

1.4. **Set the global default Python version:**

   ```bash
   pyenv global 3.10.12
   ```

   To change the Python version for a specific project, navigate to the project directory and use:

   ```bash
   pyenv local 3.10.12
   ```


### 2. **Using Virtual Environments**

To manage project-specific dependencies, you can create a virtual environment with `venv` or `virtualenv`:

```bash
python3 -m venv myenv
source myenv/bin/activate
```

Then, you can install Python packages without affecting other projects.


## Virtual environments for windows

Use anaconda, download it install it.

open the anaconda prompt terminal in windows. Install git for anaconda:

Install gitlab for conda:

```bash
> conda install -c anaconda git
```

And create a virtual environment

```bash
> conda create --name py3.11.4 -c anaconda python=3.11.4
```

Activate the virtual environment

```bash
> conda activate py3.11.4
```

Run the MOLONARI installation process from there. You can launch molonaviz from there.

For developpers, run code . from there to be sure to be in the proper environment

Deactivate the virtual environment 


```bash
> conda deactivate
```




 

