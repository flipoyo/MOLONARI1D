# Compile and Upload an .ino File

## Arduino Extension for VScode

Name: Arduino

Id: moozzyk.Arduino

Description: Arduino support for Visual Studio Code

Version: 0.0.4

Publisher: moozzyk

VS Marketplace Link: https://marketplace.visualstudio.com/items?itemName=moozzyk.Arduino


## Install the arduino-cli Compiler

You need to install the arduino-cli compiler on your machine.

To install `arduino-cli` on Ubuntu 22.04, you can follow these steps:

1. **Update the packages**:
   Open a terminal and make sure your package list is up to date by running:
   ```bash
   sudo apt update
   ```

2. **Install the necessary dependencies**:
   You will need `curl` to download the installation script. Install it if it is not already installed:
   ```bash
   sudo apt install curl
   ```

3. **Download the installation script**:
   Use `curl` to download the Arduino CLI installation script:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh
   ```

4. **Run the installation script**:
   Run the downloaded script to install `arduino-cli`:
   ```bash
   sh install.sh
   ```

5. **Follow the instructions**:
   The script will guide you through the installation process. You can choose the installation location and add `arduino-cli` to your PATH if you wish.

6. **Verify the installation**:
   Once the installation is complete, you can verify that `arduino-cli` is correctly installed by running:
   ```bash
   arduino-cli version
   ```

This should display the installed version of Arduino CLI, confirming that the installation was successful.

If you encounter any issues or need a specific version, you can refer to the [official Arduino CLI documentation](https://arduino.github.io/arduino-cli/latest/installation/) for more details.


## Add the Necessary Packages

To add the `LoRa.h` library to `arduino-cli` on Ubuntu using the command line, follow these steps:

1. **Install `arduino-cli`**:
   If you haven't already, make sure `arduino-cli` is installed. You can follow the installation instructions mentioned earlier.

2. **Create a directory for libraries**:
   Create a directory to store your Arduino libraries if it doesn't already exist:
   ```bash
   mkdir -p ~/Arduino/libraries
   ```

3. **Download the LoRa library**:
   Use `git` to clone the LoRa library repository into the libraries directory:
   ```bash
   git clone https://github.com/sandeepmistry/arduino-LoRa.git ~/Arduino/libraries/LoRa
   ```

4. **Verify the installation**:
   You can verify that the library has been correctly added by listing the installed libraries with `arduino-cli`:
   ```bash
   arduino-cli lib list
   ```

5. **Use the library in your project**:
   - Create a new sketch or open an existing sketch.
   - Include the library in your code by adding:
     ```cpp
     #include <LoRa.h>
     ```



## Add the Board to be Used

For the Arduino MKR WAN 1310, here are the commands:
```bash
arduino-cli core update-index
arduino-cli core install arduino:samd
```


# Compile and Upload Your Code
   Use `arduino-cli` to compile and upload your code to your Arduino board. For example:
   ```bash
   arduino-cli compile --fqbn arduino:samd:mkrwan1310 --output-dir ~/Arduino/build --verbose /home/nflipo/MOLONARI1D/hardwareProgramming/Tests\ Codes/Sensor_Lora
   arduino-cli upload --fqbn arduino:samd:mkrwan1310 --port /dev/ttyACM0 --input-dir ~/Arduino/build /home/nflipo/MOLONARI1D/hardwareProgramming/Tests\ Codes/Sensor_Lora
   ```
   Replace `arduino:samd:mkrwan1310` with the Fully Qualified Board Name (FQBN) of your board and `/dev/ttyUSB0` with the appropriate serial port.