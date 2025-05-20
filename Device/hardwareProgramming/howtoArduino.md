# Compile and Upload an .ino File

## Arduino Extension for VScode

Name: Arduino

Id: moozzyk.Arduino

Description: Arduino support for Visual Studio Code

Version: 0.0.4

Publisher: moozzyk

VS Marketplace Link: https://marketplace.visualstudio.com/items?itemName=moozzyk.Arduino



## __Linux__ procedure

### Install the arduino-cli Compiler

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


### Add the Necessary Packages

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

      For another library, such as ArduinoLowPower or SD:
      ```bash
      git clone https://github.com/arduino-libraries/ArduinoLowPower.git ~/Arduino/libraries/ArduinoLowPower
      git clone https://github.com/arduino-libraries/SD.git ~/Arduino/libraries/SD
      ```

      For another library, such as RTCZero.h and Adafruit_I2CDevice.h:
      ```bash
      git clone https://github.com/adafruit/RTClib.git ~/Arduino/libraries/RTClib
      git clone https://github.com/adafruit/Adafruit_BusIO.git ~/Arduino/libraries/Adafruit_BusIO
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



### Add the Board to be Used

   For the Arduino MKR WAN 1310, here are the commands:
   ```bash
   arduino-cli core update-index
   arduino-cli core install arduino:samd
   ```


### Compile and Upload Your Code

   Use `arduino-cli` to compile and upload your code to your Arduino board. For example:
   ```bash
   arduino-cli compile --fqbn arduino:samd:mkrwan1310 --output-dir ~/Arduino/build --verbose /home/nflipo/MOLONARI1D/Device/hardwareProgramming/Presentation\ Demo/Sensor_demo/Sensor_demo.ino
   arduino-cli upload --fqbn arduino:samd:mkrwan1310 --port /dev/ttyACM0 --input-dir ~/Arduino/build 
   ```
   Replace `arduino:samd:mkrwan1310` with the Fully Qualified Board Name (FQBN) of your board and `/dev/ttyUSB0` with the appropriate serial port. In VScode on ubuntu22.04, axess to your port for a nonsudo user must be granted first. With a sudo user please do the following:
   ```bash
   sudo usermod -aG dialout $USER
   ```
   Utiliser ```arduino-cli``` pour détecter les ports : 
   ```bash
   arduino-cli board list
   ```


Open the Serial Monitor, either with
```bash
arduino-cli monitor -p /dev/ttyACM0 -c baudrate=115200
```

Remplace ```115200``` by the speed declared in the sketch (via ```Serial.begin(115200)``` for instance).

Other method: Open the Serial Monitor in VS Code

1. Plug in your Arduino board.
2. Open your project folder in VS Code.
3. Make sure the correct port is selected (e.g., `/dev/ttyACM0`):
   - Open the command palette (`Ctrl+Shift+P`) > `Arduino: Select Serial Port`
4. Open the command palette again (`Ctrl+Shift+P`) and type:
`Arduino: Open Serial Monitor`
5. Choose the appropriate **baud rate** (e.g., `9600`, `115200`, depending on your sketch).

The serial monitor will appear in the **Terminal** panel at the bottom.

Tip :  Automatically Open Serial Monitor After Upload

To automatically open the serial monitor after uploading your sketch:

1. Go to **File > Preferences > Settings**
2. Search for: `Arduino: Open Serial Monitor After Upload`
3. Enable this option.

This will save time when testing sketches that output data via `Serial.print()`.




### Create a Project with Makefile

   It is possible to compile multiple sketches that depend on each other using a Makefile with arduino-cli. You can create a Makefile to automate the compilation and uploading of multiple sketches. Here is an example of a Makefile to compile and upload multiple sketches:

   ```makefile
   # Define the board and port
   BOARD = arduino:samd:mkrwan1310
   PORT = /dev/ttyACM0

   # Define the directories for the sketches
   SKETCH_DIRS = \
   /home/nflipo/MOLONARI1D/hardwareProgramming/Tests\ Codes/Sensor_Lora \
   /home/nflipo/MOLONARI1D/hardwareProgramming/Tests\ Codes/Another_Sketch

   # Define the output directory
   OUTPUT_DIR = ~/Arduino/build

   # Define the arduino-cli command
   ARDUINO_CLI = arduino-cli

   # Default target
   all: compile upload

   # Compile all sketches
   compile:
   @for dir in $(SKETCH_DIRS); do \
   echo "Compiling $$dir..."; \
   $(ARDUINO_CLI) compile --fqbn $(BOARD) --output-dir $(OUTPUT_DIR) $$dir; \
   done

   # Upload all sketches
   upload:
   @for dir in $(SKETCH_DIRS); do \
   echo "Uploading $$dir..."; \
   $(ARDUINO_CLI) upload --fqbn $(BOARD) --port $(PORT) --input-dir $(OUTPUT_DIR) $$dir; \
   done

   # Clean the output directory
   clean:
   rm -rf $(OUTPUT_DIR)

   .PHONY: all compile upload clean
   ```

   To use this Makefile, place it in the root directory of your project and run the following commands in the terminal:

   1. **Compile all sketches**:
      ```bash
      make compile
      ```

   2. **Upload all sketches**:
      ```bash
      make upload
      ```

   3. **Clean the output directory**:
      ```bash
      make clean
      ```

   This Makefile compiles and uploads all the sketches defined in the `SKETCH_DIRS` variable. You can add or remove sketch paths in this variable as needed.


## Windows procedure

### Install the arduino-cli Compiler on Windows

   To install `arduino-cli` on Windows, follow these steps:

   1. **Download the Arduino CLI executable**:
      Go to the [Arduino CLI releases page](https://github.com/arduino/arduino-cli/releases) and download the latest Windows executable (`arduino-cli.exe`).

   2. **Move the executable to a directory in your PATH**:
      Move the downloaded `arduino-cli.exe` to a directory that is included in your system's PATH environment variable. For example, you can create a directory `C:\ArduinoCLI` and add it to your PATH.

   3. **Verify the installation**:
      Open a Command Prompt and verify that `arduino-cli` is correctly installed by running:
      ```cmd
      arduino-cli version
      ```
      This should display the installed version of Arduino CLI, confirming that the installation was successful.

      If you encounter any issues or need a specific version, you can refer to the [official Arduino CLI documentation](https://arduino.github.io/arduino-cli/latest/installation/) for more details.

### Add the Necessary Packages

   To add the `LoRa.h` library to `arduino-cli` on Windows using the command line, follow these steps:

   1. **Install `arduino-cli`**:
      If you haven't already, make sure `arduino-cli` is installed. You can follow the installation instructions mentioned earlier.

   2. **Create a directory for libraries**:
      Create a directory to store your Arduino libraries if it doesn't already exist:
      ```cmd
      mkdir %HOMEPATH%\Documents\Arduino\libraries
      ```

   3. **Download the LoRa library**:
      Use `git` to clone the LoRa library repository into the libraries directory:
      ```cmd
      git clone https://github.com/sandeepmistry/arduino-LoRa.git %HOMEPATH%\Documents\Arduino\libraries\LoRa
      ```

   4. **Verify the installation**:
      You can verify that the library has been correctly added by listing the installed libraries with `arduino-cli`:
      ```cmd
      arduino-cli lib list
      ```

   5. **Use the library in your project**:
      - Create a new sketch or open an existing sketch.
      - Include the library in your code by adding:
        ```cpp
        #include <LoRa.h>
        ```

### Add the Board to be Used

   For the Arduino MKR WAN 1310, here are the commands:
   ```cmd
   arduino-cli core update-index
   arduino-cli core install arduino:samd
   ```

### Compile and Upload Your Code

   Use `arduino-cli` to compile and upload your code to your Arduino board. For example:
   ```cmd
   arduino-cli compile --fqbn arduino:samd:mkrwan1310 --output-dir %HOMEPATH%\Documents\Arduino\build --verbose "C:\path\to\your\sketch"
   arduino-cli upload --fqbn arduino:samd:mkrwan1310 --port COM3 --input-dir %HOMEPATH%\Documents\Arduino\build "C:\path\to\your\sketch"
   ```
   Replace `arduino:samd:mkrwan1310` with the Fully Qualified Board Name (FQBN) of your board and `COM3` with the appropriate serial port.

# Create a Project with a Batch File

   It is possible to compile multiple sketches that depend on each other using a batch file with arduino-cli. You can create a batch file to automate the compilation and uploading of multiple sketches. Here is an example of a batch file to compile and upload multiple sketches:

   ```bat
   @echo off
   setlocal

   REM Define the board and port
   set BOARD=arduino:samd:mkrwan1310
   set PORT=COM3

   REM Define the directories for the sketches
   set SKETCH_DIRS=C:\path\to\your\sketch1 C:\path\to\your\sketch2

   REM Define the output directory
   set OUTPUT_DIR=%HOMEPATH%\Documents\Arduino\build

   REM Define the arduino-cli command
   set ARDUINO_CLI=arduino-cli

   REM Compile all sketches
   for %%d in (%SKETCH_DIRS%) do (
       echo Compiling %%d...
       %ARDUINO_CLI% compile --fqbn %BOARD% --output-dir %OUTPUT_DIR% %%d
   )

   REM Upload all sketches
   for %%d in (%SKETCH_DIRS%) do (
       echo Uploading %%d...
       %ARDUINO_CLI% upload --fqbn %BOARD% --port %PORT% --input-dir %OUTPUT_DIR% %%d
   )

   REM Clean the output directory
   rmdir /S /Q %OUTPUT_DIR%

   endlocal
   ```

   To use this batch file, save it with a `.bat` extension (e.g., `compile_upload.bat`) and run it from the Command Prompt.

   1. **Compile all sketches**:
      ```cmd
      compile_upload.bat
      ```

   This batch file compiles and uploads all the sketches defined in the `SKETCH_DIRS` variable. You can add or remove sketch paths in this variable as needed.