

# Materials

The materials we will need are:

- A computer
- Two ethernet cables (one to connect the Gateway to the PC and another to connect to the internet)
- An antenna
- A power supply that provides between 9 and 60V DC
- An Ethernet to USB adapter if your computer does not have an Ethernet port

# Gateway Configuration (Robustel R3000 - LG4LA)

The steps to achieve a satisfactory connection with the Gateway are:

0) Start and connect to the Gateway
1) Update Firmware and Applications
2) Establish the internet connection
3) Configure the connection type
4) Extra configurations
5) Error visualization

It is **VERY IMPORTANT** to emphasize from the beginning that, for step (2) if you have any kind of problem, it is necessary to talk to the school's IT department, specifically with Riaz SYED, since the school blocks all types of connections outside the most common ports. Therefore, only they can enable internet connections through different ports.

**Email: riaz.syed@minesparis.psl.eu**

(We strongly recommend contacting Riaz SYED in case of any eventuality, we started talking to him late and if we had done it earlier, we would have saved a lot of time)

## Step 0 - Start and connect to the Gateway

To start, the first thing we need to do is connect the Gateway to the power supply.

Then we need to connect the ethernet cables:
- ETH1 port: connect it to the PC
- ETH0 port: connect it to the Internet

Once this is done, go to a browser and type in the search bar: 192.168.0.1

This should give us access to the Gateway's online interface.

Connection failure: if entering the IP in the browser does not find the page, reverse the connection of the cables in the ethernet ports, this will probably solve the error.

## Step 1 - Update Firmware and Applications

Next, we need to log in to the Gateway's online interface, for which the username and password will be:

- Username: admin
- Password: molonari1D (or admin if it reset)

![Interior view](Images/Robustel_login.png)

Once inside, we will look for the Firmware and applications version.

The Firmware version is in the "Status" section, which opens by default when entering the online interface. Therefore, in the "System Information" section, we can read "Firmware Version".

![Interior view](Images/Firmware_version.png)

The applications version is in the "System" section, in the "App Center" sub-section. There we will see a table called "Installed Apps", where one of the columns is "Version".

![Interior view](Images/App_version.png)

Now that we know the versions installed on our device, we need to go to the following provider page:

https://rcms-cloud.robustel.net/rcms/index

Where we need to create an account (with the MINES email it is possible).

Once logged into the page, in the top bar there is a section called "App Center".

![Interior view](Images/Robustel_page.png)

Inside there, we have three sections, of which the ones we are interested in are: Firmware and RobustOS App.

In both sections of interest, we must filter by "Series", choosing the option "R3000 LG Series". And what we will do, whether in Firmware or RobustOS App, is to see what is the latest available version compatible with our device.

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

## Step 2 - Establish the internet connection

To verify internet access, we need to go back to the "Status" section of the Gateway's online interface and observe the "Internet Status" part. If it is blank as in the following image:

![Interior view](Images/status_internet.png)

We need to configure the connection as indicated below.

If we see values, as in the following image:

![Interior view](Images/internet_connection2.png)

It means the connection is established. We can skip the next section and go directly to Verification using Ping.

### Connection configuration

To configure the internet connection, we need to go to the "Interface" section, "Ethernet" sub-section.

Once there, we will see a table called "Port Settings", where each row indicates the characteristics of each ethernet port. This table should look like the following image:

![Interior view](Images/port_ethernet.png)

Where the most important thing is what the "Port Assignment" column indicates for each of the ports.

If you do not see a table identical to the one above, what we need to do is:

In the row of the "eth0" port, click on the pencil symbol on the right:

![Interior view](Images/pencil_eth0.png)

This will open a window called "Port Settings", where what we are interested in is modifying the "Port Assignment", for which we must display the list of options and choose "wan".

![Interior view](Images/port_assignement.png)

Then, click on "Submit", and to finish, we must click on "Save & Apply" which we will see in yellow.

![Interior view](Images/save_apply.png)

By doing this, the gateway will lose connection to the computer. What we need to do is reverse the connection of the ethernet cables in the ports, being the new connection as follows:

- ETH1 port: connect it to the PC
- ETH0 port: connect it to the Internet

Once this is done, we would have a connection to the Gateway's online interface again, and an internet connection.

To verify it, for safety, the steps indicated in Verification using Ping must be performed.

### Verification using Ping

We will perform the following verification for safety:

We will go to the "System" section, "Tools" sub-section, and in the "Ping" window, we must enter the value: 8.8.8.8 in IP Address.
Then click on "Start".

If the message we get is like the following:

![Interior view](Images/ping_try.png)

It means the connection was not successful, it is necessary to talk to Riaz SYED, because there is a connection problem and it is probably the school's Firewall.

If the message we get is like the following:

![Interior view](Images/ping_works.png)

The connection was successful, no configuration changes are necessary, you can move on to the next section.

## Step 3 - Configure the connection type

Here we will configure the type of connection that will be established between the network and the Gateway.

To do this, we must go to the "Packet Forwarders" section, and the first thing we need to do is disable "Semtech UDP Forwarder" which we will not use. To do this, we will enter the corresponding sub-section, and where it says "Enable" we must verify that it is indicated "OFF".

![Interior view](Images/off_semtech_2.png)

Once this is done, we will go to the "Basic Station" section which is of interest. And there the necessary configuration is as follows:

![Interior view](Images/basic_station2.png)

The information to complete is:

- Server Address: terra-forma-obs.fr
- Server Port: 10080

And it must be "ON" as seen in the image: Enable, LoRaWan Public, and TLS Enable.

Then, we must go to the "Cert Manager" tab, and there we must upload the "CA Cert" and the "Client Key".

We must now upload the correct Certificates to be able to connect to our server. However, we first need to configure the gateway on Chirpstack, as it's from that platform that we'll get the certificates.

## Step 5 - Error visualization

To visualize if there are errors, or what type of errors we are having, we must use the "Debug" tab.

To do this, we will go to the "System" section, "Debug" sub-section, and then click on the "Refresh" button to see the logs of the gateway.

![Interior view](Images/debug.png)


## Step 6 - Extra configurations

Here we will detail some additional configurations that must be made for optimal operation, or in case you encounter some problems.

An additional configuration for the better operation of the Gateway is to modify the NTP. To do this, we must go to the "Services" section, "NTP" sub-section.

There we will modify the "Time Zone" to: "UTC+01:00"

And in "NTP Client Setting", we must set "Enable" to "ON", and in "Primary NTP Server" the IP will be: pool.ntp.org

The configuration will be:

![Interior view](Images/ntp_config.png)

Here we need to contact Riaz SYED again, because to access this server we need to enable UDP Port 123. Therefore, we must send him an email with the information:

- Server Address: pool.ntp.org
- Server Port: 123

To enable this server.

Another additional configuration, to avoid unnecessary error messages, is to disable the GPS that we will not use, for that we will go to the "Services" section, "GPS" sub-section, and disable all options:

![Interior view](Images/gps_off.png)