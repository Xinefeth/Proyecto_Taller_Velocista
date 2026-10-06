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
  return UNITY_END();
}
