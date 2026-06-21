**Distributed Sensor Network using CAN and ESP32**  
This repository contains the implementation of a **distributed embedded system**  
   
 based on multiple ESP32 nodes connected through a **CAN (Controller Area Network) bus**.  
   
 The project focuses on coordination, synchronization, and distributed decision-making,  
   
 following classic principles of **Distributed Computing**.  
The system was developed as part of an academic assignment and organized with  
   
 production-quality structure to also serve as a technical portfolio project.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OMQ2AABAAsSPBCUZfEnoYmFDBhAU2QtIq6DIzW7UHAMBfnGt1V8fXEwAAXrse/wcF74lXkIsAAAAASUVORK5CYII=)  
**Overview**  
The system is composed of **four ESP32 nodes** connected to a shared CAN bus.  
   
 All nodes execute the **same firmware**, differing only by a local logical identifier.  
There is no fixed master or gateway node.  
   
 Instead, a **leader is elected dynamically** at runtime using a distributed algorithm.  
   
 The elected leader becomes responsible for coordinating the system.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OYQ1AABSAwY9JoICqL4Z8Ikiggn9mu0twy8wc1RkAAH9xbdVa7V9PAAB47X4A9CgEJQFjJ/EAAAAASUVORK5CYII=)  
**Distributed Architecture**  
**Node Roles**  
Each node may assume one of the following roles during execution:  
- **Leader**  
  - Generates the global logical clock (heartbeat)  
  - Coordinates communication timing  
  - Issues administrative control commands  
- **Follower**  
  - Synchronizes using the heartbeat  
  - Transmits data only in its assigned time slot  
- **Election State**  
  - Temporary state during leader election  
Roles are **not fixed** and emerge dynamically at runtime.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANklEQVR4nO3OYQ1AABSAwc8mi5wvkwZyCKCAACr4Z7a7BLfMzFYdAQDwF+da3dX+9QQAgNeuB6feBdUJcyS2AAAAAElFTkSuQmCC)  
**Implemented Distributed Computing Requirements**  
This project explicitly implements the following requirements from the course specification:  
**1. Logical Clock Synchronization ✅**  
- A **logical clock** is implemented using a periodic  **heartbeat message**  
   
 generated exclusively by the elected leader.  
- All nodes synchronize their actions based on this logical time.  
- No physical clock synchronization is used.  
**2. Leader Election ✅**  
- A **distributed leader election algorithm** is implemented.  
- All nodes execute the same election logic.  
- The leader is selected dynamically based on node identifiers.  
- Leadership is observable both via serial logs and physical LEDs.  
These two mechanisms are independent but **integrated**:  
   
 the elected leader becomes the unique source of the logical clock.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANElEQVR4nO3OUQmAABBAsSeILQSjXgcrmkOs4J8IW4ItM7NXZwAA/MW1Vlt1fBwBAOC9+wEukwQ+V/SggAAAAABJRU5ErkJggg==)  
**Communication Model**  
**CAN Bus**  
- Communication uses a shared CAN bus (broadcast model).  
- All nodes receive all messages.  
- Message priority is enforced using CAN identifiers.  
**Message Categories**  
- Leader election messages  
- Leader announcement messages  
- Heartbeat messages (logical clock)  
- Sensor data messages (TDMA coordinated)  
- Administrative control commands  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANklEQVR4nO3OQQmAABRAsSfYxZo/jkUsYQLPJrCCNxG2BFtmZquOAAD4i3Ot7mr/egIAwGvXA4rDBc72meO5AAAAAElFTkSuQmCC)  
**TDMA-Based Coordination**  
Sensor data transmission follows a **logical TDMA scheme**:  
node transmits when:  
   
 (heartbeat_tick % total_nodes) == node_slot  
   
 Where:  
- node_slot = NODE_ID - 1  
This guarantees:  
- Deterministic communication  
- One transmission per time slot  
- Logical exclusion without relying on CAN arbitration alone  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANElEQVR4nO3OMQ0AIAwAwZIgBKn1gjJsdGLBABMhuZt+/JaZIyJmAADwi9VP1NMNAABu1AaU4gUeBSGW2wAAAABJRU5ErkJggg==)  
**Administrative Control**  
An administrative command interface is implemented:  
22 10 <NODE_ID> 00  -> enable node  
   
 22 10 <NODE_ID> 11  -> disable node  
- Only the **leader node** may issue administrative commands.  
- Disabled nodes remain synchronized but do not transmit data.  
- Control logic is isolated in a dedicated module for easy expansion.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OMQ2AABAAsSNhQAQ60PcrIhnxgQU2QtIq6DIze3UGAMBf3Gu1VcfXEwAAXrseS14EKxPCORkAAAAASUVORK5CYII=)  
**Human–Machine Interface (HMI)**  
Each node provides local visual feedback via LEDs:  
| | |  
|-|-|  
| **LED Color** | **Meaning** |   
| Blue | Node is the current leader |   
| Yellow | Node activity (system alive) |   
| Red | Reserved for fault indication (future work) |   
   
This allows observing system behavior without a computer.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANklEQVR4nO3OQQmAABRAsScYxpg/h5VMYARvRrCCNxG2BFtmZquOAAD4i3Ot7mr/egIAwGvXA224BcUMk6pDAAAAAElFTkSuQmCC)  
**Serial Observability**  
Every node logs all relevant events over the serial interface,  
   
 including:  
- Leader election  
- Heartbeat generation  
- Data transmission (TX)  
- Data reception from other nodes (RX)  
- Administrative commands  
Any node connected to a computer can act as a **global observer**  
   
 of the distributed system.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OMQ2AABAAsSNBCUrfD6LYGNDAgAU2QtIq6DIzW7UHAMBfHGt1V+fXEwAAXrseHDAF/orRG+cAAAAASUVORK5CYII=)  
**Firmware Notes**  
- All ESP32 boards use the **same firmware**.  
- Only NODE_ID must be changed per device.  
- CAN controller: MCP2515 (8 MHz)  
- CAN bitrate: 500 kbps  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANElEQVR4nO3OQQmAABRAsad4FCtY9ecwnkms4E2ELcGWmTmrKwAA/uLeqrU6vp4AAPDa/gDzUgM9+S8z3AAAAABJRU5ErkJggg==)  
**Academic Context**  
This project was developed for the **Distributed Computing** course and  
   
 addresses key distributed systems concepts such as:  
- Logical time  
- Distributed coordination  
- Leader election  
- Message-based synchronization  
- Decentralized control  
The design is intentionally extensible to support fault detection and recovery  
   
 in future iterations.  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAANUlEQVR4nO3OMQ2AABAAsSNhZscZXlheJwqQgQU2QtIq6DIze3UGAMBf3Gu1VcfXEwAAXrseop8EQrmJduIAAAAASUVORK5CYII=)  
**Future Work**  
Planned extensions include:  
- Leader failure detection and re-election  
- Heartbeat timeout handling  
- Explicit acknowledgment (ACK/NACK) mechanisms  
- Real sensor data integration  
- Web-based monitoring and control  
![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnEAAAACCAYAAAA3pIp+AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAMUlEQVR4nO3WAQkAIBAEsBPMYs4PZhMDWMAA5njYUmxU1UqyAwBAF2cmeZE4AIBO7gentgXapSWpbgAAAABJRU5ErkJggg==)  
**License**  
This project is released under the MIT License.  
