// Vueltas guardadas mientras no hay enlace con la API (EN-12): sin Arduino, se prueba en PC
// (pio test -e native). Al reconectar se envían juntas en un mensaje `sync` y se borran de aquí
// cuando la API las confirma con ack. El contrato permite hasta 50 vueltas por `sync`.
#pragma once
#include <stddef.h>
#include <stdint.h>

// Resumen de una vuelta, con los mismos campos del mensaje `vuelta` del contrato.
struct VueltaGuardada {
  uint32_t id_vuelta;
  uint32_t tiempo_interno_ms;
  float error_acumulado;
  uint32_t lineas_perdidas;
  float bateria_v;
};

class VueltasGuardadas {
 public:
  static constexpr size_t CAPACIDAD = 50;

  // Guarda una vuelta. Si ya hay CAPACIDAD, descarta la más antigua y la cuenta en descartadas().
  void agregar(const VueltaGuardada& v);

  size_t cantidad() const { return n_; }
  uint32_t descartadas() const { return descartadas_; }

  // La i-ésima más antigua (0 = la próxima a enviar), o nullptr si `i` está fuera de rango.
  const VueltaGuardada* obtener(size_t i) const;

  // Quita las `n` más antiguas, las que la API confirmó. Si n > cantidad(), quita todas.
  void confirmar(size_t n);

 private:
  VueltaGuardada datos_[CAPACIDAD];
  size_t inicio_ = 0;
  size_t n_ = 0;
  uint32_t descartadas_ = 0;
};
