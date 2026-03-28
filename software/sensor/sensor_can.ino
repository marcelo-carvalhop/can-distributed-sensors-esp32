// ESP32 + MCP2515 + TJA1050
// Sensor CAN sincronizado por heartbeat

#include <Arduino.h>
#include <SPI.h>
#include <ACAN2515.h>

static const byte MCP_CS  = 5;
static const byte MCP_INT = 4;

ACAN2515 can(MCP_CS, SPI, MCP_INT);

const uint32_t MCP_QUARTZ_HZ = 8000000;
const uint32_t CAN_BITRATE  = 500UL * 1000UL;

const uint8_t SENSOR_ID = 2;      // <<< MUDE PARA 1,2 ou 3
const uint16_t SENSOR_CAN_ID = 0x202; // 0x201,0x202,0x203

uint8_t lastTick = 0;
uint8_t heartbeatCount = 0;
const uint8_t SEND_EVERY_N_HEARTBEATS = 4;

void setup() {
  Serial.begin(115200);
  delay(300);

  Serial.println("\n[SENSOR] Init CAN");

  SPI.begin(13, 19, 23, 5);

  ACAN2515Settings settings(MCP_QUARTZ_HZ, CAN_BITRATE);
  const uint16_t err = can.begin(settings, [] { can.isr(); });

  if (err != 0) {
    Serial.print("Erro MCP2515: 0x");
    Serial.println(err, HEX);
    while (true);
  }

  Serial.println("CAN OK (Sensor)");
}

void sendSensorMessage(uint8_t tick) {
  CANMessage msg;
  msg.id  = SENSOR_CAN_ID;
  msg.len = 8;

  msg.data[0] = SENSOR_ID;
  msg.data[1] = tick;
  msg.data[2] = 0xAA; // payload genérico (futuro: temperatura)
  for (int i = 3; i < 8; i++) msg.data[i] = 0;

  if (can.tryToSend(msg)) {
    Serial.print("TX Sensor ");
    Serial.print(SENSOR_ID);
    Serial.print(" no tick ");
    Serial.println(tick);
  }
}

void loop() {
  CANMessage rx;

  if (can.receive(rx)) {
    if (rx.id == 0x100 && rx.data[0] == 0x01) {
      uint8_t tick = rx.data[1];

      // Detecta novo heartbeat
      if (tick != lastTick) {
        lastTick = tick;
        heartbeatCount++;

        if (heartbeatCount >= SEND_EVERY_N_HEARTBEATS) {
          heartbeatCount = 0;
          sendSensorMessage(tick);
        }
      }
    }
  }
}
