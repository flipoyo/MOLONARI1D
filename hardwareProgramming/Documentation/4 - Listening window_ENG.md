# Listening Window for LoRa

Work of MOLONARI2023 team, not updated yet by MOLONARI2024 team

## Intro

When sending a message via LoRa, the receiver must have its radio turned on and be listening for messages. The problem is that listening consumes energy—too much to do it continuously (it already represents 70% of our emissions if we listen for 10 seconds every 15 minutes).  
The solution: the transmitter and receiver agree in advance on when the message will be sent. The receiver will listen during this short time interval, called the "listening window," for example, 10 seconds, and the transmitter will send the message at that time.

This is a feature the 2023 sensor team thought about but did not have time to implement.

## Operation

The difficulty is properly synchronizing the transmitter and receiver. The simplest method is to wait 15 minutes after the last successful transmission and then listen for 10 seconds.

## Clock Drift

A problem that will arise is the inaccuracy of the clocks on both devices. They drift by a few seconds per day relative to each other (the exact order of magnitude needs to be verified). There is a risk that after a few days, the two devices will lose synchronization.

First solution: Use common references  
We use the last successful transmission as a common time reference between the two devices. This provides an opportunity to re-synchronize them.  
That way, as long as the two devices communicate regularly, they remain synchronized.

## Catch-up

Things get more complicated when the two devices can no longer communicate for an extended period, such as if a flood blocks communications. The devices may then become completely unsynchronized with each other.  
The receiver will need to enter a "catch-up" mode, where it attempts to restore synchronization. To do this, the receiver will deliberately fall behind to more quickly cover the phase differences between the transmitter and receiver.  
In practice, instead of waiting 15 minutes between two listening windows, it will wait 15 minutes and 10 seconds. If the transmitter has fallen behind, the receiver will compensate by also falling behind, and the connection will be reestablished. On the other hand, if the transmitter is ahead, by consistently falling behind, the receiver will eventually gain time on the next transmission and restore synchronization.
