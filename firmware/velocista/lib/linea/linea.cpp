#include "linea.h"

namespace linea {

bool calcularError(const uint16_t lecturas[CANALES], bool lineaBlanca, uint16_t umbral, float& error) {
  uint32_t suma = 0;
  uint32_t ponderada = 0;
  bool detectada = false;
  for (int i = 0; i < CANALES; i++) {
    uint16_t v = lecturas[i] > MAXIMO ? MAXIMO : lecturas[i];
    if (lineaBlanca) v = MAXIMO - v;
    if (v > umbral) detectada = true;
    suma += v;
    ponderada += static_cast<uint32_t>(v) * static_cast<uint32_t>(i);
  }
  if (!detectada || suma == 0) return false;
  const float centro = (CANALES - 1) / 2.0f;              // 7.5
  const float posicion = static_cast<float>(ponderada) / suma;  // 0 … 15
  error = (posicion - centro) / centro;
  return true;
}

}  // namespace linea
