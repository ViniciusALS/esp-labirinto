"""
FisioGame - Dashboard de monitoramento do ESP32 (Streamlit)

O ESP32 (Platforma_Esp) envia por Bluetooth Classic (SPP), a cada ~20 ms,
uma linha com as posicoes dos dois joysticks:

    XD,YD,XE,YE        ex.: 12.30,-4.50,0.00,88.10

No PC, depois de parear o "Labirinto_ESP32", o sistema cria uma porta serial
(macOS: /dev/cu.Labirinto_ESP32, Windows: COMx); este dashboard le essa porta
com pyserial.

Para desenvolver sem o hardware existe o modo "Simulação". Ele fica sempre
identificado na tela e nos arquivos CSV (coluna `fonte`), para nunca ser
confundido com dados reais do ESP32.

Executar:  streamlit run app.py
"""

import math
import random
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pyserial nao instalado
    serial = None
    list_ports = None

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

NOME_BT = "Labirinto_ESP32"
# Posicao dos joysticks vai de -100 a 100 (Joystick::retornaPosicaoX/Y no firmware)
ZONA_MORTA = 5.0     # abaixo disso o joystick conta como parado
LIMITE = 100.0       # posicao no fim do curso
TIMEOUT_SEM_DADOS_S = 3.0

POSICOES = ["xd", "yd", "xe", "ye"]
COLUNAS = ["hora", "fonte", *POSICOES, "estado"]


def estado_de(amostra):
    """NORMAL: joysticks parados. ATIVO: algum inclinado. LIMITE: algum no fim do curso."""
    valores = [abs(amostra[p]) for p in POSICOES]
    if any(v >= LIMITE for v in valores):
        return "LIMITE"
    if any(v >= ZONA_MORTA for v in valores):
        return "ATIVO"
    return "NORMAL"


class Telemetria:
    """Recebe amostras (serial ou simulacao) em uma thread e guarda o historico."""

    def __init__(self):
        self.lock = threading.Lock()
        self.dados = deque(maxlen=15000)  # ~5 min a 50 amostras/s
        self.eventos = deque(maxlen=200)
        self.fonte = "nenhuma"
        self.erro = ""
        self.ultimo_rx = None
        self.total = 0
        self._stop = threading.Event()
        self._thread = None
        self._csv = None
        self._estado_anterior = None

    # ---- controle ----
    def parar(self):
        self._stop.set()
        self.fonte = "nenhuma"

    def iniciar(self, fonte, porta=None, baud=115200):
        self.parar()
        self._stop = threading.Event()
        with self.lock:
            self.dados.clear()
            self.eventos.clear()
            self.total = 0
            self.ultimo_rx = None
            self._estado_anterior = None
        self.erro = ""
        self.fonte = fonte
        self._csv = DATA_DIR / f"log_{fonte}_{datetime.now():%Y%m%d_%H%M%S}.csv"
        alvo = self._loop_serial if fonte == "esp32" else self._loop_simulacao
        args = (self._stop, porta, baud) if fonte == "esp32" else (self._stop,)
        self._thread = threading.Thread(target=alvo, args=args, daemon=True)
        self._thread.start()

    # ---- entrada de dados ----
    def _processar_linha(self, linha, fonte):
        partes = linha.strip().split(",")
        if len(partes) != len(POSICOES):
            return  # linha quebrada (comum no inicio da conexao): ignora
        try:
            valores = [float(p) for p in partes]
        except ValueError:
            return
        amostra = {"hora": datetime.now(), "fonte": fonte, **dict(zip(POSICOES, valores))}
        amostra["estado"] = estado_de(amostra)
        self._registrar(amostra)

    def _registrar(self, amostra):
        with self.lock:
            self.dados.append(amostra)
            self.total += 1
            self.ultimo_rx = time.time()
            if amostra["estado"] != self._estado_anterior:
                self.eventos.appendleft({
                    "hora": amostra["hora"].strftime("%H:%M:%S"),
                    "de": self._estado_anterior or "-",
                    "para": amostra["estado"],
                    **{p: amostra[p] for p in POSICOES},
                    "fonte": amostra["fonte"],
                })
                self._estado_anterior = amostra["estado"]
        # log em disco
        novo = not self._csv.exists()
        with open(self._csv, "a", encoding="utf-8") as f:
            if novo:
                f.write(",".join(COLUNAS) + "\n")
            f.write(",".join(
                amostra["hora"].isoformat(timespec="milliseconds") if c == "hora" else str(amostra[c])
                for c in COLUNAS) + "\n")

    def _loop_serial(self, stop, porta, baud):
        if serial is None:
            self.erro = "pyserial nao instalado (pip install pyserial)"
            return
        try:
            with serial.Serial(porta, baud, timeout=1) as s:
                while not stop.is_set():
                    linha = s.readline().decode("utf-8", "ignore")
                    if linha:
                        self._processar_linha(linha, "esp32")
        except Exception as e:  # porta ocupada, ESP desligado, etc.
            self.erro = f"{type(e).__name__}: {e}"

    def _loop_simulacao(self, stop):
        """Ciclo de 40 s: parado -> joystick direito inclina ate o limite -> volta;
        o esquerdo faz o mesmo no eixo Y, defasado em 20 s."""
        t0 = time.time()
        while not stop.is_set():
            t = time.time() - t0
            amostra = {
                "hora": datetime.now(), "fonte": "simulacao",
                "xd": round(curva_simulacao(t % 40) + random.gauss(0, 0.6), 2),
                "yd": round(random.gauss(0, 0.6), 2),
                "xe": round(random.gauss(0, 0.6), 2),
                "ye": round(-curva_simulacao((t + 20) % 40) + random.gauss(0, 0.6), 2),
            }
            for p in POSICOES:
                amostra[p] = max(-LIMITE, min(LIMITE, amostra[p]))
            amostra["estado"] = estado_de(amostra)
            self._registrar(amostra)
            time.sleep(0.02)

    # ---- saida ----
    def dataframe(self):
        with self.lock:
            df = pd.DataFrame(list(self.dados), columns=COLUNAS)
        return df

    def lista_eventos(self):
        with self.lock:
            return pd.DataFrame(list(self.eventos))


def curva_simulacao(t):
    """Posicao simulada em funcao de t (0-40 s), usada apenas na simulacao."""
    if t < 10:
        return 0.0
    if t < 20:
        return (t - 10) * 5.0                # 0 -> 50
    if t < 27:
        return 50 + (t - 20) * 50 / 7        # 50 -> 100 (limite)
    if t < 35:
        return 100 * (1 + math.cos(math.pi * (t - 27) / 8)) / 2   # volta a 0
    return 0.0


@st.cache_resource
def get_store():
    return Telemetria()


# ======================= Interface =======================
st.set_page_config(page_title="FisioGame - Dashboard", page_icon="🎮", layout="wide")
store = get_store()

st.title("🎮 FisioGame - Monitoramento do ESP32")

with st.sidebar:
    st.header("Conexão")
    fonte_ui = st.radio("Fonte de dados", ["ESP32 via Bluetooth", "Simulação (demonstração)"])
    if fonte_ui.startswith("ESP32"):
        portas = []
        if list_ports is not None:
            portas = [f"{p.device} - {p.description}" for p in list_ports.comports()]
            # deixa a porta do ESP32 no topo da lista
            portas.sort(key=lambda p: NOME_BT not in p)
        if portas:
            escolha = st.selectbox("Porta serial / Bluetooth", portas)
        else:
            escolha = st.text_input(f"Porta (ex.: /dev/cu.{NOME_BT} ou COM5)")
        baud = st.number_input("Baud rate", value=115200, step=1200,
                               help="Ignorado pelo Bluetooth, mas exigido pela porta serial.")
        c1, c2 = st.columns(2)
        if c1.button("Conectar", type="primary") and escolha:
            store.iniciar("esp32", escolha.split(" - ")[0].strip(), int(baud))
        if c2.button("Desconectar"):
            store.parar()
        st.caption(f"Pareie primeiro o dispositivo **{NOME_BT}** nas configurações Bluetooth do computador.")
    else:
        if st.button("Iniciar simulação", type="primary"):
            store.iniciar("simulacao")
        if st.button("Parar"):
            store.parar()
        st.caption("Dados gerados por software. Não representam leituras do ESP32.")
    janela = st.slider("Amostras exibidas nos gráficos (50/s)", 100, 5000, 500, step=100)


@st.fragment(run_every=1.0)
def painel(janela):
    df = store.dataframe()
    sem_dados = df.empty
    atraso = (time.time() - store.ultimo_rx) if store.ultimo_rx else None

    if store.erro:
        st.error(f"Erro de conexão: {store.erro}")
    if store.fonte == "simulacao":
        st.warning("MODO SIMULAÇÃO - os dados abaixo são gerados por software, não vêm do ESP32.")
    elif store.fonte == "esp32" and not sem_dados and atraso is not None and atraso <= TIMEOUT_SEM_DADOS_S:
        st.success("AO VIVO - dados recebidos do ESP32 via Bluetooth.")
    elif store.fonte == "esp32" and not sem_dados:
        st.error(f"Conexão perdida: nenhum pacote há {atraso:.0f} s.")
    elif store.fonte == "esp32":
        st.info("Conectando... aguardando o primeiro pacote do ESP32.")
    else:
        st.info("Sem fonte de dados ativa. Escolha uma opção na barra lateral e clique em Conectar/Iniciar.")

    if sem_dados:
        return

    ult = df.iloc[-1]
    cor = {"NORMAL": "🟢", "ATIVO": "🟡", "LIMITE": "🔴"}.get(ult["estado"], "⚪")
    m = st.columns(5)
    m[0].metric(f"Estado {cor}", ult["estado"])
    m[1].metric("Direito X", f"{ult['xd']:.1f}")
    m[2].metric("Direito Y", f"{ult['yd']:.1f}")
    m[3].metric("Esquerdo X", f"{ult['xe']:.1f}")
    m[4].metric("Esquerdo Y", f"{ult['ye']:.1f}")

    if ult["estado"] == "LIMITE":
        st.error("ALERTA: joystick no fim do curso.")
    elif ult["estado"] == "ATIVO":
        st.warning("Joystick inclinado.")
    else:
        st.success("Condição normal: joysticks parados.")

    d = df.tail(janela).copy()
    d["tempo (s)"] = (d["hora"] - d["hora"].iloc[0]).dt.total_seconds().round(2)
    d = d.set_index("tempo (s)")
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Joystick direito")
        st.line_chart(d[["xd", "yd"]].rename(columns={"xd": "X", "yd": "Y"}))
    with g2:
        st.subheader("Joystick esquerdo")
        st.line_chart(d[["xe", "ye"]].rename(columns={"xe": "X", "ye": "Y"}))
    g3, g4 = st.columns(2)
    with g3:
        st.subheader("Posição atual (X × Y)")
        pos = pd.DataFrame({
            "X": [ult["xd"], ult["xe"], -LIMITE, LIMITE],
            "Y": [ult["yd"], ult["ye"], -LIMITE, LIMITE],
            # os dois pontos invisiveis fixam a escala em -100..100
            "joystick": ["direito", "esquerdo", "escala", "escala"],
            "tamanho": [200, 200, 0, 0],
        })
        st.scatter_chart(pos, x="X", y="Y", color="joystick", size="tamanho")
    with g4:
        st.subheader("Status do sistema")
        taxa = len(df[df["hora"] > df["hora"].iloc[-1] - pd.Timedelta(seconds=10)]) / 10
        st.write(f"- Fonte: **{ult['fonte']}**")
        st.write(f"- Amostras recebidas: **{store.total}**")
        st.write(f"- Taxa: **{taxa:.1f} amostras/s**")
        st.write(f"- Última amostra: **{ult['hora']:%H:%M:%S}**")
        st.write(f"- Arquivo de log: `{store._csv.name if store._csv else '-'}`")
        st.subheader("Eventos (mudança de estado)")
        ev = store.lista_eventos()
        if not ev.empty:
            st.dataframe(ev.head(8), hide_index=True)


painel(janela)

# ---------- Registro de testes (fora do fragmento, para nao reiniciar a digitacao) ----------
st.divider()
st.header("Registro de testes")
st.caption("Clique em registrar durante o teste. Cada linha guarda a leitura exibida no momento "
           "(com a fonte: esp32 ou simulacao).")

CENARIOS = {
    "Teste 01 - Condição normal": "Joysticks parados -> estado NORMAL, posições próximas de 0.",
    "Teste 02 - Condição de alerta": "Joystick inclinado -> estado ATIVO/LIMITE, posição fora de 0, dashboard atualiza.",
}
ARQ_TESTES = DATA_DIR / "registro_testes.csv"
cen = st.selectbox("Cenário", list(CENARIOS))
st.write(f"**Resultado esperado:** {CENARIOS[cen]}")
col_a, col_b = st.columns([1, 3])
passou = col_a.radio("Resultado observado", ["Passou", "Falhou"], horizontal=True)
obs = col_b.text_input("Observações")
if st.button("Registrar leitura atual"):
    df_now = store.dataframe()
    if df_now.empty:
        st.error("Sem dados no momento. Conecte o ESP32 antes de registrar.")
    else:
        u = df_now.iloc[-1]
        linha = pd.DataFrame([{
            "registro": datetime.now().isoformat(timespec="seconds"), "cenario": cen,
            "fonte": u["fonte"], **{p: u[p] for p in POSICOES}, "estado": u["estado"],
            "resultado": passou, "observacoes": obs,
        }])
        linha.to_csv(ARQ_TESTES, mode="a", header=not ARQ_TESTES.exists(), index=False)
        st.success("Leitura registrada.")
if ARQ_TESTES.exists():
    reg = pd.read_csv(ARQ_TESTES)
    st.dataframe(reg, hide_index=True)
    st.download_button("Baixar registro de testes (CSV)", reg.to_csv(index=False).encode("utf-8"),
                       "registro_testes.csv", "text/csv")

with st.expander("Histórico completo da sessão"):
    hist = store.dataframe()
    st.dataframe(hist.tail(500), hide_index=True)
    if not hist.empty:
        st.download_button("Baixar histórico (CSV)", hist.to_csv(index=False).encode("utf-8"),
                           "historico_sessao.csv", "text/csv")
