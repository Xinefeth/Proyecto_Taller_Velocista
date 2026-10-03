// Lógica pura del cronometraje: sin Arduino, se prueba en PC (pio test -e native).
#pragma once
#include <stdint.h>

class CalculadorVueltas {
 public:
  explicit CalculadorVueltas(int64_t antirreboteUs) : antirrebote_(antirreboteUs) {}

  // Registra un corte en `marcaUs` (reloj propio del cronómetro).
  // Devuelve false si se descarta por antirrebote.
  // Si es válido, `vueltaMs` queda en -1 para la salida o en el tiempo desde el corte anterior.
  bool registrar(int64_t marcaUs, int64_t& vueltaMs);

  // Nueva sesión: el próximo corte vuelve a ser una salida y la cuenta empieza en 1.
  void rearmar() {
    ultimo_ = -1;
    cortes_ = 0;
  }

  uint32_t cortes() const { return cortes_; }

 private:
  int64_t antirrebote_;
  int64_t ultimo_ = -1;
  uint32_t cortes_ = 0;
};
