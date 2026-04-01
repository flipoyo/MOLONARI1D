# Installation & Setup

**Prerequisites:**
- [pixi](https://pixi.sh/latest/) (environment and dependency manager)
- Arduino IDE 2.x (for hardware development)
- Git with shallow clone support

**1. Clone Repository:**
```bash
git clone --depth=1 https://github.com/flipoyo/MOLONARI1D.git
cd MOLONARI1D
```

**2. Install Python Components with pixi:**

Here is a step-by-step guide to install the ecosystem: 
- Install and lock the project environment from the repository root:
```bash
pixi install
```

- Then run commands inside the environment:
```bash
pixi run python -c "import pyheatmy; print('pyheatmy ready')"
pixi run python -c "import molonaviz; print('molonaviz ready')"
```

You are now set to use the ecosystem. To launch it, run ```pixi run molonaviz``` in a terminal.

**WARNING** For less advanced users, use pixi directly instead of manually setting up Python/conda/venv.

**3. Validate Installation:**
```bash
# Test pyheatmy
pixi run python -c "import pyheatmy; print('pyheatmy ready')"

# Test Molonaviz structure (expected GUI import error in headless mode)
pixi run validate-molonaviz-structure
```

**4. Run Tests:**
```bash
# Unit tests (~5 seconds)
pixi run test-pyheatmy

# Scientific workflow validation (~85 seconds)
pixi run test-notebooks
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
pixi run molonaviz
```

**Hardware Programming:**
```bash
cd hardware/sensors/temperature/Sensor/
# Compile and upload to Arduino MKR WAN 1310
arduino-cli compile --fqbn arduino:samd:mkrwan1310 Sensor.ino
arduino-cli upload --fqbn arduino:samd:mkrwan1310 Sensor.ino --port /dev/ttyACM0
```

# Environment management

Use pixi on Linux, macOS, and Windows. The same commands are valid in all environments:

```bash
pixi install
pixi run test-pyheatmy
pixi run molonaviz
```
