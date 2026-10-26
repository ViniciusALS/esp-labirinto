#include "joystick.h"
#include "plataforma.h"

#define JOYSTICK_DIREITA_LED_PIN 19 //ok
#define JOYSTICK_ESQUERDA_LED_PIN 18 //ok
#define MOTOR_X_PIN 32
#define MOTOR_Y_PIN 33


Joystick joystickDireita(JOYSTICK_DIREITA_LED_PIN, 0x68);
Joystick joystickEsquerda(JOYSTICK_ESQUERDA_LED_PIN, 0x69);
Plataforma plataforma(MOTOR_X_PIN, MOTOR_Y_PIN);

void setup() {
  Serial.begin(115200);

  joystickDireita.setup();
  joystickEsquerda.setup();
  plataforma.setup();
}

void loop() {
  
  // ---------- TESTES ---------------
  // testaJoysticksLeds();

  // testaMotorXMin();
  // testaMotorXMid();
  // testaMotorXMax();
  testaMotorXFull();

  // testaMotorYMin();
  // testaMotorYMid();
  // testaMotorYMax();
  testaMotorYFull();



}

// Testes
void testaJoysticksLeds() {
  joystickDireita.ligaLed();
  joystickEsquerda.desligaLed();
  delay(5000);                      

  joystickDireita.desligaLed();
  joystickEsquerda.ligaLed();
  delay(5000);  
}


void testaMotorXMin() {
  plataforma.movePlataformaParaAngulo(-100, 0);
}

void testaMotorXMid() {
  plataforma.movePlataformaParaAngulo(0, 0);
}

void testaMotorXMax() {
  plataforma.movePlataformaParaAngulo(100, 0);
}

void testaMotorXFull() {
  for (int val = 100; val > -100; val--) {
    plataforma.movePlataformaParaAngulo(val, 0);
    delay(15);
  }
  
  for (int val = -100; val < 100; val++) {
    plataforma.movePlataformaParaAngulo(val, 0);
    delay(15);
  }
}


void testaMotorYMin() {
  plataforma.movePlataformaParaAngulo(0, -100);
}

void testaMotorYMid() {
  plataforma.movePlataformaParaAngulo(0, 0);
}

void testaMotorYMax() {
  plataforma.movePlataformaParaAngulo(0, 100);
}

void testaMotorYFull() {
  for (int val = 100; val > -100; val--) {
    plataforma.movePlataformaParaAngulo(0, val);
    delay(15);
  }
  
  for (int val = -100; val < 100; val++) {
    plataforma.movePlataformaParaAngulo(0, val);
    delay(15);
  }
}
