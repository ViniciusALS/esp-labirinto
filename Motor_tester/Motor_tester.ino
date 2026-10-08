#include <ESP32Servo.h>

#define MOTOR_INFERIOR_PIN 2
#define MOTOR_SUPERIOR_PIN 15

#define MOTOR_INFERIOR_PISO 50
#define MOTOR_INFERIOR_TETO 120

#define MOTOR_SUPERIOR_PISO 50
#define MOTOR_SUPERIOR_TETO 120

#define MID_POINT 90


Servo motorInferior;
Servo motorSuperior;  

int val = 0;    

void setup() {
  motorInferior.attach(MOTOR_INFERIOR_PIN);  
  // motorInferior.write(45);

  motorSuperior.attach(MOTOR_SUPERIOR_PIN);
  // motorSuperior.write(MID_POINT);
}

void loop() {
  for (int pos = MOTOR_INFERIOR_PISO; pos <= MOTOR_INFERIOR_TETO; pos += 5) {
    motorInferior.write(pos);
    motorSuperior.write(pos);
    delay(25); 
  }


  for (int pos = MOTOR_INFERIOR_TETO; pos >= MOTOR_INFERIOR_PISO; pos -= 5) {
    motorInferior.write(pos);
    motorSuperior.write(pos);
    delay(25); 
  }              

  // motorSuperior.write(MOTOR_SUPERIOR_PISO);
  // delay(5000); // waits 15ms to reach the position

  // motorSuperior.write(MOTOR_SUPERIOR_TETO);
  // delay(5000); // waits 15ms to reach the position

}