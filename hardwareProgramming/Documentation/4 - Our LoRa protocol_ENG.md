# **A Journey Through Building a LoRa-Based Local Communication Protocol**

## 1. **Introduction**

Picture a cluster of sensors scattered in and around a river. Some are submerged, measuring water temperature and pressure; others rest above the surface, monitoring additional conditions. All these sensors need to send their data to a single relay device no more than 100 meters away. Sounds straightforward, right? But here’s the twist: these sensors are battery-powered and need to run for months—or even years—without intervention.

We needed a solution that could:

- **Handle signal transmission through water and across the water-to-air boundary**, a challenge many standard wireless technologies struggle with.
- **Conserve power** to maximize the sensors’ operational lifespan on a single battery charge.
- **Scale seamlessly**, ensuring that the design could accommodate future deployments with additional clusters forming part of a larger network.

This is where **LoRa** technology came into play. LoRa, short for “Long Range,” became the cornerstone of our solution. It provides a highly efficient physical communication layer, excelling in **low-power, long-range, and low-frequency communication**—all of which are critical to our system’s success.

But LoRa is just the foundation. While it solves the problem of transmitting data at the physical layer, it doesn’t provide the coordination or structure our system requires. That’s where our custom **local communication protocol** steps in. Built on top of LoRa, this protocol ensures seamless communication between all sensors (powered by **Arduino MKR WAN 1310** devices) and the central relay device (also an **Arduino MKR WAN 1310**).

This document is your guide to understanding how this protocol works, why it’s designed the way it is, and how future developers can build on it to continue our vision.

![Communication view](Images\Chaine_informations.jpg)

## 2. **Project Goals**

The primary goal of this part of the project is simple: **design a reliable and efficient local communication network protocol** that works seamlessly in challenging environments like rivers. However, achieving this required meeting a few specific objectives:

### a. **Reliable Data Transmission**

- Ensure that data collected by sensors is accurately transmitted to the relay device without significant losses or corruption.
- Handle various potential issues, like packet loss or temporary communication failures, with retry mechanisms and acknowledgments.

### b. **Power Efficiency**

- Since the system is battery-powered, the protocol must minimize energy consumption. This means reducing idle listening times for sensors and using low-power technology like LoRa.

### c. **Adaptability to Field Conditions**

- Address the unique challenges of signal transmission through water and the water-to-air boundary.
- Create a system that can operate effectively in both submerged and surface-level conditions.
  -Develop strategies for handling flood scenarios, which are common in the target environment and may disrupt communication for several days. The system should recover seamlessly once conditions stabilize.

### d. **Scalability for Future Needs**

- Design the protocol so it can scale up to support additional sensors or be integrated into a larger network. This includes allowing multiple clusters of sensors and relays to interconnect in future deployments.

### e. **Simple and Maintainable Design**

- The protocol and its implementation should be straightforward enough for future developers to understand, modify, and expand without excessive complexity.

### f. **Tested and Proven in Real-World Conditions**

- Validate the protocol’s performance in the same type of environment it’s intended to operate in—rivers with real-world obstacles and distances.

By meeting these goals, this system provides a robust foundation for monitoring water conditions, conserving energy, and enabling future growth.

## **3. System Overview**

This section provides a clear picture of the system’s architecture, the roles of its components, and how they work together to achieve the project’s goals.

### **3.1. Components**

- **Sensors**:

  - Devices that measure environmental parameters such as temperature and pressure. Each sensor is an **Arduino MKR WAN 1310**, equipped with a LoRa module for communication.
  - Operate in low-power mode and wake only when it’s time to transmit data.

- **Relay Device**:

  - An **Arduino MKR WAN 1310** acting as the central hub. It manages communication with all sensors, collects their data, and forwards it to the server.
  - Responsible for ensuring data integrity and managing the communication schedule.

- **Communication Protocol**:
  - A custom protocol built over the LoRa physical layer to handle the interaction between sensors and the relay.
  - Ensures secure, reliable, and energy-efficient communication.

### **3.2. How It Works**

1. **Data Collection**:

   - Sensors collect data from the field at regular intervals every 15 min (e.g., temperature and pressure).
   - Each sensor stores its data locally until it’s time to transmit. (in our prototype the temperature senser transmit one time per day at 23:45 , and for the other sensors you can adjust a deferent time)

2. **Scheduled Communication**:

   - Sensors and the relay communicate in one-to-one sessions according to a predefined schedule.
   - Each session begins with a **three-way handshake**, where the sensor “wakes up” and establishes a secure comunication link with the relay.

3. **Data Transmission**:

   - Sensors send data packets to the relay, which acknowledges receipt (ACK).
   - If ACK isn't received, sensors retry transmission up to six times, with increasing delay intervals.

4. **Relay to Server**:
   - Once data is collected, the relay device prepares it for transmission to the server. This step is outside the scope of this documentation.

### **3.3. System Topology**

- The network is based on a **tree topology**, which is scalable and cost-efficient.

### **Why Tree Topology?**

- **Reduces Costs**: Minimizes the number of expensive gateways by allowing one gateway to collect data from multiple networks.
- **Extends Coverage**: Enables the use of intermediate relays (repeaters) to connect distant sensors, especially in hard-to-reach locations.
- **Scalable**: Easily integrates new sensors or relays into the structure, making it ideal for larger deployments.

![Visualisation 1](Images\download.png)

### **Current Implementation**

- Currently, the system uses a **star topology**, a simplified case of the tree structure:
  - A single relay device directly manages all sensors.
  - Suitable for small-scale deployments and initial testing.

### **Future Scalability**

  - The design supports transitioning to a tree topology, where:
  - Multiple relays act as intermediate nodes.
  - One gateway collects data from several connected networks.

  ![Visualisation 1](Images\tree_topology.png)

This flexibility ensures the system can grow while maintaining reliability and minimizing costs.

## 4. **Protocol Design: Data Packet Structure and Communication Process**

### **Data Packet Structure**

The protocol’s data packets are designed to be lightweight, efficient, and include essential information for communication and error checking. Below is the structure:

| **Field Name**    | **Size**        | **Description**                                                             |
| ----------------- | --------------- | --------------------------------------------------------------------------- |
| **Checksum**      | 8 bits (1 byte) | Ensures data integrity by verifying the packet.                             |
| **Destination**   | 8 bits (1 byte) | Address of the receiving device.                                            |
| **Local Address** | 8 bits (1 byte) | Address of the sending device.                                              |
| **Packet Number** | 8 bits (1 byte) | Sequential number to track packet order.                                    |
| **Request Type**  | 8 bits (1 byte) | Type of the request (e.g., data, control).                                  |
| **Payload**       | Variable        | Contains the actual data or commands (max ~200 bytes, typically ~50 bytes). |

#### **Example**:

A typical packet from a sensor might look like this:

- **Checksum**: `0xa5` (calculated checksum value).
- **Destination**: `0x01` (relay address).
- **Local Address**: `0x05` (sensor address).
- **Packet Number**: `0x02` (second packet in the sequence).
- **Request Type**: `0xc3` (data transfer request).
- **Payload**: ("2024-11-07,10:00:12,21.55,22.11,21.99,21") the data.

Each field is processed sequentially during transmission, ensuring reliability and traceability.

### **Communication Sessions**

#### **Triggering Communication**

- **Initiator**: Sensors initiate communication to conserve power and maintain scheduling.
- **Scheduling Control**: Currently resides with the sensors via their real-time clocks. While the relay could control scheduling, it would require real-time capabilities, increasing costs unnecessarily.

#### **Three-Way Handshake**

Communication begins with a handshake process:

1. **Sensor → Relay**: Sensor sends a SYN (synchronize) message to request a session.
2. **Relay → Sensor**: Relay responds with a SYN-ACK message, acknowledging the request.
3. **Sensor → Relay**: Sensor confirms with an ACK, completing the handshake.

**Payload Use in Handshake (Future Opportunities)**:  
The **Relay → Sensor** packet's payload (currently empty) can include backward-propagation messages, enabling the relay to send control or information requests to the sensor. Examples:

1. **Real-Time Request**: Sync the relay’s schedule with the sensor’s clock.
2. **Delete Data Request**: Clear sensor’s old data.
3. **Battery Status**: Report remaining battery life.
4. **Mode Change**: Switch between normal and fast modes (e.g., send data more frequently).
5. **Rescheduling**: Adjust the sensor’s communication schedule.

**Handling Multiple Backward Messages**:

- Messages can be stacked in a structure (e.g., a queue).
- Each message is processed sequentially in the sensor.

##### **Ensuring Data Acknowledgment**

The handshake also provides the opportunity to confirm whether data from the previous session successfully reached the server. For example:

- Relay includes a "shift number" in the packet number field, indicating the number of unacknowledged packets by the server from the previous session (i.e. the session of yesterday)

This streamlined process ensures reliable communication while allowing flexibility for future enhancements.

## 5. **Problems Faced During Implementation**  


1. **Understanding the 2023 Codebase**:  
   - **Issue**: The inherited code was difficult to comprehend due to condensed functions, poor modularization, and a lack of task separation.  
   - **Solution**: The functions were divided into smaller subfunctions, making it easier to assign specific tasks to group members and to maintain the code in the future.  

2. **Lack of ACK Mechanism**:  
   - **Issue**: The previous design lacked acknowledgment (ACK) for data packets, risking loss of critical information during communication.  
   - **Solution**: We introduced an ACK mechanism with retries (up to 6 attempts) to confirm successful transmission.  

3. **Sensor-Initiated Communication**:  
   - **Issue**: Communication was initiated by the relay, requiring sensors to keep their LoRa module in constant listening mode, which drained their battery.  
   - **Solution**: Redesigned the protocol so sensors initiate communication, significantly reducing power consumption by allowing sensors to sleep when idle.  

4. **LoRa Functions Not Organized in a Class**:  
   - **Issue**: LoRa-related functions were scattered and not encapsulated in a class. This made the code harder to maintain and extend.  
   - **Solution**: Created a dedicated `LoraCommunication` class to manage all LoRa-related tasks. The class includes variables like `destination`, `localAddress`, and `myNet` (a set of authorized sensor addresses) to centralize and optimize functionality.  

5. **Handling Multiple Sensors Simultaneously**:  
   - **Issue**: The system struggled when two sensors tried to communicate with the relay simultaneously.  
   - **Solution**: Introduced a `destination` address variable in the `LoraCommunication` class to ensure the relay only interacts with one sensor at a time. The `isValidDestination` function was updated to manage connections properly.  

6. **LoRa Library Limitations**:  
   - **Issue**: The LoRa library had compatibility issues with Arduino MKR WAN 1310. For example, the `enableCRC()` function was non-functional without low-level adjustments, and packet-sending bugs occasionally caused devices to “hear” their own transmissions.
   - The interrupt mode for receiving data (developed by the LoRa library) wasn’t compatible with our device. This mode  could allow the relay to sleep and wake upon receiving a message, drastically improving battery life. 
   - **Solution**:  
     - Implemented a custom checksum function.  
     - Increased the retry count to 6 and added longer delays between retries, which seemed to help clear the device's receive buffer.  
     - Addressed serial monitor connectivity issues by uploading a minimal “Hello World” program to reset the device before uploading the main code. 
     -While we couldn’t use the LoRa library’s interrupt mode, we recommend exploring manual adjustments or using functions from other libraries like MKRWAN. Enabling interrupt-based wake-up would let the relay sleep between messages, significantly extending battery life. 

7. **Frequent SD File Access**:  
   - **Issue**: Frequent file access to read data from the SD card increased the risk of communication failures with the card.  
   - **Solution**: Minimized SD card access by queuing all data in memory for a single read operation, reducing both delay and potential file corruption risks.  

8. **Cursor Management in the Reader Class**:  
   - **Issue**: The cursor for the data file was updated based on ACKs from the relay, which only confirmed successful receipt at the relay—not at the server.  
   - **Solution**: Incorporated a mechanism to track acknowledgment at the server level using a backward propagation strategy via the `shift` parameter in the handshake process.  

9. **Addressing Design**:  
   - **Issue**: Addressing lacked a structured approach, complicating downlink (server-to-sensor) communication in a tree topology.  
   - **Solution**: Developed an address-masking scheme similar to IP addressing. While not implemented in the prototype, the system was designed to accommodate this feature for future scalability.  


---

#### **Quirks and Workarounds**  

- **SD File Access**: Frequent file reads increased the risk of losing communication with the SD card. Switching to memory-based queuing solved this issue effectively.  
- **USB Sensitivity**: Occasionally, the LoRa library caused connection issues with the serial monitor. Switching USB cables or uploading a simpler code resolved the problem, though it required patience.  

---

#### **Unresolved Issues and Recommendations**  

1. **Backward Data Propagation**:  
   - While the backward propagation mechanism is partially implemented, it requires further development for robust use in large-scale deployments.  

2. **Advanced Scheduling**:  
   - Currently, sensors manage their own schedules. A more efficient system would involve the relay taking over scheduling responsibilities.  

3. **Flood Recovery**:  
   - The system needs strategies for recovering from extended outages caused by floods or other natural disasters.
   - Maybe by increasing the number of sessions per day.   

4. **Address Masking in Practice**:  
   - Although the addressing scheme supports masking for tree topology, it remains untested and requires validation in a real-world setup.  
5. **Power Efficiency for the Relay**
  -Interrupt Mode for the Relay: Fixing or implementing interrupt-based reception for the relay is a high-priority task for future teams.

This iterative process of problem-solving has improved the protocol’s reliability and efficiency while laying a solid foundation for future development and scalability.

---
### **6. Testing and Results**
---

#### **How the System Was Tested**  

Testing during development often felt like solving a live puzzle. Our primary approach was to write small, focused test scripts using the `LoraCommunication` class. These scripts, found in the *example transmission LoRa* files, allowed us to simulate various scenarios with non-real data. This lightweight and modular strategy enabled us to quickly tweak and debug the protocol without needing to deploy the entire system every time.

We can’t stress enough how valuable this technique is for development. It kept the process nimble, letting us focus on specific issues like checksum validation or packet structure without worrying about real-world constraints. For anyone continuing this project, we highly recommend creating similar testing scripts to refine your work before moving into the field.

---

#### **Field Testing: Signal Through Water**  

![Signal Through Water](Images\Screenshot2024-11-30.png)

In 2023, the team conducted a fascinating test: trying to send and receive LoRa signals through water, across the challenging water-air boundary. This test aimed to simulate real-world deployment conditions where sensors might be submerged. Unfortunately, the results weren’t promising. You can refer to the image below for details. 

We hypothesize several reasons for the poor performance:  
1. **Metallic Enclosure**:  
   - The sensors were housed in metallic boxes with only one plastic side. This design likely caused the signal to bounce around inside the box, severely dampening its strength before it could escape.  
2. **Antenna Type**:  
   - The chosen antenna might not have been ideal for underwater communication.  

**Proposed Solutions for Future Tests**:  
- Experiment with different antenna types designed for underwater or near-water communication.  
- Modify the box design to reduce signal interference. For example:
  - Embed the antenna in the plastic cover.  
  - Move the antenna entirely outside the box.  
- Test with lower LoRa frequencies, such as 169 MHz or 433 MHz, which might perform better in such conditions.  

---

#### **Field Testing: Long-Range Communication**  

![Long-Range Communication](Images\field-test.png)

Fast forward to 2024, when our team performed a long-range communication test. The goal was simple: push the boundaries of LoRa's advertised 2 km range or more. Our test maxed out at around **800 meters**, far short of expectations. This was another wake-up call, showing that ideal conditions in datasheets don’t always translate to the field.

**Proposed Solutions**:    
- Experiment with signal power levels—this could extend the range but requires some research and adjustments.  
- Again, try alternative frequencies or antennas to see if they improve signal propagation.  
- Practical Advice:  Test in larger, open areas like the Luxembourg Gardens, using Google Earth to measure distances.

Both these tests—signal through water and long-range communication—can be carried out independently of protocol development. They are critical for optimizing the hardware side of the system. So some of your group can start with this ;) . 

---

#### **Power Consumption Testing**  

With battery life being a key constraint, we conducted basic power consumption tests. The method was straightforward: run the entire system for a day and calculate the average power consumption. While effective for an overview, this method doesn’t capture detailed variations in power usage across different operational modes. 

- Results were pretty good : up to 2.5 yeas , WOW.

For a more detailed analysis, we recommend exploring techniques used in previous years, which break down power consumption by specific tasks like packet transmission or sensor readings.  

---

### **Key Takeaways and Future Directions**  

Testing showed us that real-world performance depends on a combination of software, hardware, and environmental factors. While our protocol code is robust, the hardware setup, particularly antennas and enclosures, remains an area for improvement. Field tests like these are critical for bridging the gap between theory and practice.  

The groundwork is laid; now it’s up to future teams to refine, test, and innovate. The story of our project continues with you!

# **Final Words**

Dear future team,  

As we reach the end of this documentation, I can’t help but feel there’s still so much more I’d like to share with you. But let’s take a moment here—yes, I know, this all looks like a lot. Don’t worry, you’ve got this!  

Here’s my advice for you:  

1. **Start with a Deep Dive Into the Existing Code**  
   - Understand every part, no matter how daunting it may seem at first. Take your time—learning the code is like getting to know an old, wise friend.  

2. **Read This Documentation Carefully**  
   - Yes, I know it’s long (ChatGPT does like to overwrite!), but there’s gold in here, I promise.  

3. **Use ChatGPT Wisely**  
   - It’s tempting to lean on it for big changes, but trust me—it’s better for understanding concepts or solving small subproblems. For major updates, trust your understanding of the code and let ChatGPT support you when needed.  

4. **Plan and Work in Parallel**  
   - Distribute tasks effectively. Some of the independent issues, like the hardware tests mentioned, can run alongside the protocol development. Task management is the key to speeding up progress.  

---

## **Tasks To Focus On**

Here’s a quick recap of key tasks to tackle:  

- **Backward Propagation**: Implementing feedback or control signals from the relay to sensors.  
- **Time Scheduling**: Optimizing session timing for data transmission.  
- **Interrupt Mode**: Solving compatibility issues and using it to conserve relay power.  
- **LoRaWAN Integration**: Debugging and ensuring smooth transitions between local communication and server transmission modes.  
- **Hardware Tests**:  
  - Signal propagation through water.  
  - Long-range transmission optimization.  

And one more question I didn’t cover earlier—**How does the server differentiate sensor data?**  
It’s simple. When sending data to the server, include each sensor’s address in the packet. The server will maintain a translation table, mapping sensor addresses concatenated with relay IDs to the relevant dataset points.

---

## **Final Notes**

This project is a stepping stone toward something greater. By successfully building this network, you’ll not only create a robust river monitoring system but also lay the groundwork for larger, more impactful projects in environmental preservation and public safety.  

Remember:  

- **Teamwork is Your Superpower:** Collaborate, document, and divide tasks smartly.  
- **Experiment Without Fear:** Some of the best solutions arise from trial and error.  
- **Think Big, Act Now:** A successful prototype today will scale into a remarkable system tomorrow.  

You’re contributing to something meaningful—protecting the environment and helping communities. You should feel proud of your work and excited about what lies ahead.  

Best of luck, and know this—you have the honor of continuing something vital. Take it far, and leave your mark.  

Warm regards,  
Your predecessor