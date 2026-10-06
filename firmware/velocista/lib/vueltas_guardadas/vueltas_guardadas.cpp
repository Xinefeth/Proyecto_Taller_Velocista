#include "vueltas_guardadas.h"

#include <stdarg.h>
#include <stdio.h>

namespace {

// Escribe con formato a continuación de lo ya escrito. Devuelve false si no cabe.
bool escribir(char* destino, size_t capacidad, size_t& usado, const char* formato, ...) {
  if (usado >= capacidad) return false;
  va_list args;
  va_start(args, formato);
  const int n = vsnprintf(destino + usado, capacidad - usado, formato, args);
  va_end(args);
  if (n < 0 || static_cast<size_t>(n) >= capacidad - usado) return false;
  usado += static_cast<size_t>(n);
  return true;
}

}  // namespace

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

size_t VueltasGuardadas::aSync(char* destino, size_t capacidad, uint32_t seq, uint32_t ts,
                               size_t& enviadas, size_t maximo) const {
  enviadas = 0;
  if (n_ == 0 || maximo == 0 || destino == nullptr) return 0;
  const size_t tope = CAPACIDAD;
  const size_t limite = maximo < tope ? maximo : tope;
  const size_t cuantas = n_ < limite ? n_ : limite;
  size_t usado = 0;
  bool cabe = escribir(destino, capacidad, usado,
                       "{\"tipo\":\"sync\",\"seq\":%lu,\"ts\":%lu,\"datos\":{\"vueltas\":[",
                       static_cast<unsigned long>(seq), static_cast<unsigned long>(ts));
  for (size_t i = 0; i < cuantas && cabe; i++) {
    const VueltaGuardada& v = *obtener(i);
    cabe = escribir(
        destino, capacidad, usado,
        "%s{\"id_vuelta\":%lu,\"tiempo_interno_ms\":%lu,\"error_acumulado\":%.2f,"
        "\"lineas_perdidas\":%lu,\"bateria_v\":%.2f}",
        i == 0 ? "" : ",", static_cast<unsigned long>(v.id_vuelta),
        static_cast<unsigned long>(v.tiempo_interno_ms), static_cast<double>(v.error_acumulado),
        static_cast<unsigned long>(v.lineas_perdidas), static_cast<double>(v.bateria_v));
  }
  if (cabe) cabe = escribir(destino, capacidad, usado, "]}}");
  if (!cabe) {  // no cabe: no se entrega un mensaje a medias
    destino[0] = '\0';
    return 0;
  }
  enviadas = cuantas;
  return usado;
}
