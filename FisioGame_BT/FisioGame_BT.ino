/*
  FisioGame - Firmware do ESP32 (Sexta Entrega)

  Fluxo do sistema:
    MPU6050 (joystick)  ->  ESP32 (processamento)  ->  2 servomotores (inclinam o labirinto)
                                      |
                                      +-> Bluetooth Classic (SPP) -> Dashboard (Streamlit, PC)

  - Le a inclinacao do joystick (acelerometro do MPU6050).
  - Converte a inclinacao em angulo para os servos (eixo inferior = roll, superior = pitch).
  - Classifica o estado do sistema: NORMAL, ATIVO ou LIMITE.
  - Envia uma linha JSON a cada 200 ms por Bluetooth (e tambem pela Serial USB, para depuracao).

  Placa: ESP32 "classico" (ESP32-WROOM/DevKit). ESP32-S3/C3 NAO possuem Bluetooth Classic.
  Bibliotecas: Adafruit MPU6050 (a versao modificada da equipe, com o endereco I2C ajustado),
               Adafruit Unified Sensor, ESP32Servo.
  Pinos dos servos: os mesmos do Servo_tester (GPIO 2 e GPIO 15).
*/

#include <Wire.h>
#include <Adafruit_Sensor.h>
#include "Adafruit_MPU6050.h"
#include <ESP32Servo.h>
#include <BluetoothSerial.h>
#include <math.h>

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error "Bluetooth Classic nao esta habilitado nesta placa/configuracao."
#endif

// ---------- Configuracao ----------
#define NOME_BLUETOOTH "FisioGame-ESP32"

#define MOTOR_INFERIOR_PIN 2
#define MOTOR_SUPERIOR_PIN 15

#define SERVO_PISO 50      // limites mecanicos (mesmos do Motor_tester)
#define SERVO_TETO 120
#define SERVO_MEIO 90

#define ZONA_MORTA_GRAUS 5.0f   // abaixo disso o joystick e considerado "parado"
#define GANHO 1.0f              // graus de servo por grau de inclinacao
#define FILTRO_ALFA 0.25f       // filtro passa-baixa (0..1, menor = mais suave)

#define PERIODO_CONTROLE_MS 50
#define PERIODO_ENVIO_MS 200

// ---------- Objetos ----------
Adafruit_MPU6050 mpu;
BluetoothSerial SerialBT;
Servo motorInferior;
Servo motorSuperior;

float rollFiltrado = 0, pitchFiltrado = 0;
unsigned long ultimoControle = 0, ultimoEnvio = 0;

// Ultimos valores calculados (usados no envio)
float ax = 0, ay = 0, az = 0, temperatura = 0;
int anguloInferior = SERVO_MEIO, anguloSuperior = SERVO_MEIO;
const char *estado = "NORMAL";

int limitaServo(float valor, bool &noLimite) {
  int v = (int)lroundf(valor);
  if (v <= SERVO_PISO) { noLimite = true; return SERVO_PISO; }
  if (v >= SERVO_TETO) { noLimite = true; return SERVO_TETO; }
  return v;
}

void setup() {
  Serial.begin(115200);
  SerialBT.begin(NOME_BLUETOOTH);

  motorInferior.attach(MOTOR_INFERIOR_PIN);
  motorSuperior.attach(MOTOR_SUPERIOR_PIN);
  motorInferior.write(SERVO_MEIO);
  motorSuperior.write(SERVO_MEIO);

  while (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    delay(500);
  }
  Serial.println("MPU6050 Found!");
  Serial.print("Bluetooth ativo como: ");
  Serial.println(NOME_BLUETOOTH);
}

void loop() {
  unsigned long agora = millis();

  // ----- Leitura + processamento + atuacao -----
  if (agora - ultimoControle >= PERIODO_CONTROLE_MS) {
    ultimoControle = agora;

    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    ax = a.acceleration.x;
    ay = a.acceleration.y;
    az = a.acceleration.z;
    temperatura = temp.temperature;

    // Inclinacao (graus) a partir do acelerometro
    float roll = atan2f(ay, az) * 180.0f / PI;
    float pitch = atan2f(-ax, sqrtf(ay * ay + az * az)) * 180.0f / PI;

    rollFiltrado += FILTRO_ALFA * (roll - rollFiltrado);
    pitchFiltrado += FILTRO_ALFA * (pitch - pitchFiltrado);

    // Zona morta: joystick parado -> servos no meio
    float r = fabsf(rollFiltrado) < ZONA_MORTA_GRAUS ? 0 : rollFiltrado;
    float p = fabsf(pitchFiltrado) < ZONA_MORTA_GRAUS ? 0 : pitchFiltrado;

    bool noLimite = false;
    anguloInferior = limitaServo(SERVO_MEIO + GANHO * r, noLimite);
    anguloSuperior = limitaServo(SERVO_MEIO + GANHO * p, noLimite);

    motorInferior.write(anguloInferior);
    motorSuperior.write(anguloSuperior);

    if (noLimite) estado = "LIMITE";
    else if (r != 0 || p != 0) estado = "ATIVO";
    else estado = "NORMAL";
  }

  // ----- Comunicacao (Bluetooth + Serial USB) -----
  if (agora - ultimoEnvio >= PERIODO_ENVIO_MS) {
    ultimoEnvio = agora;

    char linha[256];
    snprintf(linha, sizeof(linha),
             "{\"t\":%lu,\"roll\":%.1f,\"pitch\":%.1f,\"ax\":%.2f,\"ay\":%.2f,\"az\":%.2f,"
             "\"temp\":%.1f,\"servo_inf\":%d,\"servo_sup\":%d,\"estado\":\"%s\"}",
             agora, rollFiltrado, pitchFiltrado, ax, ay, az, temperatura,
             anguloInferior, anguloSuperior, estado);

    if (SerialBT.hasClient()) SerialBT.println(linha);
    Serial.println(linha);
  }
}
