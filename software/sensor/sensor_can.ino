#include <Arduino.h>
#include <SPI.h>
#include <ACAN2515.h>

#include "can_ids.h"
#include "protocol.h"

/* =========================================================
 * CONFIGURAÇÃO DO HARDWARE
 * ========================================================= */

static const byte MCP_CS  = 5;
static const byte MCP_INT = 4;

static const uint32_t MCP_QUARTZ_HZ = 8000000;
static const uint32_t CAN_BITRATE  = 500UL * 1000UL;

ACAN2515 can(MCP_CS, SPI, MCP_INT);

/* =========================================================
 * CONFIGURAÇÃO DO SENSOR
 * ========================================================= */

// <<< ALTERE APENAS ESTE VALOR EM CADA NÓ >>>
#define SENSOR_ID  1

// slot TDMA derivado do ID do sensor
#define SENSOR_SLOT  (SENSOR_ID - 1)

/* =========================================================
 * ESTADO DO SENSOR
 * ========================================================= */

bool enabled = true;
uint8_t totalSensores = 1;

/* =========================================================
 * ENVIO DE DADOS DO SENSOR
 * ========================================================= */

void sendSensorData(uint8_t tick) {
  CANMessage msg;
  msg.id  = CAN_ID_SENSOR;
  msg.len = 8;

  msg.data[0] = SENSOR_ID;
  msg.data[1] = tick;
  msg.data[2] = 0xAA;                 // payload genérico
  msg.data[3] = enabled ? 1 : 0;      // status
  for (int i = 4; i < 8; i++) {
    msg.data[i] = 0x00;
  }

  can.tryToSend(msg);

  Serial.print("[TX] Sensor ");
  Serial.print(SENSOR_ID);
  Serial.print(" tick=");
  Serial.println(tick);
}

/* =========================================================
 * TRATAMENTO DE COMANDO DE CONTROLE
 * ========================================================= */

void handleControl(const CANMessage& msg) {
  if (msg.data[0] != CTRL_OPCODE) return;
  if (msg.data[1] != CTRL_SUBCMD_SENSOR) return;
  if (msg.data[2] != SENSOR_ID) return;

  enabled = (msg.data[3] == CTRL_ACTION_ON);

  Serial.print("[CTRL RX] Sensor ");
  Serial.print(SENSOR_ID);
  Serial.print(" -> ");
  Serial.println(enabled ? "LIGADO" : "DESLIGADO");
}

/* =========================================================
 * TRATAMENTO DO HEARTBEAT
 * ========================================================= */

void handleHeartbeat(const CANMessage& msg) {
  if (msg.data[0] != MSG_TYPE_HEARTBEAT) return;

  uint8_t tick = msg.data[1];
  totalSensores = msg.data[2];

  if (!enabled) return;

  // TDMA lógico baseado em heartbeat
  if ((tick % totalSensores) == SENSOR_SLOT) {
    sendSensorData(tick);
  }
}

/* =========================================================
 * SETUP
 * ========================================================= */

void setup() {
  Serial.begin(115200);
  delay(300);

  Serial.print("[SENSOR ");
  Serial.print(SENSOR_ID);
  Serial.println("] Inicializando");

  SPI.begin(13, 19, 23, 5);

  ACAN2515Settings settings(MCP_QUARTZ_HZ, CAN_BITRATE);
  const uint16_t err = can.begin(settings, [] { can.isr(); });

  if (err != 0) {
    Serial.print("[ERRO] Falha MCP2515: 0x");
    Serial.println(err, HEX);
    while (true) { }
  }

  Serial.println("[SENSOR] CAN OK");
}

/* =========================================================
 * LOOP PRINCIPAL
 * ========================================================= */

void loop() {
  CANMessage rx;

  if (can.receive(rx)) {
    if (rx.id == CAN_ID_CONTROL) {
      handleControl(rx);
    }
    else if (rx.id == CAN_ID_HEARTBEAT) {
      handleHeartbeat(rx);
    }
  }
}
