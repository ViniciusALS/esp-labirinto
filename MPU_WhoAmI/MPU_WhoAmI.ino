// Lê o registrador WHO_AM_I (0x75) direto, sem biblioteca.
// Serve para descobrir qual chip está de fato na placa "MPU6050".

#include <Wire.h>

void probe(uint8_t addr) {
  Wire.beginTransmission(addr);
  Wire.write(0x75);                  // WHO_AM_I
  if (Wire.endTransmission(false) != 0) {
    Serial.print("Sem ACK em 0x");
    Serial.println(addr, HEX);
    return;
  }
  Wire.requestFrom(addr, (uint8_t)1);
  if (!Wire.available()) {
    Serial.println("Sem resposta");
    return;
  }
  uint8_t id = Wire.read();
  Serial.print("Endereco I2C 0x");
  Serial.print(addr, HEX);
  Serial.print("  ->  WHO_AM_I = 0x");
  Serial.println(id, HEX);
}

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);
  Wire.begin();                      // ESP32: Wire.begin(SDA, SCL) se usar outros pinos
  Serial.println("\nMPU WHO_AM_I probe");
  probe(0x68);                       // AD0 = GND
  probe(0x69);                       // AD0 = VCC
}

void loop() {}
