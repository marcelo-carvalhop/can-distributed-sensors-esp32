#ifndef PROTOCOL_H
#define PROTOCOL_H

// -------------------------------------------------
// Tipos de mensagem
// -------------------------------------------------

#define MSG_TYPE_HEARTBEAT   0x01

// -------------------------------------------------
// Protocolo de controle remoto
// -------------------------------------------------

#define CTRL_OPCODE         0x22
#define CTRL_SUBCMD_SENSOR  0x10

#define CTRL_ACTION_ON      0x00
#define CTRL_ACTION_OFF     0x11

#endif
