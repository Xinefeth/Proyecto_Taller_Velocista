#include "vueltas_guardadas.h"

void VueltasGuardadas::agregar(const VueltaGuardada& v) {
  if (n_ == CAPACIDAD) {  // lleno: se pierde la más antigua, no la más reciente
    inicio_ = (inicio_ + 1) % CAPACIDAD;
    n_--;
    descartadas_++;
  }
  datos_[(inicio_ + n_) % CAPACIDAD] = v;
  n_++;
}

const VueltaGuardada* VueltasGuardadas::obtener(size_t i) const {
  return i < n_ ? &datos_[(inicio_ + i) % CAPACIDAD] : nullptr;
}

void VueltasGuardadas::confirmar(size_t n) {
  if (n > n_) n = n_;
  inicio_ = (inicio_ + n) % CAPACIDAD;
  n_ -= n;
}
