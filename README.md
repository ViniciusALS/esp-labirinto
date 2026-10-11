# esp-labirinto

Repositório do código do sistema embarcado **FisioGame** (labirinto controlado por joystick), em ESP32.

## Pastas

| Pasta | Conteúdo |
|---|---|
| `FisioGame_BT/` | **Firmware atual (Sexta Entrega)**: joystick MPU6050 → ESP32 → 2 servos + envio de telemetria por Bluetooth |
| `Prototipo/` | Teste de leitura do MPU6050 (Quarta/Quinta Entrega) |
| `Motor_tester/` | Teste de varredura dos 2 servomotores |
| `MPU_WhoAmI/`, `WhoAmI_I2C/`, `I2C_Scanner/` | Diagnóstico do endereço I2C do MPU6050 |
| `Joystick_led_blink/` | Teste simples de saída digital |
| `Maze_generator/` | Gerador do labirinto (PNG/SVG) e modelo 3D |
| `Diagrama Protoboard.fzz` | Esquema de ligação (Fritzing) |

## FisioGame_BT

- Placa: ESP32 clássico (com Bluetooth Classic; ESP32-S3/C3 não servem).
- Bibliotecas: Adafruit MPU6050 (versão modificada da equipe), Adafruit Unified Sensor, ESP32Servo.
- Servos: GPIO 2 (inferior) e GPIO 15 (superior), alimentação externa com GND comum.
- Bluetooth: aparece como **FisioGame-ESP32**; envia uma linha JSON a cada 200 ms (também na Serial USB, 115200 bps).

O dashboard que consome esses dados fica em um repositório separado: `fisiogame-dashboard`.
