## Backup on server

Here we will explain the configuration for the final instance of communication:

First, the configuration of the Gateway, the device we will use to connect our Relay (which is next to the river) with the Server (on the internet).

Second, the configuration of the Server, necessary to receive and process the information without needing to go to the field.

## Gateway Configuration (Robustel R3000 - LG4LA)

The steps to achieve a successful connection with the Gateway are:

0) Start and connect to the Gateway
1) Update Firmware and Applications
2) Connect to the Internet
3) Configure the connection type
4) Extra configurations

It is **VERY IMPORTANT** to emphasize from the beginning that, for step (2) in case of any problem, it is necessary to talk to the school's IT department, specifically with Riaz SYED, as the school blocks all connections outside the most common ports. Therefore, only they can enable Internet connections through different ports.

**Email: riaz.syed@minesparis.psl.eu**

(We strongly recommend contacting Riaz SYED in case of any eventuality, we started talking to him late and if we had done it earlier, we would have saved a lot of time)

# Materials

The materials we will need to make the connection are:

- A computer that allows ethernet connection (the classroom computer at Mines can be used)
- Two ethernet cables (one to connect the Gateway to the PC and another to connect to the internet)
- An antenna
- A power source that provides between 9 and 60V DC

# Step 0 - Start and connect to the Gateway

To begin, the first thing we need to do is connect the Gateway to the power source.

Then we need to connect the ethernet cables:
- ETH1 port: connect it to the PC
- ETH0 port: connect it to the Internet

After this, go to a browser and type in the search bar: 192.168.0.1

This should give us access to the Gateway's online interface.

Connection failure: if the page is not found when entering the IP in the browser, reverse the connection of the cables in the ethernet ports, this will probably solve the error.

# Step 1 - Update Firmware and Applications

Next, we need to log in to the Gateway's online interface, for which the username and password will be:

Username: admin
Password: admin

![Interior view](Images/Robustel_login.png)

Once inside, we will look for the Firmware and applications version:

- The Firmware version is in the "Status" section, which opens by default when entering the online interface. Therefore, in the "System Information" section, we can read "Firmware Version".

![Interior view](Images/Firmware_version.png)

- The applications version is in the "System" section, in the "App Center" sub-section. There we will see a table called "Installed Apps", where one of the columns is "Version".

![Interior view](Images/App_version.png)

Now that we know the versions installed on our device, we need to go to the following provider page:

https://rcms-cloud.robustel.net/rcms/index

Where we need to create an account (with the MINES email it is possible).

Once logged in to the page, in the top bar there is a section called "App Center".

![Interior view](Images/Robustel_page.png)

Inside there, we have three sections, of which the ones we are interested in are: Firmware and RobustOS App.

In both sections of interest, we must filter by "Series", choosing the "R3000 LG Series" option. And what we will do, whether in Firmware or RobustOS App, is to see what the latest available version compatible with our device is.

![Interior view](Images/Uses_app_robustel.png)

If the installed version we saw before matches the latest available version compatible with our Gateway, this section ends here, you can move on to the next one.

If the installed version we saw before does not match the latest available version compatible with our Gateway, what we need to do is the following:

For the Firmware case, we will go to the "System" section, "Update" sub-section. Inside there, we will go to the "Firmware Update" tab, where we will upload the file we downloaded, by clicking on "Browse.." and then update by clicking on "Update".

![Interior view](Images/update_firmware.png)

For the applications case, we will go again to the "System" section, "App Center" sub-section, and there in the "Installed Apps" table we need to do the following:

First, click on the cross on the right to delete the installed versions.

![Interior view](Images/delete_apps.png)

Then, upload the downloaded files to install them. To do this, click on "Browse.." and then install by clicking on "Install".

![Interior view](Images/put_apps.png)

# Step 2 - Connect to the internet

To verify internet access, we need to go back to the "Status" section of the Gateway's online interface and observe the "Internet Status" part. If it is blank as in the following image:

![Interior view](Images/status_internet.png)

We need to configure the connection as indicated below.

If we see values, as in the following image:

![Interior view](Images/internet_connection.png)

It means the connection is made. We can skip the next section and go directly to Verification using Ping.

# Connection configuration

To configure the internet connection, we need to go to the "Interface" section, "Ethernet" sub-section.

Once there, we will see a table called "Port Settings", where each row indicates the characteristics of each ethernet port. This table should look like the following image:

![Interior view](Images/port_ethernet.png)

Where the most important thing is what the "Port Assignment" column indicates for each of the ports.

If we do not see an identical table to the one above, what we need to do is:

In the row of the "eth0" port, click on the pencil symbol on the right:

![Interior view](Images/pencil_eth0.png)

This will open a window called "Port Settings", where what we are interested in is modifying the "Port Assignment", for which we need to drop down the list of options and choose "wan".

![Interior view](Images/port_assignement.png)

Then, click on "Submit", and to finish, we need to click on "Save & Apply" which we will see in yellow.

![Interior view](Images/save_apply.png)

By doing this, the gateway will lose the connection to the computer. What we need to do is reverse the connection of the ethernet cables in the ports, being the new connection as follows:

- ETH1 port: connect it to the PC
- ETH0 port: connect it to the Internet

Once this is done, we would have a connection to the Gateway's online interface again, and an internet connection.

To verify it, for security, the steps indicated in Verification using Ping must be performed.

# Verification using Ping

We will perform the following verification for security:

We will go to the "System" section, "Tools" sub-section, and in the "Ping" window, we need to enter the value: 8.8.8.8 in IP Address
Then click on "Start".

If the message we get is like the following:

![Interior view](Images/ping_try.png)

It means the connection was not successful, it is necessary to talk to Riaz SYED, because there is a connection problem and it is probably the school's Firewall.

If the message we get is like the following:

![Interior view](Images/ping_works.png)

The connection was successful, no configuration modification is necessary, you can move on to the next section.

# Step 3 - Configure the connection type

Here we will configure the type of connection that will be established between the network and the Gateway.

To do this, we need to go to the "Packet Forwarders" section, and the first thing we need to do is disable both "Loriot" and "Semtech UDP Forwarder" which we will not use. To do this, we will enter the corresponding sub-sections, and where it says "Enable" we need to verify that it is indicated "OFF".

![Interior view](Images/off_semtech.png)

![Interior view](Images/loriot_off.png)

Once this is done, we will go to the "Basic Station" section which is of interest. And there the necessary configuration is as follows:

![Interior view](Images/basic_station.png)

The information to complete is:

- Server Address: eu1.cloud.thethings.network
- Server Port: 8887

And it must be "ON" as seen in the image: Enable, LoRaWan Public, and TLS Enable.

Then, we need to go to the "Cert Manager" tab, and there we need to upload the "CA Cert" and the "Client Key".

To obtain the "CA Cert" we need to go to the following link:

https://letsencrypt.org/certificates/

And download the file provided by the page by clicking on "pem", as indicated in the following image:

![Interior view](Images/root_pem.png)

And to generate the "Client Key", we need to follow the steps indicated in the following tutorial:

https://www.thethingsindustries.com/docs/gateways/concepts/lora-basics-station/lns/

With these two files downloaded/generated, we can upload them to our Gateway. To do this, we need to click on "Browse" and then on "Import".

![Interior view](Images/Cert_manager.png)

And finish by clicking on "Save & Apply", then on "Reboot".

Finally, it is necessary to contact Riaz SYED to request that the selected port associated with the server's IP address be enabled. Therefore, we need to send him an email with:

- Server Address: eu1.cloud.thethings.network
- Server Port: 8887

And once Riaz SYED confirms that it has been enabled, we will consider this section finished.

# Step 4 - Extra configurations

Here we will detail some additional configurations that must be made for optimal operation.

An additional configuration for the better operation of the Gateway is to modify the NTP

## Server in The Things Stack SANDBOX

# Server Configuration

First, what we need to do is create an account on The Things Stack Network, for this we will enter the following link:

https://www.thethingsnetwork.org/

And in the upper right corner, click on "Login".

Then, we choose the option "Login to The Things Network", and there we create an account.

Once the account is created, we need to go to the upper right margin where the name we gave to the account appears, click, and choose the "Console" option. There, within the "Existing Clusters" we choose: Europe1

Only here can we start configuring the devices, applications, and Gateway, within the Server.

The first thing we will do is create an application, for this, on the left side we will see three options: Home, Applications, Gateways.

Clicking on "Applications" and then on the "Add application" button.

We will give the application a name, whichever we like (for example: "Molonari-Project") and to finish click on "Create application".

Once the application is created, within it we must register the "End devices", which in our case will be the Arduino that plays the role of the Relay. For this, in the right column, we will find the "End Devices" section, click there, and then on "Register End Device".

Once inside, we will choose the option "Enter end device specifics manually". And in the options given we will put:

Frequency plan: Europe 863-870 MHz (SF9 for RX2 - recommended)
LoRaWAN version: LoRaWAN Specification 1.0.3

Then, within the "Provisioning information" section:

JoinEUI: 00 00 00 00 00 00 00 00
DevEUI: the value obtained by using the "deveui" code in the Arduino that will be our Relay.
AppKey: we will generate it by clicking on "Generate"
End device ID: we will give it the name we want (for example: Molonari-relay)

We will finish by pressing "Register end device"

It is IMPORTANT to emphasize here that the values of JoinEUI, AppKey, and DevEUI will be used in the Relay code to establish a connection with the server, so they must be saved and noted, to later place them in the Relay code. If these parameters are not modified in the code, the connection with the server will not be established.

Finally, we must register the Gateway, for this in the right column we will change the section, and choose the "Gateways" option.

Once inside, click on the "Register gateway" button. There we must load:

Gateway EUI: this value will be found in the Gateway's online interface, in the "Interface" section, "LoRa" sub-section, it is the value called "Gateway ID".

Once this value is registered, we must confirm it, and then complete:

Gateway ID: we put the name we want (for example: Molonari-Gateway)
Frequency plan: Europe 863-870 MHz (SF9 for RX2 - recommended)
Require authenticated connection: we must check this option
Share gateway information: both options are checked by default, we leave it that way.

With all this done, we will have our Gateway and Arduino registered, as well as our application created.

# Using the server

Having finished the previous point, to





