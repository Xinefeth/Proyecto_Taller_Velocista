// Lógica pura de la regleta: sin Arduino, se prueba en PC (pio test -e native).
#pragma once
#include <stdint.h>

namespace linea {

constexpr int CANALES = 16;
constexpr uint16_t MAXIMO = 1000;  // lectura calibrada máxima

// Posición de la línea respecto al centro, normalizada en [-1, 1]
// (-1 = extremo izquierdo, 0 = centro, 1 = extremo derecho).
// `lineaBlanca` invierte las lecturas. Devuelve false si ningún sensor supera `umbral`
// (línea perdida) y en ese caso no modifica `error`.
bool calcularError(const uint16_t lecturas[CANALES], bool lineaBlanca, uint16_t umbral, float& error);

}  // namespace linea
