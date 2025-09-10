# MOLONARI1D Environmental Monitoring Ecosystem

MOLONARI1D is a comprehensive ecosystem for **monitoring local stream-aquifer water and heat exchanges** through underwater sensor networks. The system provides end-to-end monitoring from hardware deployment to scientific analysis, enabling long-term autonomous data collection in challenging aquatic environments.

## System Architecture Overview

MOLONARI1D implements a **multi-tier monitoring architecture** designed for scalable, autonomous environmental monitoring:

```
Underwater Sensors → Relay → Gateway → Server → Database → Analysis Tools
     (Arduino)       (LoRa)  (LoRaWAN)  (Internet) (SQL)   (Python ML/GUI)
```

**Data Flow Pipeline:**
1. **Field Sensors**: Battery-powered Arduino devices collect temperature/pressure every 15min
2. **Local Communication**: Custom LoRa protocol transmits sensor data to relay daily
3. **Wide Area Network**: LoRaWAN gateway forwards data to internet-connected server
4. **Quality Control**: Server database processes and validates incoming sensor data
5. **Analysis Interface**: Molonaviz GUI manages devices and visualizes data streams
6. **Scientific Inference**: pyheatmy performs Bayesian MCMC inversion for flux estimation

This architecture enables **months-to-years** of autonomous underwater monitoring with minimal human intervention.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Target Audiences & Usage Scenarios

### For Fablabs & Hardware Developers
**Building and deploying monitoring stations:**
- Arduino programming for sensor data collection and LoRa communication
- Hardware assembly guides for waterproof underwater sensor packages
- Communication protocol implementation for sensor-relay-gateway chains
- Power management strategies for multi-month autonomous operation
- Field deployment best practices for riverbed monitoring

### For Software Developers
**Extending the Python ecosystem:**
- Object-oriented design patterns in scientific computing applications
- MCMC algorithm implementation and optimization in pyheatmy
- PyQt5 GUI architecture and SQL database integration in Molonaviz
- Data processing pipelines from raw sensor streams to scientific results
- Testing strategies for scientific computing workflows

### For Research Users
**Operating the monitoring system:**
- Device management through Molonaviz GUI interface
- Data quality control and validation procedures  
- Scientific analysis workflows using pyheatmy inference engine
- Interpretation of water and energy flux estimates with uncertainty quantification
- Integration with existing hydrological monitoring networks

## Component Architecture & Separation

### Hardware Layer (Device/)
**Physical monitoring devices and communication infrastructure:**

**Sensor Nodes (Arduino MKR WAN 1310):**
- Waterproof packages containing temperature and pressure sensors
- Local data storage on SD cards with CSV format
- Power management for multi-month battery operation
- Custom LoRa communication protocol for data transmission

**Relay Stations (Arduino MKR WAN 1310):**
- Aggregation points collecting data from multiple sensor nodes
- LoRa receiver for sensor communication (100m range)
- LoRaWAN transmitter for gateway communication
- Data buffering and retry mechanisms for reliability

**Gateway Infrastructure (Robustel R3000):**
- LoRaWAN-to-Internet bridge for remote data access
- Ethernet connectivity for server communication
- Long-range coverage for multiple relay stations
- Network management and configuration interfaces

### Communication Protocols
**Multi-layer communication stack for remote sensor networks:**

**Sensor-to-Relay (Custom LoRa Protocol):**
- Three-way handshake for reliable connection establishment
- Scheduled communication windows (e.g., daily at 23:45 for temperature sensors)
- Automatic retry mechanisms with exponential backoff (up to 6 attempts)
- Power-efficient transmission cycles minimizing battery drain
- Tree topology supporting multiple sensors per relay

**Relay-to-Gateway (LoRaWAN):**
- Industry-standard LoRaWAN protocol for wide-area coverage
- Encrypted data transmission for security
- Adaptive data rate optimization for varying conditions
- Network server integration for internet connectivity

**Gateway-to-Server (Internet):**
- HTTP/HTTPS protocols for reliable data upload
- JSON data formatting for structured information exchange
- Error handling and connection recovery mechanisms
- Authentication and security for remote access

### Software Layer
**Python-based scientific computing ecosystem with clear architectural separation:**

**pyheatmy (Scientific Inference Engine):**
- **Core Philosophy**: Object-oriented design with clear separation of concerns
- **Column Class**: Main abstraction representing a 1D riverbed column model
- **MCMC Implementation**: Bayesian inference for parameter estimation with uncertainty
- **Data Integration**: Direct coupling with sensor data streams from Molonaviz
- **Research Extensions**: Modular architecture supporting experimental features

**Molonaviz (Device Management & Visualization):**
- **Frontend Architecture**: PyQt5-based GUI following Model-View-Controller pattern
- **Backend Design**: SQL database abstraction layer for device and data management
- **Device Registration**: Laboratory and sampling point hierarchy management
- **Data Pipeline**: Quality control workflows from raw sensor data to analysis-ready datasets
- **Analysis Integration**: Direct launching of pyheatmy inference workflows

**Object-Oriented Design Principles:**
- **Encapsulation**: Clear boundaries between hardware abstraction, data processing, and analysis
- **Inheritance**: Sensor classes extending base device functionality with type-specific features
- **Polymorphism**: Unified interfaces for different sensor types and communication protocols
- **Composition**: Complex workflows built from reusable, testable components

## Development Environment Setup

### Hardware Programming Environment
**Arduino IDE setup for sensor and relay development:**

**Required Hardware:**
- Arduino MKR WAN 1310 (sensors and relay)
- Temperature sensors (DS18B20, thermocouples)
- Pressure sensors (differential pressure measurement)
- SD card modules for local data storage
- LoRa antennas and power management circuits

**Arduino Libraries:**
```cpp
#include <MKRWAN.h>        // LoRaWAN communication
#include <RTCZero.h>       // Real-time clock for scheduling
#include <SD.h>            // SD card data storage
#include <OneWire.h>       // Temperature sensor communication
#include <DallasTemperature.h>  // DS18B20 temperature sensors
```

**Programming Environment Setup:**
```bash
# Install Arduino IDE with MKR WAN 1310 board support
# Add required libraries through Library Manager
# Configure LoRaWAN keys and network settings
```

### Python Environment Requirements
**Critical version requirements for ecosystem compatibility:**

- **pyheatmy**: Python 3.9+ (scientific computing libraries)
- **Molonaviz**: Python 3.10+ (PyQt5 GUI framework requirements)
- **Recommended**: Python 3.12 (tested and fully compatible)

**Network Timeout Considerations:**
- PyPI connections may timeout in constrained environments
- Always use `--timeout 300` for pip installations
- PYTHONPATH workarounds available for development environments

### Quick Bootstrap Sequence
**Validated installation workflow with timing expectations:**

1. **Install test dependencies** (~5 seconds):
   ```bash
   pip install pytest nbmake
   ```

2. **Install pyheatmy** (~10 seconds):
   ```bash
   cd pyheatmy/
   pip install --timeout 300 -e .
   ```

3. **Install Molonaviz dependencies** (~30-60 seconds):
   ```bash
   pip install --timeout 300 pyqt5 pandas scipy matplotlib setuptools
   ```
   **Note**: `pip install -e Molonaviz/` frequently fails due to network timeouts

4. **Validate installation**:
   ```bash
   # Test pyheatmy import
   python -c "import pyheatmy; print('pyheatmy ready')"
   
   # Test Molonaviz structure (expected GUI import error in headless mode)
   cd Molonaviz/src/
   export PYTHONPATH="$PWD:$PYTHONPATH"
   python -c "import molonaviz; print('Molonaviz structure validated')"
   ```

### Testing & Validation Workflows
**Comprehensive testing for multi-component ecosystem:**

**Unit Testing (Both Packages - ~5 seconds):**
```bash
pytest pyheatmy/ Molonaviz/
```

**Scientific Workflow Validation (~85 seconds):**
```bash
cd pyheatmy/
pytest --nbmake --nbmake-timeout=600 demoPyheatmy.ipynb demo_genData.ipynb
```

**Hardware Testing Procedures:**
```bash
# Arduino code compilation and upload verification
# LoRa communication range testing
# Power consumption measurement protocols
# Waterproofing and environmental stress testing
```

## Hardware Programming & Communication Protocols

### Arduino Sensor Programming
**Low-power environmental monitoring with LoRa communication:**

**Core Sensor Functionality:**
```cpp
// Example sensor measurement cycle (every 15 minutes)
void performMeasurement() {
    float temperature = readTemperatureSensors();
    float pressure = readPressureSensors();
    
    // Store locally on SD card
    logDataToSD(temperature, pressure, getCurrentTimestamp());
    
    // Check if transmission time (e.g., daily at 23:45)
    if (isTransmissionTime()) {
        transmitDataToRelay();
    }
    
    // Enter low-power sleep mode
    enterDeepSleep(15 * 60 * 1000); // 15 minutes
}
```

**Power Management Strategy:**
- Deep sleep between measurements (power consumption < 1mA)
- Sensor power control (turn on only during measurements)
- SD card power cycling to prevent corruption
- Real-time clock (RTC) for accurate scheduling
- Battery voltage monitoring for maintenance alerts

**Data Storage Protocol:**
- CSV format on SD card for human readability
- Timestamp synchronization with external RTC
- Data integrity checks and corruption recovery
- Local buffering for transmission failures

### LoRa Communication Protocol Design
**Custom protocol for reliable sensor-to-relay communication:**

**Three-Way Handshake Sequence:**
```
Sensor → Relay: WAKE_UP (device_id, data_available)
Relay → Sensor: ACK_WAKE (session_id, ready_to_receive)
Sensor → Relay: DATA_PACKET (session_id, sensor_data)
Relay → Sensor: DATA_ACK (session_id, received_ok)
```

**Retry Mechanism with Exponential Backoff:**
- Initial retry: 1 second delay
- Subsequent retries: 2, 4, 8, 16, 32 seconds
- Maximum 6 retry attempts before deferring to next cycle
- Battery preservation during communication failures

**Network Topology Considerations:**
- Tree structure: multiple sensors per relay (up to 10 devices)
- Range limitations: 100m underwater, 1km+ surface
- Frequency management: EU868/US915 LoRa bands
- Collision avoidance: time-division multiple access (TDMA)

**Signal Propagation Challenges:**
- Water absorption at LoRa frequencies (significant attenuation)
- Air-water boundary reflection and refraction
- Flood scenario recovery (days of disrupted communication)
- Antenna design for underwater and surface operation

### LoRaWAN Gateway Integration
**Wide-area connectivity for remote monitoring:**

**Robustel R3000 Configuration:**
- LoRaWAN network server integration
- Internet connectivity via ethernet/cellular
- Multi-channel receiver for simultaneous relay communication
- Device management and provisioning interfaces

**Data Forwarding Protocol:**
- JSON payload structure for sensor data
- HTTP/HTTPS transport with authentication
- Error recovery and connection monitoring
- Bandwidth optimization for cellular connections

### Server-Side Data Processing
**Quality control and database integration:**

**Data Validation Pipeline:**
- Timestamp verification and synchronization
- Sensor range checking and anomaly detection
- Missing data interpolation strategies
- Quality flags for downstream analysis

**Database Schema Design:**
- Device hierarchy: sites → stations → sensors
- Time-series data storage optimizations
- Metadata management for sensor configurations
- User access control and audit logging

## Software Architecture & Development

### pyheatmy: Scientific Computing Engine
**Object-oriented MCMC inference for hydrological parameter estimation:**

**Core Design Philosophy:**
- **Single Responsibility**: Each class handles one aspect of the inference problem
- **Dependency Injection**: Clear interfaces between data, models, and algorithms
- **Immutable Data**: Sensor measurements treated as immutable time series
- **Functional Composition**: Complex workflows built from pure functions

**Primary Classes & Responsibilities:**
```python
# Core abstraction for riverbed column modeling
class Column:
    """1D thermal model with sensor data integration"""
    def __init__(self, depths, temperatures, times):
        self.model_params = ModelParameters()
        self.sensor_data = SensorData(depths, temperatures, times)
        self.mcmc_sampler = MCMCSampler()
    
    def run_inference(self, n_iterations=10000):
        """Bayesian parameter estimation with uncertainty quantification"""
        return self.mcmc_sampler.sample(self.model_params, self.sensor_data)

# Sensor data abstraction
class SensorData:
    """Immutable container for temperature and pressure measurements"""
    def validate_temporal_consistency(self):
        """Ensure consistent 15-minute sampling intervals"""
    
    def interpolate_missing_values(self):
        """Handle sensor dropouts and communication failures"""

# MCMC algorithm implementation
class MCMCSampler:
    """Metropolis-Hastings sampler for parameter inference"""
    def calculate_likelihood(self, params, observations):
        """RMSE-based likelihood for temperature matching"""
    
    def propose_step(self, current_params):
        """Adaptive step size for efficient chain mixing"""
```

**Integration with Hardware Data:**
- Direct CSV import from sensor SD card storage
- Automatic timestamp alignment across multiple sensors
- Quality control flags from Molonaviz database
- Real-time analysis capability for field validation

### Molonaviz: Device Management & Visualization
**PyQt5 GUI with SQL backend for operational monitoring:**

**Model-View-Controller Architecture:**
```python
# Database abstraction layer
class DatabaseManager:
    """SQL operations for device and data management"""
    def register_device(self, device_config):
        """Add new sensor to monitoring network"""
    
    def ingest_sensor_data(self, device_id, measurements):
        """Process incoming data from communication protocols"""

# GUI frontend components
class DeviceManagerView(QMainWindow):
    """Main interface for device configuration and monitoring"""
    def __init__(self):
        self.device_tree = DeviceTreeWidget()
        self.data_viewer = DataVisualizationWidget()
        self.analysis_launcher = AnalysisWidget()

# Business logic layer
class SensorController:
    """Coordinates between GUI and database operations"""
    def handle_new_data(self, sensor_id, data_packet):
        """Process incoming LoRa data and update displays"""
```

**Laboratory Hierarchy Management:**
- **Sites**: Geographic locations with multiple monitoring stations
- **Stations**: Individual relay points with associated sensor networks
- **Sensors**: Physical devices with unique identifiers and configurations
- **Measurements**: Time-series data with quality control metadata

**Real-time Data Integration:**
- WebSocket connections for live sensor data streams
- Automatic data validation and quality flagging
- Alert generation for device failures or anomalous readings
- Export functionality for external analysis tools

### Data Pipeline Architecture
**End-to-end flow from sensors to scientific results:**

**Stage 1: Hardware Data Collection**
```
Arduino Sensors → SD Card Storage → LoRa Transmission → Relay Aggregation
```

**Stage 2: Network Communication**
```
Relay Buffer → LoRaWAN Gateway → Internet Upload → Server Reception
```

**Stage 3: Quality Control Processing**
```
Raw Data Validation → Timestamp Alignment → Missing Data Handling → Database Storage
```

**Stage 4: Scientific Analysis**
```
Molonaviz Data Selection → pyheatmy Parameter Setup → MCMC Inference → Results Visualization
```

### Development Best Practices

**Testing Strategy:**
- **Unit Tests**: Individual component validation (sensors, communication, analysis)
- **Integration Tests**: End-to-end data flow verification
- **Hardware-in-Loop**: Real sensor testing with mock communication
- **Scientific Validation**: Known-result benchmarks for MCMC algorithms

**Documentation Standards:**
- **API Documentation**: Comprehensive docstrings for all public interfaces
- **Hardware Guides**: Assembly and deployment instructions for fablabs
- **Protocol Specifications**: Detailed communication protocol documentation
- **Scientific Methods**: Mathematical foundations and validation studies

**Version Control Workflow:**
- **Feature Branches**: Separate development for hardware, software, and analysis features
- **Hardware Releases**: Tagged versions with specific Arduino library dependencies
- **Software Releases**: Coordinated releases ensuring compatibility across components
- **Data Format Versioning**: Backward compatibility for long-term monitoring datasets

## Repository Structure & Navigation

```
MOLONARI1D/
├── Device/                          # Hardware & Communication Layer
│   ├── hardware/                    # Physical device specifications
│   │   ├── dataloggerAndRelay/     # Relay station hardware designs
│   │   ├── differentialPressureSensor/  # Pressure measurement devices
│   │   └── distributedTemperatureSensor/  # Temperature sensor arrays
│   ├── hardwareProgramming/        # Arduino firmware & protocols
│   │   ├── Sensor/                 # Sensor node firmware (Arduino C++)
│   │   ├── Relay/                  # Relay station firmware (Arduino C++)
│   │   ├── Documentation/          # Protocol specs & assembly guides
│   │   └── Tests Codes/            # Hardware validation scripts
│   └── installationSystem/         # Deployment guides & procedures
│
├── pyheatmy/                       # Scientific Computing Engine
│   ├── pyheatmy/                   # Core inference algorithms
│   │   ├── core.py                 # Column class & MCMC implementation
│   │   ├── sensors.py              # Sensor data abstraction
│   │   └── params.py               # Parameter estimation classes
│   ├── tests/                      # Unit tests for scientific code
│   ├── demo*.ipynb                 # Scientific workflow demonstrations
│   └── research/                   # Experimental features & algorithms
│
├── Molonaviz/                      # Device Management & GUI
│   ├── src/molonaviz/             # PyQt5 application source
│   │   ├── backend/               # SQL database management
│   │   ├── frontend/              # GUI components & visualization
│   │   └── interactions/          # Data import/export workflows
│   └── tests/                     # GUI component unit tests
│
├── data/                          # Sample Datasets & Examples
│   ├── sensor_calibrations/       # Device-specific calibration data
│   ├── field_deployments/        # Real-world monitoring datasets
│   └── synthetic_data/           # Generated data for testing
│
├── dataAnalysis/                  # Analysis Tools & Notebooks
│   ├── quality_control/          # Data validation procedures
│   ├── visualization/            # Custom plotting and reporting tools
│   └── case_studies/            # Published research examples
│
└── .github/                      # Development & CI Configuration
    ├── workflows/                # Automated testing for all components
    └── copilot-instructions.md   # This comprehensive guide
```

## Fablab & User Deployment Guide

### For Hardware Assembly (Fablabs)
**Complete device construction and deployment workflow:**

**Phase 1: Component Assembly**
1. **Sensor Package Construction**:
   - Arduino MKR WAN 1310 programming and testing
   - Temperature sensor (DS18B20) waterproof integration
   - Pressure sensor calibration and mounting
   - SD card storage module configuration
   - Antenna selection and positioning for underwater operation

2. **Power System Design**:
   - Battery capacity calculation for target deployment duration
   - Solar panel integration for relay stations (optional)
   - Low-power sleep mode validation and current measurement
   - Voltage monitoring for maintenance scheduling

3. **Waterproofing & Packaging**:
   - IP68-rated enclosure selection and modification
   - Cable gland installation for sensor connections
   - Desiccant integration for moisture control
   - Pressure equalization for deep deployment

**Phase 2: Communication Testing**
1. **LoRa Range Validation**:
   - Line-of-sight testing between sensor and relay
   - Underwater signal propagation measurement
   - Interference testing in target deployment environment
   - Backup communication pathways for flood scenarios

2. **Protocol Implementation**:
   - Three-way handshake validation
   - Retry mechanism testing under various failure conditions
   - Data integrity verification across transmission cycles
   - Power consumption measurement during communication

**Phase 3: Field Deployment**
1. **Site Preparation**:
   - Riverbed survey and sensor placement planning
   - Relay station positioning for optimal coverage
   - Gateway connectivity verification
   - Environmental impact assessment

2. **Installation Procedures**:
   - Sensor anchoring techniques for flowing water environments
   - Cable routing and protection from debris/ice damage
   - System commissioning and initial data validation
   - Maintenance access planning and documentation

### For Research Users
**Operating deployed monitoring networks:**

**System Startup & Configuration**:
```bash
# Launch Molonaviz device management interface
molonaviz

# From GUI: Configure monitoring sites and sensor networks
# Register devices with unique identifiers and metadata
# Set data collection schedules and quality control parameters
```

**Data Analysis Workflow**:
```python
# Import and analyze sensor data using pyheatmy
import pyheatmy

# Load data from Molonaviz database or CSV files
column = pyheatmy.Column.from_sensor_data('site_01_station_A')

# Run Bayesian inference for water flux estimation
results = column.run_inference(n_iterations=10000)

# Extract flux estimates with uncertainty bounds
water_flux = results.get_parameter_distribution('darcy_velocity')
energy_flux = results.get_parameter_distribution('thermal_conductivity')
```

**Quality Control Procedures**:
- Automated anomaly detection for sensor drift or failure
- Cross-validation between co-located sensors
- Environmental context integration (weather, river stage)
- Data gap interpolation and uncertainty propagation

### For Software Developers
**Extending and maintaining the ecosystem:**

**Development Environment Setup**:
```bash
# Clone repository with shallow history for faster setup
git clone --depth=1 https://github.com/flipoyo/MOLONARI1D.git

# Set up Python environment
python -m venv molonari_dev
source molonari_dev/bin/activate  # Linux/Mac
# molonari_dev\Scripts\activate.bat  # Windows

# Install development dependencies
pip install --timeout 300 -e pyheatmy/
pip install --timeout 300 pyqt5 pandas scipy matplotlib setuptools
```

**Component Development Guidelines**:
- **Hardware Changes**: Update Arduino firmware with backward compatibility
- **Communication Protocol**: Maintain protocol version compatibility across devices
- **Scientific Algorithms**: Validate new methods against established benchmarks
- **GUI Features**: Follow PyQt5 best practices for cross-platform compatibility

**Testing & Integration**:
```bash
# Run comprehensive test suite
pytest pyheatmy/ Molonaviz/ --timeout=300

# Validate scientific workflows
cd pyheatmy/
pytest --nbmake --nbmake-timeout=600 demoPyheatmy.ipynb demo_genData.ipynb

# Hardware-in-loop testing (requires physical devices)
cd Device/hardwareProgramming/Tests\ Codes/
python sensor_communication_test.py
```

## Performance Characteristics & Operational Parameters

### Hardware Performance Specifications
**Power consumption and operational lifetimes:**

**Sensor Node Power Budget:**
- Active measurement cycle: 50mA for 30 seconds (every 15 minutes)
- LoRa transmission: 120mA for 5 seconds (daily)
- Deep sleep: 0.1mA (continuous)
- **Expected battery life**: 8-12 months on 3.7V 5000mAh Li-ion

**Communication Range & Reliability:**
- **Underwater LoRa range**: 50-100 meters (frequency dependent)
- **Surface LoRa range**: 1-3 kilometers (line of sight)
- **Data success rate**: >95% under normal conditions
- **Flood recovery time**: 24-48 hours post-event

**Data Collection Rates:**
- Sensor measurement interval: 15 minutes (configurable)
- Local storage capacity: 6+ months of measurements
- Transmission frequency: Daily (configurable by sensor type)
- Gateway upload: Real-time when connectivity available

### Software Performance Benchmarks
**Computational requirements and execution times:**

**pyheatmy MCMC Performance:**
- Core inference (10,000 iterations): ~85 seconds
- Memory usage: <500MB for typical datasets
- Convergence assessment: Built-in diagnostics and visualization
- **Scaling**: Linear with number of time points, polynomial with model complexity

**Molonaviz GUI Responsiveness:**
- Database queries: <1 second for typical site data
- Real-time plot updates: 30 FPS for live data streams
- Large dataset loading: ~5 seconds for 1 year of sensor data
- **Concurrent users**: Designed for 5-10 simultaneous connections

**Installation & Testing Timelines:**
- Python environment setup: 60-120 seconds
- Full test suite execution: ~90 seconds
- Notebook validation: 85-150 seconds per demo
- **CI/CD pipeline**: <5 minutes total execution time

### Network Architecture Scalability
**System capacity and expansion capabilities:**

**Single Relay Coverage:**
- Maximum sensors per relay: 10 devices
- Coverage area: 1km² (surface) / 0.1km² (underwater)
- Data throughput: 1KB per sensor per day
- **Collision handling**: TDMA scheduling with 15-minute guard intervals

**Multi-Relay Networks:**
- Gateway capacity: 100+ relay stations
- Network topology: Tree structure with redundant pathways
- Data aggregation: 1MB per day per gateway
- **Expansion strategy**: Hierarchical clustering for large river systems

### Environmental Operating Conditions
**Deployment specifications and limitations:**

**Physical Environment Tolerances:**
- Operating temperature: -20°C to +60°C
- Water depth: 0-10 meters (pressure sensor dependent)
- Flow velocity: 0-2 m/s (mechanical stability)
- **Submersion duration**: Indefinite with proper waterproofing

**Communication Environment Factors:**
- Water conductivity impact: Significant signal attenuation in high-conductivity water
- Ice coverage effects: Communication disruption during freeze periods
- Vegetation interference: Signal degradation in dense aquatic vegetation
- **Mitigation strategies**: Adaptive power control and alternative routing

## Troubleshooting & Maintenance

### Hardware Diagnostics
**Common failure modes and resolution procedures:**

**Power System Issues:**
- Battery voltage monitoring through built-in ADC
- Solar charging system validation (where applicable)
- Power consumption anomaly detection
- **Replacement indicators**: Voltage drops below 3.3V under load

**Communication Failures:**
- LoRa signal strength measurement and logging
- Antenna connection verification procedures
- Range testing protocols for changing environments
- **Escalation path**: Relay-to-gateway backup communication

**Data Storage Problems:**
- SD card health monitoring and corruption detection
- Alternative storage strategies (internal flash backup)
- Data recovery procedures for partial failures
- **Prevention**: Regular card replacement schedules

### Software Diagnostics
**Installation and runtime troubleshooting:**

**Python Environment Issues:**
- Version compatibility verification (3.9+ for pyheatmy, 3.10+ for Molonaviz)
- Dependency conflict resolution using virtual environments
- Network timeout workarounds for PyPI access
- **PYTHONPATH fallback**: Development installation without pip

```bash
# Network timeout recovery
pip install --timeout 300 --retries 3 package_name

# PYTHONPATH development setup
export PYTHONPATH="/path/to/pyheatmy:/path/to/Molonaviz/src:$PYTHONPATH"
```

**GUI and Database Issues:**
- Qt backend availability in headless environments
- SQL database connection validation and repair
- Cross-platform font and display scaling
- **Headless operation**: Expected ImportError for GUI components

### Data Quality Assurance
**Validation procedures and quality control:**

**Sensor Calibration Drift:**
- Automated cross-sensor validation for co-located devices
- Statistical outlier detection using historical baselines
- Temperature sensor drift correction using reference measurements
- **Recalibration triggers**: Systematic bias detection algorithms

**Communication Data Integrity:**
- Checksum validation for all transmitted data packets
- Timestamp consistency verification across sensor networks
- Missing data interpolation with uncertainty quantification
- **Error recovery**: Automatic retransmission and local storage backup

**Scientific Result Validation:**
- MCMC convergence diagnostics and chain mixing assessment
- Physical parameter bounds checking (positive flux constraints)
- Uncertainty propagation through complete analysis pipeline
- **Benchmark comparison**: Known-result validation datasets