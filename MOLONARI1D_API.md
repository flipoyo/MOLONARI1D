# MOLONARI1D API Documentation

*Updated December 2024 - Based on current pyheatmy v0.4.0 implementation*

## Project Overview

This documentation specifies the programming interfaces between the three main components of the MOLONARI1D environmental monitoring system: sensors, computation engine (pyheatmy), and user interface (Molonaviz).

## Table of Contents

1. [Introduction](#introduction)
2. [Installation and Import Guide](#installation-and-import-guide)
3. [Core Classes](#core-classes)
   - [Prior Class](#prior-class)
   - [Layer Class](#layer-class) 
   - [Column Class](#column-class)
4. [Data Generation and Simulation](#data-generation-and-simulation)
   - [synthetic_MOLONARI Class](#synthetic_molonari-class)
   - [Analy_Sol Class](#analy_sol-class)
5. [LoRa Communication API](#lora-communication-api)
   - [LoRaEmitter Class](#loraemitter-class)
   - [LoRaWANEmitter Class](#lorawannemitter-class)
   - [LoRaPacket Class](#lorapacket-class)
6. [Utility Functions](#utility-functions)
7. [Integration Examples](#integration-examples)
8. [Missing API Components](#missing-api-components)

## Introduction

This library defines the exchange interfaces between the three core components (sensors, computation, and GUI) to enable successful project execution. The API ensures seamless data flow from hardware sensors through scientific computation to user visualization.

## Installation and Import Guide

### Installation
```bash
cd pyheatmy/
pip install -e .
```

### Core Imports
```python
# Basic imports (recommended approach)
from pyheatmy import Column, Layer, Prior, Param
from pyheatmy import synthetic_MOLONARI

# Alternative: direct imports
from pyheatmy.core import Column
from pyheatmy.layers import Layer
from pyheatmy.params import Prior, Param
from pyheatmy.synthetic_MOLONARI import synthetic_MOLONARI

# LoRa communication
from pyheatmy import LoRaEmitter, LoRaWANEmitter, LoRaPacket

# Analysis tools
from pyheatmy import Analy_Sol
```

### Import Issues and Troubleshooting

If you encounter import issues, use direct PYTHONPATH approach:
```bash
export PYTHONPATH="/path/to/pyheatmy:$PYTHONPATH"
python -c "import pyheatmy; print('Success')"
```

## Core Classes

### Prior Class

The Prior class defines parameter constraints and behavior for MCMC inference.

#### Constructor Parameters

- **range**: `tuple` - Interval within which the parameter can vary
- **sigma**: `float` - Standard deviation of the Gaussian used for random walk for this parameter  
- **density**: `callable` - Density of the prior law. By default, this is a constant function corresponding to a uniform law

#### Usage Notes

Users typically need to define a Prior object only for MCMC with estimation of the sigma2 parameter.

#### Example

```python
from pyheatmy import Prior

# Define a prior for hydraulic conductivity
prior_K = Prior(
    range=(1e-6, 1e-3),     # Permeability range in m/s
    sigma=0.1,              # Random walk standard deviation
    density=None            # Uniform prior (default)
)
```

### Layer Class

The Layer class defines geological strata properties for stratified subsurface modeling.

#### Constructor Parameters

- **name**: `str` - Layer identifier
- **zLow**: `float` - Depth in meters of the bottom of the layer (positive, increasing downward from surface)
- **moinslog10IntrinK**: `float` - Value of -log10(K) where K is intrinsic permeability (default: 13.0)
- **n**: `float` - Porosity (dimensionless, default: 0.1)
- **lambda_s**: `float` - Solid thermal conductivity in W/m/K (default: 3.0)
- **rhos_cs**: `float` - Solid volumetric heat capacity in J/m³/K (default: 2.5e6)
- **q**: `float` - Heat source term (default: 0.0)
- **Prior_moinslog10IntrinK**: `Prior` - Prior for intrinsic permeability (optional)
- **Prior_n**: `Prior` - Prior for porosity (optional)
- **Prior_lambda_s**: `Prior` - Prior for thermal conductivity (optional)
- **Prior_rhos_cs**: `Prior` - Prior for heat capacity (optional)
- **Prior_q**: `Prior` - Prior for heat source (optional)

#### Layer Integration with Column

**Modern Approach (Recommended):**
Layers are integrated directly into the Column class as attributes, eliminating the need for separate layer management.

**Method 1: Constructor Integration**
```python
from pyheatmy import Column, Layer

# Create individual layers
surface_layer = Layer(
    name="Surface_Sediment",
    zLow=0.5,
    moinslog10IntrinK=5.0,
    n=0.3,
    lambda_s=2.5,
    rhos_cs=2.1e6
)

clay_layer = Layer(
    name="Clay_Layer", 
    zLow=1.2,
    moinslog10IntrinK=7.0,
    n=0.2,
    lambda_s=1.8,
    rhos_cs=2.3e6
)

# Pass layers directly to Column constructor
column = Column(
    river_bed=245.3,
    depth_sensors=[0.1, 0.3, 0.5, 0.7],
    offset=0.05,
    dH_measures=[...],
    T_measures=[...],
    all_layers=[surface_layer, clay_layer]  # Integrated approach
)
```

**Method 2: Using set_layers() Method**
```python
# Create column first
column = Column(
    river_bed=245.3,
    depth_sensors=[0.1, 0.3, 0.5, 0.7],
    offset=0.05,
    dH_measures=[...],
    T_measures=[...]
)

# Add layers using set_layers method
layers = [surface_layer, clay_layer]
column.set_layers(layers)  # Automatically sorts by zLow
```

#### Layer Methods

- **sample()**: Sample parameters from priors
- **perturb(param)**: Perturb parameters according to priors
- **set_priors_from_dict(priors_dict)**: Set priors from dictionary
- **from_dict(monolayer_dict)**: Create layer from dictionary (class method)

#### Layer Utility Functions

```python
def getListParameters(layersList, nbCells: int):
    """Extract parameter arrays for all layers"""
```

#### Example: Complete Layer Definition

```python
from pyheatmy import Column, Layer, Prior

# Create layers with priors for MCMC
surface_layer = Layer(
    name="Surface_Sediment",
    zLow=0.5,
    moinslog10IntrinK=5.0,
    n=0.3,
    lambda_s=2.5,
    rhos_cs=2.1e6,
    Prior_moinslog10IntrinK=Prior(range=(3, 8), sigma=0.1),
    Prior_n=Prior(range=(0.1, 0.5), sigma=0.02),
    Prior_lambda_s=Prior(range=(1, 4), sigma=0.1)
)

clay_layer = Layer(
    name="Clay_Layer",
    zLow=1.2, 
    moinslog10IntrinK=7.0,
    n=0.2,
    lambda_s=1.8,
    rhos_cs=2.3e6,
    Prior_moinslog10IntrinK=Prior(range=(5, 10), sigma=0.1),
    Prior_n=Prior(range=(0.05, 0.3), sigma=0.02),
    Prior_lambda_s=Prior(range=(1, 3), sigma=0.1)
)

# Create column with integrated layers
column = Column(
    river_bed=245.3,
    depth_sensors=[0.1, 0.3, 0.5, 0.7],
    offset=0.05,
    dH_measures=[...],
    T_measures=[...],
    all_layers=[surface_layer, clay_layer]
)

# Layers are now accessible via column.all_layers
print(f"Number of layers: {len(column.all_layers)}")
for layer in column.all_layers:
    print(f"Layer {layer.name} extends to {layer.zLow}m depth")
```

### Column Class

The Column class is the primary interface for hydrological analysis, representing a monitoring point with sensors. It contains 59 methods for data processing, modeling, and visualization.

#### Constructor Parameters

- **river_bed**: `float` - River bed elevation in meters  
- **depth_sensors**: `Sequence[float]` - List of sensor depths on the rod (typically 4 sensors), in meters
- **offset**: `float` - Excess rod penetration in meters (if rod is 10cm too deep, offset = 0.1)
- **dH_measures**: `list` - List of tuples containing (datetime, pressure, temperature) at column top
- **T_measures**: `list` - List of tuples containing (datetime, temperatures) at measurement points
- **sigma_meas_P**: `float` - Pressure measurement error (optional)
- **sigma_meas_T**: `float` - Temperature measurement error (optional) 
- **all_layers**: `list[Layer]` - List of geological layers (default: empty)
- **inter_mode**: `str` - Interpolation mode: 'lagrange' or 'linear' (default: 'linear')
- **eps**: `float` - Numerical epsilon (default: from config)
- **heat_source**: `np.ndarray` - Heat source term (optional)
- **nb_cells**: `int` - Number of spatial cells (default: from config)
- **rac**: `str` - Output directory path (default: "~/OUTPUT_MOLONARI1D/generated_data")
- **verbose**: `bool` - Enable verbose output (default: False)

#### Class Method: from_dict

Creates a Column object from a dictionary containing measurement data and configuration.

```python
@classmethod
def from_dict(cls, col_dict, verbose=False):
    """Create Column instance from dictionary"""
```

#### Core Computation Methods

**Direct Modeling**
- **compute_solve_transi(verbose=True)**: Solve heat and flow equations
- **tests()**: Validate data formats and completeness
- **initialization(nb_cells)**: Initialize computational grid
- **set_layers(layer)**: Set geological layers for modeling

**MCMC Inference**
- **compute_mcmc(...)**: Run Markov Chain Monte Carlo parameter estimation
- **perturbation_DREAM(...)**: DREAM algorithm perturbation
- **sample_param()**: Sample parameters from priors
- **sample_params_from_priors()**: Sample all parameters from prior distributions

#### Data Retrieval Methods

**Time and Space Coordinates**
- **get_depths_solve()**: Get depth coordinates for solutions
- **get_depths_mcmc()**: Get depth coordinates for MCMC results  
- **get_times_solve()**: Get time coordinates for solutions
- **get_times_mcmc()**: Get time coordinates for MCMC results
- **get_timelength()**: Get total time span
- **get_dt()**: Get time step in seconds
- **get_dt_in_days()**: Get time step in days

**Temperature Results**
- **get_temperatures_solve(z=None)**: Get computed temperature profiles
- **get_temperature_at_sensors(zero=0, verbose=False)**: Get temperatures at sensor locations
- **get_temperatures_quantile(quantile)**: Get temperature quantiles from MCMC

**Flow Results**  
- **get_flows_solve(z=None)**: Get total water flux estimates
- **get_advec_flows_solve()**: Get advective flow component
- **get_conduc_flows_solve()**: Get conductive flow component
- **get_flows_quantile(quantile)**: Get flow quantiles from MCMC

**Parameter Results**
- **get_best_param()**: Get optimal parameter estimates
- **get_best_sigma2()**: Get optimal measurement error variance
- **get_best_layers()**: Get optimal layer parameters
- **get_all_params()**: Get all MCMC parameter samples
- **get_all_moinslog10IntrinK()**: Get all permeability samples
- **get_all_n()**: Get all porosity samples
- **get_all_lambda_s()**: Get all thermal conductivity samples
- **get_all_rhos_cs()**: Get all heat capacity samples
- **get_all_q()**: Get all heat source samples
- **get_all_sigma2()**: Get all measurement error variance samples
- **get_all_energy()**: Get all energy values from MCMC
- **get_all_acceptance_ratio()**: Get MCMC acceptance ratios

**Model Performance**
- **get_RMSE()**: Get root mean square error for model fit
- **get_RMSE_quantile(quantile)**: Get RMSE quantiles
- **print_RMSE_at_sensor()**: Print RMSE at each sensor location
- **get_quantiles()**: Get available quantile values
- **get_id_sensors()**: Get sensor identifiers

#### Visualization Methods

**Temperature Plots**
- **plot_temperature_at_sensors(...)**: Plot temperature time series at sensors
- **plot_compare_temperatures_sensors(...)**: Compare measured vs computed temperatures
- **plot_quantile_temperatures_sensors(...)**: Plot temperature quantiles
- **plot_temperatures_umbrella(...)**: Plot temperature profiles as umbrella plot
- **plot_it_Zt(...)**: Interactive temperature-depth-time plot

**Results and Analysis Plots**
- **plot_CALC_results(fontsize=15)**: Plot calculation results summary
- **plot_all_results()**: Plot comprehensive results
- **plot_all_param_pdf()**: Plot parameter probability distributions
- **plot_darcy_flow_quantile()**: Plot Darcy velocity quantiles

#### Data Export Methods

- **print_sensor_file(fp, senType, senName)**: Export sensor configuration files
- **print_sampling_point_info(...)**: Export sampling point metadata
- **print_in_file_processed_MOLONARI_dataset(...)**: Export processed dataset

#### Utility Methods

- **create_time_in_day()**: Convert time to day units
- **set_zeroT(tunits="K")**: Set temperature reference point
- **get_list_current_params()**: Get current parameter state
- **perturb_params()**: Perturb current parameters

#### Data Format Specifications

##### Temperature Measurements (T_measures)
Each tuple contains: `(datetime, T1, T2, T3, T4)`
- **datetime**: Measurement timestamp
- **T1, T2, T3, T4**: Temperatures at the four sensor depths

##### Pressure Measurements (dH_measures)  
Each tuple contains: `(datetime, pressure, surface_temperature)`
- **datetime**: Measurement timestamp
- **pressure**: Hydraulic head measurement
- **surface_temperature**: Reference temperature

#### Example

```python
from pyheatmy import Column, Layer
from datetime import datetime

# Create layers first
surface_layer = Layer(
    name="Surface_Sediment",
    zLow=0.5,
    moinslog10IntrinK=5.0,
    n=0.3,
    lambda_s=2.5,
    rhos_cs=2.1e6
)

clay_layer = Layer(
    name="Clay_Layer",
    zLow=1.2,
    moinslog10IntrinK=7.0,
    n=0.2,
    lambda_s=1.8,
    rhos_cs=2.3e6
)

# Prepare measurement data
column_data = {
    'river_bed': 245.3,
    'depth_sensors': [0.1, 0.3, 0.5, 0.7],  # 4 sensors at different depths
    'offset': 0.05,  # 5cm extra penetration
    'sigma_meas_P': 0.01,
    'sigma_meas_T': 0.1,
    'all_layers': [surface_layer, clay_layer],  # Integrated layers
    'dH_measures': [
        (datetime(2023, 6, 1, 0, 0), (1.25, 15.2)),
        (datetime(2023, 6, 1, 1, 0), (1.23, 15.4)),
        # ... more measurements
    ],
    'T_measures': [
        (datetime(2023, 6, 1, 0, 0), (12.1, 11.8, 11.5, 11.2, 11.0)),
        (datetime(2023, 6, 1, 1, 0), (12.3, 12.0, 11.7, 11.4, 11.1)),
        # ... more measurements
    ]
}

# Create Column object with integrated layers
column = Column.from_dict(column_data)

# Alternative: Add layers after creation
# column = Column.from_dict({...})  # without all_layers
# column.set_layers([surface_layer, clay_layer])

# Run direct model (layers automatically used)
column.compute_solve_transi()

# Get results
temperatures = column.get_temperatures_solve()
flows = column.get_flows_solve()
rmse = column.get_RMSE()
```

## Data Generation and Simulation

### synthetic_MOLONARI Class

The synthetic_MOLONARI class generates synthetic sensor data for testing and validation purposes.

#### Constructor Parameters

- **offset**: `float` - Sensor offset (default: from config)
- **depth_sensors**: `list` - List of sensor depths (default: from config)
- **param_time_dates**: `list` - Time series parameters [start_date, end_date, time_step]
- **param_dH_signal**: `list` - Pressure signal parameters for step change
- **param_T_riv_signal**: `list` - River temperature signal [amplitude, period, offset]
- **param_T_aq_signal**: `list` - Aquifer temperature signal [amplitude, period, offset]
- **sigma_meas_P**: `float` - Pressure measurement noise (m)
- **sigma_meas_T**: `float` - Temperature measurement noise (°C)
- **verbose**: `bool` - Enable verbose output (default: True)

#### Key Methods

- **from_dict(time_series_dict)**: Create instance from dictionary (class method)
- **_generate_all_series()**: Generate all time series data
- **_set_Shaft_Temp_series(temperatures, id_sensors)**: Set shaft temperature data
- **_perturbate(ts, sigma)**: Add noise to time series
- **_plot_molonariT_data()**: Plot temperature data
- **_measures_column_one_layer(column, verbose=False)**: Generate measurements for single-layer column

#### Example

```python
from pyheatmy import synthetic_MOLONARI
from datetime import datetime

# Create synthetic data generator
synth = synthetic_MOLONARI(
    offset=0.05,
    depth_sensors=[0.1, 0.3, 0.5, 0.7],
    param_time_dates=[
        datetime(2023, 6, 1),
        datetime(2023, 6, 30), 
        3600  # 1 hour time step
    ],
    param_T_riv_signal=[5.0, 86400, 15.0],  # 5°C amplitude, daily period, 15°C offset
    sigma_meas_T=0.1,
    verbose=True
)

# Generate data for use with Column
molonari_data = synth._molonariT_data
pressure_data = synth._molonariP_data
```

### Analy_Sol Class  

The Analy_Sol class provides analytical solutions for validation and benchmarking.

#### Key Methods

- **compute_solve_transi_one_layer(...)**: Analytical solution for single layer
- **get_depths_solve()**: Get depth coordinates
- **get_times_solve()**: Get time coordinates  
- **get_temperatures_solve()**: Get analytical temperature solution
- **get_flows_solve()**: Get analytical flow solution

#### Example

```python
from pyheatmy import Analy_Sol

# Create analytical solution
analy = Analy_Sol(
    river_bed=1.0,
    depth_sensors=[0.1, 0.3, 0.5],
    # ... other parameters
)

# Compute analytical solution
analy.compute_solve_transi_one_layer(layer, nb_cells=100)

# Get results for comparison
analytical_temps = analy.get_temperatures_solve()
analytical_flows = analy.get_flows_solve()
```

## LoRa Communication API

### LoRaEmitter Class

Simulates LoRa device behavior for sensor data transmission.

#### Constructor Parameters

- **device_address**: `int` - Unique device address (0-255)
- **spreading_factor**: `LoRaSpreadingFactor` - LoRa spreading factor (affects range vs data rate)
- **frequency**: `LoRaFrequency` - Transmission frequency band  
- **power**: `int` - Transmission power in dBm (2-20, default: 14)
- **max_payload_size**: `int` - Maximum payload size in bytes (default: 200)
- **max_retries**: `int` - Maximum retry attempts (default: 6)
- **retry_delay_base**: `float` - Base delay for exponential backoff (default: 1.0s)
- **verbose**: `bool` - Enable verbose logging (default: False)

#### Key Methods

- **load_sensor_data(csv_file_path)**: Load sensor data from CSV
- **create_packet(payload, destination=0)**: Create LoRa packet
- **transmit_packet(packet)**: Simulate packet transmission
- **simulate_transmission_schedule()**: Run scheduled transmission simulation
- **get_transmission_statistics()**: Get transmission success statistics
- **calculate_battery_usage()**: Estimate battery consumption
- **export_transmission_log(output_file)**: Export transmission log

#### Enums and Constants

```python
class LoRaSpreadingFactor(Enum):
    SF7 = 7   # Fastest data rate, shortest range
    SF8 = 8
    SF9 = 9  
    SF10 = 10
    SF11 = 11
    SF12 = 12  # Slowest data rate, longest range

class LoRaFrequency(Enum):
    EU868 = 868.1e6    # European frequency band
    US915 = 915.0e6    # US frequency band  
    AS923 = 923.0e6    # Asian frequency band
```

#### Example

```python
from pyheatmy import LoRaEmitter, LoRaSpreadingFactor, LoRaFrequency

# Create LoRa emitter for temperature sensor
sensor = LoRaEmitter(
    device_address=42,
    spreading_factor=LoRaSpreadingFactor.SF7,
    frequency=LoRaFrequency.EU868,
    power=14,
    verbose=True
)

# Load sensor data from CSV file
sensor.load_sensor_data("sensor_data.csv")

# Simulate transmission schedule (daily transmission at 23:45)
sensor.simulate_transmission_schedule()

# Get statistics
stats = sensor.get_transmission_statistics()
battery_usage = sensor.calculate_battery_usage()
```

### LoRaWANEmitter Class

Extends LoRaEmitter for LoRaWAN network connectivity.

#### Additional Methods

- **join_network()**: Perform LoRaWAN network join
- **send_uplink(payload)**: Send LoRaWAN uplink message
- **handle_downlink()**: Process LoRaWAN downlink messages
- **configure_network_session()**: Set up network session parameters

### LoRaPacket Class

Represents LoRa packet structure used in MOLONARI1D.

#### Attributes

- **checksum**: `int` - Packet integrity checksum
- **destination**: `int` - Destination device address
- **local_address**: `int` - Source device address  
- **packet_number**: `int` - Sequential packet number
- **request_type**: `int` - Request type identifier
- **payload**: `str` - Actual data payload
- **timestamp**: `datetime` - Packet creation timestamp

#### Methods

- **calculate_checksum()**: Calculate packet checksum
- **to_bytes()**: Convert packet to byte representation
- **get_size()**: Get packet size in bytes

## Utility Functions

### Layer Utilities

```python
# Extract parameter arrays for all layers (internal utility)
getListParameters(layersList, nbCells)

# Note: Layer creation and sorting is now handled automatically 
# by the Column class through all_layers parameter and set_layers() method
```

### Time Series Utilities

```python
# Period conversion
convert_period_in_second(period, unit)

# Signal generation
create_periodic_signal(dates, amplitude, period, offset)

# Timestamp conversion
convert_to_timestamp(ts, tbt)
convert_list_to_timestamp(ts, tbt)
```

### File Management

```python
# Directory creation
create_dir(rac, verbose=True)

# File operations
open_printable_file(...)
close_printable_file(fp, verbose=True)
```

## Integration Examples

### Complete Workflow Example

```python
from pyheatmy import Column, Layer, Prior, synthetic_MOLONARI
from datetime import datetime

# 1. Option A: Use synthetic data for testing
synth = synthetic_MOLONARI(
    param_time_dates=[datetime(2023, 6, 1), datetime(2023, 6, 30), 3600],
    param_T_riv_signal=[5.0, 86400, 15.0],
    sigma_meas_T=0.1
)

# 2. Option B: Use real sensor data
column_data = {
    'river_bed': 245.0,
    'depth_sensors': [0.1, 0.3, 0.5, 0.7],
    'offset': 0.0,
    'sigma_meas_P': 0.01, 
    'sigma_meas_T': 0.1,
    'dH_measures': [...],  # From sensor database or synthetic
    'T_measures': [...]    # From sensor database or synthetic  
}

# 3. Create column object
column = Column.from_dict(column_data)

# 4. Define geological layers (modern approach)
surface_layer = Layer(
    name="surface",
    zLow=0.3,
    moinslog10IntrinK=5.0,
    n=0.35,
    lambda_s=2.5,
    rhos_cs=2.1e6
)

clay_layer = Layer(
    name="clay", 
    zLow=1.0,
    moinslog10IntrinK=7.0,
    n=0.25,
    lambda_s=1.8,
    rhos_cs=2.3e6
)

layers = [surface_layer, clay_layer]

# 5. Run direct model
column.compute_solve_transi()

# 6. Get direct model results
temperatures = column.get_temperatures_solve()
flows = column.get_flows_solve()
rmse = column.get_RMSE()

# 7. Set up MCMC inference with priors
for layer in layers:
    layer.set_priors_from_dict({
        'Prior_moinslog10IntrinK': ((3, 8), 0.1),
        'Prior_n': ((0.1, 0.5), 0.02),
        'Prior_lambda_s': ((1, 4), 0.1),
        'Prior_rhos_cs': ((1e6, 1e7), 1e5),
        'Prior_q': ((0, 1), 1e2)
    })

# 8. Run MCMC inference
column.compute_mcmc(
    layersList=layers,
    nb_iter=10000,
    nb_chains=4,
    sigma2_T=Prior(range=(0.01, 10), sigma=0.1)
)

# 9. Get MCMC results
best_params = column.get_best_param()
all_params = column.get_all_params()
temp_quantiles = column.get_temperatures_quantile(0.5)  # Median
flow_quantiles = column.get_flows_quantile(0.95)        # 95% quantile

# 10. Visualization
column.plot_all_results()
column.plot_all_param_pdf()
column.plot_darcy_flow_quantile()
```

### LoRa Communication Simulation Example

```python
from pyheatmy import LoRaEmitter, LoRaSpreadingFactor, LoRaFrequency
import pandas as pd
from datetime import datetime, timedelta

# 1. Create sensor data
dates = [datetime(2023, 6, 1) + timedelta(minutes=15*i) for i in range(2880)]
temperatures = [20 + 5*np.sin(2*np.pi*i/96) for i in range(len(dates))]
pressures = [1.2 + 0.1*np.random.normal() for i in range(len(dates))]

sensor_data = pd.DataFrame({
    'timestamp': dates,
    'temperature': temperatures, 
    'pressure': pressures,
    'battery_voltage': [3.8] * len(dates)
})
sensor_data.to_csv('sensor_001_data.csv', index=False)

# 2. Create LoRa emitter for the sensor
sensor = LoRaEmitter(
    device_address=1,
    spreading_factor=LoRaSpreadingFactor.SF7,
    frequency=LoRaFrequency.EU868,
    max_retries=6,
    verbose=True
)

# 3. Load data and simulate transmission
sensor.load_sensor_data('sensor_001_data.csv')
sensor.simulate_transmission_schedule()

# 4. Analyze transmission performance
stats = sensor.get_transmission_statistics()
battery_life = sensor.calculate_battery_usage()

print(f"Transmission success rate: {stats['success_rate']:.2%}")
print(f"Estimated battery life: {battery_life:.1f} days")
```

### Data Quality Control Example

```python
from pyheatmy import Column, Layer
import numpy as np

def validate_sensor_data(dH_measures, T_measures):
    """Validate sensor data quality before processing"""
    
    # Check temporal consistency
    dH_times = [t for t, _ in dH_measures]
    T_times = [t for t, _ in T_measures]
    
    if len(dH_times) != len(T_times):
        raise ValueError("Pressure and temperature measurements must have same length")
    
    # Check for missing data
    for i, (dH_time, T_time) in enumerate(zip(dH_times, T_times)):
        if dH_time != T_time:
            raise ValueError(f"Timestamp mismatch at index {i}")
    
    # Check measurement ranges
    pressures = [p for _, (p, _) in dH_measures]
    temperatures = [t for _, temps in T_measures for t in temps[:-1]]  # Exclude aquifer T
    
    if any(p < 0 or p > 10 for p in pressures):
        raise ValueError("Pressure values outside valid range (0-10 m)")
    
    if any(t < -5 or t > 50 for t in temperatures):
        raise ValueError("Temperature values outside valid range (-5 to 50°C)")
    
    print("Data validation passed")
    return True

# Example usage with validation
try:
    validate_sensor_data(dH_measures, T_measures)
    column = Column.from_dict(column_data)
    column.compute_solve_transi()
except ValueError as e:
    print(f"Data validation failed: {e}")
```

## Missing API Components

### Issues Identified and Resolved

#### ✅ Updated Layer Integration Architecture  
- **Previous**: Deprecated `layersListCreator` function for separate layer management
- **Current**: Layers integrated directly into Column class via `all_layers` parameter and `set_layers()` method
- **Benefit**: Simplified workflow with automatic layer sorting and integrated management

#### ✅ Added Missing Classes Documentation  
- **synthetic_MOLONARI**: Data generation for testing and validation
- **LoRaEmitter/LoRaWANEmitter**: Hardware communication simulation
- **Analy_Sol**: Analytical solutions for benchmarking
- **Layer utilities**: `getListParameters` for internal parameter extraction

#### ✅ Comprehensive Column Class Methods
- **Problem**: Only 4 methods documented vs 59 available methods
- **Solution**: Complete documentation of all Column class methods organized by category:
  - Core computation (5 methods)
  - Data retrieval (20 methods) 
  - Visualization (8 methods)
  - Data export (3 methods)
  - Utilities (4 methods)

### Remaining API Gaps

#### 🔄 Partial Documentation
These components exist but need enhanced documentation:

1. **Linear System Classes**
   - `Linear_system`, `H_stratified`, `T_stratified`, `HTK_stratified`
   - Advanced users may need access to these for custom modeling

2. **State Management**
   - `State` class for MCMC state management
   - Useful for advanced MCMC customization

3. **Checker System**
   - `@checker` decorator for computation order validation
   - `ComputationOrderException` for error handling

4. **Configuration Constants**
   - Extensive configuration parameters in `config.py`
   - Default values, physical constants, device types

#### 📋 Recommended API Extensions

1. **Simplified High-Level Interface**
   ```python
   # Proposed simplified interface
   from pyheatmy import quick_analysis
   
   results = quick_analysis(
       sensor_data_file="site_01.csv",
       geology_layers=["sand", "clay"],
       run_mcmc=True
   )
   ```

2. **Batch Processing Interface**
   ```python
   # Proposed batch processing
   from pyheatmy import batch_process_sites
   
   results = batch_process_sites(
       sites_directory="field_data/",
       output_directory="analysis_results/",
       parallel=True
   )
   ```

3. **Real-time Data Interface**
   ```python
   # Proposed real-time analysis
   from pyheatmy import RealTimeAnalyzer
   
   analyzer = RealTimeAnalyzer()
   analyzer.connect_to_database(connection_string)
   analyzer.start_monitoring(site_id="SITE_001")
   ```

### Hardware Integration Gaps

#### 🔧 Arduino Firmware Interface
- **Missing**: Direct Python interface to Arduino firmware
- **Current**: Manual file transfer from SD cards
- **Needed**: USB/WiFi communication with sensors

#### 📡 LoRaWAN Gateway Interface  
- **Missing**: Direct integration with LoRaWAN network servers
- **Current**: Simulated LoRa communication only
- **Needed**: Real network connectivity for field deployments

#### 🌐 Molonaviz Integration
- **Missing**: Programmatic interface to Molonaviz database
- **Current**: GUI-only access to device management
- **Needed**: API for automated data ingestion and device control

### Testing and Validation Infrastructure

#### ✅ Available Testing
- Unit tests for individual components
- Notebook-based workflow validation
- Synthetic data generation for testing

#### 📋 Testing Gaps
- **Hardware-in-loop testing**: Integration with real sensors
- **Performance benchmarks**: Scalability testing for large datasets
- **Robustness testing**: Error handling and edge cases
- **Cross-platform validation**: Windows/Mac/Linux compatibility

## Error Handling and Troubleshooting

### Common Import Issues

```python
# Issue: ImportError when importing pyheatmy classes
# Solution: Use direct imports or PYTHONPATH
try:
    from pyheatmy import Column, Layer, Prior
except ImportError:
    # Fallback to direct imports
    from pyheatmy.core import Column
    from pyheatmy.layers import Layer
    from pyheatmy.params import Prior

# Issue: Architecture changes for layer management
# Old deprecated approach: layersListCreator function
# New approach: integrated layers in Column class
from pyheatmy import Column, Layer

# Create layers individually and integrate them
surface_layer = Layer("surface", 0.5, 5.0, 0.3, 2.5, 2.1e6)
column = Column(..., all_layers=[surface_layer])

# Issue: Network timeouts during pip install
# Solution: Use timeout parameter
# pip install --timeout 300 -e pyheatmy/
```

### Data Format Issues

```python
# Issue: Incorrect data tuple format
# Problem: dH_measures = [(date, pressure, temperature), ...]
# Correct: dH_measures = [(date, (pressure, temperature)), ...]

# Issue: Missing aquifer temperature in T_measures
# Problem: T_measures = [(date, T1, T2, T3, T4), ...]  
# Correct: T_measures = [(date, (T1, T2, T3, T4, T_aq)), ...]
```

### Memory and Performance Issues

```python
# Issue: Memory usage for large datasets
# Solution: Use chunked processing or reduce nb_cells
column.initialization_nb_cells(50)  # Reduce from default 100

# Issue: Slow MCMC convergence
# Solution: Adjust priors and iteration counts
# Use wider priors for faster mixing
# Increase nb_iter if convergence diagnostics indicate issues
```

## Performance Considerations

- **Data Size**: Optimized for typical monitoring campaigns (months to years)
- **Computation Time**: MCMC inference scales with iteration count and data size
- **Memory Usage**: Efficient storage of large measurement datasets
- **Parallel Processing**: Multi-core MCMC execution supported

## Version Compatibility

This API specification is compatible with:
- **pyheatmy**: Version 0.4.0+
- **Molonaviz**: Version 2.0+
- **Python**: 3.9+
- **NumPy**: 1.20+
- **SciPy**: 1.7+
- **Matplotlib**: 3.3+

## Support and Documentation

For additional support:
- [pyheatmy Documentation](../pyheatmy/README.md)
- [Molonaviz User Guide](../Molonaviz/README.md) 
- [Hardware Integration Guide](../Device/README.md)
- [Example Notebooks](../pyheatmy/demo*.ipynb)
- [GitHub Issues](https://github.com/flipoyo/MOLONARI1D/issues)