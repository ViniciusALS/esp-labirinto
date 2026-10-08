#define JOYSTICK_1 3
#define JOYSTICK_2 1


// the setup function runs once when you press reset or power the board
void setup() {
  // initialize digital pin LED_BUILTIN as an output.
  pinMode(3, OUTPUT);
  pinMode(1, OUTPUT);
}

// the loop function runs over and over again forever
void loop() {
  digitalWrite(JOYSTICK_1, HIGH);  
  digitalWrite(JOYSTICK_2, LOW);
  delay(1000);                      

  digitalWrite(JOYSTICK_1, LOW); 
  digitalWrite(JOYSTICK_2, HIGH); 
  delay(1000);                     
}
