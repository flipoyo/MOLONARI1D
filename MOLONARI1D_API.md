# MOLONARI1D API Documentation

*Translated and adapted from the original French API specification (2022)*

## Project Overview

This documentation specifies the programming interfaces between the three main components of the MOLONARI1D environmental monitoring system: sensors, computation engine (pyheatmy), and user interface (Molonaviz).

## Table of Contents

1. [Introduction](#introduction)
2. [GUI to Computation Interface](#gui-to-computation-interface)
3. [Core Classes](#core-classes)
   - [Prior Class](#prior-class)
   - [Layer Class](#layer-class) 
   - [Column Class](#column-class)
4. [Computation to GUI Interface](#computation-to-gui-interface)
5. [Sensors to Computation Interface](#sensors-to-computation-interface)

## Introduction

This library defines the exchange interfaces between the three core components (sensors, computation, and GUI) to enable successful project execution. The API ensures seamless data flow from hardware sensors through scientific computation to user visualization.

## GUI to Computation Interface

This section describes the information that the GUI (Molonaviz) must send to the computation engine (pyheatmy) to define objects and use the main calculation methods.

The main objects that the GUI needs to define are:

### Core Object Types

1. **Column Class Instances**: The main class that groups pressure and temperature measurements from a monitoring point. It enables execution of direct models and MCMC inference. After calculations, it contains useful information that can be retrieved using methods described in subsequent sections.

2. **Layer Class Instances**: Used to define geological strata in the medium. This class is utilized by the stratified model for complex subsurface modeling.

3. **Prior Class Instances**: Used in MCMC context to define useful information for parameters: variation intervals (range), standard deviation of random walk for the parameter (sigma), and density function when the prior distribution is not uniform.

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

- **name**: `string` - Layer identifier
- **zLow**: `float` - Depth in meters of the bottom of the layer (positive, increasing downward from surface)
- **moinslog10K**: `float` - Value of -log10(K) where K is permeability
- **n**: `float` - Porosity (dimensionless)
- **lambda_s**: `float` - Solid thermal conductivity (W/m/K)
- **rhos_cs**: `float` - Solid volumetric heat capacity (J/m³/K)

#### Layer Creation Function

The GUI creates Layer objects using the `layersListCreator` function rather than direct instantiation.

```python
def layersListCreator(layersListInput):
    """
    Create a list of Layer objects from input parameters.
    
    Parameters:
    layersListInput: list of tuples, each containing six arguments for Layer definition
    
    Returns:
    list of Layer objects
    """
```

#### Example

```python
from pyheatmy import layersListCreator

# Define geological layers
layers_input = [
    ("Surface_Sediment", 0.5, 5.0, 0.3, 2.5, 2.1e6),
    ("Clay_Layer", 1.2, 7.0, 0.2, 1.8, 2.3e6),
    ("Sand_Layer", 2.0, 4.0, 0.4, 3.2, 2.0e6)
]

layers = layersListCreator(layers_input)
```

### Column Class

The Column class is the primary interface for hydrological analysis, representing a monitoring point with sensors.

#### Class Method: from_dict

Creates a Column object from a dictionary containing measurement data and configuration.

#### Required Dictionary Keys

- **river_bed**: `float` - River bed elevation in meters (currently unused)
- **depth_sensors**: `Sequence[float]` - List of sensor depths on the rod (4 sensors), in meters
- **offset**: `float` - Excess rod penetration in meters (if rod is 10cm too deep, offset = 0.1)
- **dH_measures**: `list` - List of tuples containing (date, pressure, temperature) at column top
- **T_measures**: `list` - List of tuples containing (date, temperatures) at measurement points
- **sigma_meas_P**: `float` - Pressure measurement error (currently unused)
- **sigma_meas_T**: `float` - Temperature measurement error (currently unused)
- **dt**: `float` - Time step for calculations in seconds
- **dz**: `float` - Spatial step for calculations in meters

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
from pyheatmy import Column
from datetime import datetime

# Prepare measurement data
column_data = {
    'river_bed': 245.3,
    'depth_sensors': [0.1, 0.3, 0.5, 0.7],  # 4 sensors at different depths
    'offset': 0.05,  # 5cm extra penetration
    'dt': 3600,      # 1 hour time step
    'dz': 0.01,      # 1cm spatial step
    'sigma_meas_P': 0.01,
    'sigma_meas_T': 0.1,
    'dH_measures': [
        (datetime(2023, 6, 1, 0, 0), 1.25, 15.2),
        (datetime(2023, 6, 1, 1, 0), 1.23, 15.4),
        # ... more measurements
    ],
    'T_measures': [
        (datetime(2023, 6, 1, 0, 0), 12.1, 11.8, 11.5, 11.2),
        (datetime(2023, 6, 1, 1, 0), 12.3, 12.0, 11.7, 11.4),
        # ... more measurements
    ]
}

# Create Column object
column = Column.from_dict(column_data)
```

## Computation to GUI Interface

This section describes the methods available to retrieve calculation results from Column objects.

### Available Methods

#### Direct Model Results

- **get_temperatures()**: Returns computed temperature profiles
- **get_flows()**: Returns water flux estimates
- **get_depths()**: Returns depth coordinates for results

#### MCMC Results

- **get_best_params()**: Returns optimal parameter estimates
- **get_confidence_intervals()**: Returns parameter uncertainty bounds  
- **get_chain()**: Returns full MCMC sample chain
- **compute_quantiles()**: Returns result quantiles

#### Model Performance

- **get_RMS_meas()**: Returns root mean square error for measurements
- **get_RMSE()**: Returns root mean square error for model fit
- **assess_conv_with_Rhat()**: Returns convergence diagnostics

#### Visualization Support

- **plot_temperatures()**: Generate temperature profile plots
- **plot_flows()**: Generate water flux plots  
- **plot_MCMC_chain()**: Generate MCMC diagnostic plots

## Sensors to Computation Interface

This section describes the data flow from hardware sensors to the computation engine.

### Data Collection Pipeline

1. **Sensor Hardware**: Arduino-based temperature and pressure sensors
2. **LoRa Communication**: Wireless data transmission to relay stations
3. **Data Aggregation**: Relay stations collect and forward data
4. **Database Storage**: Molonaviz manages data quality and storage
5. **Computation Input**: Formatted data passed to pyheatmy

### Data Formats

#### Raw Sensor Data

```csv
timestamp,sensor_id,temperature,pressure,battery_voltage
2023-06-01T00:00:00Z,SENSOR_001,12.34,1.25,3.8
2023-06-01T00:15:00Z,SENSOR_001,12.35,1.24,3.8
```

#### Processed Data for Computation

The raw sensor data is processed into the dictionary format required by Column.from_dict(), handling:

- Timestamp synchronization across sensors
- Data quality validation and filtering
- Unit conversions and calibration corrections
- Gap filling and interpolation for missing data

### Quality Control

- **Range Validation**: Ensure measurements within physically reasonable bounds
- **Temporal Consistency**: Check for appropriate measurement intervals
- **Cross-Validation**: Compare co-located sensors for consistency
- **Error Flagging**: Mark suspect data for manual review

## Integration Examples

### Complete Workflow Example

```python
from pyheatmy import Column, layersListCreator, Prior
from datetime import datetime

# 1. Define geological layers
layers_input = [
    ("surface", 0.3, 5.0, 0.35, 2.5, 2.1e6),
    ("clay", 1.0, 7.0, 0.25, 1.8, 2.3e6)
]
layers = layersListCreator(layers_input)

# 2. Create column with sensor data
column_data = {
    'river_bed': 245.0,
    'depth_sensors': [0.1, 0.3, 0.5, 0.7],
    'offset': 0.0,
    'dt': 3600, 'dz': 0.01,
    'sigma_meas_P': 0.01, 'sigma_meas_T': 0.1,
    'dH_measures': [...],  # From sensor database
    'T_measures': [...]    # From sensor database  
}
column = Column.from_dict(column_data)

# 3. Run direct model
column.compute_solve_transi(layers)

# 4. Set up MCMC inference
priors = {
    'moinslog10K': Prior(range=(3, 8), sigma=0.1),
    'n': Prior(range=(0.1, 0.5), sigma=0.02),
    'lambda_s': Prior(range=(1, 4), sigma=0.1)
}

# 5. Run MCMC inference
column.compute_mcmc(layers, priors, nb_iter=10000)

# 6. Get results
best_params = column.get_best_params()
confidence = column.get_confidence_intervals()
temperatures = column.get_temperatures()
flows = column.get_flows()
```

## Error Handling

The API includes comprehensive error handling for common issues:

- **Invalid Data Formats**: Clear error messages for malformed input
- **Missing Dependencies**: Graceful handling of missing libraries
- **Numerical Issues**: Robust handling of convergence problems
- **Memory Management**: Efficient handling of large datasets

## Performance Considerations

- **Data Size**: Optimized for typical monitoring campaigns (months to years)
- **Computation Time**: MCMC inference scales with iteration count and data size
- **Memory Usage**: Efficient storage of large measurement datasets
- **Parallel Processing**: Support for multi-core MCMC execution

## Version Compatibility

This API specification is compatible with:
- **pyheatmy**: Version 0.4.0+
- **Molonaviz**: Version 2.0+
- **Python**: 3.9+
- **NumPy**: 1.20+
- **SciPy**: 1.7+

## Support and Documentation

For additional support:
- [pyheatmy Documentation](../pyheatmy/README.md)
- [Molonaviz User Guide](../Molonaviz/README.md) 
- [Hardware Integration Guide](../Device/README.md)
- [Example Notebooks](../pyheatmy/demo*.ipynb)