
// the setup function runs once when you press reset or power the board
void setup() {
  // initialize digital pin LED_BUILTIN as an output.
  pinMode(1, OUTPUT);
}

// the loop function runs over and over again forever
void loop() {
  digitalWrite(1, HIGH);  // change state of the LED by setting the pin to the HIGH voltage level
  delay(1000);                      // wait for a second
  digitalWrite(1, LOW);   // change state of the LED by setting the pin to the LOW voltage level
  delay(1000);                      // wait for a second
}
