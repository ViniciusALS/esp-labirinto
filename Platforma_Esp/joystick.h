#ifndef JOYSTICK_H
#define JOYSTICK_H

#include <Arduino.h>
#include <MPU6500_WE.h>
#include <Wire.h>


class Joystick {
  public: 
    Joystick(byte ledPin, uint8_t mpuEndereco, int minX, int maxX, int minY, int maxY, int anguloInicioX, int anguloInicioY);

    void setup();
    void ligaLed();
    void desligaLed();

    float retornaPosicaoX();
    float retornaPosicaoY();


  private:
    byte ledPin;
    uint8_t mpuEndereco;

    int minX, maxX, minY, maxY;
    int anguloInicioX, anguloInicioY;

    MPU6500_WE mpu;
};


#endif