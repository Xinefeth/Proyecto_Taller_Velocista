// Copia este archivo como config.h (está en .gitignore) y completa tus datos.
#pragma once

#define WIFI_SSID "APAEC-LAB"
#define WIFI_PASS "clave-del-router"

#define API_HOST "192.168.50.10"
#define API_PORT 8000
#define API_RUTA "/ws/cronometro"

// Debe coincidir con DEVICE_TOKEN_CRONOMETRO del .env de la API.
#define DEVICE_TOKEN "dev-token-cronometro"

#define CRONOMETRO_ID "meta_01"
#define FIRMWARE_VERSION "0.2.0"
#define CONTRATO_VERSION "1.0"

#define PIN_RECEPTOR 27         // salida del receptor TSOP (HIGH = haz cortado)
#define PIN_EMISOR 26           // LED IR del emisor, si lo alimenta este mismo ESP32
#define USAR_EMISOR 1           // 0 si el emisor tiene su propio circuito de 38 kHz
#define ANTIRREBOTE_US 2000000  // tiempo mínimo entre dos cortes válidos
