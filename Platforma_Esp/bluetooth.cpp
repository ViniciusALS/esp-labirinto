#include "bluetooth.h"

Bluetooth::Bluetooth(const char* nome) {
  this->nome = nome;
}

void Bluetooth::setup() {
  if (!serialBT.begin(nome)) {
    Serial.println("Falha ao iniciar o Bluetooth");
    return;
  }

  Serial.print("Bluetooth pronto, pareie com: ");
  Serial.println(nome);
}

bool Bluetooth::estaConectado() {
  bool conectado = serialBT.hasClient();

  // avisa no monitor serial quando o computador conecta ou desconecta
  if (conectado != estavaConectado) {
    Serial.println(conectado ? "Bluetooth: computador conectado" : "Bluetooth: computador desconectado");
    estavaConectado = conectado;
  }

  return conectado;
}

// envia uma linha "XD,YD,XE,YE" por leitura, fácil de separar no computador
void Bluetooth::enviaPosicoes(float XD, float YD, float XE, float YE) {
  if (!estaConectado()) return;

  serialBT.print(XD);
  serialBT.print(",");
  serialBT.print(YD);
  serialBT.print(",");
  serialBT.print(XE);
  serialBT.print(",");
  serialBT.println(YE);
}
