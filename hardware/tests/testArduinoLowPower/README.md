# Low Power Operation Test

Critical validation test for battery-powered sensor operation, focusing on power consumption optimization and extended deployment duration.

## Purpose

Validates the Arduino MKR WAN 1310's low-power capabilities essential for months-long autonomous sensor deployment in remote river environments.

## Hardware Requirements

- **Arduino MKR WAN 1310** - Target microcontroller
- **Current measurement tools** - µCurrent or similar precision equipment
- **Battery simulation** - Controlled power supply for testing
- **Multimeter** - For accurate current measurement

## Power Management Testing

### Sleep Mode Validation
- **Deep Sleep**: Verify <0.1mA consumption during idle periods
- **Wake-up Timing**: Validate 15-minute measurement intervals
- **RTC Operation**: Confirm real-time clock maintains timing
- **Peripheral Power-down**: Test sensor and radio module shutdown

### Active Mode Assessment
- **Measurement Cycle**: Monitor 30-second active periods
- **Communication Power**: Validate LoRa transmission consumption
- **Processing Load**: Measure computation and data handling power
- **Peak Current**: Assess maximum instantaneous power draw

### Battery Life Estimation
- **Duty Cycle Calculation**: Measure active vs. sleep time ratios
- **Capacity Planning**: Estimate deployment duration for various batteries
- **Environmental Factors**: Account for temperature effects on battery
- **Safety Margins**: Include degradation and worst-case scenarios

## Test Configuration

### Power Measurement Setup
```cpp
// Enable power monitoring features
#define POWER_DEBUG        // Enable current measurement logging
#define SLEEP_DURATION_MS  900000  // 15 minutes between cycles
#define ACTIVE_DURATION_MS 30000   // 30 seconds measurement window
```

### Measurement Modes
- **Continuous Monitoring**: Real-time current consumption
- **Cycle Analysis**: Power profile over complete measurement cycle
- **Long-term Assessment**: Extended testing for drift analysis
- **Environmental Testing**: Temperature and humidity effects

## Expected Power Profile

### Typical Operating Cycle (15 minutes)
1. **Deep Sleep**: 14 min 30 sec @ <0.1mA = 0.024mAh
2. **Wake-up/Measurement**: 30 seconds @ 50mA = 0.42mAh  
3. **LoRa Communication**: 5 seconds @ 120mA = 0.17mAh
4. **Total per Cycle**: ~0.61mAh

### Daily Power Consumption
- **96 cycles per day** × 0.61mAh = **58.6mAh/day**
- **Monthly consumption**: ~1.76Ah
- **8-month deployment**: ~14Ah battery requirement

## Validation Criteria

### Sleep Mode Performance
- ✅ **Current Draw**: <0.1mA during sleep
- ✅ **Wake-up Accuracy**: ±30 seconds on 15-minute intervals
- ✅ **RTC Stability**: <1 minute drift per month
- ✅ **Peripheral Shutdown**: Complete radio and sensor power-down

### Active Mode Efficiency
- ✅ **Measurement Time**: <30 seconds for sensor readings
- ✅ **Communication Time**: <5 seconds for LoRa transmission
- ✅ **Processing Efficiency**: Minimal computation overhead
- ✅ **State Transitions**: Fast sleep/wake switching

### Battery Life Targets
- ✅ **Minimum Duration**: 6 months continuous operation
- ✅ **Target Duration**: 8-12 months with 5000mAh battery
- ✅ **Temperature Range**: -10°C to +50°C operation
- ✅ **Degradation Margin**: 20% capacity reduction over time

## Test Procedures

### Short-term Validation (1 hour)
1. Measure baseline sleep current
2. Trigger measurement cycle and monitor
3. Validate LoRa communication power
4. Confirm return to sleep mode

### Medium-term Assessment (24 hours)
1. Continuous power monitoring over full day
2. Validate timing accuracy over multiple cycles
3. Check for power consumption drift
4. Assess environmental stability

### Long-term Projection (1 week)
1. Extended operation simulation
2. Battery voltage discharge curve
3. Performance degradation assessment
4. Real-world condition simulation

## Environmental Considerations

### Temperature Effects
- **Battery capacity**: Reduced performance in cold conditions
- **Microcontroller operation**: Validate across temperature range
- **Crystal oscillator**: RTC accuracy temperature coefficients

### Deployment Conditions
- **Underwater pressure**: Potential current leakage paths
- **Humidity effects**: Condensation and corrosion risks
- **Mechanical stress**: Vibration and movement impacts

## Integration with System Design

This test directly informs:
- **Battery selection** for target deployment duration
- **Measurement scheduling** optimization
- **Communication duty cycles** for power efficiency
- **Hardware design** for power management

## Related Documentation

- [Power Management Design](../../docs/power-management.md)
- [Battery Selection Guide](../../docs/battery-specification.md)
- [Environmental Testing](../../deployment/environmental-validation.md)
- [Deployment Duration Planning](../../deployment/field-planning.md)