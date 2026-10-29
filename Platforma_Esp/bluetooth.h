#ifndef BLUETOOTH_H
#define BLUETOOTH_H

#include <Arduino.h>
#include <BluetoothSerial.h>


class Bluetooth {
  public:
    Bluetooth(const char* nome);

    void setup();
    bool estaConectado();
    void enviaPosicoes(float XD, float YD, float XE, float YE);


  private:
    const char* nome;
    bool estavaConectado = false;

    BluetoothSerial serialBT;
};


#endif
