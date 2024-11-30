## Back un in server

Aquí se explicará la configuración para la instancia final de la comunicación:

En primer lugar, la configuración del Gateway, dispositivo que utilizaremos para conectar nuestro Relay (que está al costado del río) con el Server (en internet).

En segundo lugar, la configuración del Server, necesaria para poder recibir y procesar la información, sin necesidad de ir al terreno.

## Configuración del Gateway (Robustel R3000 - LG4LA)

Los pasos a seguir para lograr una conexión satisfactoria con el Gateway son:
 
 0) Iniciar y conectarse al Gateway
 1) Actualizar Firmware y Aplicaciones
 2) Realizar la conexión a Onternet
 3) Configurar el tipo de conexión
 4) Configuraciones extra

Es **MUY IMPORTANTE** remarcar desde un inicio que, para el paso (2) en caso de tener cualquier tipo de problema es necesario hablar con la DSI de la escuela, específicamente con Riaz SYED, dado que la escuela bloquea todo tipo de conexiones que sean por fuera de los puertos más comunes. Con lo cual, solo ellos pueden habilitar las conexiones a Internet por puertos diferentes.

**Mail: riaz.syed@minesparis.psl.eu**

(Recomendamos fuertemente comunicarse con Riaz SYED ante cualquier eventualidad, nosotros comenzamos tarde a conversar con él y de haberlo hecho antes, hubieramos ganado mucho tiempo)

# Materiales

Los materiales que necesitaremos para realizar la conexión son:

- Una computadora que permita conexión vía ethernet (puede utilizarse la computadora del aula de Mines)
- Dos cables ethernet (uno para conectar el Gateway a la PC y otro para conectar a internet)
- Una antena
- Una fuente que provea entre 9 y 60V DC

# Paso 0 - Iniciar y conectarse al Gateway

Para comenzar, lo primero que debemos hacer es conectar a la fuente el Gateway.

Y luego debemos conectar los cables ethernet:
 - Puerto ETH1: conectarlo a la PC
 - Puerto ETH0: conectarlo a Internet

Realizado esto, ir a un navegador, y escribir en el buscador: 192.168.0.1

Esto debería darnos acceso a la interfaz online del Gateway.

Fallo en la conexión: si al ingresar la IP en el buscador no se encuentra la página, invertir la conexión de los cables en los puertos ethernet, esto probablemente solucione el error.

# Paso 1 - Actualizar Firmware y Aplicaciones

Lo que sigue es ingresar a la interfaz online del Gateway, para ello la clave y usuario serán:

Username: admin
Password: admin

![Interior view](Images/Robustel_login.jpg)

Una vez dentro, buscaremos la versión del Firmware y las aplicaciones:

- La versión del Firmware está dentro de la sección "Status", la cual se abre por defecto al ingresar a la interfaz online. Con lo cual, en la sección "System Information" podremos leer "Firmware Version".

![Interior view](Images/Firmware_version.jpg)

- La versión de las aplicaciones está dentro de la sección "System", en la sub-sección "App Center". Allí veremos una tabla llamada "Installed Apps", donde una de las columnas es "Version".

![Interior view](Images/App_version.jpg)

Ahora que conocemos las versiones instaladas en nuestro dispositivo, debemos ir a la siguiente página del proveedor:

https://rcms-cloud.robustel.net/rcms/index

En donde debemos crearnos una cuenta (con el mail de MINES es posible).

Una vez ingresando a la página, en la barra superior se encuentra una sección llamada "App Center". 

![Interior view](Images/Robustel_page.jpg)

Allí dentro tenemos tres secciones, de las cuales las que nos interesan son: Firmware y Robustos App.

En ambas secciones de interes, debemos filtrar por "Series", eligiendo la opción "R3000 LG Series". Y lo que haremos, sea en Firmware o en Robustos App, es ver cuál es la última versión disponible compatible con nuestro dispositivo.

![Interior view](Images/Uses_app_robustel.jpg)

Si la versión instalada que vimos antes coincide con la última versión disponible compatible con nuestro Gateway, aquí finaliza esta sección, puede pasar a la siguiente.

Si la versión instalada que vimos antes no coincide con la última versión disponible compatible con nuestro Gateway, lo que debemos hacer es lo siguiente:

Para el caso del Firmware, iremos a la sección "System", sub-sección "Update". Allí dentro iremos a la solapa "Firmware Update", allí cargaremos el archivo que hemos descargado, haciendo click en "Parcourir.." y luego actualizaremos haciendo click en "Update".

![Interior view](Images/update_firmware.jpg)

Para el caso de las aplicaciones, iremos nuevamente a la sección "System", sub-sección "App Center", y allí en la tabla "Installed Apps" debemos hacer lo siguiente:

Primero, hacer click sobre la cruz a la derecha, para eliminar las versiones instaladas.

![Interior view](Images/delete_apps.jpg)

Luego, cargar los archivos descargados para instalarlos. Para ellos, hacemos click en "Parcourir.." y luego instalamos haciendo click en "Install".

![Interior view](Images/put_apps.jpg)

# Paso 2 - Realizar la conexión a internet

Para verificar el acceso a internet, debemos volver a la sección "Status" de la interfaz online del Gateway y observar la parte de "Internet Status". Si se encuentra en blanco como en la siguiente imágen:

![Interior view](Images/status_internet.jpg)

Debemos realizar la configuración de la conexión, como se indica debajo.

Si vemos valores, como en la siguiente imágen:

![Interior view](Images/internet_connection.jpg)

Significa que la conexión está realizada. 

# Verificación utilizando Ping

Realizaremos la siguiente verificación por seguridad:

Iremos a la sección "System", sub-sección "Tools", y en la venta "Ping", debemos ingresar en IP Address el valor de: 8.8.8.8
Luego hacer click en "Start".

Si el mensaje que obtenemos es como el siguiente:

![Interior view](Images/ping_try.jpg)

Significa que la conexión no fue realizada con éxito, es necesario hablar con Riaz SYED, porque hay un problema de conexión y probablemente sea el Firewall de la escuela.

Si el mensaje que obtenemos es como el siguiente:

![Interior view](Images/ping_works.jpg)

La conexión fue realizada con éxito, no es necesario modificar ninguna configuración, se puede pasar a la siguiente sección.

# Configuración de la conexión

Para realizar la configuración de la conexión a internet, debemos ir a la sección "Interface", sub-sección "Ethernet".

Una vez allí, veremos una tabla llamada "Port Settings", en donde cada fila indica las características de cada puerto ethernet. Esta tabla debe verse como en la siguiente imágen:

![Interior view](Images/port_ethernet.jpg)

Donde lo más importante es lo que indica la columna "Port Assignment" para cada uno de los puertos.

En caso de no ver una tabla idéntica a la de arriba, lo que debemos hacer es:

En la fila del puerto "eth0" hacer click en el símbolo del lápiz que se encuentra a la derecha:

![Interior view](Images/pencil_eth0.jpg)

Esto nos abrirá una ventana llamada "Port Settings", donde lo que nos interesa es modificar el "Port Assignement", para lo cual debemos desplegar la lista de opciones y elegir "wan".

![Interior view](Images/port_assignement.jpg)

Luego, hacemos click en "Submit", y para finalizar, debemos hacer click en "Save & Apply" que lo visualizaremos de un color amarillo.

![Interior view](Images/save_apply.jpg)

Al hacer esto el gateway perdera la conexión a la computadora. Lo que debemos hacer es invertir la conexión de los cables ethernet en los puertos, siendo la nueva conexión la siguiente:

 - Puerto ETH1: conectarlo a la PC
 - Puerto ETH0: conectarlo a Internet

Una vez realizado esto, volveríamos a tener conexión a la interfaz online del Gateway, y conexión a internet. 

Para verificarlo, simplmenete por seguridad, pueden realizarse los pasos indicados anteriormente en la Verificación utilizando Ping.

# Paso 3 - Configurar el tipo de conexión

Aquí realizaremos la configuración del tipo de conexión que se establecerá entre la red y el Gateway.

Para ello debemos ir a la sección "Packet Forwarders", y lo primeros que debemos hacer es desactivar tanto "Loriot" como "Semtech UDP Forwarder" que no los utilizaremos. Para ellos ingresaremos en las correspondientes sub-secciones, y en donde dice "Enable" debemos verificar que esté indicado "OFF".

![Interior view](Images/off_semtech.jpg)

![Interior view](Images/loriot_off.jpg)

Una vez hecho esto, iremos a la sección "Basic Station" que es la de interes. Y allí la configuración necesaria es la siguiente:

![Interior view](Images/basic_station.jpg)

La información a completar es:

 -Server Address:eu1.cloud.thethings.network
 -Server Port: 8887

Y debe estar "ON" como se ve en la imágen: Enable, LoRaWan Public y TLS Enable.

Luego, debemos ir a la solapa "Cert Manager", y allí debemos subir el "CA Cert" y el "Client Key".

Para obtener el "CA Cert" debemos ir al siguiente link:

https://letsencrypt.org/certificates/

Y descargar el archivo que nos brinda la página al hacer click en "pem", como se indica en la siguiente imágen:

![Interior view](Images/root_pem.jpg)

Y para generar el "Client Key", debemos seguir los pasos que se indican en el siguiente tutorial:

https://www.thethingsindustries.com/docs/gateways/concepts/lora-basics-station/lns/

Con estos dos archivos descargados/generados, podemos subirlos a nuestro Gateway. Para ello debemos hacer click en "Parcourir" y luego en "Import".

![Interior view](Images/Cert_manager.jpg)

Y finalizar haciendo click en "Save & Apply", luego en "Reboot".

Para finalizar y que funcione, es necesario comunicarse 

# Paso 4 - Configuraciones extras

Aquí detallaremos algunas configuraciones adicionales que deben realizarse para un funcionamiento óptimo.

Una configuración adicional para el mejor funcionamiento del Gateway es modificar el NTP



## Server in The Things Stack SANDBOX

# Configuración del Server

En primer lugar, lo que debemos hacer es crearnos una cuenta en The Things Stack Network, para ellos ingresaremos en el siguiente link:

https://www.thethingsnetwork.org/

Y en la esquina superior derecha haremos click sobre "Login".

Luego, elegimos la opción "Login to The Things Network", y allí nos creamos una cuenta.

Una vez creada la cuenta, debemos ir al margen superior derecho donde figura el nombre que le pusimos a la cuenta, hacer click, y elegir la opción "Console". Allí, dentro de los "Existing Clusters" elegimos: Europe1

Recien aquí podemos empezar la configuración de los dispositivos, aplicaciones y Gateway, dentro del Server.

Lo primero que haremos será crear una aplicación, para ello, en el lado izquierdo veremos tres opciones: Home, Applications, Gateways.

Haciendo click en "Applications" y luego en el boton "Add application".

Le daremos un nombre a la aplicación, el que mas nos guste (por ejemplo:"Molonari-Proyect") y para finalizar click en "Create application".

Una vez creada la aplicación, dentro de ellas debemos registrar el "End evices", que para nuestro caso será el arduino que juega el rol del Relay. Para ello, en la columna del lado derecho, encontraremos la sección "End Devices", haremos click allí, y luego en "Register End Device".

Una vez dentro, elegiremos la opción "Enter end device specifics manually". Y en las opciones que nos dan pondremos:

Frequency plan: Europe 863-870 MHz (SF9 for RX2 - recommended)
LoRaWAN version: LoRaWAN Specification 1.0.3

Luego, dentro de la sección "Provisioning information":

JoinEUI: 00 00 00 00 00 00 00 00
DevEUI: el valor obtenido al utilizar el código "deveui" en el arduino que será nuestro Relay.
AppKey: la generaremos haciendo click en "Generate"
End device ID: le daremos el nombre que querramos (por ejemplo: Molonari-relay)

Finalizaremos presionando "Register end device"

Es IMPORTANTE remarcar aquí que los valores de JoinEUI, AppKey y DevEUI serán utilizados en el código del Relay para poder establecer conexión con el server, por lo cual, deben guardarse anotarse, para luego poder colocarlos en el código del Relay. Si estos parámetros no se modifican en el código, no se establecerá la conexión con el server.

Finalmente, debemos registrar el Gateway, para ello en la columna derecha cambiaremos de sección, y elegiremos la opción "Gateways". 

Una vez dentro, hacemos click sobre el boton "Register gateway". Allí debemos cargar:

Gateway EUI: este valor lo encontraremos en la interfaz online del Gateway, en la sección "Interface", sub-sección "LoRa", es el valor que allí se llama "Gateway ID".

Una vez registrado este valor, debemos confirmarlo, y luego completar:

Gateway ID: colocamos el nombre que querramos (por ejemplo: Molonari-Gateway)
Frequency plan: Europe 863-870 MHz (SF9 for RX2 - recommended)
Require authenticated connection: debemos marcar esta opción
Share gateway information: ambas opciones están marcadas por defecto, lo dejamos así.

Con todo esto realizado, tendremos nuestro Gateway y Arduino registrado, a la vez de nuestra aplicación creada.

# Utilización del server

Al haber finalizado el punto anterior, para





