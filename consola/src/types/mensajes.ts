// Sobre que la API reenvía a la consola por /ws/consola.
// Los tipos de cada mensaje de dispositivo se agregan con el contrato EN-02.

export interface MensajeConsola<T = Record<string, unknown>> {
  origen: "velocista" | "cronometro" | "api";
  tipo: string;
  datos: T;
  recibido_ms: number;
}
