# Distributed Sensor Network using CAN and ESP32

This project implements a distributed embedded system composed of
multiple ESP32 nodes communicating over a CAN bus.

## Overview
- 1 Gateway node
- 3 Sensor nodes
- Synchronization via logical clock (heartbeat)
- CAN bus (MCP2515 + TJA1050)

## Architecture
The gateway broadcasts a logical heartbeat...
(1 parágrafo curto)

## Hardware
- ESP32
- MCP2515 (8 MHz)
- TJA1050
- CAN bus with termination

## How to Run
1. Flash the gateway firmware on one ESP32
2. Flash the sensor firmware on three ESP32 boards
3. Connect all nodes to the CAN bus
4. Open serial monitor...

## Academic Context
This project was developed as part of a Distributed Computing course
and later refined for portfolio purposes.
