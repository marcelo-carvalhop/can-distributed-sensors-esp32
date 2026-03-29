#ifndef CAN_IDS_H
#define CAN_IDS_H

// Comandos de controle (alta prioridade)
#define CAN_ID_CONTROL    0x080

// Heartbeat / sincronização
#define CAN_ID_HEARTBEAT  0x100

// Dados dos sensores (todos usam o mesmo ID)
#define CAN_ID_SENSOR     0x200

#endif
