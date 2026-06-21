# **CAN Distributed Network**  
Projeto de rede distribuída utilizando ESP32 e MCP2515 sobre barramento CAN.  
O sistema implementa eleição de líder, sincronização por heartbeat, entrada dinâmica de nós, replicação de estado e tolerância a falhas.  
## **Hardware utilizado**  
Para cada nó da rede:  
- ESP32  
- MCP2515  
- Transceiver CAN (TJA1050 ou compatível)  
- LEDs de indicação  
O Gateway também utiliza ESP32 + MCP2515.  
## **Estrutura do projeto**  
.  
├── geral_v4.ino  
├── can_ids.h  
├── protocolo.h  
├── comandos.h  
├── comandos.cpp  
├── falhas.h  
├── falhas.cpp  
├── node_types.h  
├── node_config.h  
└── README.md  
   
## **Dependências**  
Instalar na Arduino IDE:  
### **ESP32 Arduino Core**  
Adicionar o gerenciador de placas ESP32:  
https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json  
   
Depois instalar:  
ESP32 by Espressif Systems  
   
### **Biblioteca MCP2515**  
Instalar:  
ACAN2515  
   
Autor:  
Pierre Molinaro  
   
## **Configuração dos nós**  
O identificador lógico do nó é definido em:  
const uint8_t NODE_ID = X;  
   
Valores possíveis:  
0 = Gateway  
1..255 = Nós funcionais  
   
Cada nó deve possuir um identificador único.  
Exemplo:  
const uint8_t NODE_ID = 0;  
   
Gateway.  
const uint8_t NODE_ID = 1;  
   
Primeiro sensor.  
const uint8_t NODE_ID = 2;  
   
Segundo sensor.  
## **Ligações do MCP2515**  
Configuração padrão utilizada:  
| | |  
|-|-|  
| **MCP2515** | **ESP32** |   
| CS | GPIO 5 |   
| INT | GPIO 4 |   
| SCK | GPIO 18 |   
| MISO | GPIO 19 |   
| MOSI | GPIO 23 |   
Velocidade CAN:  
500 kbps  
   
Cristal MCP2515:  
8 MHz  
   
Caso o módulo utilize cristal diferente, o valor deve ser alterado no código.  
## **Gravação**  
Abrir:  
geral_v4.ino  
   
Selecionar:  
ESP32 Dev Module  
   
Alterar:  
const uint8_t NODE_ID = X;  
   
Compilar.  
Gravar em cada ESP32.  
Repetir para todos os nós da rede.  
## **Inicialização da rede**  
Ligar todos os dispositivos.  
Ao iniciar:  
- Gateway entra em modo supervisor.  
- Nós funcionais entram em IDLE.  
Para iniciar a rede enviar pelo Gateway:  
22 00 FF 01  
   
O maior ID ativo assume a liderança.  
Após a eleição o líder começa a transmitir heartbeat.  
## **Estados dos nós**  
STATE_IDLE  
STATE_JOINING  
STATE_ELECTION  
STATE_RECOVERING  
STATE_LEADER  
STATE_FOLLOWER  
STATE_FAULT  
STATE_GATEWAY  
   
## **Comandos**  
### **Iniciar eleição**  
22 00 FF 01  
   
### **Solicitar status**  
22 20 FF 00  
   
### **Alterar frequência do heartbeat**  
22 30 FF 01  
22 30 FF 02  
22 30 FF 03  
22 30 FF 04  
22 30 FF 05  
   
Frequências:  
| | |  
|-|-|  
| **Modo** | **Período** |   
| 01 | 2000 ms |   
| 02 | 1500 ms |   
| 03 | 1000 ms |   
| 04 | 750 ms |   
| 05 | 500 ms |   
### **Desativar sensor**  
22 10 ID 00  
   
Exemplo:  
22 10 02 00  
   
### **Ativar sensor**  
22 10 ID 11  
   
Exemplo:  
22 10 02 11  
   
### **Limpar falha**  
22 10 ID 44  
   
Exemplo:  
22 10 02 44  
   
### **Ativar simulação de falha**  
22 10 ID 55  
   
Exemplo:  
22 10 02 55  
   
### **Desativar simulação de falha**  
22 10 ID 66  
   
Exemplo:  
22 10 02 66  
   
## **LEDs**  
Durante STATE_IDLE todos os LEDs permanecem acesos.  
Após a atribuição de função:  
### **LED Leader**  
Indica o líder da rede.  
### **LED Status**  
Pisca durante eventos de heartbeat.  
### **LED Fault**  
Indica nó desativado ou em falha.  
## **Detecção de falhas**  
O sistema implementa dois mecanismos principais.  
### **Falha por valor anômalo**  
O líder monitora os valores recebidos dos sensores.  
Após repetidas ocorrências de valor inválido o nó é marcado como:  
FOLLOWER_FAULT  
   
### **Falha por omissão**  
Se um nó deixar de responder por mais de cinco períodos de heartbeat ele é marcado como:  
FOLLOWER_FAULT  
   
## **Entrada dinâmica**  
Após a rede estar operacional um novo nó pode ser conectado.  
O nó detecta o heartbeat da rede, solicita entrada e é integrado sem provocar nova eleição.  
O líder atual permanece inalterado.  
## **Observações**  
- Não utilizar IDs duplicados.  
- O ID 0 deve ser reservado ao Gateway.  
- O Gateway não participa da eleição.  
- O Gateway não transmite dados de sensores.  
- O Gateway apenas supervisiona a rede e solicita recuperação em caso de falha do líder.  
   
