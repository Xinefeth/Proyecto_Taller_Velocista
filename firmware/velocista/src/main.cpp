// Velocista 001 · firmware con el contrato de mensajes v1.0 (EN-02)
//
// Núcleo 1: lazo de control a 1000 Hz. Nunca espera a la red.
// Núcleo 0: Wi-Fi + WebSocket con la API.
//
// Especificación: docs/contrato/ · Modelos de referencia: api/app/contrato/
// Pendiente en sus historias: lectura real de la regleta y controlador (EN-10),
// batería (EN-09), vueltas sin enlace y sync (EN-12).

#include <Arduino.h>
#include <ArduinoJson.h>
#include <WebSocketsClient.h>
#include <WiFi.h>

#include "linea.h"

#if __has_include("config.h")
#include "config.h"
#else
#error "Falta include/config.h: copia include/config.example.h como config.h"
#endif

// ---------- Parámetros del controlador: son la fuente del manifiesto ----------
// Los rangos son provisionales; se calibran en pista (EN-10).
struct Parametro {
  const char* nombre;
  const char* etiqueta;
  bool entero;
  float min, max, paso, valor;
  const char* unidad;
  bool optimizable;
};

static Parametro paramsPid[] = {
    {"kp", "Kp", false, 0, 2, 0.01, 0.35, "", true},
    {"ki", "Ki", false, 0, 0.5, 0.001, 0, "", true},
    {"kd", "Kd", false, 0, 20, 0.1, 6, "", true},
    {"vel_base", "Velocidad base", true, 0, 255, 1, 160, "pwm", true},
};
static const size_t N_PID = sizeof(paramsPid) / sizeof(paramsPid[0]);

// ---------- Estado compartido entre núcleos ----------
enum class Estado { Listo, Calibrando, Corriendo, Detenido, Error };

struct Compartido {
  Estado estado = Estado::Listo;
  bool calibrado = false;
  bool modoCompetencia = false;
  bool lineaBlanca = false;
  float error = 0;
  int pwmIzq = 0, pwmDer = 0;
  uint16_t regleta[16] = {0};
  uint32_t lazoHz = 0;
  // Acumuladores de la vuelta en curso (se reinician en cada cierre_vuelta)
  float errorAcumulado = 0;
  uint32_t lineasPerdidas = 0;
  uint32_t inicioVueltaMs = 0;
};

static Compartido robot;
static portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;
static WebSocketsClient ws;
static uint32_t seq = 0;

// Mensajes que requieren ack: se reenvían cada 1 s hasta que la API confirma.
struct Pendiente {
  uint32_t seq;
  String texto;
  uint32_t enviadoMs;
};
static Pendiente pendientes[8];
static int nPendientes = 0;

static const char* nombreEstado(Estado e) {
  switch (e) {
    case Estado::Listo: return "listo";
    case Estado::Calibrando: return "calibrando";
    case Estado::Corriendo: return "corriendo";
    case Estado::Detenido: return "detenido";
    default: return "error";
  }
}

static float leerBateria() { return 8.0f; }  // TODO(EN-09): divisor resistivo en un ADC

// ---------- Núcleo 1: control ----------
static void tareaControl(void*) {
  uint16_t lecturas[linea::CANALES] = {0};
  TickType_t ultimo = xTaskGetTickCount();
  uint32_t ciclos = 0, inicioSegundo = millis();
  bool lineaVista = true;
  for (;;) {
    // EN-10: leer los 16 canales por el multiplexor en `lecturas`, aplicar el PID con
    // paramsPid y escribir PWM compensado por batería.
    portENTER_CRITICAL(&mux);
    const bool blanca = robot.lineaBlanca;
    portEXIT_CRITICAL(&mux);
    float error = 0;
    const bool detectada = linea::calcularError(lecturas, blanca, 300, error);

    portENTER_CRITICAL(&mux);
    for (int i = 0; i < linea::CANALES; i++) robot.regleta[i] = lecturas[i];
    if (detectada) robot.error = error;
    if (robot.estado == Estado::Corriendo) {
      robot.errorAcumulado += fabsf(robot.error) * 0.001f;  // IAE con dt = 1 ms
      if (lineaVista && !detectada) robot.lineasPerdidas++;
    } else {
      robot.pwmIzq = robot.pwmDer = 0;
    }
    portEXIT_CRITICAL(&mux);
    lineaVista = detectada;

    ciclos++;
    if (millis() - inicioSegundo >= 1000) {
      portENTER_CRITICAL(&mux);
      robot.lazoHz = ciclos;
      portEXIT_CRITICAL(&mux);
      ciclos = 0;
      inicioSegundo = millis();
    }
    vTaskDelayUntil(&ultimo, pdMS_TO_TICKS(1));
  }
}

// ---------- Núcleo 0: comunicación ----------
static Compartido copiar() {
  portENTER_CRITICAL(&mux);
  Compartido c = robot;
  portEXIT_CRITICAL(&mux);
  return c;
}

static uint32_t enviar(const char* tipo, JsonDocument& datos, bool conAck) {
  JsonDocument sobre;
  sobre["tipo"] = tipo;
  sobre["seq"] = ++seq;
  sobre["ts"] = millis();
  sobre["datos"] = datos;
  String texto;
  serializeJson(sobre, texto);
  ws.sendTXT(texto);
  if (conAck) {
    if (nPendientes == 8) {  // descarta el más antiguo
      for (int i = 1; i < 8; i++) pendientes[i - 1] = pendientes[i];
      nPendientes--;
    }
    pendientes[nPendientes++] = {seq, texto, millis()};
  }
  return seq;
}

static void responderAck(uint32_t seqConfirmado, const char* motivo, const char* detalle) {
  JsonDocument sobre;
  sobre["tipo"] = "ack";
  sobre["seq"] = seqConfirmado;
  sobre["ts"] = millis();
  JsonObject d = sobre["datos"].to<JsonObject>();
  d["ok"] = motivo == nullptr;
  if (motivo) {
    d["motivo"] = motivo;
    if (detalle) d["detalle"] = detalle;
  }
  String texto;
  serializeJson(sobre, texto);
  ws.sendTXT(texto);
}

static void enviarEvento(const char* codigo, const char* nivel, const char* mensaje) {
  JsonDocument d;
  d["codigo"] = codigo;
  d["nivel"] = nivel;
  d["mensaje"] = mensaje;
  d["datos"].to<JsonObject>();
  enviar("evento", d, true);
}

static void agregarCanal(JsonArray canales, const char* nombre, const char* desc, const char* tipo,
                         const char* unidad, float min, float max, const char* grupo,
                         int longitud = 0) {
  JsonObject c = canales.add<JsonObject>();
  c["nombre"] = nombre;
  c["descripcion"] = desc;
  c["tipo"] = tipo;
  if (longitud) c["longitud"] = longitud;
  c["unidad"] = unidad;
  c["min"] = min;
  c["max"] = max;
  c["grupo"] = grupo;
}

static void enviarManifiesto() {
  JsonDocument d;
  d["contrato"] = CONTRATO_VERSION;
  d["id"] = ROBOT_ID;
  d["tipo_robot"] = "velocista";
  d["firmware"] = FIRMWARE_VERSION;

  JsonArray sensores = d["sensores"].to<JsonArray>();
  JsonObject regleta = sensores.add<JsonObject>();
  regleta["nombre"] = "regleta";
  regleta["modelo"] = "2 x QTR-8A";
  regleta["canales"].add("regleta");
  regleta["canales"].add("error");
  regleta["detalles"]["canales_fisicos"] = 16;
  regleta["detalles"]["multiplexor"] = true;
  JsonObject bateria = sensores.add<JsonObject>();
  bateria["nombre"] = "bateria";
  bateria["modelo"] = "divisor resistivo";
  bateria["canales"].add("bateria_v");

  JsonArray actuadores = d["actuadores"].to<JsonArray>();
  const char* motores[][2] = {{"motor_izq", "pwm_izq"}, {"motor_der", "pwm_der"}};
  for (auto& m : motores) {
    JsonObject a = actuadores.add<JsonObject>();
    a["nombre"] = m[0];
    a["tipo"] = "motor_dc";
    a["canales"].add(m[1]);
  }

  JsonArray canales = d["canales"].to<JsonArray>();
  agregarCanal(canales, "bateria_v", "Voltaje de la batería", "float", "V", 0, 9, "estado");
  agregarCanal(canales, "error", "Posición de la línea respecto al centro, normalizada", "float",
               "", -1, 1, "senales");
  agregarCanal(canales, "regleta", "Lecturas calibradas de los 16 sensores", "int[]", "", 0,
               1000, "senales", 16);
  agregarCanal(canales, "pwm_izq", "PWM aplicado al motor izquierdo", "int", "pwm", -255, 255,
               "senales");
  agregarCanal(canales, "pwm_der", "PWM aplicado al motor derecho", "int", "pwm", -255, 255,
               "senales");

  JsonObject pid = d["controladores"].to<JsonArray>().add<JsonObject>();
  pid["nombre"] = "pid";
  pid["descripcion"] = "PID clásico con velocidad base fija";
  JsonArray ps = pid["parametros"].to<JsonArray>();
  for (size_t i = 0; i < N_PID; i++) {
    const Parametro& p = paramsPid[i];
    JsonObject o = ps.add<JsonObject>();
    o["nombre"] = p.nombre;
    o["etiqueta"] = p.etiqueta;
    o["tipo"] = p.entero ? "int" : "float";
    o["min"] = p.min;
    o["max"] = p.max;
    o["paso"] = p.paso;
    o["valor"] = p.valor;
    o["unidad"] = p.unidad;
    o["optimizable"] = p.optimizable;
  }
  d["controlador_activo"] = "pid";

  JsonArray comandos = d["comandos"].to<JsonArray>();
  for (const char* c : {"calibrar", "arrancar", "detener", "setup", "modo", "linea", "cierre_vuelta"})
    comandos.add(c);
  d["frecuencias"]["lazo_hz"] = 1000;
  d["frecuencias"]["estado_hz"] = 1;
  d["frecuencias"]["senales_hz"] = 20;
  d["arranque"] = "comando";
  d["compensa_bateria"] = true;
  enviar("manifiesto", d, true);
}

static void enviarEstado() {
  Compartido c = copiar();
  JsonDocument d;
  d["estado"] = nombreEstado(c.estado);
  d["calibrado"] = c.calibrado;
  d["modo"] = c.modoCompetencia ? "competencia" : "prueba";
  d["linea"] = c.lineaBlanca ? "blanca" : "negra";
  d["controlador"] = "pid";
  d["lazo_hz"] = c.lazoHz;
  d["rssi_dbm"] = WiFi.RSSI();
  d["canales"]["bateria_v"] = leerBateria();
  enviar("estado", d, false);
}

static void enviarSenales() {
  Compartido c = copiar();
  JsonDocument d;
  d["t_ms"] = millis();
  JsonObject can = d["canales"].to<JsonObject>();
  can["error"] = c.error;
  JsonArray r = can["regleta"].to<JsonArray>();
  for (uint16_t v : c.regleta) r.add(v);
  can["pwm_izq"] = c.pwmIzq;
  can["pwm_der"] = c.pwmDer;
  enviar("senales", d, false);
}

static void cerrarVuelta(int idVuelta) {
  portENTER_CRITICAL(&mux);
  Compartido c = robot;
  robot.errorAcumulado = 0;
  robot.lineasPerdidas = 0;
  robot.inicioVueltaMs = millis();
  portEXIT_CRITICAL(&mux);
  JsonDocument d;
  d["id_vuelta"] = idVuelta;
  d["tiempo_interno_ms"] = millis() - c.inicioVueltaMs;
  d["error_acumulado"] = c.errorAcumulado;
  d["lineas_perdidas"] = c.lineasPerdidas;
  d["bateria_v"] = leerBateria();
  enviar("vuelta", d, true);  // TODO(EN-12): guardar para sync si no hay enlace
}

// Aplica un setup solo si todos los parámetros existen y están en rango.
static const char* aplicarSetup(JsonObject datos, String& detalle) {
  if (strcmp(datos["controlador"] | "", "pid") != 0) return "controlador_no_disponible";
  JsonObject nuevos = datos["parametros"];
  for (JsonPair kv : nuevos) {
    const Parametro* p = nullptr;
    for (size_t i = 0; i < N_PID; i++)
      if (strcmp(paramsPid[i].nombre, kv.key().c_str()) == 0) p = &paramsPid[i];
    if (!p) { detalle = kv.key().c_str(); return "parametro_desconocido"; }
    float v = kv.value().as<float>();
    if (v < p->min || v > p->max || (p->entero && v != floorf(v))) {
      detalle = kv.key().c_str();
      return "fuera_de_rango";
    }
  }
  portENTER_CRITICAL(&mux);
  for (JsonPair kv : nuevos)
    for (size_t i = 0; i < N_PID; i++)
      if (strcmp(paramsPid[i].nombre, kv.key().c_str()) == 0) paramsPid[i].valor = kv.value().as<float>();
  portEXIT_CRITICAL(&mux);
  return nullptr;
}

// Devuelve el motivo de rechazo, o nullptr si se aceptó.
static const char* atenderComando(const char* tipo, JsonObject datos, String& detalle) {
  Compartido c = copiar();
  if (c.modoCompetencia && c.estado == Estado::Corriendo && strcmp(tipo, "detener") != 0 &&
      strcmp(tipo, "cierre_vuelta") != 0)
    return "bloqueado_competencia";

  if (!strcmp(tipo, "calibrar")) {
    if (c.estado == Estado::Corriendo) return "ocupado";
    portENTER_CRITICAL(&mux);
    robot.calibrado = true;  // TODO(EN-10): rutina real de calibración
    robot.estado = Estado::Listo;
    portEXIT_CRITICAL(&mux);
    enviarEvento("calibracion_ok", "info", "Calibración terminada");
  } else if (!strcmp(tipo, "arrancar")) {
    if (!c.calibrado) return "no_calibrado";
    portENTER_CRITICAL(&mux);
    robot.estado = Estado::Corriendo;
    robot.inicioVueltaMs = millis();
    robot.errorAcumulado = 0;
    portEXIT_CRITICAL(&mux);
    enviarEvento("arranque", "info", "El robot empezó a correr");
  } else if (!strcmp(tipo, "detener")) {
    portENTER_CRITICAL(&mux);
    robot.estado = Estado::Detenido;
    portEXIT_CRITICAL(&mux);
    enviarEvento("detencion", "info", "El robot se detuvo");
  } else if (!strcmp(tipo, "setup")) {
    const char* motivo = aplicarSetup(datos, detalle);
    if (motivo) return motivo;
    enviarEvento("setup_aplicado", "info", "Setup cargado");
  } else if (!strcmp(tipo, "modo")) {
    portENTER_CRITICAL(&mux);
    robot.modoCompetencia = strcmp(datos["modo"] | "prueba", "competencia") == 0;
    portEXIT_CRITICAL(&mux);
  } else if (!strcmp(tipo, "linea")) {
    portENTER_CRITICAL(&mux);
    robot.lineaBlanca = strcmp(datos["color"] | "negra", "blanca") == 0;
    portEXIT_CRITICAL(&mux);
  } else if (!strcmp(tipo, "cierre_vuelta")) {
    cerrarVuelta(datos["id_vuelta"] | 1);
  } else {
    return "comando_desconocido";
  }
  return nullptr;
}

static void alEvento(WStype_t tipo, uint8_t* carga, size_t largo) {
  switch (tipo) {
    case WStype_CONNECTED:
      Serial.println("[ws] conectado a la API");
      enviarManifiesto();  // siempre el primer mensaje; lo pendiente se reintenta después
      break;
    case WStype_DISCONNECTED:
      Serial.println("[ws] desconectado, reintentando");
      break;
    case WStype_TEXT: {
      JsonDocument msg;
      if (deserializeJson(msg, carga, largo)) return;
      const char* t = msg["tipo"] | "";
      uint32_t s = msg["seq"] | 0;
      if (!strcmp(t, "ack")) {  // la API confirmó un mensaje nuestro
        for (int i = 0; i < nPendientes; i++)
          if (pendientes[i].seq == s) {
            for (int j = i + 1; j < nPendientes; j++) pendientes[j - 1] = pendientes[j];
            nPendientes--;
            break;
          }
        return;
      }
      String detalle;
      const char* motivo = atenderComando(t, msg["datos"].as<JsonObject>(), detalle);
      responderAck(s, motivo, detalle.length() ? detalle.c_str() : nullptr);
      break;
    }
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

  uint32_t tEstado = 0, tSenales = 0;
  for (;;) {
    ws.loop();
    uint32_t ahora = millis();
    if (ws.isConnected()) {
      if (ahora - tEstado >= 1000) {
        tEstado = ahora;
        enviarEstado();
      }
      if (copiar().estado == Estado::Corriendo && ahora - tSenales >= 50) {
        tSenales = ahora;
        enviarSenales();
      }
      for (int i = 0; i < nPendientes; i++)  // reintentos cada 1 s
        if (ahora - pendientes[i].enviadoMs >= 1000) {
          ws.sendTXT(pendientes[i].texto);
          pendientes[i].enviadoMs = ahora;
        }
    }
    vTaskDelay(pdMS_TO_TICKS(2));
  }
}

void setup() {
  Serial.begin(115200);
  xTaskCreatePinnedToCore(tareaControl, "control", 4096, nullptr, 5, nullptr, 1);
  xTaskCreatePinnedToCore(tareaRed, "red", 12288, nullptr, 2, nullptr, 0);
}

void loop() { vTaskDelete(nullptr); }
