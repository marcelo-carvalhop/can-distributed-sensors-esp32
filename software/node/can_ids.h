#ifndef CAN_IDS_H
#define CAN_IDS_H

// Eleição de líder
#define CAN_ID_ELECTION    0x050
#define CAN_ID_LEADER      0x060

// Comandos de controle (alta prioridade)
#define CAN_ID_CONTROL     0x080

// Heartbeat / sincronização lógica
#define CAN_ID_HEARTBEAT   0x100

// Dados dos sensores (TDMA)
#define CAN_ID_SENSOR      0x200

#endif

