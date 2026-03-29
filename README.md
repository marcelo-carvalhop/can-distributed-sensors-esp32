
# Distributed Sensor Network using CAN and ESP32

This project implements a **distributed embedded system** composed of four
ESP32 nodes interconnected via a **CAN bus**. The system simulates a
distributed sensor network coordinated by a gateway using **logical clock
synchronization (heartbeat)** and **message-based time slots (TDMA logic)**.

The project was originally developed for an academic context and later refined
with clean architecture and documentation for portfolio use.

---

## System Overview

The system consists of **four physical ESP32 nodes**:

- **1 Gateway node**
- **3 Sensor nodes**

All nodes are connected to the same CAN bus using MCP2515 controllers
(crystal 8 MHz) and TJA1050 transceivers.

### Node Roles

- **Gateway**
  - Broadcasts periodic heartbeat messages
  - Provides a global logical clock
  - Receives sensor data
  - Sends high-priority control commands (enable/disable sensors)

- **Sensors**
  - Receive heartbeat messages
  - Synchronize transmissions using TDMA logic
  - Share a single CAN ID for data
  - Are uniquely identified via payload fields
  - Can be remotely enabled or disabled by the gateway

---

## Communication Model

### Logical Clock Synchronization

The gateway periodically broadcasts a **heartbeat message**, which contains:

- A logical time counter (`tick`)
- The total number of sensors in the system

Each sensor uses this logical clock to determine when it is allowed to transmit.

This approach avoids reliance on physical clocks or delays and implements
synchronization **entirely through message exchange**, a key concept in
distributed systems.

---

### TDMA-Based Transmission (Logical Time Division)

Sensor data transmission follows a **logical TDMA scheme**, defined as:

sensor transmits when: (heartbeat_tick % total_sensors) == sensor_slot

Where:
- `sensor_slot = SENSOR_ID - 1`

This guarantees:
- Only one sensor transmits per heartbeat
- No collisions at the application level
- Easy scalability (adding sensors does not require protocol changes)

---

## CAN Protocol Design

### CAN Identifiers and Priorities

CAN arbitration is used to enforce **real-time priority**:

| Message Type        | CAN ID  | Priority |
|--------------------|---------|----------|
| Control Command    | 0x080   | Highest  |
| Heartbeat          | 0x100   | Medium   |
| Sensor Data        | 0x200   | Lowest   |

Lower CAN IDs have higher priority on the bus.

---

### Message Types

#### Heartbeat (Gateway → All)

- CAN ID: `0x100`
- Sent periodically
- Defines the logical clock

Payload:
- Type
- Tick value
- Total number of sensors

---

#### Sensor Data (Sensors → Gateway)

- CAN ID: `0x200` (shared by all sensors)

Payload includes:
- Sensor ID
- Heartbeat tick
- Generic payload field (placeholder for future measurements)
- Sensor status (enabled/disabled)

---

#### Control Command (Gateway → Sensors)

- CAN ID: `0x080` (highest priority)

Used to remotely enable or disable individual sensors.

Format:

[opcode] [subcommand] [sensor_id] [action]

Where:
- `action = 0x00` → enable
- `action = 0x11` → disable

---

## Serial Control Interface (Gateway)

The gateway provides a simple human interface via Serial input.

Command format:

22 10 <sensor_id> 00   // enable sensor
22 10 <sensor_id> 11   // disable sensor

The serial parser is **non-blocking**, ensuring that gateway operation and
heartbeat emission are never interrupted by user input.

---

## Hardware

Each node consists of:

- ESP32 DevKit (or compatible)
- MCP2515 CAN controller (8 MHz crystal)
- TJA1050 CAN transceiver
- Shared CAN bus with proper termination

All nodes use the same electrical topology.

---

## Project Structure

software/
├── common/
│   ├── can_ids.h
│   └── protocol.h
│
├── gateway/
│   └── gateway_can/
│       └── gateway_can.ino
│
└── sensor/
└── sensor_can/
└── sensor_can.ino

The `common/` directory centralizes protocol definitions and CAN identifiers,
ensuring consistency across all nodes.

---

## Academic Context

This project was developed as part of a **Distributed Computing** course,
addressing key concepts such as:

- Logical clock synchronization
- Distributed coordination by message exchange
- Deterministic behavior without shared memory
- Communication via an industrial field bus (CAN)

The system was intentionally designed to be extensible, serving as a foundation
for future features such as fault detection, acknowledgments, and leader
election.

---

## Current Status

✅ Logical clock synchronization implemented  
✅ TDMA-based coordinated transmission  
✅ Unified CAN ID for sensors  
✅ Priority-based control commands  
✅ Non-blocking gateway operation  

---

## Future Extensions

Planned or possible extensions include:

- Heartbeat timeout and fault detection
- Command acknowledgment (ACK)
- Sensor data payload expansion (e.g., temperature)
- Gateway redundancy and leader election
- Performance analysis under load

---

## License

This project is released under the MIT License.


