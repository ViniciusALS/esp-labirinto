#include "joystick.h"
#include "plataforma.h"
#include "bluetooth.h"

#define JOYSTICK_DIREITA_LED_PIN 19 //ok
#define JOYSTICK_ESQUERDA_LED_PIN 18 //ok
#define MOTOR_X_PIN 32
#define MOTOR_Y_PIN 33


Joystick joystickDireita(JOYSTICK_DIREITA_LED_PIN, 0x68, 0, 180, -90, 90, 0, 10);
Joystick joystickEsquerda(JOYSTICK_ESQUERDA_LED_PIN, 0x69, 0, 180, -90, 90, 0, 10);
Plataforma plataforma(MOTOR_X_PIN, MOTOR_Y_PIN);
Bluetooth bluetooth("Labirinto_ESP32");

void setup() {
  Serial.begin(115200);
  liberaBarramentoI2C();
  Wire.begin();

  joystickDireita.setup();
  joystickEsquerda.setup();
  plataforma.setup();
  bluetooth.setup();
}

void loop() {
  
  // ---------- TESTES ---------------
  // testaJoysticksLeds();

  // testaMotorXMin();
  // testaMotorXMid();
  // testaMotorXMax();
  // testaMotorXFull();

  // testaMotorYMin();
  // testaMotorYMid();
  // testaMotorYMax();
  // testaMotorYFull();

  // testaJoystickDireitaInclinacao();
  // testaJoystickEsquerdaInclinacao();

  static unsigned long ultimaAtualizacao = 0;
  if (millis() - ultimaAtualizacao < 20) return;   // 50 Hz, o mesmo ritmo do servo
  ultimaAtualizacao = millis();

  float posXD = joystickDireita.retornaPosicaoX();
  float posYD = joystickDireita.retornaPosicaoY();

  float posXE = joystickEsquerda.retornaPosicaoX();
  float posYE = joystickEsquerda.retornaPosicaoY();

  // plataforma.moveParaPosicao(posXE, posYE);
  printJoysticks(posXD, posYD, posXE, posYE);
  bluetooth.enviaPosicoes(posXD, posYD, posXE, posYE);
}


// solta um dispositivo I2C travado no meio de uma leitura
void liberaBarramentoI2C() {
  pinMode(21, INPUT_PULLUP);   // SDA
  pinMode(22, OUTPUT);         // SCL
  for (int i = 0; i < 9; i++) {
    digitalWrite(22, LOW);  delayMicroseconds(5);
    digitalWrite(22, HIGH); delayMicroseconds(5);
  }
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
  plataforma.moveParaPosicao(-100, 0);
}

void testaMotorXMid() {
  plataforma.moveParaPosicao(0, 0);
}

void testaMotorXMax() {
  plataforma.moveParaPosicao(100, 0);
}

void testaMotorXFull() {
  for (int val = 100; val > -100; val--) {
    plataforma.moveParaPosicao(val, 0);
    delay(15);
  }
  
  for (int val = -100; val < 100; val++) {
    plataforma.moveParaPosicao(val, 0);
    delay(15);
  }
}


void testaMotorYMin() {
  plataforma.moveParaPosicao(0, -100);
}

void testaMotorYMid() {
  plataforma.moveParaPosicao(0, 0);
}

void testaMotorYMax() {
  plataforma.moveParaPosicao(0, 100);
}

void testaMotorYFull() {
  for (int val = 100; val > -100; val--) {
    plataforma.moveParaPosicao(0, val);
    delay(15);
  }
  
  for (int val = -100; val < 100; val++) {
    plataforma.moveParaPosicao(0, val);
    delay(15);
  }
}

void testaJoystickDireitaInclinacao() {

  Serial.print(joystickDireita.retornaPosicaoX());
  Serial.print("\t");
  Serial.println(joystickDireita.retornaPosicaoY());

  delay(50);
}

void testaJoystickEsquerdaInclinacao() {

  Serial.print(joystickEsquerda.retornaPosicaoX());
  Serial.print("\t");
  Serial.println(joystickEsquerda.retornaPosicaoY());

  delay(50);
}

void printJoysticks(float XD, float YD, float XE, float YE) {
  Serial.print("Joystick Direito: ");
  Serial.print("X: ");
  Serial.print(XD);
  Serial.print(" Y: ");
  Serial.print(YD);
  Serial.print(", Joystick Esquerdo: ");
  Serial.print("X: ");
  Serial.print(XE);
  Serial.print(" Y: ");
  Serial.println(YE);
}