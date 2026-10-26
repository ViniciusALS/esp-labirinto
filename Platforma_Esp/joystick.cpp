#include "joystick.h"

Joystick::Joystick(byte ledPin, uint8_t mpuEndereco) {
  this->ledPin = ledPin;
  this->mpuEndereco = mpuEndereco;
}

void Joystick::setup() {
  pinMode(ledPin, OUTPUT);

  while (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    delay(500);
  }

  Serial.println("MPU6050 Found!");
}

void Joystick::ligaLed() {
  digitalWrite(ledPin, HIGH);
}

void Joystick::desligaLed() {
  digitalWrite(ledPin, LOW);
}

void Joystick::capituraAceleracaoRotacaoMPU() {
  mpu.getEvent(&a, &g, &temp);
}

void Joystick::retornaAceleracao() {
  return a;
}

void Joystick::retornRotacao() {
  return g;
}

