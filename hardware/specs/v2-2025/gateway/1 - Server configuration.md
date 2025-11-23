# Data transit through the server

After having understood the Lora communication and managed to receive the data in our relay, we must continue with the following communication stages: *communicate with the gateway and send the information to the server*.

First, the configuration of the Server, through which the data will transit before being sent to the final molonari server (cf. the `molonari.io/Molonaviz/src/receiver` for the actual receiver). It's important to note that the data will NOT be stored on this server, only transit.

Second, the configuration of the Gateway, the device we will use to connect our Relay (which is next to the river) with the Server (on the internet).

For the server, we have chosen to use the TerraForma server located in Toulouse, in order to integrate our project (Molonari) in the same ecosystem as the other TerraForma projects. Their server used the Chirpstack technology, which allows to easily manage LoraWAN connections. 
However, if a problem occurs with the connection to this server (as we had during our project, when the server certificates had expired and had to wait until they were renewed), you can always refer to the previous documentation `3 - Backup option with TTN` where they used TheThingsNetwork (TTN), a propietary webservice that also allows to manage Lora devices. 


## Chirpstack gateway logic

In order to configure this server, you need an account to be able to edit in the `Sandbox` environment. We were in contact with nicolas.deschamps@cnrs-orleans.fr, who was also very responsive to help us at the beginning.
If he doesn't respond, currently the account we used was with armand.de_fontenay@etu.minesparis.psl.eu (send us an email to get the password).

Once you've got your email and password, go to https://lns.terra-forma-obs.fr, and enter your login information.

![Interior view](Images/chirpstack_login.png)

We will now add our Robustel gateway to our list of gateways (you'll normally have an empty list of gateways).

![Interior view](Images/chirpstack_gateways.png)

Now, you need the gateway ID, which means you need to start `2 - Gateway configuration` until you can connect to it (no need to update it to finish this part of the tutorial), both are intertwined but we decided to part the two manuals for clarity purposes.

You'll have to enter a name for your gateway, and then for the "Gateway ID (EUI64)" section, you'll need to go on the robustel configuration, and search for Interface/Lora/General Settings/Default Gateway ID (or User Defined ID if "User Defined Gateway ID Enable" is switched ON).

![Interior view](Images/obtain_gateway_id.png)

Come back to Chirpstack, and add the ID to the "Gateway ID (EUI64)" section, and then click the "Submit" button.

Go to the "TLS certificate" section, and then click on "Generate certificate".

![Interior view](Images/chirpstack_generate_certificates1.png)

You'll have three fields with different keys or certificates, that all use the same structure:

-----BEGIN CERTIFICATE----- (or -----BEGIN PRIVATE KEY-----)
the certificate information
-----END CERTIFICATE----- (or -----END PRIVATE KEY-----)

You'll create three text files on your computer where you will copy each one of the texts (including the --BEGIN ...-- and -END ...-). Save the file where you have copied the "CA certificate" as 'ca.crt', the one for "TLS certificate" as 'cert.crt', and the "TLS key" as 'cert.key'.

Now go to the router web, we will now be able to add our certificates. To do this, we must click on "Browse" and then on "Import" (note that the they are in the same order as in the Chirpstack page: CA cert corresponds to CA certificate, Client Cert to TLS certificate and  Client Key to TLS key).

![Interior view](Images/robustel_adding_certificates.png)

You will see how they progressively appear on the "Certificate files" section.

Click now on "Submit" and on "Save & Apply" and you should be good to go.

## Chirpstack application

We now need to be able to add devices to Chirpstack, so that it will try to listen to what our Arduino card is gonna send. For that, go to the "Applications" section in the left menubar. Then to "Add application". Give it a recognisable name. Then go to "Add device". Enter the fields with a *.

![adding new sensor](Images\chirpstack_adding_sensor.png)

Know that the most important one is the "Device EUI" one. To know which one is your DevEUI, you can run a simple Arduino script that includes:

``` Arduino
#include <MKRWAN.h>
LoRaModem modem;

void setup() {
  Serial.begin(9600);
  while (!Serial);

  if (!modem.begin(EU868)) {  // Pour l’Europe : EU868
    Serial.println("Échec d'initialisation du modem LoRa !");
    while (true);
  }

  Serial.print("DevEUI : ");
  Serial.println(modem.deviceEUI());
}

void loop() {}
```

Then click on "Submit". You'll be sent to a page where you have to configure the Appkey. This is a key that you choose in your Arduino code, and you need to make sure both match.

![sensor appkey](Images\chirpstack_sensor_appkey.png)

Your Chirpstack is now ready to receive the information sent by your Arduino. To see the messages, go to the "Events" page inside your choosen device.

You'll see the "join" entries whenever you make a 'modem.joinOTAA(appEui, appKey);' entry on your Arduino code, and "up" entries whenever you send a message from your Arduino, as seen in the screenshot:

![see messages](Images/chirpstack_seeing_messages.png)

To see the content of the message, click on the "up" button, and then search for the data:"sample message encoded in Base64" section. The message has been encoded in Base64. If, when sent in the Arduino code, it was a plain string variable, you'll be able to easily decode it with a simple python code for example, but for this project we decided to encode our data using the ProtoBuf libraries as the TerraForma ecosystem generally uses that payload format. You'll be able to decode this with the code given in this repo (check the `decoder.py` and `sensor_pb2.py` in the `Molonaviz/src/receiver/ directory).