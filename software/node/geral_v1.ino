#include <Arduino.h>
#include <SPI.h>
#include <ACAN2515.h>

#include "can_ids.h"
#include "protocolo.h"
#include "node_types.h"
#include "node_config.h"
#include "comandos.h"



/* =========================================================
 * CONFIGURAÇÃO DO NÓ
 * ========================================================= */

const uint8_t NODE_ID    = 2;  // <<< altere para cada ESP32
const uint8_t TOTAL_NODES =4;


#define NODE_SLOT     (NODE_ID - 1)

/* =========================================================
 * LEDs (HMI LOCAL)
 * ========================================================= */

#define LED_LEADER   25   // Azul  - nó é líder
#define LED_FAULT    26   // Vermelho - reservado (falhas futuras)
#define LED_STATUS   27   // Amarelo - atividade

/* =========================================================
 * CAN
 * ========================================================= */

static const byte MCP_CS  = 5;
static const byte MCP_INT = 4;

static const uint32_t MCP_QUARTZ_HZ = 8000000;
static const uint32_t CAN_BITRATE  = 500UL * 1000UL;

ACAN2515 can(MCP_CS, SPI, MCP_INT);

/* =========================================================
 * ESTADO DO SISTEMA DISTRIBUÍDO
 * ========================================================= */

NodeState state = STATE_ELECTION;

uint8_t leaderId = 0;
uint8_t heartbeatTick = 0;

unsigned long lastHeartbeat = 0;
unsigned long electionStartTime = 0;

/* =========================================================
 * LOG SERIAL PADRONIZADO
 * ========================================================= */

void log(const char* role, const char* msg) {
  Serial.print("[NODE ");
  Serial.print(NODE_ID);
  Serial.print("] [");
  Serial.print(role);
  Serial.print("] ");
  Serial.println(msg);
}

/* =========================================================
 * LEDs
 * ========================================================= */

void updateLEDs() {
  digitalWrite(LED_LEADER, state == STATE_LEADER);
  digitalWrite(LED_STATUS, (millis() / 300) % 2); // pisca
  digitalWrite(LED_FAULT, LOW);                   // reservado
}

/* =========================================================
 * ELEIÇÃO DE LÍDER
 * ========================================================= */

void sendElectionAnnouncement() {
  CANMessage msg;
  msg.id  = CAN_ID_ELECTION;
  msg.len = 1;
  msg.data[0] = NODE_ID;

  can.tryToSend(msg);
  log("ELECTION", "Announcing candidacy");
}

void sendLeaderAnnouncement() {
  CANMessage msg;
  msg.id  = CAN_ID_LEADER;
  msg.len = 1;
  msg.data[0] = NODE_ID;

  can.tryToSend(msg);
  log("LEADER", "Leadership announced");
}

/* =========================================================
 * HEARTBEAT (APENAS O LÍDER ENVIA)
 * ========================================================= */

void sendHeartbeat() {
  CANMessage msg;
  msg.id  = CAN_ID_HEARTBEAT;
  msg.len = 3;

  msg.data[0] = MSG_TYPE_HEARTBEAT;
  msg.data[1] = heartbeatTick;
  msg.data[2] = TOTAL_NODES;

  can.tryToSend(msg);

  Serial.print("[NODE ");
  Serial.print(NODE_ID);
  Serial.print("] [LEADER] HB tick=");
  Serial.println(heartbeatTick);

  heartbeatTick++;
}

/* =========================================================
 * TDMA – ENVIO DE DADOS DO SENSOR
 * ========================================================= */

void sendSensorData(uint8_t tick) {
  uint8_t fakeValue = 0xAA;  // valor fictício (placeholder)

  CANMessage msg;
  msg.id  = CAN_ID_SENSOR;
  msg.len = 5;

  msg.data[0] = NODE_ID;
  msg.data[1] = tick;
  msg.data[2] = fakeValue;
  msg.data[3] = state;
  msg.data[4] = 0x00;

  can.tryToSend(msg);

  Serial.print("[NODE ");
  Serial.print(NODE_ID);
  Serial.print("] [TX] tick=");
  Serial.print(tick);
  Serial.print(" valor=");
  Serial.println(fakeValue, HEX);
}

/* =========================================================
 * SETUP
 * ========================================================= */

void setup() {
  Serial.begin(115200);
  delay(300);

  pinMode(LED_LEADER, OUTPUT);
  pinMode(LED_FAULT,  OUTPUT);
  pinMode(LED_STATUS, OUTPUT);

  SPI.begin(13, 19, 23, 5);

  ACAN2515Settings settings(MCP_QUARTZ_HZ, CAN_BITRATE);
  const uint16_t err = can.begin(settings, [] { can.isr(); });

  if (err != 0) {
    Serial.print("[ERROR] CAN init failed: 0x");
    Serial.println(err, HEX);
    while (true) {}
  }

  electionStartTime = millis();

  log("INIT", "Node started");
  sendElectionAnnouncement();
}

/* =========================================================
 * LOOP PRINCIPAL
 * ========================================================= */

void loop() {
  updateLEDs();

  /* ---------- Serial admin commands (leader only) ---------- */
  handleSerialCommands();   // definido em comandos.ino

  /* ---------- Heartbeat do líder ---------- */
  if (state == STATE_LEADER && millis() - lastHeartbeat >= 500) {
    lastHeartbeat = millis();
    sendHeartbeat();
  }

  /* ---------- Recepção CAN ---------- */
  CANMessage rx;
  if (can.receive(rx)) {

    /* -------- Eleição -------- */
    if (rx.id == CAN_ID_ELECTION) {
      uint8_t otherId = rx.data[0];
      if (otherId > NODE_ID) {
        state = STATE_FOLLOWER;
        log("ELECTION", "Higher ID detected, becoming follower");
      }
    }

    /* -------- Anúncio de líder -------- */
    else if (rx.id == CAN_ID_LEADER) {
      leaderId = rx.data[0];
      state = (leaderId == NODE_ID) ? STATE_LEADER : STATE_FOLLOWER;

      log(state == STATE_LEADER ? "LEADER" : "FOLLOWER",
          state == STATE_LEADER ? "I am the leader" : "Leader accepted");
    }

    /* -------- Heartbeat -------- */
    else if (rx.id == CAN_ID_HEARTBEAT && state != STATE_ELECTION) {
      uint8_t tick  = rx.data[1];
      uint8_t total = rx.data[2];

      if (sensorEnabled && (tick % total) == NODE_SLOT) {
        sendSensorData(tick);
      }
    }

    /* -------- Dados de sensores (observabilidade global) -------- */
    else if (rx.id == CAN_ID_SENSOR) {
      uint8_t fromNode = rx.data[0];
      uint8_t tick     = rx.data[1];
      uint8_t value    = rx.data[2];

      Serial.print("[NODE ");
      Serial.print(NODE_ID);
      Serial.print("] [RX] from NODE ");
      Serial.print(fromNode);
      Serial.print(" tick=");
      Serial.print(tick);
      Serial.print(" valor=");
      Serial.println(value, HEX);
    }

    /* -------- Comandos administrativos -------- */
    else if (rx.id == CAN_ID_CONTROL) {
      handleControlMessage(rx);   // definido em comandos.ino
    }
  }

  /* ---------- Final da eleição ---------- */
  if (state == STATE_ELECTION && millis() - electionStartTime > 2000) {
    state = STATE_LEADER;
    sendLeaderAnnouncement();
  }
}
