#include "vueltas.h"

bool CalculadorVueltas::registrar(int64_t marcaUs, int64_t& vueltaMs) {
  if (ultimo_ >= 0 && marcaUs - ultimo_ < antirrebote_) return false;
  vueltaMs = ultimo_ < 0 ? -1 : (marcaUs - ultimo_) / 1000;
  ultimo_ = marcaUs;
  cortes_++;
  return true;
}
