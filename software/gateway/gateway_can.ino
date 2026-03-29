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
 * CONFIGURAÇÃO DO SISTEMA
 * ========================================================= */

static const uint8_t TOTAL_SENSORES = 3;
static const unsigned long HEARTBEAT_PERIOD_MS = 500;

/* =========================================================
 * ESTADO GLOBAL
 * ========================================================= */

uint8_t heartbeatTick = 0;
unsigned long lastHeartbeat = 0;

/* =========================================================
 * ENVIO DE HEARTBEAT
 * ========================================================= */

void sendHeartbeat() {
  CANMessage msg;
  msg.id  = CAN_ID_HEARTBEAT;
  msg.len = 8;

  msg.data[0] = MSG_TYPE_HEARTBEAT;
  msg.data[1] = heartbeatTick;
  msg.data[2] = TOTAL_SENSORES;

  for (int i = 3; i < 8; i++) {
    msg.data[i] = 0x00;
  }

  can.tryToSend(msg);

  Serial.print("[HB] tick=");
  Serial.println(heartbeatTick);

  heartbeatTick++;
}

/* =========================================================
 * ENVIO DE COMANDO DE CONTROLE
 * ========================================================= */

void sendControl(uint8_t sensorId, uint8_t action) {
  if (sensorId == 0 || sensorId > TOTAL_SENSORES) {
    Serial.println("[ERRO] Sensor ID invalido");
    return;
  }

  CANMessage msg;
  msg.id  = CAN_ID_CONTROL;
  msg.len = 8;

  msg.data[0] = CTRL_OPCODE;
  msg.data[1] = CTRL_SUBCMD_SENSOR;
  msg.data[2] = sensorId;
  msg.data[3] = action;
