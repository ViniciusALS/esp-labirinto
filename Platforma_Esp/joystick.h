#ifndef JOYSTICK_H
#define JOYSTICK_H

#include <Arduino.h>
#include "Adafruit_MPU6050.h"
#include <Adafruit_Sensor.h>
#include <Wire.h>


class Joystick {
  public: 
    Joystick(byte ledPin);

    void setup();
    void ligaLed();
    void desligaLed();

    void capituraMPU();
    void retornAngulo();


  private:
    byte ledPin;
    uint8_t mpuEndereco

    Adafruit_MPU6050 mpu;

    sensors_event_t a, g, temp;
};


#endif