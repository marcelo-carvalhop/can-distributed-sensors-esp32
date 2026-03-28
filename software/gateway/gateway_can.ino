// ESP32 + MCP2515 + TJA1050
// Gateway CAN: emite heartbeat e recebe mensagens

#include <Arduino.h>
#include <SPI.h>
#include <ACAN2515.h>

static const byte MCP_CS  = 5;
static const byte MCP_INT = 4;

ACAN2515 can(MCP_CS, SPI, MCP_INT);

const uint32_t MCP_QUARTZ_HZ = 8000000;
const uint32_t CAN_BITRATE  = 500UL * 1000UL;

uint8_t heartbeatTick = 0;
unsigned long lastHeartbeat = 0;
const unsigned long HEARTBEAT_PERIOD_MS = 500;

void setup() {
  Serial.begin(115200);
  delay(300);

  Serial.println("\n[GATEWAY] Init CAN");

  SPI.begin(13, 19, 23, 5);

  ACAN2515Settings settings(MCP_QUARTZ_HZ, CAN_BITRATE);
  const uint16_t err = can.begin(settings, [] { can.isr(); });

  if (err != 0) {
    Serial.print("Erro MCP2515: 0x");
    Serial.println(err, HEX);
    while (true);
  }

  Serial.println("CAN OK (Gateway)");
}

void sendHeartbeat() {
  CANMessage msg;
  msg.id  = 0x100;
  msg.len = 8;
  msg.data[0] = 0x01;            // tipo heartbeat
  msg.data[1] = heartbeatTick;   // relógio lógico
  for (int i = 2; i < 8; i++) msg.data[i] = 0;

  if (can.tryToSend(msg)) {
    Serial.print("Heartbeat enviado, tick=");
    Serial.println(heartbeatTick);
    heartbeatTick++;
  }
}

void loop() {
  // Envia heartbeat periódico
  if (millis() - lastHeartbeat >= HEARTBEAT_PERIOD_MS) {
    lastHeartbeat = millis();
    sendHeartbeat();
  }

  // Recebe mensagens dos sensores
  CANMessage rx;
  if (can.receive(rx)) {
    Serial.print("RX ID=0x");
    Serial.print(rx.id, HEX);
    Serial.print(" | Sensor=");
    Serial.print(rx.data[0]);
    Serial.print(" | Tick=");
    Serial.println(rx.data[1]);
  }
}
