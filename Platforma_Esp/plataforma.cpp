#include "plataforma.h"

Plataforma::Plataforma(byte motorXPin, byte motorYPin) {

  this->motorXPin = motorXPin;
  this->motorYPin = motorYPin;
}


void Plataforma::setup() {

  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);
  
  motorX.setPeriodHertz(50);
  motorX.attach(motorXPin, 500, 2400);

  motorX.setPeriodHertz(50);
  motorY.attach(motorYPin, 500, 2400);
}


void Plataforma::movePlataformaParaAngulo(int valorX, int valorY) {
  
  this->anguloX = map(valorX, -100, 100, minAnguloX, maxAnguloX);
  this->anguloY = map(valorY, -100, 100, minAnguloY, maxAnguloY);
  
  motorX.write(anguloX);
  motorY.write(anguloY);

  // Serial.print("anguloX: ");
  // Serial.println(anguloX);
  // Serial.print("anguloY: ");
  // Serial.println(anguloY);
  // Serial.println();
}


