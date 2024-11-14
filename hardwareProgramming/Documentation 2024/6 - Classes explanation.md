# Understanding our classes
As a common point among all the classes used in the project, it begins by verifying that the file has not been imported before by creating an include guard, which is a common practice in C++ to prevent a file from being imported multiple times. Then, we import the libraries or other classes that we need for the current class. In the MOLONARI project, we have the following classes:

**Lora:**

**Low_power:**
**Mesure_Cache:**
**Measure:**
**Pressure_Sensor:**
**Reader:**
**SD_Initializer:**
This file will contain all the code to initialise the SD card and the CSV file. En esta clase se define un encabezado (header) que establece los nombres de las columnas en el archivo CSV, permitiendo que las mediciones se registren con un formato claro y estructurado.

* Función bool AlreadyInitialised: Esta función verifica si el archivo CSV ya ha sido creado y contiene datos. Si el archivo no existe, devuelve false. Si existe, se abre y se comprueba si tiene contenido, cerrando el archivo después de la verificación. Esto garantiza que no se sobrescriban datos importantes.

* Función bool InitialiseLog: La función principal para inicializar la tarjeta SD y el archivo CSV. Primero, intenta inicializar la tarjeta SD y si falla, devuelve false. Si la tarjeta se inicializa correctamente y el archivo CSV aún no existe, se crea uno nuevo, se escribe el encabezado y se cierra el archivo. Finalmente, si la inicialización es exitosa, devuelve true.

**Temp_Sensor:**
**Time:**
**Waiter:**
**Writer:**





