# Firmware getting started (MOLONARI1D)

This is the main entry point for firmware developers.

If you are new here, read this file first. Other README files in subfolders are component details.

## 1) What to edit

- Sensor firmware: `hardware/firmware/mains_ino/sensor/main.cpp`
- Relay firmware: `hardware/firmware/mains_ino/relay/main.cpp`
- Shared libraries: `hardware/firmware/libs/*`
- Build configuration: `hardware/platformio.ini`

## 2) SD card configuration file (important)

Each board reads a CSV config file from the SD card at boot.

Edit these source files in the repository:
- Sensor config template: `hardware/firmware/mains_ino/sensor/conf.csv`
- Relay config template: `hardware/firmware/mains_ino/relay/conf.csv`

Then copy the relevant `conf.csv` to the **root of the SD card** before booting the board.

## 3) Compile in VS Code with PlatformIO

1. Open your cloned repository's `hardware/` folder in VS Code.
2. Install PlatformIO extension.
3. Use the environment from `platformio.ini`:
   - `main_sensor` for the sensor board
   - `main_relay` for the relay board

CLI equivalent (from `hardware/`):

```bash
pio run -e main_sensor
pio run -e main_relay
```

## 4) Flash to Arduino MKR WAN 1310

You can flash with either PlatformIO or Arduino IDE.

### Option A — PlatformIO upload (VS Code or CLI)

From `hardware/`:

```bash
pio run -e main_sensor -t upload
pio run -e main_relay -t upload
```

If upload waits for a new port, double-press reset on MKR WAN 1310.

### Option B — Arduino IDE upload

If you want to flash with Arduino IDE:

1. Open `hardware/firmware/mains_ino/sensor/sensor.ino` (sensor) or `hardware/firmware/mains_ino/relay/Relay.ino` (relay).
2. In Arduino IDE, select board **Arduino MKR WAN 1310**.
3. Select the correct serial port.
4. Click **Upload**.
5. Keep `conf.csv` on the SD card root.

## 5) Minimal ergonomic workflow

1. Edit `main.cpp` (+ libs if needed).
2. Edit matching `conf.csv`.
3. Compile with PlatformIO in VS Code (`main_sensor` or `main_relay`).
4. Copy `conf.csv` to SD card root.
5. Flash board (PlatformIO or Arduino IDE).

## 6) Where to go next

- Sensor details: `hardware/firmware/mains_ino/sensor/README.md`
- Relay details: `hardware/firmware/mains_ino/relay/README.md`
- General hardware docs: `hardware/docs/`
