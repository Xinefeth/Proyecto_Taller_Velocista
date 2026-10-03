// Velocista 001 · estructura base del firmware (EN-03)
//
// Núcleo 1: lazo de control a 1000 Hz. Nunca espera a la red.
// Núcleo 0: Wi-Fi y conexión WebSocket con la API.
//
// Pendiente en sus ítems: mensajes del contrato (EN-02, EN-12), lectura de la regleta
// y controlador (EN-10), batería (EN-09).

#include <Arduino.h>
#include <WebSocketsClient.h>
#include <WiFi.h>

#include "linea.h"

#if __has_include("config.h")
#include "config.h"
#else
#error "Falta include/config.h: copia include/config.example.h como config.h"
#endif

static WebSocketsClient ws;
static volatile uint32_t lazoHz = 0;

// ---------- Núcleo 1: control ----------
static void tareaControl(void*) {
  uint16_t lecturas[linea::CANALES] = {0};
  float error = 0;
  TickType_t ultimo = xTaskGetTickCount();
  uint32_t ciclos = 0, inicio = millis();
  for (;;) {
    // EN-10: leer los 16 canales por el multiplexor en `lecturas` y aplicar el controlador.
    linea::calcularError(lecturas, false, 300, error);
    ciclos++;
    if (millis() - inicio >= 1000) {
      lazoHz = ciclos;
      ciclos = 0;
      inicio = millis();
    }
    vTaskDelayUntil(&ultimo, pdMS_TO_TICKS(1));  // 1 ms = 1000 Hz
  }
}

// ---------- Núcleo 0: comunicación ----------
static void alEvento(WStype_t tipo, uint8_t* carga, size_t largo) {
  switch (tipo) {
    case WStype_CONNECTED:
      Serial.println("[ws] conectado a la API");  // EN-02: enviar el manifiesto aquí
      break;
    case WStype_DISCONNECTED:
      Serial.println("[ws] desconectado, reintentando");
      break;
    case WStype_TEXT:
      Serial.printf("[ws] recibido %u bytes\n", static_cast<unsigned>(largo));  // EN-02: comandos
      break;
    default:
      break;
  }
}

static void tareaRed(void*) {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) vTaskDelay(pdMS_TO_TICKS(250));
  Serial.printf("[wifi] conectado, IP %s\n", WiFi.localIP().toString().c_str());

  static String cabecera = String("X-Device-Token: ") + DEVICE_TOKEN;
  ws.setExtraHeaders(cabecera.c_str());
  ws.begin(API_HOST, API_PORT, API_RUTA);
  ws.onEvent(alEvento);
  ws.setReconnectInterval(2000);
  ws.enableHeartbeat(5000, 2000, 2);

  for (;;) {
    ws.loop();
    vTaskDelay(pdMS_TO_TICKS(2));
  }
}

void setup() {
  Serial.begin(115200);
  xTaskCreatePinnedToCore(tareaControl, "control", 4096, nullptr, 5, nullptr, 1);
  xTaskCreatePinnedToCore(tareaRed, "red", 8192, nullptr, 2, nullptr, 0);
}

void loop() { vTaskDelete(nullptr); }  // todo corre en las dos tareas
