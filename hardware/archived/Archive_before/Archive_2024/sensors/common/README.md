# Common Sensor Utilities

This directory contains utilities and helper functions common to all sensor types in the MOLONARI ecosystem.

## Purpose

Provides shared functionality that can be used across different sensor implementations:

- **Data validation** and quality control
- **Sensor calibration** routines  
- **Communication helpers** for LoRa protocol
- **Power management** utilities
- **Timing and scheduling** functions

## Current Status

🚧 **Under Development** - Common utilities are currently provided through the `../../shared/` directory.

## Planned Features

- **Sensor Abstraction Layer**: Unified interface for different sensor types
- **Calibration Framework**: Standardized sensor calibration procedures
- **Data Quality Metrics**: Real-time data validation and flagging
- **Configuration Management**: Centralized sensor configuration storage

## Usage

Common utilities will be included in sensor implementations:

```cpp
#include "../../common/SensorBase.hpp"
#include "../../common/DataValidator.hpp"
#include "../../common/CalibrationManager.hpp"
```

## Contributing

This area is ideal for contributions that improve code reuse across sensor types:

1. **Identify common patterns** across existing sensor implementations
2. **Extract reusable components** into this directory
3. **Create base classes** for sensor functionality
4. **Implement standardized interfaces** for data and communication

Common utility development helps maintain consistency and reduces duplication across the hardware ecosystem.