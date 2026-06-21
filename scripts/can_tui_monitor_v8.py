import argparse
import re
import time
from dataclasses import dataclass, field
from typing import Optional

import serial
import serial.tools.list_ports

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Header, Footer, Static, RichLog, Input


# =========================================================
# Protocolo real da rede
# =========================================================

CAN_ID_ELECTION = 0x050
CAN_ID_LEADER = 0x060
CAN_ID_CONTROL = 0x080
CAN_ID_HEARTBEAT = 0x100
CAN_ID_SENSOR = 0x200

CTRL_OPCODE = 0x22
CTRL_SUBCMD_ELECTION = 0x00
CTRL_SUBCMD_SENSOR = 0x10
CTRL_SUBCMD_STATUS_REQUEST = 0x20
CTRL_SUBCMD_HEARTBEAT_RATE = 0x30
CTRL_SUBCMD_JOIN_REQUEST = 0x40

CTRL_TARGET_BROADCAST = 0xFF

CTRL_ACTION_START = 0x01
CTRL_ACTION_OFF = 0x00
CTRL_ACTION_ON = 0x11
CTRL_ACTION_DISABLE_FAULT = 0x33
CTRL_ACTION_CLEAR_FAULT = 0x44
CTRL_ACTION_SIM_FAULT_ON = 0x55
CTRL_ACTION_SIM_FAULT_OFF = 0x66

STATUS_OPCODE = 0x23
CTRL_SUBCMD_STATUS_RESPONSE = 0x21
CTRL_SUBCMD_JOIN_ACCEPT = 0x41
CTRL_SUBCMD_STATE_UPDATE = 0x50
CTRL_SUBCMD_STATE_FORCE_UPDATE = 0x51

STATUS_ROLE_LEADER = 0x00
STATUS_FOLLOWER_OK = 0x01
STATUS_FOLLOWER_DISABLED = 0x02
STATUS_FOLLOWER_FAULT = 0x03
STATUS_GATEWAY = 0x04
STATUS_JOINING = 0x05
STATUS_LEADER_CONFLICT = 0x06
STATUS_UNKNOWN = 0xFF

HB_PERIODS = {
    1: 2000,
    2: 1500,
    3: 1000,
    4: 750,
    5: 500,
}

STATUS_NAMES = {
    STATUS_ROLE_LEADER: "Lider",
    STATUS_FOLLOWER_OK: "Ativo",
    STATUS_FOLLOWER_DISABLED: "Desativado",
    STATUS_FOLLOWER_FAULT: "Falha",
    STATUS_GATEWAY: "Gateway",
    STATUS_JOINING: "Entrando",
    STATUS_LEADER_CONFLICT: "Conflito lider",
    STATUS_UNKNOWN: "Desconhecido",
}

TEXT_STATUS_TO_NAME = {
    "LIDER": "Lider",
    "ATIVO": "Ativo",
    "DESATIVADO": "Desativado",
    "FALHA": "Falha",
    "GATEWAY": "Gateway",
    "ENTRANDO": "Entrando",
    "CONFLITO_LIDER": "Conflito lider",
    "DESCONHECIDO": "Desconhecido",
    "INVALIDO": "Desconhecido",
}


# =========================================================
# Regexes para a saida real do Gateway/NODE
# =========================================================

GW_HEARTBEAT_RE = re.compile(
    r"\[GW\]\s+HEARTBEAT\s+lider=(?P<leader>\d+)\s+"
    r"rodada=(?P<tick>\d+)\s+"
    r"sensores_ativos=(?P<active>\d+)\s+"
    r"modo=(?P<mode>\d+)\s+"
    r"periodo=(?P<period>\d+)\s+ms"
)

GW_LEADER_OBS_RE = re.compile(
    r"\[GW\]\s+Lider observado:\s+NODE\s+(?P<node>\d+)"
)

GW_SENSOR_RE = re.compile(
    r"\[GW\]\s+SENSOR\s+sensor=(?P<node>\d+)\s+"
    r"rodada=(?P<tick>\d+)\s+"
    r"valor=0x(?P<value>[0-9A-Fa-f]+)\s+"
    r"ativo=(?P<active>\d+)"
)

GW_CONTROL_RX_RE = re.compile(
    r"\[GW\]\s+CONTROLE RX\s+"
    r"(?P<b0>[0-9A-Fa-f]+)\s+"
    r"(?P<b1>[0-9A-Fa-f]+)\s+"
    r"(?P<b2>[0-9A-Fa-f]+)\s+"
    r"(?P<b3>[0-9A-Fa-f]+)"
)

GW_STATUS_UPDATE_RE = re.compile(
    r"\[GW\]\s+Atualizacao(?: FORCADA)? de status recebida:\s+"
    r"\[STATUS\]\s+NODE\s+(?P<node>\d+)\s+estado=(?P<state>[A-Z_]+)"
)

STATUS_LINE_RE = re.compile(
    r"\[STATUS\]\s+NODE\s+(?P<node>\d+)\s+estado=(?P<state>[A-Z_]+)"
)

STATUS_RX_RE = re.compile(
    r"\[STATUS RX\]\s+NODE\s+(?P<node>\d+)\s+estado=(?P<state>[A-Z_]+)"
)

STATUS_TX_RE = re.compile(
    r"\[STATUS(?: FORCE)? TX\]\s+node=(?P<node>\d+)\s+status=(?P<status>[0-9A-Fa-f]+)"
)

NODE_STATUS_TX_CODE_RE = re.compile(
    r"\[NODE\s+(?P<node>\d+)\]\s+\[STATUS TX\]\s+codigo=(?P<status>[0-9A-Fa-f]+)"
)

NODE_HEARTBEAT_TX_RE = re.compile(
    r"\[NODE\s+(?P<node>\d+)\]\s+\[HEARTBEAT TX\]\s+"
    r"rodada=(?P<tick>\d+)\s+"
    r"sensores_ativos=(?P<active>\d+)\s+"
    r"modo=(?P<mode>\d+)\s+"
    r"periodo=(?P<period>\d+)\s+ms"
)

NODE_SENSOR_TX_RE = re.compile(
    r"\[NODE\s+(?P<node_prefix>\d+)\]\s+\[SENSOR TX\]\s+"
    r"sensor=(?P<node>\d+)\s+"
    r"rodada=(?P<tick>\d+)\s+"
    r"valor=0x(?P<value>[0-9A-Fa-f]+)"
)

NODE_DISCOVERED_RE = re.compile(
    r"(?:\[GW\]|\[DESCOBERTA\])\s+No descoberto:\s+NODE\s+(?P<node>\d+)"
)

GW_ELECTION_RX_RE = re.compile(
    r"\[GW\]\s+ELEICAO recebida de NODE\s+(?P<node>\d+)"
)

OLD_FRAME_RE = re.compile(
    r"\[(?P<ms>\d+)\s+ms\]\s+"
    r"(?P<dir>RX|TX)\s+"
    r"ID=0x(?P<id>[0-9A-Fa-f]+)\s+"
    r"DLC=(?P<dlc>\d+)\s+"
    r"DATA=(?P<data>[0-9A-Fa-f ]*)"
    r"(?:\s+\|\s*(?P<desc>.*))?"
)


@dataclass
class NodeState:
    node_id: int
    state: str = "Desconhecido"
    fault: str = "Nenhuma"
    last_value: str = "-"
    last_tick: str = "-"
    active: str = "-"
    rx_count: int = 0
    last_seen: Optional[float] = None


@dataclass
class NetworkState:
    nodes: dict[int, NodeState] = field(default_factory=dict)
    leader: Optional[int] = None
    heartbeat_mode: Optional[int] = None
    heartbeat_period: Optional[int] = None
    heartbeat_tick: Optional[int] = None
    active_sensors: Optional[int] = None
    frames_rx: int = 0
    frames_tx: int = 0
    events: int = 0
    errors: int = 0
    connected_since: Optional[float] = None

    def get_node(self, node_id: int) -> NodeState:
        if node_id not in self.nodes:
            self.nodes[node_id] = NodeState(node_id=node_id)
        return self.nodes[node_id]


class CanTuiMonitor(App):
    CSS = """
    Screen {
        background: #101010;
    }

    #main {
        height: 100%;
    }

    #summary {
        height: 5;
        margin: 0 1;
    }

    #nodes {
        height: 12;
        margin: 0 1;
    }

    #traffic {
        height: 1fr;
        margin: 0 1;
        border: solid #666600;
    }

    #command {
        height: 3;
        margin: 0 1 1 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Sair"),
        ("p", "show_ports", "Portas"),
        ("s", "send_status", "Status"),
        ("e", "send_election", "Eleicao"),
        ("x", "disconnect", "Desconectar"),
        ("h", "show_help", "Ajuda"),
    ]

    def __init__(self, port: Optional[str], baud: int, initial_nodes: list[int]):
        super().__init__()
        self.title = "CAN TUI MONITOR"
        self.sub_title = "Supervisorio serial minimo"

        self.port = port
        self.baud = baud
        self.ser: Optional[serial.Serial] = None
        self.state = NetworkState()

        for node_id in initial_nodes:
            self.state.nodes[node_id] = NodeState(node_id=node_id)

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical(id="main"):
            yield Static(id="summary")
            yield Static(id="nodes")
            yield RichLog(id="traffic", wrap=True, highlight=False, markup=False)
            yield Input(
                placeholder="Comando: status | eleicao | hb 5 | desativar 3 | reativar 3 | limpar 3 | sim 3 on | sim 3 off | /connect /dev/ttyUSB0",
                id="command",
            )

        yield Footer()

    def on_mount(self) -> None:
        self.summary = self.query_one("#summary", Static)
        self.nodes_panel = self.query_one("#nodes", Static)
        self.traffic = self.query_one("#traffic", RichLog)
        self.command = self.query_one("#command", Input)

        self.set_interval(0.05, self.poll_serial)
        self.set_interval(0.5, self.refresh_screen)

        self.refresh_screen()
        self.write_info("CAN TUI MONITOR iniciado.")
        self.write_info("Use /ports para listar portas seriais.")
        self.write_info("Use /connect <porta> para conectar.")
        self.write_info("Use h para ajuda.")

        if self.port:
            self.connect_serial(self.port)
        else:
            self.show_ports()

        self.command.focus()

    # =========================================================
    # Serial
    # =========================================================

    def connect_serial(self, port: str) -> None:
        self.disconnect_serial(silent=True)

        try:
            self.ser = serial.Serial(port=port, baudrate=self.baud, timeout=0)
            self.port = port
            self.state.connected_since = time.monotonic()

            try:
                self.ser.reset_input_buffer()
            except Exception:
                pass

            self.write_ok(f"Conectado em {port} @ {self.baud} bps.")
        except Exception as exc:
            self.ser = None
            self.write_error(f"Falha ao conectar em {port}: {exc}")

    def disconnect_serial(self, silent: bool = False) -> None:
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass

        self.ser = None
        self.state.connected_since = None

        if not silent:
            self.write_info("Serial desconectada.")

    def poll_serial(self) -> None:
        if not self.ser or not self.ser.is_open:
            return

        try:
            while self.ser.in_waiting:
                raw = self.ser.readline()

                if not raw:
                    break

                line = raw.decode("utf-8", errors="replace").strip()

                if line:
                    self.handle_serial_line(line)

        except Exception as exc:
            self.write_error(f"Erro de leitura serial: {exc}")
            self.disconnect_serial(silent=True)

    # =========================================================
    # Parser da saida serial real
    # =========================================================

    def handle_serial_line(self, line: str) -> None:
        if line.startswith("[GW]"):
            self.mark_gateway_seen()

        handlers = [
            self.parse_gw_heartbeat,
            self.parse_gw_sensor,
            self.parse_gw_control_rx,
            self.parse_gw_status_update,
            self.parse_status_line,
            self.parse_status_rx,
            self.parse_status_tx,
            self.parse_node_status_tx_code,
            self.parse_node_heartbeat_tx,
            self.parse_node_sensor_tx,
            self.parse_gw_leader_observed,
            self.parse_node_discovered,
            self.parse_gw_election_rx,
            self.parse_old_frame_format,
        ]

        for handler in handlers:
            if handler(line):
                return

        if "[ERRO]" in line or " invalido" in line.lower() or "falha" in line.lower():
            self.state.events += 1
            self.write_event(line)
            return

        self.write_raw(line)

    def mark_gateway_seen(self) -> None:
        now = time.monotonic()
        gateway = self.state.get_node(0)
        gateway.state = "Gateway"
        gateway.active = "Sim"
        gateway.last_seen = now
        gateway.rx_count += 1

    def parse_gw_heartbeat(self, line: str) -> bool:
        m = GW_HEARTBEAT_RE.search(line)
        if not m:
            return False

        leader = int(m.group("leader"))
        tick = int(m.group("tick"))
        active = int(m.group("active"))
        mode = int(m.group("mode"))
        period = int(m.group("period"))

        self.apply_heartbeat(leader, tick, active, mode, period)
        self.state.frames_rx += 1
        self.write_rx(line)
        return True

    def parse_gw_sensor(self, line: str) -> bool:
        m = GW_SENSOR_RE.search(line)
        if not m:
            return False

        node_id = int(m.group("node"))
        tick = int(m.group("tick"))
        value = int(m.group("value"), 16)
        active = int(m.group("active"))

        self.apply_sensor_value(node_id, tick, value, active)
        self.state.frames_rx += 1
        self.write_rx(line)
        return True

    def parse_gw_control_rx(self, line: str) -> bool:
        m = GW_CONTROL_RX_RE.search(line)
        if not m:
            return False

        data = [
            int(m.group("b0"), 16),
            int(m.group("b1"), 16),
            int(m.group("b2"), 16),
            int(m.group("b3"), 16),
        ]

        self.apply_control_or_status_frame(data)
        self.state.frames_rx += 1
        self.write_ctrl(line)
        return True

    def parse_gw_status_update(self, line: str) -> bool:
        m = GW_STATUS_UPDATE_RE.search(line)
        if not m:
            return False

        node_id = int(m.group("node"))
        state_name = self.text_status_name(m.group("state"))

        self.apply_node_status(node_id, state_name)
        self.state.frames_rx += 1
        self.write_status(line)
        return True

    def parse_status_line(self, line: str) -> bool:
        m = STATUS_LINE_RE.search(line)
        if not m:
            return False

        node_id = int(m.group("node"))
        state_name = self.text_status_name(m.group("state"))

        self.apply_node_status(node_id, state_name)
        self.state.frames_rx += 1
        self.write_status(line)
        return True

    def parse_status_rx(self, line: str) -> bool:
        m = STATUS_RX_RE.search(line)
        if not m:
            return False

        node_id = int(m.group("node"))
        state_name = self.text_status_name(m.group("state"))

        self.apply_node_status(node_id, state_name)
        self.state.frames_rx += 1
        self.write_status(line)
        return True

    def parse_status_tx(self, line: str) -> bool:
        m = STATUS_TX_RE.search(line)
        if not m:
            return False

        node_id = int(m.group("node"))
        status = int(m.group("status"), 16)

        self.apply_node_status(node_id, STATUS_NAMES.get(status, f"0x{status:02X}"))
        self.state.frames_rx += 1
        self.write_status(line)
        return True

    def parse_node_status_tx_code(self, line: str) -> bool:
        m = NODE_STATUS_TX_CODE_RE.search(line)
        if not m:
            return False

        node_id = int(m.group("node"))
        status = int(m.group("status"), 16)

        self.apply_node_status(node_id, STATUS_NAMES.get(status, f"0x{status:02X}"))
        self.state.frames_rx += 1
        self.write_status(line)
        return True

    def parse_node_heartbeat_tx(self, line: str) -> bool:
        m = NODE_HEARTBEAT_TX_RE.search(line)
        if not m:
            return False

        leader = int(m.group("node"))
        tick = int(m.group("tick"))
        active = int(m.group("active"))
        mode = int(m.group("mode"))
        period = int(m.group("period"))

        self.apply_heartbeat(leader, tick, active, mode, period)
        self.state.frames_rx += 1
        self.write_rx(line)
        return True

    def parse_node_sensor_tx(self, line: str) -> bool:
        m = NODE_SENSOR_TX_RE.search(line)
        if not m:
            return False

        node_id = int(m.group("node"))
        tick = int(m.group("tick"))
        value = int(m.group("value"), 16)

        self.apply_sensor_value(node_id, tick, value, 1)
        self.state.frames_rx += 1
        self.write_rx(line)
        return True

    def parse_gw_leader_observed(self, line: str) -> bool:
        m = GW_LEADER_OBS_RE.search(line)
        if not m:
            return False

        leader = int(m.group("node"))
        self.state.leader = leader
        self.apply_node_status(leader, "Lider")
        self.state.events += 1
        self.write_event(line)
        return True

    def parse_node_discovered(self, line: str) -> bool:
        m = NODE_DISCOVERED_RE.search(line)
        if not m:
            return False

        node_id = int(m.group("node"))
        node = self.state.get_node(node_id)
        node.state = "Entrando" if node.state == "Desconhecido" else node.state
        node.last_seen = time.monotonic()
        self.state.events += 1
        self.write_event(line)
        return True

    def parse_gw_election_rx(self, line: str) -> bool:
        m = GW_ELECTION_RX_RE.search(line)
        if not m:
            return False

        node_id = int(m.group("node"))
        self.apply_node_status(node_id, "Entrando")
        self.state.events += 1
        self.write_event(line)
        return True

    def parse_old_frame_format(self, line: str) -> bool:
        m = OLD_FRAME_RE.match(line)
        if not m:
            return False

        direction = m.group("dir")
        data_text = m.group("data").strip()
        data = []

        if data_text:
            try:
                data = [int(x, 16) for x in data_text.split()]
            except ValueError:
                data = []

        if direction == "RX":
            self.state.frames_rx += 1
            self.write_rx(line)
        else:
            self.state.frames_tx += 1
            self.write_tx(line)

        if data:
            self.apply_control_or_status_frame(data)

        return True

    # =========================================================
    # Atualizacao do modelo
    # =========================================================

    def apply_heartbeat(self, leader: int, tick: int, active: int, mode: int, period: int) -> None:
        now = time.monotonic()

        self.state.leader = leader
        self.state.heartbeat_tick = tick
        self.state.active_sensors = active
        self.state.heartbeat_mode = mode
        self.state.heartbeat_period = period

        leader_node = self.state.get_node(leader)
        leader_node.state = "Gateway" if leader == 0 else "Lider"
        leader_node.last_tick = str(tick)
        leader_node.active = "Sim"
        leader_node.last_seen = now
        leader_node.rx_count += 1

    def apply_sensor_value(self, node_id: int, tick: int, value: int, active: int) -> None:
        now = time.monotonic()
        node = self.state.get_node(node_id)

        if node.state in ("Desconhecido", "Entrando"):
            node.state = "Ativo" if active else "Desativado"

        if active == 0:
            node.state = "Desativado"

        node.last_value = f"0x{value:02X}"
        node.last_tick = str(tick)
        node.active = "Sim" if active else "Nao"
        node.last_seen = now
        node.rx_count += 1

        if value == 0xFF:
            node.fault = "Valor anomalo"
        elif node.fault == "Valor anomalo" and node.state != "Falha":
            node.fault = "Nenhuma"

    def apply_node_status(self, node_id: int, state_name: str) -> None:
        now = time.monotonic()
        node = self.state.get_node(node_id)

        if node_id == 0 and state_name in ("Desconhecido", "Invalido"):
            state_name = "Gateway"

        node.state = state_name
        node.last_seen = now
        node.rx_count += 1

        if state_name == "Lider":
            self.state.leader = node_id
            node.active = "Sim"
            node.fault = "Nenhuma"
        elif state_name == "Gateway":
            node.active = "Sim"
            node.fault = "Nenhuma"
        elif state_name == "Ativo":
            node.active = "Sim"
            if node.fault == "Confirmada":
                node.fault = "Nenhuma"
        elif state_name == "Falha":
            node.active = "Nao"
            node.fault = "Confirmada"
        elif state_name == "Desativado":
            node.active = "Nao"
        elif state_name == "Entrando":
            node.active = "Sim"
            if node.fault == "Confirmada":
                node.fault = "Nenhuma"

    def apply_control_or_status_frame(self, data: list[int]) -> None:
        if len(data) < 4:
            return

        b0, b1, b2, b3 = data[:4]

        if b0 == STATUS_OPCODE and b1 in (
            CTRL_SUBCMD_STATUS_RESPONSE,
            CTRL_SUBCMD_STATE_UPDATE,
            CTRL_SUBCMD_STATE_FORCE_UPDATE,
        ):
            self.apply_node_status(b2, STATUS_NAMES.get(b3, f"0x{b3:02X}"))
            return

        if b0 != CTRL_OPCODE:
            return

        if b1 == CTRL_SUBCMD_ELECTION and b2 == CTRL_TARGET_BROADCAST and b3 == CTRL_ACTION_START:
            self.state.events += 1
            return

        if b1 == CTRL_SUBCMD_SENSOR:
            # Comandos de sensor observados ou enviados nao alteram o estado visual.
            # O estado so muda quando a propria rede publica STATUS/UPDATE.
            return

        if b1 == CTRL_SUBCMD_HEARTBEAT_RATE:
            self.state.heartbeat_mode = b3
            self.state.heartbeat_period = HB_PERIODS.get(b3)
            return

    def text_status_name(self, raw: str) -> str:
        return TEXT_STATUS_TO_NAME.get(raw.upper(), raw)

    # =========================================================
    # Interface
    # =========================================================

    def refresh_screen(self) -> None:
        self.summary.update(self.build_summary_panel())
        self.nodes_panel.update(self.build_nodes_table())

    def build_summary_panel(self) -> Panel:
        connected = self.ser is not None and self.ser.is_open

        conn_text = "CONECTADO" if connected else "DESCONECTADO"
        port_text = self.port or "-"

        if self.state.connected_since:
            uptime = int(time.monotonic() - self.state.connected_since)
            uptime_text = f"{uptime // 60:02d}:{uptime % 60:02d}"
        else:
            uptime_text = "--:--"

        leader = self.state.leader if self.state.leader is not None else "-"
        hb_mode = self.state.heartbeat_mode if self.state.heartbeat_mode is not None else "-"
        hb_period = (
            f"{self.state.heartbeat_period} ms"
            if self.state.heartbeat_period is not None
            else "-"
        )
        hb_tick = (
            str(self.state.heartbeat_tick)
            if self.state.heartbeat_tick is not None
            else "-"
        )
        active = self.state.active_sensors if self.state.active_sensors is not None else "-"

        text = (
            f"Porta: {port_text} | Baud: {self.baud} | Estado: {conn_text} | Uptime: {uptime_text}\n"
            f"Lider: {leader} | HB: modo {hb_mode} / {hb_period} | Rodada: {hb_tick} | Sensores ativos: {active} | "
            f"RX: {self.state.frames_rx} | TX: {self.state.frames_tx} | Eventos: {self.state.events}"
        )

        body_style = "green" if connected else "yellow"

        return Panel(
            Text(text, style=body_style),
            title=Text("CAN TUI MONITOR", style="bold yellow"),
            border_style="yellow",
        )

    def build_nodes_table(self) -> Table:
        table = Table(title="Estado dos nos", expand=True)

        table.add_column("No", justify="right", width=12)
        table.add_column("Estado", width=18)
        table.add_column("Falha", width=18)
        table.add_column("Ultimo valor", width=16)
        table.add_column("Rodada", width=10)
        table.add_column("Ativo", width=8)
        table.add_column("RX", justify="right", width=8)

        for node_id in sorted(self.state.nodes):
            node = self.state.nodes[node_id]

            table.add_row(
                self.node_label(node.node_id),
                Text(node.state, style=self.style_for_state(node.state)),
                Text(node.fault, style=self.style_for_fault(node.fault)),
                Text(node.last_value, style="bold magenta"),
                node.last_tick,
                node.active,
                str(node.rx_count),
            )

        return table

    def node_label(self, node_id: int) -> str:
        if node_id == 0:
            return "0 Gateway"
        return str(node_id)

    def style_for_state(self, state: str) -> str:
        s = state.lower()

        if "lider" in s:
            return "bold cyan"
        if "ativo" in s or "gateway" in s:
            return "green"
        if "desativado" in s or "entrando" in s:
            return "yellow"
        if "falha" in s or "conflito" in s:
            return "bold red"

        return "white"

    def style_for_fault(self, fault: str) -> str:
        f = fault.lower()

        if f == "nenhuma":
            return "green"
        if "simulada" in f or "valor" in f:
            return "yellow"
        if "confirmada" in f:
            return "bold red"

        return "white"

    # =========================================================
    # Entrada do usuario
    # =========================================================

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        self.command.value = ""

        if not value:
            return

        if value.startswith("/"):
            self.handle_local_command(value)
            return

        command = self.build_command(value)

        if command is None:
            self.write_error("Comando invalido. Use h para ajuda.")
            return

        if self.is_leader_reserved_command(command):
            self.write_error("Comando bloqueado no TUI: 22 10 ID 33 e reservado ao lider.")
            return

        self.send_serial_command(command)

    def handle_local_command(self, value: str) -> None:
        parts = value.split()
        cmd = parts[0].lower()

        if cmd == "/ports":
            self.show_ports()
            return

        if cmd == "/connect":
            if len(parts) < 2:
                self.write_error("Uso: /connect <porta>")
                return
            self.connect_serial(parts[1])
            return

        if cmd in ("/disconnect", "/disc", "/dc"):
            self.disconnect_serial()
            return

        if cmd == "/help":
            self.show_help()
            return

        self.write_error(f"Comando local desconhecido: {cmd}")

    def show_ports(self) -> None:
        ports = list(serial.tools.list_ports.comports())

        if not ports:
            self.write_error("Nenhuma porta serial encontrada.")
            return

        self.write_info("Portas seriais disponiveis:")

        for port in ports:
            desc = port.description or "-"
            self.write_info(f"  {port.device} | {desc}")

    def send_serial_command(self, command: str) -> None:
        if not self.ser or not self.ser.is_open:
            self.write_error("Serial desconectada. Use /connect <porta>.")
            return

        try:
            self.ser.write((command + "\n").encode("utf-8"))
            self.ser.flush()

            self.state.frames_tx += 1
            self.write_tx(f"TX SERIAL > {command}")

        except Exception as exc:
            self.write_error(f"Erro ao enviar comando: {exc}")
            self.disconnect_serial(silent=True)

    def apply_sent_command_to_local_state(self, command: str) -> None:
        try:
            data = [int(x, 16) for x in command.split()]
        except ValueError:
            return

        self.apply_control_or_status_frame(data)

    def build_command(self, value: str) -> Optional[str]:
        tokens = value.strip().split()

        if len(tokens) == 4 and all(self.is_hex_byte(t) for t in tokens):
            return " ".join(f"{int(t, 16):02X}" for t in tokens)

        if not tokens:
            return None

        op = tokens[0].lower()

        if op in ("eleicao", "eleição"):
            return "22 00 FF 01"

        if op == "status":
            if len(tokens) == 1:
                return "22 20 FF 00"

            node = self.parse_number(tokens[1])
            if node is None:
                return None

            return f"22 20 {node:02X} 00"

        if op in ("hb", "heartbeat"):
            if len(tokens) != 2:
                return None

            mode = self.parse_number(tokens[1])
            if mode is None or mode < 1 or mode > 5:
                return None

            return f"22 30 FF {mode:02X}"

        if op == "desativar":
            if len(tokens) != 2:
                return None

            node = self.parse_number(tokens[1])
            if node is None:
                return None

            return f"22 10 {node:02X} 00"

        if op == "reativar":
            if len(tokens) != 2:
                return None

            node = self.parse_number(tokens[1])
            if node is None:
                return None

            return f"22 10 {node:02X} 11"

        if op == "limpar":
            if len(tokens) != 2:
                return None

            node = self.parse_number(tokens[1])
            if node is None:
                return None

            return f"22 10 {node:02X} 44"

        if op in ("sim", "simular", "injecao", "injeção"):
            if len(tokens) != 3:
                return None

            node = self.parse_number(tokens[1])
            action = tokens[2].lower()

            if node is None:
                return None

            if action in ("on", "1", "ativar", "ligar"):
                return f"22 10 {node:02X} 55"

            if action in ("off", "0", "desativar", "desligar"):
                return f"22 10 {node:02X} 66"

            return None

        return None

    def is_leader_reserved_command(self, command: str) -> bool:
        try:
            data = [int(x, 16) for x in command.split()]
        except ValueError:
            return False

        return (
            len(data) == 4
            and data[0] == CTRL_OPCODE
            and data[1] == CTRL_SUBCMD_SENSOR
            and data[3] == CTRL_ACTION_DISABLE_FAULT
        )

    def parse_number(self, token: str) -> Optional[int]:
        try:
            if token.lower().startswith("0x"):
                value = int(token, 16)
            else:
                value = int(token, 10)

            if 0 <= value <= 255:
                return value

            return None
        except ValueError:
            return None

    def is_hex_byte(self, token: str) -> bool:
        token = token.strip()

        if token.lower().startswith("0x"):
            token = token[2:]

        if not token or len(token) > 2:
            return False

        try:
            value = int(token, 16)
            return 0 <= value <= 255
        except ValueError:
            return False

    # =========================================================
    # Acoes de teclado
    # =========================================================

    def action_show_ports(self) -> None:
        self.show_ports()

    def action_send_status(self) -> None:
        self.send_serial_command("22 20 FF 00")

    def action_send_election(self) -> None:
        self.send_serial_command("22 00 FF 01")

    def action_disconnect(self) -> None:
        self.disconnect_serial()

    def action_show_help(self) -> None:
        self.show_help()

    def show_help(self) -> None:
        help_text = """
Comandos locais:
  /ports
  /connect <porta>
  /disconnect
  /dc
  /help

Comandos da rede:
  eleicao              -> 22 00 FF 01
  status               -> 22 20 FF 00
  status <id>          -> 22 20 ID 00
  hb <1..5>            -> 22 30 FF modo
  desativar <id>       -> 22 10 ID 00
  reativar <id>        -> 22 10 ID 11
  limpar <id>          -> 22 10 ID 44
  sim <id> on          -> 22 10 ID 55
  sim <id> off         -> 22 10 ID 66

Comando removido do TUI:
  22 10 ID 33 fica bloqueado, pois a desativacao por falha e decisao do lider.

Heartbeat real:
  hb 1 = 2000 ms
  hb 2 = 1500 ms
  hb 3 = 1000 ms
  hb 4 = 750 ms
  hb 5 = 500 ms

Atalhos:
  e = eleicao
  s = status geral
  p = listar portas
  x = desconectar serial
  h = ajuda
  q = sair
"""
        for line in help_text.strip().splitlines():
            self.write_info(line)

    # =========================================================
    # Escrita colorida no painel de trafego
    # =========================================================

    def write_rx(self, message: str) -> None:
        self.traffic.write(Text(message, style="green"))

    def write_ctrl(self, message: str) -> None:
        self.traffic.write(Text(message, style="cyan"))

    def write_status(self, message: str) -> None:
        self.traffic.write(Text(message, style="magenta"))

    def write_tx(self, message: str) -> None:
        self.traffic.write(Text(message, style="bold red"))

    def write_event(self, message: str) -> None:
        self.traffic.write(Text(f"EVENTO | {message}", style="yellow"))

    def write_error(self, message: str) -> None:
        self.traffic.write(Text(f"ERRO | {message}", style="bold red"))

    def write_ok(self, message: str) -> None:
        self.traffic.write(Text(f"OK | {message}", style="bold green"))

    def write_info(self, message: str) -> None:
        self.traffic.write(Text(f"INFO | {message}", style="white"))

    def write_raw(self, message: str) -> None:
        self.traffic.write(Text(message, style="dim white"))


def parse_nodes(value: str) -> list[int]:
    value = value.strip()
    if not value:
        return []

    result = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        result.append(int(part, 0))

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="CAN TUI MONITOR adaptado ao protocolo real da rede")
    parser.add_argument("-p", "--port", default=None, help="Porta serial. Ex.: /dev/ttyUSB0, /dev/ttyACM0, COM3")
    parser.add_argument("-b", "--baud", default=115200, type=int, help="Baud rate serial")
    parser.add_argument("-n", "--nodes", default="", help="IDs iniciais dos nos. Ex.: 1,2,3,4,5. Vazio = descoberta automatica")

    args = parser.parse_args()

    app = CanTuiMonitor(
        port=args.port,
        baud=args.baud,
        initial_nodes=parse_nodes(args.nodes),
    )

    app.run()


if __name__ == "__main__":
    main()
