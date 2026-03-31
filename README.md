# Distributed Sensor Network using CAN and ESP32

This repository contains the implementation of a **distributed embedded system**
based on multiple ESP32 nodes connected through a **CAN (Controller Area Network) bus**.
The project focuses on coordination, synchronization, and distributed decision-making,
following classic principles of **Distributed Computing**.

The system was developed as part of an academic assignment and organized with
production-quality structure to also serve as a technical portfolio project.

---

## Overview

The system is composed of **four ESP32 nodes** connected to a shared CAN bus.
All nodes execute the **same firmware**, differing only by a local logical identifier.

There is no fixed master or gateway node.  
Instead, a **leader is elected dynamically** at runtime using a distributed algorithm.
The elected leader becomes responsible for coordinating the system.

---

## Distributed Architecture

### Node Roles

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

---

## Implemented Distributed Computing Requirements

This project explicitly implements the following requirements from the course specification:

### 1. Logical Clock Synchronization ✅

- A **logical clock** is implemented using a periodic **heartbeat message**
  generated exclusively by the elected leader.
- All nodes synchronize their actions based on this logical time.
- No physical clock synchronization is used.

### 2. Leader Election ✅

- A **distributed leader election algorithm** is implemented.
- All nodes execute the same election logic.
- The leader is selected dynamically based on node identifiers.
- Leadership is observable both via serial logs and physical LEDs.

These two mechanisms are independent but **integrated**:
the elected leader becomes the unique source of the logical clock.

---

## Communication Model

### CAN Bus

- Communication uses a shared CAN bus (broadcast model).
- All nodes receive all messages.
- Message priority is enforced using CAN identifiers.

### Message Categories

- Leader election messages
- Leader announcement messages
- Heartbeat messages (logical clock)
- Sensor data messages (TDMA coordinated)
- Administrative control commands

---

## TDMA-Based Coordination

Sensor data transmission follows a **logical TDMA scheme**:

node transmits when:
(heartbeat_tick % total_nodes) == node_slot
Where:
- `node_slot = NODE_ID - 1`

This guarantees:
- Deterministic communication
- One transmission per time slot
- Logical exclusion without relying on CAN arbitration alone

---

## Administrative Control

An administrative command interface is implemented:

22 10 <NODE_ID> 00  -> enable node
22 10 <NODE_ID> 11  -> disable node

- Only the **leader node** may issue administrative commands.
- Disabled nodes remain synchronized but do not transmit data.
- Control logic is isolated in a dedicated module for easy expansion.

---

## Human–Machine Interface (HMI)

Each node provides local visual feedback via LEDs:

| LED Color  | Meaning |
|-----------|--------|
| Blue      | Node is the current leader |
| Yellow   | Node activity (system alive) |
| Red      | Reserved for fault indication (future work) |

This allows observing system behavior without a computer.

---

## Serial Observability

Every node logs all relevant events over the serial interface,
including:

- Leader election
- Heartbeat generation
- Data transmission (TX)
- Data reception from other nodes (RX)
- Administrative commands

Any node connected to a computer can act as a **global observer**
of the distributed system.

---

## Repository Structure

can-distributed-sensors-esp32/
│
├── README.md
├── LICENSE
│
├── docs/
│   ├── relatorio/
│   │   └── entrega1.pdf
│   └── especificacao-protocolo.md
│
├── hardware/
│   ├── esquema-conexao.md
│   └── componentes.md
│
├── software/
│   └── node/
│       ├── geral_v1.ino
│       ├── comandos.h
│       ├── comandos.cpp
│       ├── node_types.h
│       ├── node_config.h
│       ├── can_ids.h
│       └── protocolo.h
│
└── .gitignore


---

## Firmware Notes

- All ESP32 boards use the **same firmware**.
- Only `NODE_ID` must be changed per device.
- CAN controller: MCP2515 (8 MHz)
- CAN bitrate: 500 kbps

---

## Academic Context

This project was developed for the **Distributed Computing** course and
addresses key distributed systems concepts such as:

- Logical time
- Distributed coordination
- Leader election
- Message-based synchronization
- Decentralized control

The design is intentionally extensible to support fault detection and recovery
in future iterations.

---

## Future Work

Planned extensions include:

- Leader failure detection and re-election
- Heartbeat timeout handling
- Explicit acknowledgment (ACK/NACK) mechanisms
- Real sensor data integration
- Web-based monitoring and control

---

## License

This project is released under the MIT License.

