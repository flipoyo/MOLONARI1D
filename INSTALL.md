# Installation & Setup

**Prerequisites:**
- Python 3.10+ (for Molonaviz) or 3.9+ (for pyheatmy only)
- Arduino IDE 2.x (for hardware development)
- Git with shallow clone support

**1. Clone Repository:**
```bash
git clone --depth=1 https://github.com/flipoyo/MOLONARI1D.git
cd MOLONARI1D
```

**2. Install Python Components:**

Here is a step-by-step guide to install the ecosystem: 
- First install **pyheatmy**, from the **pyheatmy** folder, by running ```pip install -e .```
For more informations on the software, please check the folder.

- Second install **molonaviz**, from the **Molonaviz** folder, by running ```pip install -e .```
For more informations on the software, please check the folder.

You are now set to use the ecosystem. To launch it, you can simply run ```molonaviz``` in a terminal.

**WARNING** For less advanced users, please refer to the end of the section to set-up your environment to at least `python3.10+`

**3. Validate Installation:**
```bash
# Test pyheatmy
python -c "import pyheatmy; print('pyheatmy ready')"

# Test Molonaviz structure (expected GUI import error in headless mode)
cd Molonaviz/src/
export PYTHONPATH="$PWD:$PYTHONPATH"
python -c "import molonaviz; print('Molonaviz structure validated')"
```

**4. Run Tests:**
```bash
# Unit tests (~5 seconds)
cd ../../
pytest pyheatmy/ Molonaviz/

# Scientific workflow validation (~85 seconds)
cd pyheatmy/
pytest --nbmake --nbmake-timeout=600 demoPyheatmy.ipynb demo_genData.ipynb
```

## Usage Examples

**Scientific Analysis with pyheatmy:**
```python
import pyheatmy

# Load sensor data and run MCMC inference
column = pyheatmy.Column.from_sensor_data('site_data.csv')
results = column.run_inference(n_iterations=10000)

# Extract flux estimates with uncertainty
water_flux = results.get_parameter_distribution('darcy_velocity')
```

**Device Management with Molonaviz:**
```bash
# Launch GUI (requires X11/display)
cd Molonaviz/src/
python -m molonaviz.main
```

**Hardware Programming:**
```bash
cd hardware/sensors/temperature/Sensor/
# Compile and upload to Arduino MKR WAN 1310
arduino-cli compile --fqbn arduino:samd:mkrwan1310 Sensor.ino
arduino-cli upload --fqbn arduino:samd:mkrwan1310 Sensor.ino --port /dev/ttyACM0
```

# Virtual environments

## For `Linux`

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


## For `Windows`

Download it install anaconda. (https://www.anaconda.com/download)

Open the anaconda prompt terminal in windows. Install git for anaconda:

Install gitlab for conda:

```bash
> conda install -c anaconda git
```

Create a virtual environment and activate it:

```bash
> conda create --name py3.11.4 -c anaconda python=3.11.4
> conda activate py3.11.4
```

Run the MOLONARI installation process from there. You can launch molonaviz from there.

You can deactivate the virtual environment with the following command:

```bash
> conda deactivate
```

## For `macOS`

Once ``conda`` is installed, run:

```bash
> conda create -n molonari python=3.12
> conda activate molonari
> cd ../chemin/pyheatmy
> pip install -e .
```