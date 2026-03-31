#ifndef COMANDOS_H
#define COMANDOS_H

#include <Arduino.h>
#include <ACAN2515.h>

#include "node_types.h"

// Estado do sensor (usado pelo TDMA)
extern bool sensorEnabled;

// Interfaces públicas
void handleSerialCommands();
void handleControlMessage(const CANMessage& rx);

#endif
