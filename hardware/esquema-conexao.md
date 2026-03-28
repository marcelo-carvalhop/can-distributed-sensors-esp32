# Esquema de Conexão – ESP32 + MCP2515 + CAN

Este documento descreve as conexões elétricas utilizadas no projeto
**Distributed Sensor Network using CAN and ESP32**.

A arquitetura é composta por quatro nós físicos (1 gateway e 3 sensores),
todos conectados ao mesmo barramento CAN utilizando módulos MCP2515
com transceptor TJA1050.

---

## 1. Visão Geral do Hardware

Cada nó do sistema possui:

- 1 × ESP32 (DevKit ou equivalente)
- 1 × Módulo CAN MCP2515 (cristal de 8 MHz)
- 1 × Transceptor CAN TJA1050 (normalmente integrado ao módulo)
- Barramento CAN compartilhado (CAN_H e CAN_L)
- Resistores de terminação (120 Ω) nas extremidades do barramento

Todos os nós utilizam a mesma topologia de conexão.

---

## 2. Conexão ESP32 ↔ MCP2515 (SPI)

A comunicação entre o ESP32 e o MCP2515 é feita via SPI.
Foi utilizado o barramento **VSPI** do ESP32.

### Mapeamento de Pinos

| Sinal MCP2515 | Pino ESP32 | Descrição |
|--------------|-----------|-----------|
| VCC          | 5V*       | Alimentação do módulo |
| GND          | GND       | Terra comum |
| SCK          | GPIO 13   | Clock SPI |
| MOSI         | GPIO 23   | SPI Master Out |
| MISO         | GPIO 19   | SPI Master In |
| CS (SS)      | GPIO 5    | Chip Select |
| INT          | GPIO 4    | Interrupção do MCP2515 |

\* **Observação**: A maioria dos módulos MCP2515 com TJA1050 aceita 5V
na alimentação, mas os sinais SPI são tolerantes a 3,3V.
Sempre verificar o módulo utilizado.

---

## 3. Conexão CAN (Barramento)

O barramento CAN é comum a todos os nós e utiliza dois sinais diferenciais:

- **CAN_H**
- **CAN_L**

### Conexão típica entre os nós

        ESP32
          │
       MCP2515
          │
        TJA1050
          │
     CAN_H ──────────────── Barramento CAN
     CAN_L ────────────────

Todos os nós são conectados em paralelo ao mesmo barramento.

---

## 4. Resistores de Terminação

Para garantir a integridade do sinal no barramento CAN:

- Devem existir **dois resistores de 120 Ω**
- Um em cada extremidade física do barramento
- Nenhum nó intermediário deve possuir terminação ativa

[ Nó 1 ]──120Ω──┬──────────┬──120Ω──[ Nó 4 ]
                │          │
            [ Nó 2 ]   [ Nó 3 ]

Em muitos módulos, a terminação pode ser ativada por jumper.
Certifique-se de habilitar apenas nos nós das extremidades.

---

## 5. Alimentação

- Todos os ESP32 podem ser alimentados via USB
- O GND de todos os módulos deve estar em comum
- O barramento CAN **não fornece alimentação**

⚠️ **Importante**: Evitar diferenças de potencial entre os GNDs,
principalmente quando usar fontes separadas.

---

## 6. Observações Importantes

- O cristal do MCP2515 utilizado neste projeto é de **8 MHz**
  (configurado explicitamente no código).
- O bitrate CAN configurado é **500 kbps**.
- O pino INT é obrigatório para uso correto da biblioteca ACAN2515.
- Cabos curtos e par trançado são recomendados para CAN_H e CAN_L.

---

## 7. Reprodutibilidade

Este esquema de conexão é idêntico para:

- Nó Gateway
- Nós Sensores (1, 2 e 3)

A diferenciação entre gateway e sensores é feita **exclusivamente por firmware**.



