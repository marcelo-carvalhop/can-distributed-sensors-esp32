#include "comandos.h"
#include "node_config.h"
#include "can_ids.h"
#include "protocolo.h"

// Variáveis globais vindas do geral_v1.ino
extern NodeState state;
extern ACAN2515 can;

// Estado local do sensor
bool sensorEnabled = true;

/* =========================================================
 * ENVIO DE COMANDO (somente líder)
 * ========================================================= */

void sendControlCommand(uint8_t targetId, uint8_t action) {
  if (state != STATE_LEADER) {
    Serial.print("[NODE ");
    Serial.print(NODE_ID);
    Serial.println("] [CTRL] Ignored (not leader)");
    return;
  }

  CANMessage msg;
  msg.id  = CAN_ID_CONTROL;
  msg.len = 4;

  msg.data[0] = CTRL_OPCODE;
  msg.data[1] = CTRL_SUBCMD_SENSOR;
  msg.data[2] = targetId;
  msg.data[3] = action;

  can.tryToSend(msg);

  Serial.print("[NODE ");
  Serial.print(NODE_ID);
  Serial.print("] [CTRL TX] Sensor ");
  Serial.print(targetId);
  Serial.print(action == CTRL_ACTION_ON ? " ENABLED" : " DISABLED");
  Serial.println();
}

/* =========================================================
 * PARSER SERIAL NÃO BLOQUEANTE
 * ========================================================= */

void handleSerialCommands() {
  static char buffer[64];
  static uint8_t idx = 0;

  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n' || c == '\r') {
      buffer[idx] = '\0';
      idx = 0;

      if (strlen(buffer) == 0) return;

      uint8_t opcode, subcmd, id, action;
      int parsed = sscanf(
        buffer,
        "%hhx %hhx %hhx %hhx",
        &opcode, &subcmd, &id, &action
      );

      if (parsed != 4) {
        Serial.println("[CTRL] Invalid format");
        return;
      }

      if (opcode != CTRL_OPCODE || subcmd != CTRL_SUBCMD_SENSOR) {
        Serial.println("[CTRL] Invalid opcode/subcommand");
        return;
      }

      sendControlCommand(id, action);
    } else {
      if (idx < sizeof(buffer) - 1) {
        buffer[idx++] = c;
      }
    }
  }
}

/* =========================================================
 * TRATAMENTO DE COMANDO RECEBIDO VIA CAN
 * ========================================================= */

void handleControlMessage(const CANMessage& rx) {
  if (rx.id != CAN_ID_CONTROL) return;

  if (rx.data[0] != CTRL_OPCODE ||
      rx.data[1] != CTRL_SUBCMD_SENSOR)
    return;

  if (rx.data[2] != NODE_ID) return;

  sensorEnabled = (rx.data[3] == CTRL_ACTION_ON);

  Serial.print("[NODE ");
  Serial.print(NODE_ID);
  Serial.print("] [CTRL RX] ");
  Serial.println(sensorEnabled ? "ENABLED" : "DISABLED");
}
