#ifndef PLATAFORMA_H
#define PLATAFORMA_H

#include <Arduino.h>

#include <ESP32Servo.h>


class Plataforma {
  public:
    Plataforma(byte motorXPin, byte motorYPin);

    void setup();

    void moveParaPosicao(int anguloX, int anguloY);


  private:
    byte motorXPin;
    byte motorYPin;

    Servo motorX;
    Servo motorY;

    int anguloX;
    const int minAnguloX = 45;
    // const int midAnguloX = 50;
    const int maxAnguloX = 125;

    int anguloY;
    const int minAnguloY = 45;
    // const int midAnguloY = 100;
    const int maxAnguloY = 125;

};

#endif