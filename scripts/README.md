**CAN TUI MONITOR**  
O **CAN TUI MONITOR** é um monitor serial em modo texto para acompanhar uma rede CAN por meio de um Gateway conectado ao computador.  
A interface funciona diretamente no terminal e foi feita para lembrar ferramentas como htop. Ela permite visualizar a rede em tempo real, consultar o estado dos nós e enviar comandos sem usar o Monitor Serial da Arduino IDE.  
O programa não acessa o barramento CAN diretamente. A comunicação ocorre pela porta serial do Gateway, que recebe os frames CAN e publica as informações no terminal.  
**Funcionalidades**  
O programa permite:  
- conectar e desconectar de uma porta serial;  
- listar as portas seriais disponíveis;  
- acompanhar mensagens publicadas pelo Gateway;  
- visualizar os nós encontrados automaticamente;  
- identificar o líder atual;  
- visualizar o último valor enviado por cada nó em hexadecimal;  
- visualizar a rodada em que o último valor foi recebido;  
- visualizar se o nó está ativo;  
- visualizar o estado confirmado pela rede;  
- enviar comandos de eleição, status, heartbeat e controle dos sensores;  
- ativar e desativar a simulação de falha por software;  
- usar comandos textuais ou comandos brutos em hexadecimal.  
O nó de ID 0 é tratado como **Gateway/Monitor**. Ele não é considerado um nó inválido.  
**Arquivo principal**  
O programa está no arquivo:  
can_tui_monitor_v8.py  
   
**Dependências**  
O programa usa Python e os seguintes pacotes:  
- pyserial: comunicação com a porta serial;  
- textual: construção da interface TUI;  
- rich: tabelas, textos, painéis e cores no terminal.  
Também são usados módulos da biblioteca padrão do Python:  
- argparse;  
- re;  
- time;  
- dataclasses;  
- typing.  
Os módulos da biblioteca padrão não precisam ser instalados separadamente.  
**Requisitos recomendados**  
- Linux Mint, Ubuntu ou outra distribuição baseada em Debian;  
- Python 3.9 ou superior;  
- uma porta USB serial disponível;  
- Gateway configurado para usar a mesma velocidade serial do programa;  
- terminal com suporte a cores.  
A velocidade serial padrão usada pelo programa é 115200 bps.  
**Instalação no Linux Mint, Ubuntu ou Debian**  
**1. Instalar os pacotes do sistema**  
Abra o terminal e execute:  
sudo apt update  
 sudo apt install python3-full python3-venv python3-pip  
   
Esses pacotes fornecem o Python, o pip e o suporte para ambientes virtuais.  
**2. Criar a pasta do projeto**  
mkdir -p ~/can_tui_monitor  
 cd ~/can_tui_monitor  
   
Copie o arquivo can_tui_monitor_v8.py para essa pasta.  
**3. Criar o ambiente virtual**  
python3 -m venv .venv  
   
**4. Ativar o ambiente virtual**  
source .venv/bin/activate  
   
Quando o ambiente estiver ativo, o terminal normalmente mostrará (.venv) antes do nome do usuário.  
Exemplo:  
(.venv) marcelo@theo:~/can_tui_monitor$  
   
**5. Atualizar o pip**  
python -m pip install --upgrade pip  
   
**6. Instalar as dependências Python**  
python -m pip install pyserial textual rich  
   
Outra opção é usar o arquivo requirements.txt:  
python -m pip install -r requirements.txt  
   
O conteúdo esperado do requirements.txt é:  
pyserial  
 textual  
 rich  
   
**Execução básica**  
Com o ambiente virtual ativo, execute:  
python can_tui_monitor_v8.py  
   
O programa será iniciado sem conexão automática. Dentro do TUI, use:  
/ports  
   
para listar as portas encontradas.  
Depois conecte usando, por exemplo:  
/connect /dev/ttyUSB0  
   
ou:  
/connect /dev/ttyACM0  
   
**Executar conectando automaticamente**  
É possível informar a porta ao iniciar o programa:  
python can_tui_monitor_v8.py --port /dev/ttyUSB0  
   
Forma reduzida:  
python can_tui_monitor_v8.py -p /dev/ttyUSB0  
   
Também é possível definir o baud rate:  
python can_tui_monitor_v8.py --port /dev/ttyUSB0 --baud 115200  
   
Forma reduzida:  
python can_tui_monitor_v8.py -p /dev/ttyUSB0 -b 115200  
   
**Informar nós iniciais**  
Por padrão, a tabela começa vazia e os nós são adicionados automaticamente conforme aparecem nas mensagens da rede.  
Para iniciar mostrando alguns IDs conhecidos:  
python can_tui_monitor_v8.py --nodes 0,1,2,3,4,5  
   
Também é possível combinar essa opção com a porta serial:  
python can_tui_monitor_v8.py -p /dev/ttyUSB0 -n 0,1,2,3,4,5  
   
A opção --nodes apenas cria as linhas iniciais da tabela. Outros nós continuam sendo adicionados automaticamente quando forem detectados.  
**Parâmetros de execução**  
-p, --port     Porta serial usada pelo Gateway  
 -b, --baud     Velocidade serial, padrão 115200  
 -n, --nodes    IDs iniciais separados por vírgula  
 -h, --help     Mostra a ajuda do programa  
   
Para visualizar a ajuda pelo terminal:  
python can_tui_monitor_v8.py --help  
   
**Comandos locais do TUI**  
Os comandos locais controlam o próprio monitor e não são enviados para a rede CAN.  
/ports                  Lista as portas seriais disponíveis  
 /connect <porta>        Conecta na porta informada  
 /disconnect             Desconecta da porta serial  
 /disc                    Forma reduzida para desconectar  
 /dc                      Forma reduzida para desconectar  
 /help                    Mostra a ajuda dentro do TUI  
   
Exemplos:  
/ports  
 /connect /dev/ttyUSB0  
 /dc  
   
**Atalhos de teclado**  
e    Envia o comando de eleição  
 s    Solicita o status de todos os nós  
 p    Lista as portas seriais  
 x    Desconecta da porta serial  
 h    Mostra a ajuda  
 q    Fecha o programa  
   
Os atalhos funcionam quando o campo de entrada não está consumindo a tecla como parte de um comando.  
**Comandos da rede**  
**Iniciar eleição**  
eleicao  
   
Comando enviado:  
22 00 FF 01  
   
**Solicitar o status de todos os nós**  
status  
   
Comando enviado:  
22 20 FF 00  
   
**Solicitar o status de um nó**  
status 3  
   
Comando enviado:  
22 20 03 00  
   
O ID digitado nos aliases é interpretado como decimal. Também é possível usar o prefixo hexadecimal:  
status 0x0A  
   
**Alterar o heartbeat**  
hb 1  
 hb 2  
 hb 3  
 hb 4  
 hb 5  
   
Os modos disponíveis são:  
Modo 1    2000 ms  
 Modo 2    1500 ms  
 Modo 3    1000 ms  
 Modo 4     750 ms  
 Modo 5     500 ms  
   
Exemplo:  
hb 5  
   
Comando enviado:  
22 30 FF 05  
   
**Desativar um nó manualmente**  
desativar 3  
   
Comando enviado:  
22 10 03 00  
   
**Reativar um nó**  
reativar 3  
   
Comando enviado:  
22 10 03 11  
   
**Limpar uma falha confirmada**  
limpar 3  
   
Comando enviado:  
22 10 03 44  
   
Esse comando também solicita a reativação do sensor e o desligamento da simulação de falha no nó.  
**Ativar simulação de falha por software**  
sim 3 on  
   
Comando enviado:  
22 10 03 55  
   
Também são aceitos:  
simular 3 on  
 injecao 3 on  
   
**Desativar simulação de falha por software**  
sim 3 off  
   
Comando enviado:  
22 10 03 66  
   
**Comandos brutos em hexadecimal**  
O TUI também aceita comandos com quatro bytes em hexadecimal:  
22 00 FF 01  
 22 20 FF 00  
 22 10 03 00  
 22 10 03 11  
 22 10 03 44  
 22 10 03 55  
 22 10 03 66  
 22 30 FF 05  
   
Cada byte precisa ter no máximo dois dígitos hexadecimais.  
**Comando reservado ao líder**  
O comando abaixo não pode ser enviado pelo TUI:  
22 10 ID 33  
   
Ele representa a desativação de um nó por falha confirmada. Essa decisão pertence ao líder da rede.  
Mesmo que o comando seja digitado manualmente, o TUI bloqueia o envio.  
**Atualização dos estados**  
O envio de um comando pelo TUI não muda imediatamente o estado mostrado na tabela.  
Por exemplo, ao executar:  
desativar 3  
   
O programa envia 22 10 03 00, mas não altera o nó 3 para Desativado apenas por causa do comando enviado.  
O estado visual só é alterado quando o Gateway publica uma resposta de status ou uma atualização de estado da própria rede. Isso evita mostrar um resultado que ainda não foi confirmado.  
As principais mensagens consideradas são:  
23 21 ID STATUS    Resposta de status  
 23 50 ID STATUS    Atualização de estado  
 23 51 ID STATUS    Atualização forçada de estado  
   
**Estados reconhecidos**  
0x00    Líder  
 0x01    Ativo  
 0x02    Desativado  
 0x03    Falha  
 0x04    Gateway  
 0x05    Entrando  
 0x06    Conflito de líder  
 0xFF    Desconhecido  
   
**Informações mostradas na tabela**  
A tabela contém as seguintes colunas:  
Nó              ID do nó. O nó 0 aparece como Gateway  
 Estado          Estado confirmado pela rede  
 Falha           Tipo de falha observada ou confirmada  
 Último valor    Último valor recebido em hexadecimal  
 Rodada          Rodada do último valor recebido, em decimal  
 Ativo           Indica se o nó foi observado como ativo  
 RX              Quantidade de mensagens processadas para o nó  
   
O líder é considerado ativo quando um heartbeat dele é recebido.  
O Gateway é considerado ativo quando o TUI recebe mensagens iniciadas por [GW].  
Um nó funcional é considerado ativo quando o Gateway recebe e publica seus dados de sensor ou quando a rede confirma seu estado como ativo.  
**Porta serial ocupada**  
A porta serial só pode ser usada por um programa de cada vez.  
Antes de abrir o TUI, feche:  
- Monitor Serial da Arduino IDE;  
- PlatformIO Serial Monitor;  
- screen;  
- minicom;  
- qualquer outro programa conectado à mesma porta.  
**Erro de permissão na porta serial**  
Se aparecer uma mensagem semelhante a Permission denied, adicione o usuário ao grupo dialout:  
sudo usermod -aG dialout $USER  
   
Depois encerre a sessão do usuário e entre novamente. Também é possível reiniciar o computador.  
Para confirmar os grupos do usuário:  
groups  
   
O grupo dialout deve aparecer na lista.  
Evite executar o monitor com sudo. O correto é ajustar a permissão do usuário.  
**Erro **externally-managed-environment  
Esse erro ocorre quando o sistema impede a instalação de pacotes Python diretamente no ambiente global.  
Não use:  
pip install --break-system-packages  
   
Use o ambiente virtual indicado neste README:  
python3 -m venv .venv  
 source .venv/bin/activate  
 python -m pip install pyserial textual rich  
   
**Erro **ModuleNotFoundError  
Exemplo:  
ModuleNotFoundError: No module named 'serial'  
   
Ative o ambiente virtual e instale as dependências:  
cd ~/can_tui_monitor  
 source .venv/bin/activate  
 python -m pip install pyserial textual rich  
   
Confirme que o Python usado pertence ao ambiente virtual:  
which python  
   
A saída deve apontar para algo semelhante a:  
/home/usuario/can_tui_monitor/.venv/bin/python  
   
**Tela desorganizada ou sem cores**  
Use um terminal com suporte a cores e aumente o tamanho da janela.  
Terminais comuns que funcionam bem:  
- GNOME Terminal;  
- Konsole;  
- Tilix;  
- terminal padrão do Linux Mint;  
- Windows Terminal.  
O programa precisa de espaço para mostrar o cabeçalho, a tabela de nós, o tráfego e a linha de comandos.  
**Encerrar o ambiente virtual**  
Depois de fechar o programa, use:  
deactivate  
   
**Execuções futuras**  
Nas próximas vezes, não é necessário instalar tudo novamente. Use apenas:  
cd ~/can_tui_monitor  
 source .venv/bin/activate  
 python can_tui_monitor_v8.py  
   
Ou conectando automaticamente:  
cd ~/can_tui_monitor  
 source .venv/bin/activate  
 python can_tui_monitor_v8.py -p /dev/ttyUSB0  
   
**Estrutura mínima sugerida**  
can_tui_monitor/  
 ├── .venv/  
 ├── can_tui_monitor_v8.py  
 ├── requirements.txt  
 └── README.md  
   
**Observação final**  
O TUI depende do formato das mensagens publicadas pelo firmware do Gateway. Se os textos ou campos enviados pela serial forem alterados, as expressões de leitura do arquivo can_tui_monitor_v8.py também poderão precisar de atualização.  
