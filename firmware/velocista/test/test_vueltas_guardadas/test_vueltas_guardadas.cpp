#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unity.h>

#include "vueltas_guardadas.h"

void setUp() {}
void tearDown() {}

static VueltaGuardada vuelta(uint32_t id) { return {id, 18000 + id, 2.5f, 1, 7.9f}; }

void test_empieza_vacio() {
  VueltasGuardadas g;
  TEST_ASSERT_EQUAL_UINT32(0, g.cantidad());
  TEST_ASSERT_NULL(g.obtener(0));
  TEST_ASSERT_EQUAL_UINT32(0, g.descartadas());
}

void test_la_capacidad_es_la_del_contrato() {
  TEST_ASSERT_EQUAL_UINT32(50, VueltasGuardadas::CAPACIDAD);
}

void test_guarda_en_orden_de_la_mas_antigua_a_la_mas_nueva() {
  VueltasGuardadas g;
  for (uint32_t i = 1; i <= 3; i++) g.agregar(vuelta(i));
  TEST_ASSERT_EQUAL_UINT32(3, g.cantidad());
  TEST_ASSERT_EQUAL_UINT32(1, g.obtener(0)->id_vuelta);
  TEST_ASSERT_EQUAL_UINT32(3, g.obtener(2)->id_vuelta);
  TEST_ASSERT_NULL(g.obtener(3));
}

void test_conserva_todos_los_campos() {
  VueltasGuardadas g;
  g.agregar({4, 18110, 2.61f, 1, 7.91f});
  const VueltaGuardada* v = g.obtener(0);
  TEST_ASSERT_EQUAL_UINT32(4, v->id_vuelta);
  TEST_ASSERT_EQUAL_UINT32(18110, v->tiempo_interno_ms);
  TEST_ASSERT_FLOAT_WITHIN(0.001f, 2.61f, v->error_acumulado);
  TEST_ASSERT_EQUAL_UINT32(1, v->lineas_perdidas);
  TEST_ASSERT_FLOAT_WITHIN(0.001f, 7.91f, v->bateria_v);
}

void test_confirmar_quita_las_mas_antiguas() {
  VueltasGuardadas g;
  for (uint32_t i = 1; i <= 5; i++) g.agregar(vuelta(i));
  g.confirmar(2);
  TEST_ASSERT_EQUAL_UINT32(3, g.cantidad());
  TEST_ASSERT_EQUAL_UINT32(3, g.obtener(0)->id_vuelta);
}

void test_confirmar_de_mas_deja_la_cola_vacia() {
  VueltasGuardadas g;
  g.agregar(vuelta(1));
  g.confirmar(10);
  TEST_ASSERT_EQUAL_UINT32(0, g.cantidad());
  TEST_ASSERT_NULL(g.obtener(0));
}

void test_lleno_descarta_la_mas_antigua_y_la_cuenta() {
  VueltasGuardadas g;
  for (uint32_t i = 1; i <= 52; i++) g.agregar(vuelta(i));
  TEST_ASSERT_EQUAL_UINT32(50, g.cantidad());
  TEST_ASSERT_EQUAL_UINT32(2, g.descartadas());
  TEST_ASSERT_EQUAL_UINT32(3, g.obtener(0)->id_vuelta);
  TEST_ASSERT_EQUAL_UINT32(52, g.obtener(49)->id_vuelta);
}

void test_sigue_en_orden_despues_de_dar_la_vuelta_al_arreglo() {
  VueltasGuardadas g;
  for (uint32_t i = 1; i <= 50; i++) g.agregar(vuelta(i));
  g.confirmar(30);
  for (uint32_t i = 51; i <= 80; i++) g.agregar(vuelta(i));
  TEST_ASSERT_EQUAL_UINT32(50, g.cantidad());
  TEST_ASSERT_EQUAL_UINT32(0, g.descartadas());
  for (uint32_t i = 0; i < 50; i++) TEST_ASSERT_EQUAL_UINT32(31 + i, g.obtener(i)->id_vuelta);
}

void test_se_puede_reutilizar_tras_vaciarla() {
  VueltasGuardadas g;
  for (uint32_t i = 1; i <= 7; i++) g.agregar(vuelta(i));
  g.confirmar(7);
  g.agregar(vuelta(8));
  TEST_ASSERT_EQUAL_UINT32(1, g.cantidad());
  TEST_ASSERT_EQUAL_UINT32(8, g.obtener(0)->id_vuelta);
}

// ---------- Mensaje sync (contrato: docs/contrato/ejemplos/velocista.sync.json) ----------

static char texto[8192];

void test_sync_es_igual_al_ejemplo_del_contrato() {
  VueltasGuardadas g;
  g.agregar({4, 18110, 2.61f, 1, 7.91f});
  size_t enviadas = 99;
  size_t bytes = g.aSync(texto, sizeof(texto), 1204, 90400, enviadas);
  const char* esperado =
      "{\"tipo\":\"sync\",\"seq\":1204,\"ts\":90400,\"datos\":{\"vueltas\":[{\"id_vuelta\":4,"
      "\"tiempo_interno_ms\":18110,\"error_acumulado\":2.61,\"lineas_perdidas\":1,"
      "\"bateria_v\":7.91}]}}";
  TEST_ASSERT_EQUAL_STRING(esperado, texto);
  TEST_ASSERT_EQUAL_UINT32(strlen(esperado), bytes);
  TEST_ASSERT_EQUAL_UINT32(1, enviadas);
}

void test_sync_lleva_las_vueltas_de_la_mas_antigua_a_la_mas_nueva() {
  VueltasGuardadas g;
  for (uint32_t i = 3; i <= 5; i++) g.agregar(vuelta(i));
  size_t enviadas = 0;
  g.aSync(texto, sizeof(texto), 1, 1, enviadas);
  TEST_ASSERT_EQUAL_UINT32(3, enviadas);
  const char* a = strstr(texto, "\"id_vuelta\":3");
  const char* b = strstr(texto, "\"id_vuelta\":4");
  const char* c = strstr(texto, "\"id_vuelta\":5");
  TEST_ASSERT_NOT_NULL(a);
  TEST_ASSERT_TRUE(a < b && b < c);
}

void test_sync_respeta_el_maximo_y_solo_se_confirman_las_enviadas() {
  VueltasGuardadas g;
  for (uint32_t i = 1; i <= 10; i++) g.agregar(vuelta(i));
  size_t enviadas = 0;
  TEST_ASSERT_TRUE(g.aSync(texto, sizeof(texto), 1, 1, enviadas, 4) > 0);
  TEST_ASSERT_EQUAL_UINT32(4, enviadas);
  TEST_ASSERT_NULL(strstr(texto, "\"id_vuelta\":5"));
  g.confirmar(enviadas);
  TEST_ASSERT_EQUAL_UINT32(6, g.cantidad());
  TEST_ASSERT_EQUAL_UINT32(5, g.obtener(0)->id_vuelta);
}

void test_sync_no_escribe_nada_si_no_hay_vueltas_o_no_cabe() {
  VueltasGuardadas g;
  size_t enviadas = 7;
  TEST_ASSERT_EQUAL_UINT32(0, g.aSync(texto, sizeof(texto), 1, 1, enviadas));
  TEST_ASSERT_EQUAL_UINT32(0, enviadas);
  for (uint32_t i = 1; i <= 3; i++) g.agregar(vuelta(i));
  char chico[60];
  strcpy(chico, "basura");
  TEST_ASSERT_EQUAL_UINT32(0, g.aSync(chico, sizeof(chico), 1, 1, enviadas));
  TEST_ASSERT_EQUAL_UINT32(0, enviadas);
  TEST_ASSERT_EQUAL_CHAR('\0', chico[0]);     // nunca queda un mensaje a medias
  TEST_ASSERT_EQUAL_UINT32(3, g.cantidad());  // y no se pierde nada
}

void test_sync_con_las_50_vueltas_cabe_en_un_solo_mensaje() {
  VueltasGuardadas g;
  for (uint32_t i = 1; i <= 50; i++) g.agregar(vuelta(i));
  size_t enviadas = 0;
  TEST_ASSERT_TRUE(g.aSync(texto, sizeof(texto), 1, 1, enviadas) > 0);
  TEST_ASSERT_EQUAL_UINT32(50, enviadas);
}

// ---------- Simulación: el Wi-Fi se cae y vuelve, sin placa ni red ----------
// Un robot falso cierra vueltas: con Wi-Fi las manda al instante y sin Wi-Fi las guarda. Al
// reconectar manda un `sync` con todo lo guardado. Una API falsa anota cada id_vuelta que recibe,
// ignora las repetidas y responde con ack.

struct ApiFalsa {
  uint32_t recibidas[300];
  size_t n = 0;
  size_t repetidas = 0;
  size_t mensajesSync = 0;

  void anotar(uint32_t id) {
    for (size_t i = 0; i < n; i++)
      if (recibidas[i] == id) {
        repetidas++;
        return;
      }
    recibidas[n++] = id;
  }
  void recibirSync(const char* json) {
    mensajesSync++;
    const char* p = json;
    while ((p = strstr(p, "\"id_vuelta\":")) != nullptr) {
      p += strlen("\"id_vuelta\":");
      anotar(static_cast<uint32_t>(strtoul(p, nullptr, 10)));
    }
  }
};

struct RobotFalso {
  VueltasGuardadas guardadas;
  ApiFalsa& api;
  bool wifi = true;
  bool seRompeElAck = false;
  uint32_t seq = 0;

  explicit RobotFalso(ApiFalsa& a) : api(a) {}

  void cerrarVuelta(uint32_t id) {
    if (wifi)
      api.anotar(id);
    else
      guardadas.agregar(vuelta(id));
  }
  void caeElWifi() { wifi = false; }
  void vuelveElWifi() {
    wifi = true;
    char buffer[8192];
    size_t enviadas = 0;
    if (guardadas.aSync(buffer, sizeof(buffer), ++seq, 1000, enviadas) == 0) return;
    api.recibirSync(buffer);
    if (!seRompeElAck) guardadas.confirmar(enviadas);  // solo se borra lo que la API confirmó
  }
};

void test_simulacion_una_caida_del_wifi_no_pierde_vueltas() {
  ApiFalsa api;
  RobotFalso robot(api);
  TEST_MESSAGE("Con Wi-Fi: las vueltas 1 y 2 llegan a la API al instante");
  robot.cerrarVuelta(1);
  robot.cerrarVuelta(2);
  TEST_MESSAGE("Se cae el Wi-Fi: las vueltas 3, 4 y 5 se guardan en el robot");
  robot.caeElWifi();
  robot.cerrarVuelta(3);
  robot.cerrarVuelta(4);
  robot.cerrarVuelta(5);
  TEST_ASSERT_EQUAL_UINT32(2, api.n);
  TEST_ASSERT_EQUAL_UINT32(3, robot.guardadas.cantidad());
  TEST_MESSAGE("Vuelve el Wi-Fi: el robot manda un sync con las 3 guardadas y la API confirma");
  robot.vuelveElWifi();
  TEST_ASSERT_EQUAL_UINT32(1, api.mensajesSync);
  TEST_ASSERT_EQUAL_UINT32(0, robot.guardadas.cantidad());
  TEST_MESSAGE("Vuelta 6 con Wi-Fi: llega normal");
  robot.cerrarVuelta(6);
  TEST_ASSERT_EQUAL_UINT32(6, api.n);
  for (uint32_t i = 0; i < 6; i++) TEST_ASSERT_EQUAL_UINT32(i + 1, api.recibidas[i]);
  TEST_ASSERT_EQUAL_UINT32(0, api.repetidas);
  TEST_MESSAGE("Resultado: la API tiene las vueltas 1 a 6, en orden y sin repetir");
}

void test_simulacion_si_se_pierde_el_ack_no_se_borra_y_se_reenvia() {
  ApiFalsa api;
  RobotFalso robot(api);
  robot.caeElWifi();
  robot.cerrarVuelta(1);
  robot.cerrarVuelta(2);
  TEST_MESSAGE("Vuelve el Wi-Fi, pero el ack se pierde: el robot conserva las 2 vueltas");
  robot.seRompeElAck = true;
  robot.vuelveElWifi();
  TEST_ASSERT_EQUAL_UINT32(2, robot.guardadas.cantidad());
  TEST_MESSAGE("Se reconecta otra vez y esta vez el ack llega: se borran");
  robot.seRompeElAck = false;
  robot.vuelveElWifi();
  TEST_ASSERT_EQUAL_UINT32(0, robot.guardadas.cantidad());
  TEST_MESSAGE("La API recibio el sync dos veces pero ignoro las repetidas");
  TEST_ASSERT_EQUAL_UINT32(2, api.mensajesSync);
  TEST_ASSERT_EQUAL_UINT32(2, api.n);
  TEST_ASSERT_EQUAL_UINT32(2, api.repetidas);
}

void test_simulacion_una_caida_larga_conserva_las_50_vueltas_mas_recientes() {
  ApiFalsa api;
  RobotFalso robot(api);
  robot.caeElWifi();
  for (uint32_t i = 1; i <= 120; i++) robot.cerrarVuelta(i);
  TEST_MESSAGE("120 vueltas sin Wi-Fi: caben 50; se pierden las 70 mas antiguas");
  TEST_ASSERT_EQUAL_UINT32(50, robot.guardadas.cantidad());
  TEST_ASSERT_EQUAL_UINT32(70, robot.guardadas.descartadas());
  robot.vuelveElWifi();
  TEST_ASSERT_EQUAL_UINT32(50, api.n);
  TEST_ASSERT_EQUAL_UINT32(71, api.recibidas[0]);
  TEST_ASSERT_EQUAL_UINT32(120, api.recibidas[49]);
  TEST_ASSERT_EQUAL_UINT32(0, robot.guardadas.cantidad());
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_empieza_vacio);
  RUN_TEST(test_la_capacidad_es_la_del_contrato);
  RUN_TEST(test_guarda_en_orden_de_la_mas_antigua_a_la_mas_nueva);
  RUN_TEST(test_conserva_todos_los_campos);
  RUN_TEST(test_confirmar_quita_las_mas_antiguas);
  RUN_TEST(test_confirmar_de_mas_deja_la_cola_vacia);
  RUN_TEST(test_lleno_descarta_la_mas_antigua_y_la_cuenta);
  RUN_TEST(test_sigue_en_orden_despues_de_dar_la_vuelta_al_arreglo);
  RUN_TEST(test_se_puede_reutilizar_tras_vaciarla);
  RUN_TEST(test_sync_es_igual_al_ejemplo_del_contrato);
  RUN_TEST(test_sync_lleva_las_vueltas_de_la_mas_antigua_a_la_mas_nueva);
  RUN_TEST(test_sync_respeta_el_maximo_y_solo_se_confirman_las_enviadas);
  RUN_TEST(test_sync_no_escribe_nada_si_no_hay_vueltas_o_no_cabe);
  RUN_TEST(test_sync_con_las_50_vueltas_cabe_en_un_solo_mensaje);
  RUN_TEST(test_simulacion_una_caida_del_wifi_no_pierde_vueltas);
  RUN_TEST(test_simulacion_si_se_pierde_el_ack_no_se_borra_y_se_reenvia);
  RUN_TEST(test_simulacion_una_caida_larga_conserva_las_50_vueltas_mas_recientes);
  return UNITY_END();
}
