// Copia este archivo como config.h (está en .gitignore) y completa tus datos.
#pragma once

#define WIFI_SSID "APAEC-LAB"
#define WIFI_PASS "clave-del-router"

#define API_HOST "192.168.50.10"
#define API_PORT 8000
#define API_RUTA "/ws/cronometro"

// Debe coincidir con DEVICE_TOKEN_CRONOMETRO del .env de la API.
#define DEVICE_TOKEN "dev-token-cronometro"

#define FIRMWARE_VERSION "0.1.0"

#define PIN_RECEPTOR 27         // salida del receptor TSOP (HIGH = haz cortado)
#define ANTIRREBOTE_US 2000000  // tiempo mínimo entre dos cortes válidos
