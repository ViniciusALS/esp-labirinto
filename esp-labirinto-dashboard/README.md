# FisioGame - Dashboard

Dashboard em **Python + Streamlit** que monitora o ESP32 do projeto FisioGame (labirinto controlado por dois joysticks com MPU6500 e 2 servomotores). Os dados chegam por **Bluetooth Classic (SPP)**.

Código do ESP32: repositório `esp-labirinto` (pasta `Platforma_Esp/`).

## Como rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```

Abre em http://localhost:8501.

## Conectando ao ESP32

1. Grave o `Platforma_Esp.ino` no ESP32 (ESP32 clássico, ex.: DevKit/WROOM).
2. Pareie o dispositivo **Labirinto_ESP32** nas configurações Bluetooth do computador.
3. No dashboard: fonte **ESP32 via Bluetooth**, escolha a porta e clique **Conectar**.
   - **macOS:** `/dev/cu.Labirinto_ESP32` (aparece no topo da lista).
   - **Windows:** em **Mais opções de Bluetooth → Portas COM** aparecem duas portas; a de **saída** (Outgoing) é a correta.
   - **Linux:** `sudo rfcomm bind 0 <MAC_DO_ESP32>` e use `/dev/rfcomm0`.

O baud rate é ignorado pelo Bluetooth.

## Formato dos dados

O ESP32 envia 1 linha a cada 20 ms (50 amostras/s) com a posição dos dois joysticks, de -100 a 100:

```
XD,YD,XE,YE
12.30,-4.50,0.00,88.10
```

`D` = joystick direito, `E` = joystick esquerdo. Linhas em outro formato são ignoradas.

O estado é calculado no dashboard: `NORMAL` (todas as posições abaixo de 5, joysticks parados), `ATIVO` (algum joystick inclinado), `LIMITE` (algum joystick em ±100, fim do curso: alerta).

## O que o dashboard mostra

- Estado do sistema e alertas (normal / ativo / limite / conexão perdida)
- Posição X e Y de cada joystick ao longo do tempo e posição atual em um gráfico X × Y
- Status da conexão (taxa de amostras, última amostra, arquivo de log)
- Eventos de mudança de estado
- Histórico da sessão (download em CSV) e log automático em `data/`
- **Registro de testes**: botão que grava a leitura atual com o cenário e o resultado observado em `data/registro_testes.csv`

## Modo simulação

Existe apenas para desenvolver o dashboard sem o hardware. Ele fica **sempre identificado** na tela e na coluna `fonte` dos CSVs (`simulacao` x `esp32`). Não use dados simulados como evidência de teste.

## Estrutura

```
app.py              # dashboard (leitura serial/BT + interface)
requirements.txt
data/               # logs CSV gerados em execução
.streamlit/config.toml
```
