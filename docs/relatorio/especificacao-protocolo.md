# CAN Protocol Specification

## Message Types

### Heartbeat (CAN ID 0x100)
- Sent periodically by the gateway
- Provides logical time reference

### Sensor Data (CAN ID 0x200)
- Shared by all sensors
- Sensor ID provided in payload

### Control Command (CAN ID 0x080)
- High priority message
- Enables or disables a specific sensor
