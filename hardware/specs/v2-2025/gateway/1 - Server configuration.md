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

Explanation to add the Application (with the relay, and gateway).
