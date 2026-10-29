#include "joystick.h"

Joystick::Joystick(byte ledPin, uint8_t mpuEndereco, int minX, int maxX, int minY, int maxY, int anguloInicioX, int anguloInicioY) : mpu(mpuEndereco) {
  this->ledPin = ledPin;
  this->mpuEndereco = mpuEndereco;
  this->minX = minX;
  this->maxX = maxX;
  this->minY = minY;
  this->maxY = maxY;
  this->anguloInicioX = anguloInicioX;
  this->anguloInicioY = anguloInicioY;
}

void Joystick::setup() {
  pinMode(ledPin, OUTPUT);

    // o MPU não desliga quando o ESP32 reinicia: força um reset para começar limpo
  Wire.beginTransmission(mpuEndereco);
  Wire.write(0x6B);  // PWR_MGMT_1
  Wire.write(0x80);  // DEVICE_RESET
  Wire.endTransmission();
  delay(100);

  while (!mpu.init()) {
    Serial.println("MPU6500 nao responde");
    delay(500);
  }
  
  // calibra com o joystick parado e na horizontal: essa posição vira o "zero"
  // mpu.autoOffsets();

  mpu.setAccRange(MPU6500_ACC_RANGE_2G);
  mpu.enableAccDLPF(true);
  mpu.setAccDLPF(MPU6500_DLPF_6);

  Serial.println("MPU6500 encontrado!");
}

void Joystick::ligaLed() {
  digitalWrite(ledPin, HIGH);
}

void Joystick::desligaLed() {
  digitalWrite(ledPin, LOW);
}

float Joystick::retornaPosicaoX() {
  float anguloX = mpu.getRoll() - anguloInicioX;
  float posicaoX = map(anguloX, minX, maxX, -100, 100);
  return constrain(posicaoX, -100, 100);
}

float Joystick::retornaPosicaoY() {
  float anguloY = mpu.getPitch() - anguloInicioY;
  float posicaoY = map(anguloY, minY, maxY, -100, 100);
  return constrain(posicaoY, -100, 100);
}

