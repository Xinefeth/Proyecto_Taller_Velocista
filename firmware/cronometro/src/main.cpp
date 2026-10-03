// Cronómetro de meta · estructura base del firmware (EN-03)
//
// La marca de tiempo se toma en la interrupción con el reloj propio del ESP32 y el
// tiempo de vuelta se calcula con CalculadorVueltas (lib/vueltas, probado en PC).
// Pendiente en sus ítems: mensajes del contrato (EN-02), calibración de la barrera (EN-13),
// integración con la consola (EN-15).

#include <Arduino.h>
#include <WebSocketsClient.h>
#include <WiFi.h>
#include <esp_timer.h>

#include "vueltas.h"

#if __has_include("config.h")
#include "config.h"
#else
#error "Falta include/config.h: copia include/config.example.h como config.h"
#endif

static WebSocketsClient ws;
static CalculadorVueltas calculador(ANTIRREBOTE_US);
static volatile int64_t marcaIsr = 0;
static volatile bool hayCorte = false;

void IRAM_ATTR alCortarBarrera() {
  marcaIsr = esp_timer_get_time();
  hayCorte = true;
}

static void alEvento(WStype_t tipo, uint8_t*, size_t) {
  if (tipo == WStype_CONNECTED) Serial.println("[ws] conectado a la API");  // EN-02: identificarse
  if (tipo == WStype_DISCONNECTED) Serial.println("[ws] desconectado, reintentando");
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_RECEPTOR, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_RECEPTOR), alCortarBarrera, RISING);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  static String cabecera = String("X-Device-Token: ") + DEVICE_TOKEN;
  ws.setExtraHeaders(cabecera.c_str());
  ws.begin(API_HOST, API_PORT, API_RUTA);
  ws.onEvent(alEvento);
  ws.setReconnectInterval(2000);
  ws.enableHeartbeat(5000, 2000, 2);
}

void loop() {
  ws.loop();
  if (hayCorte) {
    noInterrupts();
    const int64_t marca = marcaIsr;
    hayCorte = false;
    interrupts();
    int64_t vueltaMs = 0;
    if (calculador.registrar(marca, vueltaMs)) {
      Serial.printf("[meta] corte %u · vuelta %lld ms\n", calculador.cortes(), static_cast<long long>(vueltaMs));
      // EN-02: enviar el corte a la API y guardarlo hasta recibir la confirmación.
    }
  }
}
