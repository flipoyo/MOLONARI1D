# MOLONARI Hardware Deployment Guide

This directory contains guides and resources for deploying MOLONARI monitoring systems in field environments.

## Deployment Overview

MOLONARI deployments involve multiple components that must be carefully planned and coordinated:

1. **Sensor Network Planning**: Site survey, sensor placement, coverage analysis
2. **Hardware Assembly**: Device construction, waterproofing, testing
3. **Communication Setup**: LoRa range testing, gateway placement, network configuration
4. **Field Installation**: Underwater deployment, relay positioning, system commissioning
5. **Monitoring & Maintenance**: Ongoing system monitoring, battery replacement, data validation

## Quick Deployment Checklist

### Pre-Deployment (Lab)

- [ ] **Hardware Assembly**: All sensors and relays assembled and tested
- [ ] **Software Upload**: Correct firmware uploaded to all devices
- [ ] **Communication Test**: LoRa communication verified between all devices
- [ ] **Power Validation**: Battery life projections confirmed through testing
- [ ] **Waterproofing**: All underwater components properly sealed and tested
- [ ] **Gateway Setup**: LoRaWAN gateway configured and connected to internet
- [ ] **Server Configuration**: Data collection server ready to receive data

### Site Preparation

- [ ] **Site Survey**: Deployment locations identified and GPS coordinates recorded
- [ ] **Permits**: Required environmental and research permits obtained
- [ ] **Access Planning**: Site access routes identified for installation and maintenance
- [ ] **Safety Assessment**: Hazard analysis completed, safety equipment prepared
- [ ] **Weather Monitoring**: Deployment scheduled for appropriate weather conditions

### Field Installation

- [ ] **Sensor Deployment**: Underwater sensors properly anchored and positioned
- [ ] **Relay Installation**: Relay stations positioned for optimal coverage
- [ ] **Gateway Placement**: Gateway installed with good cellular/internet connectivity
- [ ] **Communication Validation**: End-to-end communication tested
- [ ] **Initial Data Collection**: First data transmissions verified
- [ ] **Documentation**: All device locations, serial numbers, and configurations recorded

### Post-Deployment

- [ ] **Monitoring Setup**: Real-time monitoring dashboards configured
- [ ] **Alert Configuration**: Battery and communication failure alerts enabled  
- [ ] **Maintenance Schedule**: Regular maintenance visits planned
- [ ] **Data Backup**: Data backup and archival procedures implemented
- [ ] **Team Training**: Field personnel trained on system operation and troubleshooting

## Detailed Installation Guides

### Hardware Assembly
- **Installation Guide**: `1 - Installation guide_ENG.md`
  - Complete hardware assembly instructions
  - Wiring diagrams and component specifications
  - Testing procedures for assembled devices

### Sensor Hardware Configuration
- **Hardware Details**: `3 - Sensor's hardware-ENG.md`
  - SD card setup and formatting
  - RTC configuration and time synchronization
  - Power management and battery optimization

### Communication Protocol Setup
- **LoRa Protocol**: `4 - Our LoRa protocol_ENG.md`
  - Custom protocol configuration
  - Range testing procedures
  - Troubleshooting communication issues

### Gateway and Network Configuration
- **Network Setup**: `5 - Gateway and server configurations.md`
  - LoRaWAN gateway configuration
  - The Things Network (TTN) setup
  - Server-side data processing configuration

## Site-Specific Considerations

### Riverbed Environment

**Underwater Sensor Placement:**
- **Depth Requirements**: Sensors typically deployed 0.5-2m below riverbed surface
- **Flow Considerations**: Account for water flow direction and velocity
- **Seasonal Variations**: Plan for flood events and water level changes
- **Sediment Protection**: Protect sensors from debris and sediment accumulation

**Antenna Positioning:**
- **LoRa Range**: Underwater range limited to 50-100m, surface range 1-3km
- **Relay Placement**: Position relays to optimize coverage of all sensors
- **Gateway Coverage**: Ensure reliable LoRaWAN connectivity to internet gateway

### Environmental Challenges

**Waterproofing:**
- **IP68 Rating**: All underwater components must meet IP68 standards
- **Pressure Testing**: Test waterproof seals under pressure before deployment
- **Cable Management**: Proper sealing of cable entries and connections

**Power Management:**
- **Battery Capacity**: Size batteries for 8-12 month operation cycles
- **Solar Options**: Consider solar panels for relay stations in accessible locations
- **Low-Temperature Performance**: Account for battery performance in cold conditions

**Communication Reliability:**
- **Water Attenuation**: LoRa signals significantly attenuated underwater
- **Ice Formation**: Plan for signal disruption during freezing conditions
- **Vegetation Growth**: Account for seasonal vegetation affecting signal propagation

## Installation System Components

The `installationSystem/` directory contains:

### Physical Deployment Hardware
- **Mounting Systems**: Anchoring and positioning hardware for underwater sensors
- **Enclosures**: Waterproof housings for electronics and batteries
- **Cable Management**: Waterproof cable routing and connector systems
- **Buoyancy Control**: Flotation systems for relay positioning

### Installation Tools
- **Deployment Equipment**: Specialized tools for underwater installation
- **Testing Equipment**: Field testing tools for communication and power validation
- **Safety Equipment**: Personal protective equipment for water-based installations

### Documentation Templates
- **Site Records**: Forms for documenting device locations and configurations
- **Maintenance Logs**: Templates for tracking system status and maintenance activities
- **Troubleshooting Guides**: Field-ready troubleshooting procedures

## Maintenance and Support

### Regular Maintenance Schedule

**Monthly (Remote):**
- Monitor data transmission rates and quality
- Check battery voltage levels via telemetry
- Validate communication link status
- Review error logs and alert notifications

**Quarterly (Field Visit):**
- Visual inspection of above-water components
- Communication range testing
- Battery voltage measurement
- Data download from local storage (backup)

**Annually (Major Service):**
- Battery replacement for sensor nodes
- Waterproof seal inspection and replacement
- Firmware updates and configuration changes
- Complete system testing and recalibration

### Troubleshooting

**Communication Issues:**
- Check antenna connections and positioning
- Validate LoRa frequency settings and power levels
- Test communication range with portable equipment
- Review interference sources (other RF equipment)

**Power Problems:**
- Measure battery voltage under load conditions
- Check solar panel connections (if applicable)
- Validate sleep mode operation and current consumption
- Review environmental factors affecting battery performance

**Data Quality Issues:**
- Verify sensor calibration and drift
- Check for physical damage or fouling
- Validate data processing and transmission
- Review environmental factors affecting measurements

### Emergency Procedures

**Flood Events:**
- Communication disruption expected for 24-48 hours
- Sensor data stored locally during disruption
- Relay stations may require repositioning or recovery
- Gateway connectivity may be affected by power outages

**Equipment Failure:**
- Backup communication pathways via redundant relays
- Local data storage provides data recovery options
- Modular design allows individual component replacement
- Remote diagnostics enable efficient troubleshooting

**Environmental Hazards:**
- Ice formation may damage surface equipment
- High flow events may relocate underwater sensors
- Lightning protection for above-ground electronics
- Wildlife interference with cable runs

## Support Resources

### Technical Support
- **Hardware Issues**: Open GitHub issues for technical problems
- **Installation Questions**: Consult detailed guides in this directory
- **Custom Configurations**: Modify Arduino code for site-specific requirements

### Training and Documentation
- **Field Training**: Hands-on training for deployment teams
- **User Manuals**: Complete system operation documentation
- **Best Practices**: Lessons learned from previous deployments

### Community and Collaboration
- **Research Networks**: Integration with other monitoring systems
- **Data Sharing**: Protocols for sharing environmental data
- **Equipment Sharing**: Coordination with other research groups

For specific installation questions or custom deployment requirements, please consult the detailed guides in this directory or open an issue on GitHub for technical support.