// Cronómetro de meta · firmware con el contrato de mensajes v1.0 (EN-02)
//
// La marca de tiempo se toma en la interrupción con el reloj propio del ESP32.
// El tiempo de vuelta es la resta entre dos cortes de este mismo reloj:
// no hace falta sincronizar relojes con la laptop ni con el robot.
// Cada corte se guarda hasta que la API confirma con ack y se reenvía cada 1 s.
// Especificación: docs/contrato-mensajes.md (sección 10)

#include <Arduino.h>
#include <ArduinoJson.h>
#include <WebSocketsClient.h>
#include <WiFi.h>
#include <esp_timer.h>

#include "vueltas.h"

#if __has_include("config.h")
#include "config.h"
#else
#error "Falta include/config.h: copia include/config.example.h como config.h"
#endif

struct Pendiente {
  uint32_t seq;
  String texto;
  uint32_t enviadoMs;
};

static const int CAPACIDAD = 32;
static Pendiente pendientes[CAPACIDAD];
static int nPendientes = 0;

static volatile int64_t marcaIsr = 0;
static volatile bool hayCorte = false;
static CalculadorVueltas calculador(ANTIRREBOTE_US);
static uint32_t seq = 0;
static WebSocketsClient ws;

void IRAM_ATTR alCortarBarrera() {
  marcaIsr = esp_timer_get_time();  // el antirrebote lo aplica CalculadorVueltas (lib/vueltas)
  hayCorte = true;
}

static void enviar(const char* tipo, JsonDocument& datos, bool conAck) {
  JsonDocument sobre;
  sobre["tipo"] = tipo;
  sobre["seq"] = ++seq;
  sobre["ts"] = millis();
  sobre["datos"] = datos;
  String texto;
  serializeJson(sobre, texto);
  if (ws.isConnected()) ws.sendTXT(texto);
  if (conAck) {
    if (nPendientes == CAPACIDAD) {  // descarta el más antiguo
      for (int i = 1; i < CAPACIDAD; i++) pendientes[i - 1] = pendientes[i];
      nPendientes--;
    }
    pendientes[nPendientes++] = {seq, texto, millis()};
  }
}

static void quitarPendiente(uint32_t s) {
  for (int i = 0; i < nPendientes; i++)
    if (pendientes[i].seq == s) {
      for (int j = i + 1; j < nPendientes; j++) pendientes[j - 1] = pendientes[j];
      nPendientes--;
      return;
    }
}

static void responderAck(uint32_t s) {
  JsonDocument sobre;
  sobre["tipo"] = "ack";
  sobre["seq"] = s;
  sobre["ts"] = millis();
  sobre["datos"]["ok"] = true;
  String texto;
  serializeJson(sobre, texto);
  ws.sendTXT(texto);
}

static const char* estadoBarrera() {
  // Con el haz recibido el TSOP da LOW; HIGH sostenido = algo tapa la barrera.
  static uint32_t altoDesde = 0;
  if (digitalRead(PIN_RECEPTOR) == LOW) {
    altoDesde = 0;
    return "ok";
  }
  if (!altoDesde) altoDesde = millis();
  return millis() - altoDesde > 1000 ? "bloqueada" : "ok";
}

static void alEvento(WStype_t tipo, uint8_t* carga, size_t largo) {
  if (tipo == WStype_CONNECTED) {
    int guardados = nPendientes;  // cortes que quedaron sin ack
    JsonDocument d;
    d["id"] = CRONOMETRO_ID;
    d["firmware"] = FIRMWARE_VERSION;
    d["contrato"] = CONTRATO_VERSION;
    d["antirrebote_ms"] = ANTIRREBOTE_US / 1000;
    enviar("hola", d, true);
    for (int i = 0; i < guardados; i++) ws.sendTXT(pendientes[i].texto);  // después del hola
  } else if (tipo == WStype_TEXT) {
    JsonDocument msg;
    if (deserializeJson(msg, carga, largo)) return;
    const char* t = msg["tipo"] | "";
    uint32_t s = msg["seq"] | 0;
    if (!strcmp(t, "ack")) {
      quitarPendiente(s);
    } else if (!strcmp(t, "rearmar")) {
      calculador.rearmar();  // el próximo corte es una salida
      responderAck(s);
    }
  }
}

void setup() {
  Serial.begin(115200);
#if USAR_EMISOR
  ledcSetup(0, 38000, 8);  // portadora de 38 kHz para el LED IR
  ledcAttachPin(PIN_EMISOR, 0);
  ledcWrite(0, 128);
#endif
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
  uint32_t ahora = millis();

  if (hayCorte) {
    noInterrupts();
    int64_t marca = marcaIsr;
    hayCorte = false;
    interrupts();

    int64_t vueltaMs = 0;
    if (!calculador.registrar(marca, vueltaMs)) return;  // rebote descartado
    JsonDocument d;
    d["n_corte"] = calculador.cortes();
    if (vueltaMs < 0) d["tiempo_vuelta_ms"] = nullptr;
    else d["tiempo_vuelta_ms"] = vueltaMs;
    d["marca_us"] = marca;
    Serial.printf("[meta] corte %u\n", calculador.cortes());
    enviar("corte", d, true);
  }

  static uint32_t tEstado = 0;
  if (ws.isConnected() && ahora - tEstado >= 5000) {
    tEstado = ahora;
    JsonDocument d;
    d["barrera"] = estadoBarrera();
    d["rssi_dbm"] = WiFi.RSSI();
    d["pendientes"] = nPendientes;
    enviar("estado", d, false);
  }

  if (ws.isConnected())
    for (int i = 0; i < nPendientes; i++)  // reintentos cada 1 s
      if (ahora - pendientes[i].enviadoMs >= 1000) {
        ws.sendTXT(pendientes[i].texto);
        pendientes[i].enviadoMs = ahora;
      }
}
